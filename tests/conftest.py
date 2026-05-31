"""Pytest configuration and fixtures for param_id_gui test suite."""

import pytest
import numpy as np
from pathlib import Path
from typing import Dict, Any


# ── Project Fixtures ──────────────────────────────────────────

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_data():
    """Return sample data for testing."""
    return {
        "voltage": [12.0, 12.0, 12.0],
        "current": [1.0, 1.5, 2.0],
        "time": [0.0, 0.1, 0.2],
    }


# ── Model Fixtures ────────────────────────────────────────────

@pytest.fixture
def pmsm_params():
    """Return default PMSM parameters."""
    return {
        "Rs": 0.5,      # Stator resistance [Ω]
        "Ld": 5e-4,     # d-axis inductance [H]
        "Lq": 1e-3,     # q-axis inductance [H]
        "flux_pm": 0.03, # PM flux linkage [Wb]
        "J": 1e-4,      # Moment of inertia [kg·m²]
        "B": 1e-3,      # Viscous friction [N·m·s/rad]
        "Pp": 4,         # Pole pairs
    }


@pytest.fixture
def buck_params():
    """Return default Buck converter parameters."""
    return {
        "Vin": 12.0,    # Input voltage [V]
        "L": 100e-6,    # Inductance [H]
        "C": 100e-6,    # Capacitance [F]
        "R_load": 10.0, # Load resistance [Ω]
        "f_sw": 100e3,  # Switching frequency [Hz]
    }


@pytest.fixture
def boost_params():
    """Return default Boost converter parameters."""
    return {
        "Vin": 5.0,     # Input voltage [V]
        "L": 100e-6,    # Inductance [H]
        "C": 100e-6,    # Capacitance [F]
        "R_load": 50.0, # Load resistance [Ω]
        "f_sw": 100e3,  # Switching frequency [Hz]
    }


@pytest.fixture
def foc_params():
    """Return default FOC controller parameters."""
    return {
        "id_kp": 5.0,
        "id_ki": 0.1,
        "iq_kp": 5.0,
        "iq_ki": 0.1,
        "speed_kp": 1.0,
        "speed_ki": 0.01,
    }


# ── Algorithm Fixtures ────────────────────────────────────────

@pytest.fixture
def lm_config():
    """Return default LM configuration."""
    return {
        "max_iterations": 1000,
        "tolerance": 1e-6,
        "lambda_init": 1e-3,
        "lambda_factor": 10.0,
        "lambda_min": 1e-10,
        "lambda_max": 1e10,
    }


@pytest.fixture
def pso_config():
    """Return default PSO configuration."""
    return {
        "n_particles": 50,
        "max_iterations": 100,
        "w": 0.7,           # Inertia weight
        "c1": 1.5,          # Cognitive parameter
        "c2": 1.5,          # Social parameter
        "w_decay": 0.99,    # Inertia decay
    }


# ── Numerical Fixtures ────────────────────────────────────────

@pytest.fixture
def time_vector():
    """Return a time vector for simulation testing."""
    return np.linspace(0, 0.1, 1000)  # 100ms, 1000 points


@pytest.fixture
def voltage_signal():
    """Return a sample voltage signal."""
    t = np.linspace(0, 0.1, 1000)
    return 12.0 * np.sin(2 * np.pi * 50 * t)  # 50Hz sine


@pytest.fixture
def current_signal():
    """Return a sample current signal."""
    t = np.linspace(0, 0.1, 1000)
    return 2.0 * np.sin(2 * np.pi * 50 * t - 0.1)  # 50Hz sine with phase shift


@pytest.fixture
def residual_function():
    """Return a simple residual function for optimizer testing."""
    def residuals(params: np.ndarray) -> np.ndarray:
        # Simple quadratic: f(x) = (x - 2)^2 + (x - 3)^2
        return np.array([
            params[0] - 2.0,
            params[1] - 3.0,
        ])
    return residuals


@pytest.fixture
def jacobian_function():
    """Return a simple Jacobian function for optimizer testing."""
    def jacobian(params: np.ndarray) -> np.ndarray:
        # Jacobian of the residual function
        return np.array([
            [1.0, 0.0],
            [0.0, 1.0],
    ])
    return jacobian


# ── HDF5 Fixtures ─────────────────────────────────────────────

@pytest.fixture
def tmp_hdf5_file(tmp_path):
    """Return a temporary HDF5 file path."""
    return tmp_path / "test_data.h5"


# ── Mock Fixtures ─────────────────────────────────────────────

@pytest.fixture
def mock_model():
    """Return a simple mock model for testing."""
    class MockModel:
        def __init__(self):
            self.params = {"gain": 1.0, "offset": 0.0}
            self.state = {"output": 0.0}
        
        def step(self, inputs: Dict[str, float]) -> Dict[str, float]:
            output = self.params["gain"] * inputs.get("input", 0.0) + self.params["offset"]
            self.state["output"] = output
            return {"output": output}
        
        def reset(self):
            self.state = {"output": 0.0}
    
    return MockModel()


@pytest.fixture
def mock_optimizer():
    """Return a simple mock optimizer for testing."""
    class MockOptimizer:
        def __init__(self):
            self.history = []
            self.iterations = 0
        
        def optimize(self, residual_func, x0, **kwargs):
            # Simple gradient descent
            x = x0.copy()
            for i in range(10):
                r = residual_func(x)
                x -= 0.1 * r
                self.history.append(float(np.sum(r**2)))
                self.iterations += 1
            return x, {"iterations": self.iterations, "history": self.history}
    
    return MockOptimizer()
