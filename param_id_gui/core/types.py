"""Core data structures and type definitions for param_id_gui.

Uses Pydantic for data validation and type safety.
Updated for testing git hooks.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
import numpy as np


# ── Type Aliases ──────────────────────────────────────────────

# Numeric types
FloatArray = np.ndarray
TimeNs = int  # Time in nanoseconds
TimeSec = float  # Time in seconds

# Parameter types
ParamValue = Union[float, int, bool, str]
ParamDict = Dict[str, ParamValue]


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


class OptimizerProtocol(Protocol):
    """Protocol for optimization algorithms."""
    
    def optimize(
        self,
        residual_func: Any,
        x0: np.ndarray,
        **kwargs: Any,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Run optimization."""
        ...


# ── Enums ─────────────────────────────────────────────────────

class SimulationState(str, Enum):
    """Simulation state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class ModelType(str, Enum):
    """Model type enumeration."""
    MOTOR = "motor"
    POWER = "power"
    CONTROLLER = "controller"
    CUSTOM = "custom"


class AlgorithmType(str, Enum):
    """Algorithm type enumeration."""
    LEVENBERG_MARQUARDT = "lm"
    PARTICLE_SWARM = "pso"
    GENETIC = "ga"
    CUSTOM = "custom"


class FidelityLevel(int, Enum):
    """Model fidelity level."""
    L0_IDEAL = 0        # Ideal model
    L1_LINEAR = 1       # Linear model
    L2_LUMPED = 2       # Lumped parameter model
    L3_DISTRIBUTED = 3  # Distributed parameter model


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


class BuckConverterParams(ModelParams):
    """Buck converter parameters."""
    
    Vin: float = Field(default=12.0, gt=0, description="Input voltage [V]")
    L: float = Field(default=100e-6, gt=0, description="Inductance [H]")
    C: float = Field(default=100e-6, gt=0, description="Capacitance [F]")
    R_load: float = Field(default=10.0, gt=0, description="Load resistance [Ω]")
    f_sw: float = Field(default=100e3, gt=0, description="Switching frequency [Hz]")


class BoostConverterParams(ModelParams):
    """Boost converter parameters."""
    
    Vin: float = Field(default=5.0, gt=0, description="Input voltage [V]")
    L: float = Field(default=100e-6, gt=0, description="Inductance [H]")
    C: float = Field(default=100e-6, gt=0, description="Capacitance [F]")
    R_load: float = Field(default=50.0, gt=0, description="Load resistance [Ω]")
    f_sw: float = Field(default=100e3, gt=0, description="Switching frequency [Hz]")


class FOCParams(ModelParams):
    """FOC controller parameters."""
    
    id_kp: float = Field(default=5.0, gt=0, description="d-axis PI proportional gain")
    id_ki: float = Field(default=0.1, gt=0, description="d-axis PI integral gain")
    iq_kp: float = Field(default=5.0, gt=0, description="q-axis PI proportional gain")
    iq_ki: float = Field(default=0.1, gt=0, description="q-axis PI integral gain")
    speed_kp: float = Field(default=1.0, gt=0, description="Speed PI proportional gain")
    speed_ki: float = Field(default=0.01, gt=0, description="Speed PI integral gain")


# ── Simulation State Models ───────────────────────────────────

class SimulationStateModel(BaseModel):
    """Simulation state data."""
    
    state: SimulationState = Field(default=SimulationState.IDLE, description="Current simulation state")
    time_ns: int = Field(default=0, ge=0, description="Current simulation time [ns]")
    step_count: int = Field(default=0, ge=0, description="Number of steps completed")
    error_message: Optional[str] = Field(default=None, description="Error message if state is ERROR")


class SimulationResult(BaseModel):
    """Simulation result data."""
    
    success: bool = Field(description="Whether simulation completed successfully")
    time_vector: List[float] = Field(description="Time vector [s]")
    data: Dict[str, List[float]] = Field(description="Simulation data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


# ── Algorithm Configuration Models ────────────────────────────

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
    max_iterations: int = Field(default=100, gt=0, description="Maximum iterations")
    w: float = Field(default=0.7, gt=0, le=1, description="Inertia weight")
    c1: float = Field(default=1.5, gt=0, description="Cognitive parameter")
    c2: float = Field(default=1.5, gt=0, description="Social parameter")
    w_decay: float = Field(default=0.99, gt=0, le=1, description="Inertia decay rate")


class OptimizationResult(BaseModel):
    """Optimization result data."""
    
    success: bool = Field(description="Whether optimization converged")
    optimal_params: List[float] = Field(description="Optimal parameters found")
    residual_norm: float = Field(description="Final residual norm")
    iterations: int = Field(description="Number of iterations performed")
    history: List[float] = Field(default_factory=list, description="Cost function history")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


# ── Data Bus Models ───────────────────────────────────────────

class Signal(BaseModel):
    """Signal data for data bus."""
    
    name: str = Field(description="Signal name")
    value: float = Field(description="Signal value")
    timestamp_ns: int = Field(default=0, description="Timestamp [ns]")
    quality: int = Field(default=0xFF, description="Signal quality flags")


class TopicConfig(BaseModel):
    """Topic configuration for data bus."""
    
    name: str = Field(description="Topic name")
    max_subscribers: int = Field(default=100, gt=0, description="Maximum subscribers")
    history_size: int = Field(default=1000, gt=0, description="History buffer size")


# ── HDF5 Data Models ─────────────────────────────────────────

class HDF5DatasetInfo(BaseModel):
    """HDF5 dataset information."""
    
    name: str = Field(description="Dataset name")
    shape: Tuple[int, ...] = Field(description="Dataset shape")
    dtype: str = Field(description="Dataset dtype")
    attrs: Dict[str, Any] = Field(default_factory=dict, description="Dataset attributes")


class HDF5GroupInfo(BaseModel):
    """HDF5 group information."""
    
    name: str = Field(description="Group name")
    datasets: List[HDF5DatasetInfo] = Field(default_factory=list, description="Datasets in group")
    groups: List[str] = Field(default_factory=list, description="Subgroup names")
    attrs: Dict[str, Any] = Field(default_factory=dict, description="Group attributes")


# ── Validation Helpers ────────────────────────────────────────

@field_validator("Rs", "Ld", "Lq", "flux_pm", "J", "B", mode="before")
@classmethod
def validate_positive_float(cls, v: float) -> float:
    """Validate that float values are positive."""
    if not isinstance(v, (int, float)):
        raise ValueError(f"Expected numeric value, got {type(v)}")
    if np.isnan(v) or np.isinf(v):
        raise ValueError("Value cannot be NaN or Inf")
    return float(v)


@field_validator("Pp", mode="before")
@classmethod
def validate_positive_int(cls, v: int) -> int:
    """Validate that int values are positive."""
    if not isinstance(v, int):
        raise ValueError(f"Expected integer value, got {type(v)}")
    if v <= 0:
        raise ValueError("Value must be positive")
    return v
