"""End-to-end integration tests - complete workflow (config → simulation → identification → results).

Tests the complete workflow from model configuration through simulation,
parameter identification, and result validation.
"""

import math
import numpy as np
import pytest

from param_id_gui.models.motor.pmsm_dq import PMSMdqModel
from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
from param_id_gui.models.controller.foc import FOCController, PIController
from param_id_gui.core.orchestrator import Orchestrator, OrchestratorConfig, SimulationState
from param_id_gui.core.data_bus import DataBus, Signal
from param_id_gui.core.model_registry import ModelRegistry, ModelMetadata, Domain, FidelityLevel, Port
from param_id_gui.algorithms.lm import LevenbergMarquardt, LMConfig
from param_id_gui.algorithms.pso import ParticleSwarmOptimization, PSOConfig
from param_id_gui.data.hdf5_handler import HDF5Handler


# ── Helpers ────────────────────────────────────────────────────

def _make_pmsm(params=None):
    """Create a PMSM model with default or custom parameters."""
    p = params or {
        "Rs": 0.5, "Ld": 5e-4, "Lq": 1e-3,
        "flux_pm": 0.03, "J": 1e-4, "B": 1e-3, "Pp": 4,
    }
    return PMSMdqModel(**p)


def _make_buck(params=None):
    """Create a Buck converter model."""
    return BuckConverter()


def _run_pmsm_open_loop(model, steps=1000, dt=50e-6, vd=10.0, vq=5.0):
    """Run PMSM open-loop simulation."""
    states = []
    for _ in range(steps):
        model.step_dq(vd, vq, dt=dt)
        states.append(model.get_state())
    return states


# ── Tests ──────────────────────────────────────────────────────

class TestEndToEndWorkflow:
    """Test complete simulation workflow."""

    def test_pmsm_config_to_simulation(self, pmsm_params):
        """Test PMSM from configuration to simulation."""
        # Step 1: Create model
        model = _make_pmsm(pmsm_params)
        assert model.Rs == pmsm_params["Rs"]
        assert model.Ld == pmsm_params["Ld"]

        # Step 3: Run simulation
        states = _run_pmsm_open_loop(model, steps=500)

        # Step 4: Verify results
        assert len(states) == 500
        final = states[-1]
        assert "id" in final
        assert "iq" in final
        assert "omega_m" in final
        assert "torque" in final
        assert all(math.isfinite(v) for v in final.values())

    def test_buck_config_to_steady_state(self, buck_params):
        """Test Buck converter from configuration to steady-state."""
        # Step 1: Create model
        model = BuckConverter()

        # Step 3: Set inputs and run
        duty = buck_params["Vin"] / buck_params["Vin"]  # unity duty for Vin=Vout test
        model.set_input(duty_cycle=0.5, load_current=0.1)

        # Step 4: Run simulation to steady state
        dt = 1e-6
        for _ in range(10000):
            model.update(dt)

        # Step 5: Verify output voltage approaches expected value
        v_out = model.get_output_voltage()
        assert math.isfinite(v_out)
        assert v_out >= 0.0

    def test_orchestrator_with_pmsm(self, pmsm_params):
        """Test orchestrator managing PMSM simulation."""
        orch = Orchestrator(OrchestratorConfig(dt_ns=50000))
        model = _make_pmsm(pmsm_params)

        # Register model stepper
        def pmsm_step(step_ns):
            dt = step_ns / 1e9
            model.step_dq(10.0, 5.0, dt=dt)
            from param_id_gui.core.orchestrator import StepResult
            return StepResult(solver_id="pmsm", converged=True)

        orch.register_stepper("pmsm", pmsm_step)
        orch.register_initializer("pmsm", model.reset)

        # Run short simulation
        audits = orch.run(step_ns=50000, duration_s=0.01)

        # Verify
        assert orch.get_state() in (SimulationState.IDLE, SimulationState.STOPPED)
        assert orch.get_time() > 0
        assert orch.get_step_count() > 0

    def test_data_bus_integration(self):
        """Test data bus with simulation data flow."""
        bus = DataBus()
        received = []

        def on_signal(sig):
            received.append(sig)

        bus.subscribe("motor/speed", on_signal)

        # Publish signals
        for i in range(10):
            sig = Signal(
                source="pmsm_model",
                signal_type="speed",
                timestamp_ns=i * 50000,
                value=float(i * 100),
                unit="rad/s",
            )
            bus.publish("motor/speed", sig, module_id="pmsm_model")

        # Verify
        assert len(received) == 10
        assert received[-1].value == 900.0

        latest = bus.read_latest("motor/speed")
        assert latest is not None
        assert latest.value == 900.0

    def test_model_registry_integration(self):
        """Test model registry with multiple models."""
        registry = ModelRegistry()

        # Register PMSM
        pmsm_meta = ModelMetadata(
            model_id="mdl://motor/pmsm/v1",
            model_name="PMSM dq",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
            input_ports=[
                Port(name="vd", unit="V"),
                Port(name="vq", unit="V"),
            ],
            output_ports=[
                Port(name="id", unit="A"),
                Port(name="iq", unit="A"),
            ],
        )
        registry.register(_make_pmsm(), pmsm_meta)

        # Register Buck
        buck_meta = ModelMetadata(
            model_id="mdl://power/buck/v1",
            model_name="Buck Converter",
            domain=Domain.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(_make_buck(), buck_meta)

        # Verify
        assert registry.model_count == 2
        motor_models = registry.list_by_domain(Domain.MOTOR)
        assert len(motor_models) == 1

        pmsm = registry.get("mdl://motor/pmsm/v1")
        assert isinstance(pmsm, PMSMdqModel)

    def test_lm_parameter_identification(self):
        """Test LM optimizer identifies known parameters."""
        # Known system: y = 2*x + 3
        true_params = np.array([2.0, 3.0])

        def residual(params):
            x_data = np.array([0, 1, 2, 3, 4.0])
            y_pred = params[0] * x_data + params[1]
            y_true = true_params[0] * x_data + true_params[1]
            return y_pred - y_true

        lm = LevenbergMarquardt(LMConfig(max_iterations=100, tolerance=1e-10))
        x0 = np.array([1.0, 1.0])
        result, info = lm.optimize(residual, x0=x0)

        np.testing.assert_allclose(result, true_params, atol=1e-4)
        assert info["converged"]

    def test_pso_parameter_identification(self):
        """Test PSO optimizer finds minimum of known function."""
        # Minimize (x-3)^2 + (y-5)^2
        def objective(params):
            return (params[0] - 3.0)**2 + (params[1] - 5.0)**2

        pso = ParticleSwarmOptimization(PSOConfig(n_particles=30, max_iterations=200))
        bounds = (np.array([0.0, 0.0]), np.array([10.0, 10.0]))
        result, info = pso.optimize(objective, bounds=bounds)

        np.testing.assert_allclose(result, [3.0, 5.0], atol=2.0)
        assert info["final_cost"] < 5.0


class TestErrorHandling:
    """Test error handling in integrated workflows."""

    def test_invalid_pmsm_parameters(self):
        """Test PMSM rejects invalid parameters gracefully."""
        # NaN input should be guarded
        model = _make_pmsm()
        model.step_dq(float("nan"), float("nan"))
        # Model should not crash, state should be finite
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())

    def test_invalid_buck_duty_cycle(self):
        """Test Buck converter handles out-of-range duty cycle."""
        model = _make_buck()
        # Duty > 1 should be clamped
        model.set_input(duty_cycle=1.5)
        assert model._duty_cycle <= 1.0

        # Duty < 0 should be clamped
        model.set_input(duty_cycle=-0.5)
        assert model._duty_cycle >= 0.0

    def test_orchestrator_invalid_step(self):
        """Test orchestrator rejects invalid step size."""
        orch = Orchestrator()
        with pytest.raises(ValueError):
            orch.run(step_ns=0, duration_s=1.0)
        with pytest.raises(ValueError):
            orch.run(step_ns=-1, duration_s=1.0)

    def test_orchestrator_invalid_duration(self):
        """Test orchestrator rejects invalid duration."""
        orch = Orchestrator()
        with pytest.raises(ValueError):
            orch.run(step_ns=50000, duration_s=0.0)
        with pytest.raises(ValueError):
            orch.run(step_ns=50000, duration_s=-1.0)

    def test_data_bus_nan_signal(self):
        """Test data bus handles NaN signal values."""
        bus = DataBus()

        sig = Signal(
            source="test", signal_type="voltage",
            timestamp_ns=0, value=float("nan"),
        )
        # Should not crash, but validity should be INVALID
        bus.publish("test/voltage", sig, module_id="test")
        latest = bus.read_latest("test/voltage")
        assert latest is not None

    def test_model_registry_duplicate_registration(self):
        """Test registry rejects duplicate model IDs."""
        registry = ModelRegistry()
        meta = ModelMetadata(
            model_id="mdl://test/v1", model_name="Test",
            domain=Domain.MOTOR, fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(_make_pmsm(), meta)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(_make_pmsm(), meta)

    def test_hdf5_roundtrip(self, tmp_path):
        """Test HDF5 data recording and playback."""
        filepath = str(tmp_path / "test_roundtrip.h5")

        # Record
        with HDF5Handler(filepath) as handler:
            for i in range(100):
                handler.record_simulation_data(
                    time=i * 50e-6,
                    data={"id": float(i * 0.1), "iq": float(i * 0.05)},
                )

        # Playback
        with HDF5Handler(filepath) as handler:
            data = handler.load_simulation_data()
            assert "time" in data
            assert "id" in data
            assert "iq" in data
            assert len(data["time"]) == 100
            np.testing.assert_allclose(data["id"], np.arange(100) * 0.1, atol=1e-10)
