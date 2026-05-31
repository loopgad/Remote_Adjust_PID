"""Power electronics models for DC-DC converters."""

from typing import Dict, Any, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class BuckConverterParameters:
    """Buck converter parameters."""
    Vin: float = 12.0      # Input voltage (V)
    L: float = 0.001       # Inductance (H)
    C: float = 0.0001      # Capacitance (F)
    R: float = 0.01        # ESR of capacitor (Ohm)
    Rl: float = 0.05       # Inductor resistance (Ohm)
    f_sw: float = 100000   # Switching frequency (Hz)


@dataclass
class BoostConverterParameters:
    """Boost converter parameters."""
    Vin: float = 5.0       # Input voltage (V)
    L: float = 0.001       # Inductance (H)
    C: float = 0.0001      # Capacitance (F)
    R: float = 0.01        # ESR of capacitor (Ohm)
    Rl: float = 0.05       # Inductor resistance (Ohm)
    f_sw: float = 100000   # Switching frequency (Hz)


class BuckConverter:
    """Buck converter model for DC-DC power conversion.
    
    This class implements the average model of a Buck converter
    for simulation purposes.
    """
    
    def __init__(self, params: Optional[BuckConverterParameters] = None):
        """Initialize Buck converter model.
        
        Args:
            params: Buck converter parameters (uses defaults if None)
        """
        self.params = params or BuckConverterParameters()
        self.state = {
            'iL': 0.0,     # Inductor current (A)
            'vC': 0.0,     # Capacitor voltage (V)
        }
        self._duty_cycle = 0.5  # Duty cycle [0, 1]
        self._load_current = 0.0  # Load current (A)
    
    def set_input(self, duty_cycle: float, load_current: float = 0.0):
        """Set converter inputs.
        
        Args:
            duty_cycle: Duty cycle [0, 1]
            load_current: Load current (A)
        """
        self._duty_cycle = max(0.0, min(1.0, duty_cycle))
        self._load_current = load_current
    
    def get_state(self) -> Dict[str, float]:
        """Get current model state.
        
        Returns:
            Dictionary of state variables
        """
        return self.state.copy()
    
    def update(self, dt: float) -> Dict[str, float]:
        """Update model state for one time step.
        
        Args:
            dt: Time step (s)
            
        Returns:
            Updated state dictionary
        """
        # Extract parameters
        Vin = self.params.Vin
        L = self.params.L
        C = self.params.C
        R = self.params.R
        Rl = self.params.Rl
        
        # Extract state
        iL = self.state['iL']
        vC = self.state['vC']
        
        # Extract input
        d = self._duty_cycle
        i_load = self._load_current
        
        # Average model equations
        # L * diL/dt = d*Vin - vC - Rl*iL
        # C * dvC/dt = iL - i_load - vC/R
        diL = (d * Vin - vC - Rl * iL) / L
        dvC = (iL - i_load - vC / R) / C
        
        # Update state using Euler integration
        self.state['iL'] += diL * dt
        self.state['vC'] += dvC * dt
        
        return self.get_state()
    
    def reset(self):
        """Reset model state to initial values."""
        self.state = {
            'iL': 0.0,
            'vC': 0.0,
        }
        self._duty_cycle = 0.5
        self._load_current = 0.0
    
    def get_output_voltage(self) -> float:
        """Get output voltage.
        
        Returns:
            Output voltage (V)
        """
        return self.state['vC']


class BoostConverter:
    """Boost converter model for DC-DC power conversion.
    
    This class implements the average model of a Boost converter
    for simulation purposes.
    """
    
    def __init__(self, params: Optional[BoostConverterParameters] = None):
        """Initialize Boost converter model.
        
        Args:
            params: Boost converter parameters (uses defaults if None)
        """
        self.params = params or BoostConverterParameters()
        self.state = {
            'iL': 0.0,     # Inductor current (A)
            'vC': 0.0,     # Capacitor voltage (V)
        }
        self._duty_cycle = 0.5  # Duty cycle [0, 1]
        self._load_current = 0.0  # Load current (A)
    
    def set_input(self, duty_cycle: float, load_current: float = 0.0):
        """Set converter inputs.
        
        Args:
            duty_cycle: Duty cycle [0, 1]
            load_current: Load current (A)
        """
        self._duty_cycle = max(0.0, min(1.0, duty_cycle))
        self._load_current = load_current
    
    def get_state(self) -> Dict[str, float]:
        """Get current model state.
        
        Returns:
            Dictionary of state variables
        """
        return self.state.copy()
    
    def update(self, dt: float) -> Dict[str, float]:
        """Update model state for one time step.
        
        Args:
            dt: Time step (s)
            
        Returns:
            Updated state dictionary
        """
        # Extract parameters
        Vin = self.params.Vin
        L = self.params.L
        C = self.params.C
        R = self.params.R
        Rl = self.params.Rl
        
        # Extract state
        iL = self.state['iL']
        vC = self.state['vC']
        
        # Extract input
        d = self._duty_cycle
        i_load = self._load_current
        
        # Average model equations
        # L * diL/dt = Vin - (1-d)*vC - Rl*iL
        # C * dvC/dt = (1-d)*iL - i_load - vC/R
        diL = (Vin - (1 - d) * vC - Rl * iL) / L
        dvC = ((1 - d) * iL - i_load - vC / R) / C
        
        # Update state using Euler integration
        self.state['iL'] += diL * dt
        self.state['vC'] += dvC * dt
        
        return self.get_state()
    
    def reset(self):
        """Reset model state to initial values."""
        self.state = {
            'iL': 0.0,
            'vC': 0.0,
        }
        self._duty_cycle = 0.5
        self._load_current = 0.0
    
    def get_output_voltage(self) -> float:
        """Get output voltage.
        
        Returns:
            Output voltage (V)
        """
        return self.state['vC']
