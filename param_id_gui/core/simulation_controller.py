"""Simulation Controller — GUI ↔ Core Bridge

Bridges the GUI panels with the core simulation engine:
- SimulationController: QObject that coordinates Orchestrator + DataBus + ModelRegistry
- SimulationWorker: QObject that runs simulation in a QThread

Usage:
    controller = SimulationController(orchestrator, data_bus, model_registry)
    controller.start_simulation("PMSM", params, duration=0.1, step_size=1e-4)
"""

import logging
import math
from typing import Optional, Dict, Any, Callable

from PySide6.QtCore import QObject, Signal, QThread, QTimer

from .orchestrator import Orchestrator
from .data_bus import DataBus, Signal as DataSignal
from .model_registry import ModelRegistry
from .types import SimulationState

logger = logging.getLogger(__name__)

__all__ = ["SimulationController", "SimulationWorker"]


class SimulationWorker(QObject):
    """Worker that runs simulation in a QThread.
    
    Uses moveToThread() pattern (Qt recommended) instead of inheriting QThread.
    """
    
    # Signals
    step_completed = Signal(dict)  # Latest simulation state
    finished = Signal()            # Simulation completed
    error_occurred = Signal(str)   # Error message
    
    def __init__(self, orchestrator: Orchestrator, data_bus: DataBus,
                 model_name: str, params: Dict[str, Any],
                 duration: float, step_size: float,
                 parent: Optional[QObject] = None):
        """Initialize worker.
        
        Args:
            orchestrator: Orchestrator instance
            data_bus: DataBus instance
            model_name: Model identifier
            params: Model parameters
            duration: Simulation duration in seconds
            step_size: Simulation step size in seconds
            parent: Parent QObject
        """
        super().__init__(parent)
        self._orchestrator = orchestrator
        self._data_bus = data_bus
        self._model_name = model_name
        self._params = params
        self._duration = duration
        self._step_size = step_size
        self._is_running = False
    
    def run(self) -> None:
        """Run simulation. Called in QThread context."""
        try:
            self._is_running = True
            step_ns = int(self._step_size * 1e9)
            
            # Register stepper function
            def step_fn():
                if not self._is_running:
                    return
                # Get current time
                t = self._orchestrator.get_time()
                
                # Publish time to DataBus
                self._data_bus.publish_scalar(
                    f"{self._model_name}/time", t, "s",
                    timestamp_ns=int(t * 1e9),
                    module_id="simulation_controller"
                )
                
                # Emit step completed signal with current state
                state = {
                    "time": t,
                    "step_count": self._orchestrator.get_step_count(),
                    "state": self._orchestrator.get_state().value,
                }
                self.step_completed.emit(state)
            
            # Register stepper
            self._orchestrator.register_stepper("simulation_controller", step_fn)
            
            # Run simulation
            self._orchestrator.run(step_ns, self._duration)
            
            # Simulation completed
            self._is_running = False
            self.finished.emit()
            
        except Exception as e:
            self._is_running = False
            logger.exception("Simulation error")
            self.error_occurred.emit(str(e))
    
    def stop(self) -> None:
        """Signal worker to stop."""
        self._is_running = False


class SimulationController(QObject):
    """Controller that bridges GUI ↔ Orchestrator ↔ DataBus.
    
    Coordinates the simulation lifecycle and provides data access for GUI updates.
    """
    
    # Signals
    state_changed = Signal(str)    # "idle"/"running"/"paused"/"stopped"/"error"
    step_completed = Signal(dict)  # Latest simulation state
    error_occurred = Signal(str)   # Error message
    
    def __init__(self, orchestrator: Orchestrator, data_bus: DataBus,
                 model_registry: ModelRegistry, parent: Optional[QObject] = None):
        """Initialize controller.
        
        Args:
            orchestrator: Orchestrator instance
            data_bus: DataBus instance
            model_registry: ModelRegistry instance
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self._orchestrator = orchestrator
        self._data_bus = data_bus
        self._model_registry = model_registry
        
        # Worker thread
        self._worker: Optional[SimulationWorker] = None
        self._worker_thread: Optional[QThread] = None
        
        # Current simulation state
        self._current_model_name: Optional[str] = None
        self._current_params: Optional[Dict[str, Any]] = None
        self._latest_data: Dict[str, Any] = {}
        
        # Subscribe to DataBus for data collection
        self._data_bus.subscribe("simulation_controller/time", self._on_time_update)
    
    def _on_time_update(self, signal: DataSignal) -> None:
        """Handle time update from DataBus."""
        self._latest_data["time"] = signal.value
    
    def start_simulation(self, model_name: str, params: Dict[str, Any],
                        duration: float = 1.0, step_size: float = 1e-4) -> None:
        """Start simulation in a background thread.
        
        Args:
            model_name: Model identifier
            params: Model parameters
            duration: Simulation duration in seconds
            step_size: Simulation step size in seconds
        """
        # Check if already running
        if self._orchestrator.get_state() == SimulationState.RUNNING:
            logger.warning("Simulation already running")
            return
        
        # Store current simulation config
        self._current_model_name = model_name
        self._current_params = params.copy()
        
        # Reset orchestrator
        self._orchestrator.reset()
        
        # Create worker and thread
        self._worker_thread = QThread()
        self._worker = SimulationWorker(
            self._orchestrator, self._data_bus,
            model_name, params, duration, step_size
        )
        self._worker.moveToThread(self._worker_thread)
        
        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_simulation_finished)
        self._worker.error_occurred.connect(self._on_simulation_error)
        self._worker.step_completed.connect(self._on_step_completed)
        
        # Cleanup on finished
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error_occurred.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._cleanup_worker)
        
        # Start thread
        self._orchestrator.state = SimulationState.RUNNING
        self.state_changed.emit("running")
        self._worker_thread.start()
        
        logger.info("Simulation started: model=%s, duration=%.3f s, step=%.6f s",
                    model_name, duration, step_size)
    
    def pause_simulation(self) -> None:
        """Pause the simulation."""
        if self._orchestrator.get_state() == SimulationState.RUNNING:
            self._orchestrator.pause()
            self.state_changed.emit("paused")
            logger.info("Simulation paused")
    
    def stop_simulation(self) -> None:
        """Stop the simulation."""
        if self._worker:
            self._worker.stop()
        self._orchestrator.stop()
        self.state_changed.emit("stopped")
        logger.info("Simulation stopped")
    
    def reset_simulation(self) -> None:
        """Reset the simulation."""
        self.stop_simulation()
        self._orchestrator.reset()
        self._latest_data.clear()
        self._current_model_name = None
        self._current_params = None
        self.state_changed.emit("idle")
        logger.info("Simulation reset")
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get latest simulation data for GUI updates.
        
        Returns:
            Dictionary with simulation state data
        """
        # Update with current orchestrator state
        self._latest_data["state"] = self._orchestrator.get_state().value
        self._latest_data["step_count"] = self._orchestrator.get_step_count()
        return self._latest_data.copy()
    
    def get_current_model_name(self) -> Optional[str]:
        """Get current model name."""
        return self._current_model_name
    
    def get_current_params(self) -> Optional[Dict[str, Any]]:
        """Get current model parameters."""
        return self._current_params
    
    def _on_step_completed(self, state: Dict[str, Any]) -> None:
        """Handle step completed from worker."""
        self._latest_data.update(state)
        self.step_completed.emit(state)
    
    def _on_simulation_finished(self) -> None:
        """Handle simulation finished."""
        self._orchestrator.state = SimulationState.IDLE
        self.state_changed.emit("idle")
        logger.info("Simulation completed")
    
    def _on_simulation_error(self, error_msg: str) -> None:
        """Handle simulation error."""
        self._orchestrator.state = SimulationState.ERROR
        self.state_changed.emit("error")
        self.error_occurred.emit(error_msg)
        logger.error("Simulation error: %s", error_msg)
    
    def _cleanup_worker(self) -> None:
        """Clean up worker and thread."""
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        if self._worker_thread:
            self._worker_thread.deleteLater()
            self._worker_thread = None
