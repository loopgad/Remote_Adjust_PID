"""High-precision parameter identification automation software with PySide6 GUI and C++ acceleration."""

__version__ = "0.1.0"
__author__ = "ParamID Team"

# Core modules
from .core.orchestrator import Orchestrator
from .core.data_bus import DataBus
from .core.model_registry import ModelRegistry

__all__ = [
    "Orchestrator",
    "DataBus",
    "ModelRegistry",
]
