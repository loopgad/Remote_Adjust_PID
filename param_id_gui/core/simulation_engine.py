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
    
    Runs simulation in a background thread using Orchestrator + DataBus + ModelRegistry.
    Reports progress via callbacks.
    """

    def __init__(self, orchestrator: Orchestrator, data_bus: DataBus,
                 model_registry: ModelRegistry):
        self._orchestrator = orchestrator
        self._data_bus = data_bus
        self._model_registry = model_registry
        self._stop_event = threading.Event()
        self._latest_data: Dict[str, Any] = {}
        self._data_lock = threading.Lock()
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
        """Start simulation in a background thread.
        
        Args:
            model_name: Model identifier in registry
            params: Model parameters
            duration: Simulation duration in seconds
            step_size: Simulation step size in seconds
            on_step: Callback with state dict after each step
            on_finished: Callback when simulation completes
            on_error: Callback with error message on failure
            
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

        default_inputs = model.get_default_inputs() if hasattr(model, 'get_default_inputs') else {}

        def step_fn(step_ns: int) -> StepResult:
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
            self._data_bus.publish_scalar(
                f"{model_name}/time", t, "s",
                timestamp_ns=int(t * 1e9),
                module_id="simulation_engine"
            )
            state = {
                "time": t,
                "step_count": self._orchestrator.get_step_count(),
                "state": self._orchestrator.get_state().value,
                **model_state,
            }
            with self._data_lock:
                self._latest_data.update(state)
            if on_step:
                on_step(state)
            return StepResult(solver_id="simulation_engine")

        def run_fn() -> None:
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

        self._orchestrator.set_state(SimulationState.RUNNING)
        self._thread = threading.Thread(target=run_fn, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Signal simulation to stop."""
        self._stop_event.set()
        self._orchestrator.stop()

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
