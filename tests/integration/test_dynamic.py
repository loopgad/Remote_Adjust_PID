"""Task 25: 动态调用测试 - 模型/算法动态加载与调用.

Tests dynamic model loading via ModelRegistry, algorithm selection,
and runtime interface compliance.
"""

import math
import importlib
import numpy as np
import pytest

from param_id_gui.core.model_registry import (
    ModelRegistry, ModelMetadata, Domain, FidelityLevel, Port,
)
from param_id_gui.core.types import ModelProtocol, OptimizerProtocol
from param_id_gui.models.motor.pmsm_dq import PMSMdqModel
from param_id_gui.models.power.power_models import (
    BuckConverter, BoostConverter, IdealBattery, RintBattery, AverageInverter,
)
from param_id_gui.algorithms.lm import LevenbergMarquardt, LMConfig
from param_id_gui.algorithms.pso import ParticleSwarmOptimization, PSOConfig


# ── Dynamic Model Loading ─────────────────────────────────────

class TestDynamicModelLoading:
    """Test dynamic model loading and registration."""

    def test_register_and_retrieve_pmsm(self):
        """Should be able to register and retrieve PMSM model."""
        registry = ModelRegistry()
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        meta = ModelMetadata(
            model_id="mdl://motor/pmsm/v1",
            model_name="PMSM dq",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)

        retrieved = registry.get("mdl://motor/pmsm/v1")
        assert isinstance(retrieved, PMSMdqModel)

    def test_register_and_retrieve_buck(self):
        """Should be able to register and retrieve Buck converter."""
        registry = ModelRegistry()
        model = BuckConverter()
        meta = ModelMetadata(
            model_id="mdl://power/buck/v1",
            model_name="Buck Converter",
            domain=Domain.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)

        retrieved = registry.get("mdl://power/buck/v1")
        assert isinstance(retrieved, BuckConverter)

    def test_register_and_retrieve_boost(self):
        """Should be able to register and retrieve Boost converter."""
        registry = ModelRegistry()
        model = BoostConverter()
        meta = ModelMetadata(
            model_id="mdl://power/boost/v1",
            model_name="Boost Converter",
            domain=Domain.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)

        retrieved = registry.get("mdl://power/boost/v1")
        assert isinstance(retrieved, BoostConverter)

    def test_dynamic_model_invocation(self):
        """Should be able to invoke model methods dynamically."""
        registry = ModelRegistry()
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        meta = ModelMetadata(
            model_id="mdl://motor/pmsm/v1",
            model_name="PMSM dq",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)

        # Dynamic invocation
        retrieved = registry.get("mdl://motor/pmsm/v1")
        retrieved.step_dq(10.0, 5.0, dt=1e-5)
        state = retrieved.get_state()

        assert "id" in state
        assert "iq" in state
        assert all(math.isfinite(v) for v in state.values())

    def test_dynamic_reset(self):
        """Should be able to reset model dynamically."""
        registry = ModelRegistry()
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        meta = ModelMetadata(
            model_id="mdl://motor/pmsm/v1",
            model_name="PMSM dq",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)

        # Run, then reset
        retrieved = registry.get("mdl://motor/pmsm/v1")
        retrieved.step_dq(10.0, 5.0, dt=1e-5)
        retrieved.reset()

        state = retrieved.get_state()
        assert state["id"] == 0.0
        assert state["iq"] == 0.0
        assert state["omega_m"] == 0.0

    def test_unregister_model(self):
        """Should be able to unregister a model."""
        registry = ModelRegistry()
        model = BuckConverter()
        meta = ModelMetadata(
            model_id="mdl://power/buck/v1",
            model_name="Buck Converter",
            domain=Domain.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
        )
        registry.register(model, meta)
        assert registry.model_count == 1

        registry.unregister("mdl://power/buck/v1")
        assert registry.model_count == 0

        with pytest.raises(KeyError):
            registry.get("mdl://power/buck/v1")

    def test_list_by_domain(self):
        """Should list models filtered by domain."""
        registry = ModelRegistry()

        registry.register(
            PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4),
            ModelMetadata(model_id="mdl://motor/pmsm", model_name="PMSM",
                         domain=Domain.MOTOR, fidelity=FidelityLevel.L2_LUMPED),
        )
        registry.register(
            BuckConverter(),
            ModelMetadata(model_id="mdl://power/buck", model_name="Buck",
                         domain=Domain.POWER, fidelity=FidelityLevel.L2_LUMPED),
        )

        motor_models = registry.list_by_domain(Domain.MOTOR)
        assert len(motor_models) == 1
        assert "mdl://motor/pmsm" in motor_models

        power_models = registry.list_by_domain(Domain.POWER)
        assert len(power_models) == 1

    def test_list_by_fidelity(self):
        """Should list models filtered by fidelity level."""
        registry = ModelRegistry()

        registry.register(
            IdealBattery(),
            ModelMetadata(model_id="mdl://power/battery/l0", model_name="Ideal Battery",
                         domain=Domain.POWER, fidelity=FidelityLevel.L0_STUB),
        )
        registry.register(
            BuckConverter(),
            ModelMetadata(model_id="mdl://power/buck/l2", model_name="Buck",
                         domain=Domain.POWER, fidelity=FidelityLevel.L2_LUMPED),
        )

        l0_models = registry.list_by_fidelity(FidelityLevel.L0_STUB)
        assert len(l0_models) == 1

        l2_models = registry.list_by_fidelity(FidelityLevel.L2_LUMPED)
        assert len(l2_models) == 1

    def test_dependency_validation(self):
        """Should detect missing dependencies."""
        registry = ModelRegistry()

        registry.register(
            BuckConverter(),
            ModelMetadata(
                model_id="mdl://power/buck",
                model_name="Buck",
                domain=Domain.POWER,
                fidelity=FidelityLevel.L2_LUMPED,
                dependencies=["mdl://power/battery"],
            ),
        )

        missing = registry.validate_dependencies()
        assert len(missing) == 1
        assert "mdl://power/battery" in missing[0]


# ── Dynamic Algorithm Selection ───────────────────────────────

class TestDynamicAlgorithmSelection:
    """Test dynamic algorithm selection and invocation."""

    def test_lm_as_optimizer_protocol(self):
        """LM should satisfy OptimizerProtocol."""
        lm = LevenbergMarquardt()
        # Verify it has the optimize method
        assert hasattr(lm, "optimize")
        assert callable(lm.optimize)

    def test_pso_as_optimizer_protocol(self):
        """PSO should satisfy OptimizerProtocol."""
        pso = ParticleSwarmOptimization()
        assert hasattr(pso, "optimize")
        assert callable(pso.optimize)

    def test_dynamic_lm_invocation(self):
        """Should be able to invoke LM dynamically."""
        def residual(params):
            return params - np.array([2.0, 3.0])

        lm = LevenbergMarquardt(LMConfig(max_iterations=50))
        result, info = lm.optimize(residual, x0=np.array([1.0, 1.0]))

        np.testing.assert_allclose(result, [2.0, 3.0], atol=1e-3)
        assert info["converged"]

    def test_dynamic_pso_invocation(self):
        """Should be able to invoke PSO dynamically."""
        def objective(params):
            return (params[0] - 5.0)**2 + (params[1] - 10.0)**2

        pso = ParticleSwarmOptimization(PSOConfig(n_particles=20, max_iterations=100))
        bounds = (np.array([0.0, 0.0]), np.array([20.0, 20.0]))
        result, info = pso.optimize(objective, bounds=bounds)

        np.testing.assert_allclose(result, [5.0, 10.0], atol=2.0)

    def test_algorithm_selection_by_type(self):
        """Should select algorithm based on type string."""
        from param_id_gui.core.types import AlgorithmType

        def get_optimizer(algo_type: str):
            if algo_type == AlgorithmType.LEVENBERG_MARQUARDT.value:
                return LevenbergMarquardt()
            elif algo_type == AlgorithmType.PARTICLE_SWARM.value:
                return ParticleSwarmOptimization()
            else:
                raise ValueError(f"Unknown algorithm: {algo_type}")

        lm = get_optimizer("lm")
        assert isinstance(lm, LevenbergMarquardt)

        pso = get_optimizer("pso")
        assert isinstance(pso, ParticleSwarmOptimization)

    def test_optimizer_with_custom_config(self):
        """Should be able to configure optimizer dynamically."""
        config = LMConfig(max_iterations=500, tolerance=1e-8, lambda_init=1e-2)
        lm = LevenbergMarquardt(config)

        assert lm.config.max_iterations == 500
        assert lm.config.tolerance == 1e-8
        assert lm.config.lambda_init == 1e-2


# ── Interface Compliance ──────────────────────────────────────

class TestInterfaceCompliance:
    """Test that models and algorithms comply with protocols."""

    def test_pmsm_has_step(self):
        """PMSM should have step method."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        assert hasattr(model, "step")
        assert callable(model.step)

    def test_pmsm_has_reset(self):
        """PMSM should have reset method."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        assert hasattr(model, "reset")
        assert callable(model.reset)

    def test_pmsm_has_get_state(self):
        """PMSM should have get_state method."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        assert hasattr(model, "get_state")
        assert callable(model.get_state)

    def test_buck_has_update(self):
        """Buck converter should have update method."""
        model = BuckConverter()
        assert hasattr(model, "update")
        assert callable(model.update)

    def test_buck_has_reset(self):
        """Buck converter should have reset method."""
        model = BuckConverter()
        assert hasattr(model, "reset")
        assert callable(model.reset)

    def test_boost_has_update(self):
        """Boost converter should have update method."""
        model = BoostConverter()
        assert hasattr(model, "update")
        assert callable(model.update)

    def test_lm_returns_tuple(self):
        """LM optimize should return (params, info) tuple."""
        def residual(params):
            return params - 1.0

        lm = LevenbergMarquardt(LMConfig(max_iterations=10))
        result = lm.optimize(residual, x0=np.array([0.5]))

        assert isinstance(result, tuple)
        assert len(result) == 2
        params, info = result
        assert isinstance(info, dict)
        assert "iterations" in info
        assert "final_cost" in info

    def test_pso_returns_tuple(self):
        """PSO optimize should return (params, info) tuple."""
        def objective(params):
            return np.sum(params**2)

        pso = ParticleSwarmOptimization(PSOConfig(n_particles=5, max_iterations=10))
        bounds = (np.array([-10.0]), np.array([10.0]))
        result = pso.optimize(objective, bounds=bounds)

        assert isinstance(result, tuple)
        assert len(result) == 2
        params, info = result
        assert isinstance(info, dict)

    def test_registry_metadata_completeness(self):
        """Registry metadata should contain all required fields."""
        registry = ModelRegistry()
        meta = ModelMetadata(
            model_id="mdl://test/v1",
            model_name="Test Model",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
            input_ports=[Port(name="vin", unit="V")],
            output_ports=[Port(name="vout", unit="V")],
            version="1.0.0",
            author="test",
        )
        registry.register(object(), meta)

        retrieved = registry.get_metadata("mdl://test/v1")
        assert retrieved.model_id == "mdl://test/v1"
        assert retrieved.model_name == "Test Model"
        assert retrieved.domain == Domain.MOTOR
        assert retrieved.fidelity == FidelityLevel.L2_LUMPED
        assert len(retrieved.input_ports) == 1
        assert len(retrieved.output_ports) == 1
