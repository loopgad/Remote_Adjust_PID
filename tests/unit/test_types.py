"""Tests for core type definitions."""

import pytest
import numpy as np
from param_id_gui.core.types import (
    SimulationState,
    ModelType,
    AlgorithmType,
    FidelityLevel,
    PMSMParams,
    BuckConverterParams,
    BoostConverterParams,
    FOCParams,
    LMConfig,
    PSOConfig,
    SimulationStateModel,
    SimulationResult,
    OptimizationResult,
    Signal,
)


# ── Enum Tests ────────────────────────────────────────────────

def test_simulation_state_enum():
    """Test SimulationState enum values."""
    assert SimulationState.IDLE == "idle"
    assert SimulationState.RUNNING == "running"
    assert SimulationState.PAUSED == "paused"
    assert SimulationState.STOPPED == "stopped"
    assert SimulationState.ERROR == "error"


def test_model_type_enum():
    """Test ModelType enum values."""
    assert ModelType.MOTOR == "motor"
    assert ModelType.POWER == "power"
    assert ModelType.CONTROLLER == "controller"
    assert ModelType.CUSTOM == "custom"


def test_algorithm_type_enum():
    """Test AlgorithmType enum values."""
    assert AlgorithmType.LEVENBERG_MARQUARDT == "lm"
    assert AlgorithmType.PARTICLE_SWARM == "pso"
    assert AlgorithmType.GENETIC == "ga"
    assert AlgorithmType.CUSTOM == "custom"


def test_fidelity_level_enum():
    """Test FidelityLevel enum values."""
    assert FidelityLevel.L0_IDEAL == 0
    assert FidelityLevel.L1_LINEAR == 1
    assert FidelityLevel.L2_LUMPED == 2
    assert FidelityLevel.L3_DISTRIBUTED == 3


# ── Parameter Model Tests ─────────────────────────────────────

def test_pmsm_params_defaults():
    """Test PMSMParams default values."""
    params = PMSMParams()
    assert params.Rs == 0.5
    assert params.Ld == 5e-4
    assert params.Lq == 1e-3
    assert params.flux_pm == 0.03
    assert params.J == 1e-4
    assert params.B == 1e-3
    assert params.Pp == 4


def test_pmsm_params_custom_values():
    """Test PMSMParams with custom values."""
    params = PMSMParams(Rs=1.0, Ld=1e-3, Lq=2e-3, flux_pm=0.05, J=1e-3, B=1e-2, Pp=6)
    assert params.Rs == 1.0
    assert params.Ld == 1e-3
    assert params.Lq == 2e-3
    assert params.flux_pm == 0.05
    assert params.J == 1e-3
    assert params.B == 1e-2
    assert params.Pp == 6


def test_pmsm_params_validation_negative():
    """Test PMSMParams rejects negative values."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        PMSMParams(Rs=-1.0)


def test_pmsm_params_validation_zero():
    """Test PMSMParams rejects zero for required positive fields."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        PMSMParams(Rs=0.0)


def test_buck_converter_params_defaults():
    """Test BuckConverterParams default values."""
    params = BuckConverterParams()
    assert params.Vin == 12.0
    assert params.L == 100e-6
    assert params.C == 100e-6
    assert params.R_load == 10.0
    assert params.f_sw == 100e3


def test_boost_converter_params_defaults():
    """Test BoostConverterParams default values."""
    params = BoostConverterParams()
    assert params.Vin == 5.0
    assert params.L == 100e-6
    assert params.C == 100e-6
    assert params.R_load == 50.0
    assert params.f_sw == 100e3


def test_foc_params_defaults():
    """Test FOCParams default values."""
    params = FOCParams()
    assert params.id_kp == 5.0
    assert params.id_ki == 0.1
    assert params.iq_kp == 5.0
    assert params.iq_ki == 0.1
    assert params.speed_kp == 1.0
    assert params.speed_ki == 0.01


# ── Algorithm Config Tests ────────────────────────────────────

def test_lm_config_defaults():
    """Test LMConfig default values."""
    config = LMConfig()
    assert config.max_iterations == 1000
    assert config.tolerance == 1e-6
    assert config.lambda_init == 1e-3
    assert config.lambda_factor == 10.0
    assert config.lambda_min == 1e-10
    assert config.lambda_max == 1e10


def test_pso_config_defaults():
    """Test PSOConfig default values."""
    config = PSOConfig()
    assert config.n_particles == 50
    assert config.max_iterations == 100
    assert config.w == 0.7
    assert config.c1 == 1.5
    assert config.c2 == 1.5
    assert config.w_decay == 0.99


# ── Simulation State Tests ────────────────────────────────────

def test_simulation_state_model_defaults():
    """Test SimulationStateModel default values."""
    state = SimulationStateModel()
    assert state.state == SimulationState.IDLE
    assert state.time_ns == 0
    assert state.step_count == 0
    assert state.error_message is None


def test_simulation_result_creation():
    """Test SimulationResult creation."""
    result = SimulationResult(
        success=True,
        time_vector=[0.0, 0.1, 0.2],
        data={"voltage": [12.0, 12.0, 12.0]},
    )
    assert result.success is True
    assert len(result.time_vector) == 3
    assert "voltage" in result.data


# ── Optimization Result Tests ─────────────────────────────────

def test_optimization_result_creation():
    """Test OptimizationResult creation."""
    result = OptimizationResult(
        success=True,
        optimal_params=[1.0, 2.0, 3.0],
        residual_norm=1e-6,
        iterations=100,
    )
    assert result.success is True
    assert len(result.optimal_params) == 3
    assert result.residual_norm == 1e-6
    assert result.iterations == 100


# ── Signal Tests ──────────────────────────────────────────────

def test_signal_creation():
    """Test Signal creation."""
    signal = Signal(name="voltage", value=12.0, timestamp_ns=1000)
    assert signal.name == "voltage"
    assert signal.value == 12.0
    assert signal.timestamp_ns == 1000
    assert signal.quality == 0xFF


# ── Integration Tests ─────────────────────────────────────────

def test_param_model_serialization():
    """Test that parameter models can be serialized to dict."""
    params = PMSMParams(Rs=1.0, Ld=1e-3)
    data = params.model_dump()
    assert isinstance(data, dict)
    assert data["Rs"] == 1.0
    assert data["Ld"] == 1e-3


def test_param_model_from_dict():
    """Test that parameter models can be created from dict."""
    data = {"Rs": 1.0, "Ld": 1e-3, "Lq": 2e-3, "flux_pm": 0.05, "J": 1e-3, "B": 1e-2, "Pp": 6}
    params = PMSMParams(**data)
    assert params.Rs == 1.0
    assert params.Ld == 1e-3


def test_enum_comparison():
    """Test enum comparison with strings."""
    assert SimulationState.IDLE == "idle"
    assert ModelType.MOTOR == "motor"
    assert AlgorithmType.LEVENBERG_MARQUARDT == "lm"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
