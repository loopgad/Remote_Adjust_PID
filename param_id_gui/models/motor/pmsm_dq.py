"""PMSM dq-axis model for motor simulation."""

from typing import Dict, Any, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class PMSMParameters:
    """PMSM model parameters."""
    Rs: float = 0.5      # Stator resistance (Ohm)
    Ld: float = 0.005    # d-axis inductance (H)
    Lq: float = 0.005    # q-axis inductance (H)
    psi_f: float = 0.1   # Permanent magnet flux linkage (Wb)
    p: int = 4           # Number of pole pairs
    J: float = 0.001     # Moment of inertia (kg·m²)
    B: float = 0.001     # Viscous friction coefficient (N·m·s/rad)


class PMSMModel:
    """PMSM dq-axis model for motor simulation.
    
    This class implements the dq-axis model of a Permanent Magnet Synchronous
    Motor (PMSM) for simulation purposes.
    """
    
    def __init__(self, params: Optional[PMSMParameters] = None):
        """Initialize PMSM model.
        
        Args:
            params: PMSM parameters (uses defaults if None)
        """
        self.params = params or PMSMParameters()
        self.state = {
            'id': 0.0,      # d-axis current (A)
            'iq': 0.0,      # q-axis current (A)
            'omega': 0.0,   # Mechanical angular velocity (rad/s)
            'theta': 0.0,   # Mechanical angle (rad)
        }
        self._input = {
            'vd': 0.0,      # d-axis voltage (V)
            'vq': 0.0,      # q-axis voltage (V)
            'tl': 0.0,      # Load torque (N·m)
        }
    
    def set_input(self, **kwargs):
        """Set model inputs.
        
        Args:
            **kwargs: Input values (vd, vq, tl)
        """
        self._input.update(kwargs)
    
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
        Rs = self.params.Rs
        Ld = self.params.Ld
        Lq = self.params.Lq
        psi_f = self.params.psi_f
        p = self.params.p
        J = self.params.J
        B = self.params.B
        
        # Extract state
        id_ = self.state['id']
        iq = self.state['iq']
        omega = self.state['omega']
        
        # Extract input
        vd = self._input['vd']
        vq = self._input['vq']
        tl = self._input['tl']
        
        # Electrical dynamics (dq-axis)
        # Ld * did/dt = vd - Rs*id + omega*Lq*iq
        # Lq * diq/dt = vq - Rs*iq - omega*Ld*id - omega*psi_f
        did = (vd - Rs * id_ + omega * Lq * iq) / Ld
        diq = (vq - Rs * iq - omega * Ld * id_ - omega * psi_f) / Lq
        
        # Mechanical dynamics
        # J * domega/dt = Te - B*omega - tl
        # Te = 1.5 * p * (psi_f * iq + (Ld - Lq) * id_ * iq)
        Te = 1.5 * p * (psi_f * iq + (Ld - Lq) * id_ * iq)
        domega = (Te - B * omega - tl) / J
        
        # Update state using Euler integration
        self.state['id'] += did * dt
        self.state['iq'] += diq * dt
        self.state['omega'] += domega * dt
        self.state['theta'] += omega * dt
        
        # Normalize theta to [0, 2*pi)
        self.state['theta'] = self.state['theta'] % (2 * np.pi)
        
        return self.get_state()
    
    def reset(self):
        """Reset model state to initial values."""
        self.state = {
            'id': 0.0,
            'iq': 0.0,
            'omega': 0.0,
            'theta': 0.0,
        }
        self._input = {
            'vd': 0.0,
            'vq': 0.0,
            'tl': 0.0,
        }
    
    def get_torque(self) -> float:
        """Calculate electromagnetic torque.
        
        Returns:
            Electromagnetic torque (N·m)
        """
        id_ = self.state['id']
        iq = self.state['iq']
        
        Te = 1.5 * self.params.p * (
            self.params.psi_f * iq + 
            (self.params.Ld - self.params.Lq) * id_ * iq
        )
        return Te
