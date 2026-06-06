"""Core data structures and type definitions for param_id_gui.

Uses Pydantic for data validation and type safety.
"""

import math
from enum import Enum
from typing import Any, Callable, Dict, Protocol, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
import numpy as np

# Re-export canonical definitions from domain-specific modules
from .model_registry import FidelityLevel, Domain  # noqa: F401
from .data_bus import Signal  # noqa: F401


# ── Type Aliases ──────────────────────────────────────────────


# ── Protocols ─────────────────────────────────────────────────

class ModelProtocol(Protocol):
    """Protocol for simulation models."""
    
    def step(self, inputs: Dict[str, float], dt_ns: int = ...) -> Dict[str, float]:
        """Execute one simulation step."""
        ...
    
    def reset(self) -> None:
        """Reset model to initial state."""
        ...
    
    def get_state(self) -> Dict[str, float]:
        """Get current model state."""
        ...
    
    def get_default_inputs(self) -> Dict[str, float]:
        """Get default input dictionary for this model."""
        ...


class OptimizerProtocol(Protocol):
    """Protocol for optimization algorithms."""

    def optimize(
        self,
        func: Callable[[np.ndarray], np.ndarray],
        **kwargs: Any,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Run optimization.

        Args:
            func: Objective/residual function to minimize
            **kwargs: Algorithm-specific parameters (x0, bounds, progress_callback, etc.)

        Returns:
            Tuple of (optimized parameters, info dict with keys:
                final_cost, iterations, converged, etc.)
        """
        ...


# ── Enums ─────────────────────────────────────────────────────

class SimulationState(str, Enum):
    """Simulation state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"



class AlgorithmType(str, Enum):
    """Algorithm type enumeration."""
    LEVENBERG_MARQUARDT = "lm"
    PARTICLE_SWARM = "pso"

# FidelityLevel is imported from model_registry above (L0-L4)


# ── Data Models ───────────────────────────────────────────────

class ModelParams(BaseModel):
    """Base class for model parameters."""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )


class PMSMParams(ModelParams):
    """PMSM motor parameters."""
    
    Rs: float = Field(default=0.5, gt=0, description="Stator resistance [Ω]")
    Ld: float = Field(default=5e-4, gt=0, description="d-axis inductance [H]")
    Lq: float = Field(default=1e-3, gt=0, description="q-axis inductance [H]")
    flux_pm: float = Field(default=0.03, ge=0, description="PM flux linkage [Wb]")
    J: float = Field(default=1e-4, gt=0, description="Moment of inertia [kg·m²]")
    B: float = Field(default=1e-3, ge=0, description="Viscous friction [N·m·s/rad]")
    Pp: int = Field(default=4, gt=0, description="Number of pole pairs")

    @field_validator("Rs", "Ld", "Lq", "flux_pm", "J", "B", mode="before")
    @classmethod
    def validate_positive_float(cls, v: Union[int, float]) -> float:
        if not isinstance(v, (int, float)):
            raise ValueError(f"Expected numeric value, got {type(v)}")
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Value cannot be NaN or Inf")
        return float(v)

    @field_validator("Pp", mode="before")
    @classmethod
    def validate_positive_int(cls, v: Union[int, float]) -> int:
        if not isinstance(v, (int, float)):
            raise ValueError(f"Expected integer value, got {type(v)}")
        if isinstance(v, float) and not v.is_integer():
            raise ValueError(f"Pole pairs must be an integer, got {v}")
        v = int(v)
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class ConverterParams(ModelParams):
    """Base class for DC-DC converter parameters."""
    
    L: float = Field(default=100e-6, gt=0, description="Inductance [H]")
    C: float = Field(default=100e-6, gt=0, description="Capacitance [F]")
    f_sw: float = Field(default=100e3, gt=0, description="Switching frequency [Hz]")


class BuckConverterParams(ConverterParams):
    """Buck converter parameters."""
    
    Vin: float = Field(default=12.0, gt=0, description="Input voltage [V]")
    R_load: float = Field(default=10.0, gt=0, description="Load resistance [Ω]")


class BoostConverterParams(ConverterParams):
    """Boost converter parameters."""
    
    Vin: float = Field(default=5.0, gt=0, description="Input voltage [V]")
    R_load: float = Field(default=50.0, gt=0, description="Load resistance [Ω]")


class FOCParams(ModelParams):
    """FOC controller parameters."""
    
    id_kp: float = Field(default=5.0, gt=0, description="d-axis PI proportional gain")
    id_ki: float = Field(default=0.1, gt=0, description="d-axis PI integral gain")
    iq_kp: float = Field(default=5.0, gt=0, description="q-axis PI proportional gain")
    iq_ki: float = Field(default=0.1, gt=0, description="q-axis PI integral gain")
    speed_kp: float = Field(default=1.0, gt=0, description="Speed PI proportional gain")
    speed_ki: float = Field(default=0.01, gt=0, description="Speed PI integral gain")


class LMConfig(BaseModel):
    """Levenberg-Marquardt configuration."""
    
    max_iterations: int = Field(default=1000, gt=0, description="Maximum iterations")
    tolerance: float = Field(default=1e-6, gt=0, description="Convergence tolerance")
    lambda_init: float = Field(default=1e-3, gt=0, description="Initial damping parameter")
    lambda_factor: float = Field(default=10.0, gt=1, description="Lambda adjustment factor")
    lambda_min: float = Field(default=1e-10, gt=0, description="Minimum lambda value")
    lambda_max: float = Field(default=1e10, gt=0, description="Maximum lambda value")


class PSOConfig(BaseModel):
    """Particle Swarm Optimization configuration."""
    
    n_particles: int = Field(default=50, gt=0, description="Number of particles")
    max_iterations: int = Field(default=1000, gt=0, description="Maximum iterations")
    tolerance: float = Field(default=1e-6, gt=0, description="Convergence tolerance")
    w: float = Field(default=0.7298, gt=0, le=1, description="Inertia weight")
    c1: float = Field(default=1.4962, gt=0, description="Cognitive parameter")
    c2: float = Field(default=1.4962, gt=0, description="Social parameter")
    w_decay: float = Field(default=0.99, gt=0, le=1, description="Inertia decay rate")




# Signal is imported from data_bus above (canonical version with validation)



