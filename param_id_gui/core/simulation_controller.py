"""Simulation Controller — GUI ↔ Core Bridge

Wraps SimulationEngine with Qt signals for GUI integration.
SimulationEngine (pure Python) handles the actual simulation.
SimulationController (Qt QObject) provides signals/slots for GUI panels.

Usage:
    controller = SimulationController(orchestrator, data_bus, model_registry)
    controller.start_simulation("PMSM", params, duration=0.1, step_size=1e-4)
"""

import logging
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, QThread

from .orchestrator import Orchestrator
from .data_bus import DataBus
from .model_registry import ModelRegistry
from .simulation_engine import SimulationEngine
from .types import SimulationState

logger = logging.getLogger(__name__)

__all__ = ["SimulationController"]


class _SimulationWorker(QObject):
    """Internal worker that runs SimulationEngine.start() in a QThread."""
    
    started = Signal()
    finished = Signal()
    error_occurred = Signal(str)
    step_completed = Signal(dict)
    
    def __init__(self, engine: SimulationEngine,
                 model_name: str, params: Dict[str, Any],
                 duration: float, step_size: float,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._engine = engine
        self._model_name = model_name
        self._params = params
        self._duration = duration
        self._step_size = step_size
    
    def run(self) -> None:
        """Run simulation in QThread context."""
        self.started.emit()
        self._engine.start(
            self._model_name, self._params,
            duration=self._duration, step_size=self._step_size,
            on_step=lambda state: self.step_completed.emit(state),
            on_finished=lambda: self.finished.emit(),
            on_error=lambda msg: self.error_occurred.emit(msg),
        )


class SimulationController(QObject):
    """Qt adapter wrapping SimulationEngine. Provides signals for GUI panels."""
    
    state_changed = Signal(str)
    step_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, orchestrator: Orchestrator, data_bus: DataBus,
                 model_registry: ModelRegistry, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._engine = SimulationEngine(orchestrator, data_bus, model_registry)
        self._orchestrator = orchestrator
        self._worker: Optional[_SimulationWorker] = None
        self._worker_thread: Optional[QThread] = None
    
    def start_simulation(self, model_name: str, params: Dict[str, Any],
                        duration: float = 1.0, step_size: float = 1e-4) -> None:
        """Start simulation in a background QThread.

        State management: orchestrator.run() sets RUNNING internally.
        We emit state_changed from the worker's started signal.
        """
        if self._orchestrator.get_state() == SimulationState.RUNNING:
            logger.warning("Simulation already running")
            return

        # Clean up any previous worker/thread
        self._cleanup()

        self._engine.update_params(model_name, params)
        self._orchestrator.reset()

        self._worker_thread = QThread()
        self._worker = _SimulationWorker(
            self._engine, model_name, params, duration, step_size
        )
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.started.connect(lambda: self.state_changed.emit("running"))
        self._worker.finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.step_completed.connect(self._on_step)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error_occurred.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._cleanup)

        self._worker_thread.start()

        logger.info("Simulation started: model=%s, duration=%.3f s, step=%.6f s",
                    model_name, duration, step_size)
    
    def pause_simulation(self) -> None:
        if self._orchestrator.get_state() == SimulationState.RUNNING:
            self._orchestrator.pause()
            self.state_changed.emit("paused")
    
    def resume_simulation(self) -> None:
        if self._orchestrator.get_state() == SimulationState.PAUSED:
            self._orchestrator.set_state(SimulationState.RUNNING)
            self.state_changed.emit("running")
    
    def stop_simulation(self) -> None:
        self._engine.stop()
        self.state_changed.emit("stopped")
    
    def reset_simulation(self) -> None:
        self.stop_simulation()
        self._orchestrator.reset()
        self._engine.reset()
        self.state_changed.emit("idle")
    
    def get_latest_data(self) -> Dict[str, Any]:
        return self._engine.get_latest_data()
    
    def get_current_model_name(self) -> Optional[str]:
        return self._engine.get_current_model_name()
    
    def get_current_params(self) -> Optional[Dict[str, Any]]:
        return self._engine.get_current_params()
    
    def update_params(self, model_name: str, params: Dict[str, Any]) -> None:
        self._engine.update_params(model_name, params)
    
    def _on_step(self, state: Dict[str, Any]) -> None:
        self.step_completed.emit(state)
    
    def _on_finished(self) -> None:
        self._orchestrator.set_state(SimulationState.IDLE)
        self.state_changed.emit("idle")
        logger.info("Simulation completed")
    
    def _on_error(self, msg: str) -> None:
        self._orchestrator.set_state(SimulationState.ERROR)
        self.state_changed.emit("error")
        self.error_occurred.emit(msg)
        logger.error("Simulation error: %s", msg)
    
    def _cleanup(self) -> None:
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        if self._worker_thread:
            self._worker_thread.deleteLater()
            self._worker_thread = None
