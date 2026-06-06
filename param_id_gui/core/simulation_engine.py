"""Simulation Engine — Pure Python simulation runner (no Qt dependency).

Provides SimulationEngine that coordinates Orchestrator + DataBus + ModelRegistry
without any PySide6 dependency. Can be used standalone or wrapped by SimulationController.

Usage:
    engine = SimulationEngine(orchestrator, data_bus, model_registry)
    engine.start("PMSM", params, duration=0.1, step_size=1e-4)
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable

from .orchestrator import Orchestrator, StepResult
from .data_bus import DataBus
from .model_registry import ModelRegistry
from .types import SimulationState

logger = logging.getLogger(__name__)

__all__ = ["SimulationEngine"]


class SimulationEngine:
    """Pure Python simulation runner. No Qt dependency.

    Runs simulation synchronously in the calling thread via Orchestrator.
    Reports progress via callbacks. Thread management is handled by the caller
    (e.g., SimulationController wraps this in a QThread).
    """

    def __init__(self, orchestrator: Orchestrator, data_bus: DataBus,
                 model_registry: ModelRegistry):
        self._orchestrator = orchestrator
        self._data_bus = data_bus
        self._model_registry = model_registry
        self._stop_event = threading.Event()
        self._data_lock = threading.Lock()
        self._latest_data: Dict[str, Any] = {}
        self._current_model_name: Optional[str] = None
        self._current_params: Optional[Dict[str, Any]] = None

    def start(
        self,
        model_name: str,
        params: Dict[str, Any],
        duration: float = 1.0,
        step_size: float = 1e-4,
        on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Run simulation synchronously in the calling thread.

        This method blocks until the simulation completes or is stopped.
        Thread management is the caller's responsibility.

        Args:
            model_name: Model identifier in registry
            params: Model parameters to apply before simulation
            duration: Simulation duration in seconds
            step_size: Simulation step size in seconds
            on_step: Callback(state_dict) after each step (throttled to ~20Hz)
            on_finished: Callback when simulation completes normally
            on_error: Callback(error_msg) on failure

        Returns:
            True if simulation started, False if already running
        """
        if self._orchestrator.get_state() == SimulationState.RUNNING:
            logger.warning("Simulation already running")
            return False

        self._current_model_name = model_name
        self._current_params = params.copy()
        self._stop_event.clear()

        step_ns = int(step_size * 1e9)

        try:
            model = self._model_registry.get(model_name)
        except KeyError:
            msg = f"Model '{model_name}' not found in registry"
            logger.error(msg)
            if on_error:
                on_error(msg)
            return False

        # Apply user parameters to model instance (C4 fix)
        self._apply_params_to_model(model, params)

        default_inputs = model.get_default_inputs() if hasattr(model, 'get_default_inputs') else {}

        # Signal throttling: report at most every 50ms (~20Hz)
        last_report_time = 0.0
        report_interval = 0.05

        def step_fn(step_ns: int) -> StepResult:
            nonlocal last_report_time
            if self._stop_event.is_set():
                return StepResult(solver_id="simulation_engine", converged=False)
            try:
                model_state = model.step(default_inputs, step_ns)
            except Exception as e:
                logger.error("Model step failed: %s", e)
                return StepResult(
                    solver_id="simulation_engine",
                    converged=False,
                    error_estimate=float('inf'),
                )
            t = self._orchestrator.get_time()
            # Throttled state update and callback
            if t - last_report_time >= report_interval:
                last_report_time = t
                state = {
                    "time": t,
                    "step_count": self._orchestrator.get_step_count(),
                    "state": self._orchestrator.get_state().value,
                }
                if isinstance(model_state, dict):
                    state.update(model_state)
                with self._data_lock:
                    self._latest_data.update(state)
                if on_step:
                    on_step(state)
            return StepResult(solver_id="simulation_engine")

        try:
            self._orchestrator.register_stepper("simulation_engine", step_fn)
            self._orchestrator.run(step_ns, duration)
            if on_finished:
                on_finished()
        except Exception as e:
            logger.exception("Simulation error")
            if on_error:
                on_error(str(e))
        finally:
            self._stop_event.set()

        return True

    def _apply_params_to_model(self, model: Any, params: Dict[str, Any]) -> None:
        """Apply parameter dict to model instance.

        Tries configure() method first, falls back to direct attribute setting.
        """
        if not params:
            return
        if hasattr(model, 'configure'):
            try:
                model.configure(params)
                return
            except Exception as e:
                logger.warning("model.configure() failed: %s, trying direct set", e)
        # Fallback: set attributes directly
        for key, value in params.items():
            if hasattr(model, key):
                try:
                    setattr(model, key, value)
                except Exception:
                    logger.debug("Could not set model.%s = %s", key, value)

    def stop(self) -> None:
        """Signal simulation to stop."""
        self._stop_event.set()
        self._orchestrator.stop()

    def reset(self) -> None:
        """Reset engine state. Thread-safe."""
        with self._data_lock:
            self._latest_data.clear()
        self._current_model_name = None
        self._current_params = None
        self._stop_event.clear()

    def get_latest_data(self) -> Dict[str, Any]:
        """Get latest simulation state data."""
        with self._data_lock:
            self._latest_data["state"] = self._orchestrator.get_state().value
            self._latest_data["step_count"] = self._orchestrator.get_step_count()
            return self._latest_data.copy()

    def get_current_model_name(self) -> Optional[str]:
        """Get current model name."""
        return self._current_model_name

    def get_current_params(self) -> Optional[Dict[str, Any]]:
        """Get current model parameters."""
        return self._current_params

    def update_params(self, model_name: str, params: Dict[str, Any]) -> None:
        """Update current model name and parameters."""
        self._current_model_name = model_name
        self._current_params = params
