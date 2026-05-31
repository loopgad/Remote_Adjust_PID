"""C++ Core Compatibility Layer

Provides automatic detection and fallback for the C++ accelerated core module.
When the C++ module is available, it returns the module instance.
When unavailable, it returns None and logs a warning.

Usage:
    from param_id_gui.core._core_compat import get_core, get_solver, get_filters
    
    core = get_core()
    if core:
        # Use C++ accelerated functions
        solver = core.solvers.RK4Solver(1e-4)
    else:
        # Fallback to pure Python implementation
        pass
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

__all__ = ["get_core", "get_solver", "get_filters"]

_core_module = None
_core_available = None


def get_core() -> Optional[Any]:
    """Get the C++ core module if available.
    
    Returns:
        The C++ core module instance, or None if unavailable.
    """
    global _core_module, _core_available
    
    if _core_available is not None:
        return _core_module
    
    try:
        import param_id_gui._core as core
        _core_module = core
        _core_available = True
        logger.info("C++ core module loaded successfully")
        return _core_module
    except ImportError as e:
        _core_available = False
        logger.warning("C++ core unavailable, using Python fallback: %s", e)
        return None
    except Exception as e:
        _core_available = False
        logger.warning("C++ core loading failed: %s", e)
        return None


def get_solver(dt: float = 1e-4) -> Optional[Any]:
    """Get an ODE solver instance.
    
    Args:
        dt: Time step for the solver.
    
    Returns:
        RK4Solver instance if C++ is available, None otherwise.
    """
    core = get_core()
    if core is not None:
        try:
            return core.solvers.RK4Solver(dt)
        except Exception as e:
            logger.warning("Failed to create C++ solver: %s", e)
            return None
    return None


def get_filters() -> Optional[Any]:
    """Get the filters module.
    
    Returns:
        The filters submodule if C++ is available, None otherwise.
    """
    core = get_core()
    if core is not None:
        try:
            return core.filters
        except Exception as e:
            logger.warning("Failed to access C++ filters: %s", e)
            return None
    return None
