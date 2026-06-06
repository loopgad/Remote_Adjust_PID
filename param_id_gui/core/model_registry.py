"""Model Registry — metadata-driven model management.

Every model in the simulation platform is registered here with
a unique ID, version, fidelity level, I/O ports, units, and
validation status.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FidelityLevel(int, Enum):
    """Model fidelity levels."""
    L0_STUB = 0          # stub — I/O only
    L1_EMPIRICAL = 1     # empirical — curves / lookup tables
    L2_LUMPED = 2        # lumped parameter — ODE with R/L/C/J/B
    L3_PHYSICS = 3       # physics-based — nonlinear, switching
    L4_HIGH_FIDELITY = 4 # high fidelity — FEM, CFD, full SPICE


class Domain(str, Enum):
    """Model domains."""
    POWER = "power"
    MOTOR = "motor"
    SENSOR = "sensor"
    CONTROLLER = "controller"
    MECHANICAL = "mechanical"
    THERMAL = "thermal"
    GRID = "grid"
    FPGA = "fpga"
    ML = "ml"
    BATTERY = "battery"


@dataclass
class Port:
    """Model input/output port definition."""
    name: str
    unit: str                       # SI unit: "V", "A", "rad", "N.m" ...
    dtype: str = "float64"
    range_min: float = -float("inf")
    range_max: float = float("inf")
    description: str = ""

    def __post_init__(self) -> None:
        if self.range_min > self.range_max:
            raise ValueError(f"range_min ({self.range_min}) > range_max ({self.range_max})")


@dataclass
class ModelMetadata:
    """Complete metadata for a simulation model."""

    model_id: str                   # "mdl://motor/pmsm/dq/v1"
    model_name: str                 # human-readable
    domain: Domain
    fidelity: FidelityLevel

    input_ports: List[Port] = field(default_factory=list)
    output_ports: List[Port] = field(default_factory=list)

    sim_step_ns: int = 50000        # recommended simulation step
    latency_ns: int = 1000          # model computation latency
    is_realtime_capable: bool = False
    is_hil_capable: bool = False

    assumptions: List[str] = field(default_factory=list)
    valid_range: Dict[str, Any] = field(default_factory=dict)

    version: str = "1.0.0"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    validation_status: str = "NOT_TESTED"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "domain": self.domain.value,
            "fidelity": self.fidelity.value,
            "version": self.version,
            "step_ns": self.sim_step_ns,
        }


class ModelRegistry:
    """Central registry for all simulation models."""

    def __init__(self):
        """Initialize model registry."""
        self._models: Dict[str, Any] = {}       # model_id → model instance
        self._metadata: Dict[str, ModelMetadata] = {}  # model_id → metadata

    # ── registration ─────────────────────────────────────────

    def register(self, model: Any, metadata: ModelMetadata) -> None:
        """Register a model with metadata.

        Args:
            model: Model instance (should have step/reset/get_state methods)
            metadata: Model metadata

        Raises:
            ValueError: If model_id already registered
        """
        mid = metadata.model_id
        if mid in self._models:
            raise ValueError(f"Model {mid} already registered")
        missing = [m for m in ("step", "reset", "get_state") if not hasattr(model, m)]
        if missing:
            logger.warning("Model %s missing methods: %s", mid, ", ".join(missing))
        self._models[mid] = model
        self._metadata[mid] = metadata

    def get(self, model_id: str) -> Any:
        """Get a model instance by ID.

        Args:
            model_id: Model identifier

        Returns:
            Model instance

        Raises:
            KeyError: If model not found
        """
        # SECURITY (CWE-209): generic error message, no internal ID leak
        if model_id not in self._models:
            raise KeyError("Model not found in registry")
        return self._models[model_id]

    def get_metadata(self, model_id: str) -> ModelMetadata:
        """Get model metadata by ID.

        Args:
            model_id: Model identifier

        Returns:
            Model metadata

        Raises:
            KeyError: If metadata not found
        """
        # SECURITY (CWE-209): generic error message
        if model_id not in self._metadata:
            raise KeyError("Model metadata not found")
        return self._metadata[model_id]

    # ── queries ──────────────────────────────────────────────

    def list_by_domain(self, domain: Domain) -> Dict[str, ModelMetadata]:
        """List models by domain.

        Args:
            domain: Domain to filter by

        Returns:
            Dictionary of {model_id: metadata}
        """
        return {mid: m for mid, m in self._metadata.items()
                if m.domain == domain}

    def list_by_fidelity(self, level: FidelityLevel) -> Dict[str, ModelMetadata]:
        """List models by fidelity level.

        Args:
            level: Fidelity level to filter by

        Returns:
            Dictionary of {model_id: metadata}
        """
        return {mid: m for mid, m in self._metadata.items()
                if m.fidelity == level}

    def list_all(self) -> Dict[str, ModelMetadata]:
        """List all registered models.

        Returns:
            Dictionary of {model_id: metadata}
        """
        return dict(self._metadata)

    def list_models(self) -> List[str]:
        """List all registered model names.

        Returns:
            List of model names
        """
        return list(self._models.keys())

    @property
    def model_count(self) -> int:
        """Get number of registered models."""
        return len(self._models)

    def validate_dependencies(self) -> List[str]:
        """Check all model dependencies are satisfied.

        Returns:
            List of missing dependency descriptions
        """
        missing = []
        for meta in self._metadata.values():
            for dep in meta.dependencies:
                if dep not in self._models:
                    missing.append(f"{meta.model_id} → missing {dep}")
        return missing

    def unregister(self, model_id: str) -> None:
        """Unregister a model.

        Args:
            model_id: Model identifier
        """
        if model_id not in self._models and model_id not in self._metadata:
            logger.warning("Unregister called for unknown model_id '%s'", model_id)
        self._models.pop(model_id, None)
        self._metadata.pop(model_id, None)
