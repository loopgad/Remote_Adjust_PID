"""Simulation orchestrator for coordinating simulation components."""

from typing import Any, Dict, Optional
from enum import Enum
import threading
import time


class SimulationState(Enum):
    """Simulation state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class GlobalClock:
    """Global clock for simulation timing."""
    
    def __init__(self, dt: float = 0.001):
        """Initialize global clock.
        
        Args:
            dt: Time step in seconds
        """
        self.dt = dt
        self.current_time = 0.0
        self.step_count = 0
    
    def step(self):
        """Advance clock by one time step."""
        self.current_time += self.dt
        self.step_count += 1
    
    def reset(self):
        """Reset clock to initial state."""
        self.current_time = 0.0
        self.step_count = 0


class Orchestrator:
    """Simulation orchestrator for coordinating simulation components.
    
    This class manages the simulation lifecycle, including starting, pausing,
    stopping, and resetting simulations. It coordinates between different
    simulation components like ODE solvers, models, and data buses.
    """
    
    def __init__(self, dt: float = 0.001):
        """Initialize orchestrator.
        
        Args:
            dt: Time step in seconds
        """
        self.clock = GlobalClock(dt)
        self.state = SimulationState.IDLE
        self.components: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
    
    def register_component(self, name: str, component: Any):
        """Register a simulation component.
        
        Args:
            name: Component name
            component: Component instance
        """
        self.components[name] = component
    
    def start(self):
        """Start the simulation."""
        with self._lock:
            if self.state == SimulationState.RUNNING:
                return
            
            self.state = SimulationState.RUNNING
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
    
    def pause(self):
        """Pause the simulation."""
        with self._lock:
            if self.state == SimulationState.RUNNING:
                self.state = SimulationState.PAUSED
    
    def stop(self):
        """Stop the simulation."""
        with self._lock:
            self.state = SimulationState.STOPPED
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
    
    def reset(self):
        """Reset the simulation."""
        with self._lock:
            self.state = SimulationState.IDLE
            self.clock.reset()
            for component in self.components.values():
                if hasattr(component, 'reset'):
                    component.reset()
    
    def _run(self):
        """Internal simulation loop."""
        while self.state == SimulationState.RUNNING:
            try:
                # Update all components
                for component in self.components.values():
                    if hasattr(component, 'update'):
                        component.update(self.clock.current_time)
                
                # Advance clock
                self.clock.step()
                
                # Small delay to prevent CPU hogging
                time.sleep(0.001)
                
            except Exception as e:
                self.state = SimulationState.ERROR
                print(f"Simulation error: {e}")
                break
    
    def get_state(self) -> SimulationState:
        """Get current simulation state.
        
        Returns:
            Current simulation state
        """
        return self.state
    
    def get_time(self) -> float:
        """Get current simulation time.
        
        Returns:
            Current simulation time in seconds
        """
        return self.clock.current_time
