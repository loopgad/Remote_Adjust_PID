"""FOC controller for PMSM motor control."""

from typing import Dict, Any, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class FOCParameters:
    """FOC controller parameters."""
    # PI controller gains for d-axis
    Kp_d: float = 10.0
    Ki_d: float = 100.0
    
    # PI controller gains for q-axis
    Kp_q: float = 10.0
    Ki_q: float = 100.0
    
    # PI controller gains for speed
    Kp_speed: float = 1.0
    Ki_speed: float = 10.0
    
    # Limits
    max_voltage: float = 50.0  # Maximum voltage (V)
    max_current: float = 20.0  # Maximum current (A)
    
    # Motor parameters (for coordinate transformation)
    p: int = 4  # Number of pole pairs


class FOCController:
    """Field-Oriented Control (FOC) controller for PMSM motors.
    
    This class implements the FOC algorithm for controlling PMSM motors,
    including Clarke/Park transformations, PI controllers, and SVPWM.
    """
    
    def __init__(self, params: Optional[FOCParameters] = None):
        """Initialize FOC controller.
        
        Args:
            params: FOC parameters (uses defaults if None)
        """
        self.params = params or FOCParameters()
        
        # PI controller states
        self._integral_d = 0.0
        self._integral_q = 0.0
        self._integral_speed = 0.0
        
        # Reference values
        self._id_ref = 0.0      # d-axis current reference (A)
        self._iq_ref = 0.0      # q-axis current reference (A)
        self._speed_ref = 0.0   # Speed reference (rad/s)
        
        # Control mode
        self._mode = "torque"  # "torque" or "speed"
    
    def set_mode(self, mode: str):
        """Set control mode.
        
        Args:
            mode: Control mode ("torque" or "speed")
        """
        if mode not in ["torque", "speed"]:
            raise ValueError("Mode must be 'torque' or 'speed'")
        self._mode = mode
    
    def set_reference(self, **kwargs):
        """Set reference values.
        
        Args:
            **kwargs: Reference values (id_ref, iq_ref, speed_ref)
        """
        if 'id_ref' in kwargs:
            self._id_ref = kwargs['id_ref']
        if 'iq_ref' in kwargs:
            self._iq_ref = kwargs['iq_ref']
        if 'speed_ref' in kwargs:
            self._speed_ref = kwargs['speed_ref']
    
    def clarke_transform(self, ia: float, ib: float, ic: float) -> tuple:
        """Perform Clarke transformation (abc -> alpha-beta).
        
        Args:
            ia: Phase a current (A)
            ib: Phase b current (A)
            ic: Phase c current (A)
            
        Returns:
            Tuple of (ialpha, ibeta) currents (A)
        """
        ialpha = (2.0/3.0) * (ia - 0.5*ib - 0.5*ic)
        ibeta = (2.0/3.0) * ((np.sqrt(3)/2)*ib - (np.sqrt(3)/2)*ic)
        return ialpha, ibeta
    
    def park_transform(self, ialpha: float, ibeta: float, theta: float) -> tuple:
        """Perform Park transformation (alpha-beta -> dq).
        
        Args:
            ialpha: Alpha-axis current (A)
            ibeta: Beta-axis current (A)
            theta: Electrical angle (rad)
            
        Returns:
            Tuple of (id, iq) currents (A)
        """
        id_ = ialpha * np.cos(theta) + ibeta * np.sin(theta)
        iq = -ialpha * np.sin(theta) + ibeta * np.cos(theta)
        return id_, iq
    
    def inverse_park_transform(self, vd: float, vq: float, theta: float) -> tuple:
        """Perform inverse Park transformation (dq -> alpha-beta).
        
        Args:
            vd: d-axis voltage (V)
            vq: q-axis voltage (V)
            theta: Electrical angle (rad)
            
        Returns:
            Tuple of (valpha, vbeta) voltages (V)
        """
        valpha = vd * np.cos(theta) - vq * np.sin(theta)
        vbeta = vd * np.sin(theta) + vq * np.cos(theta)
        return valpha, vbeta
    
    def update(self, id_meas: float, iq_meas: float, speed_meas: float, 
               theta: float, dt: float) -> tuple:
        """Update FOC controller.
        
        Args:
            id_meas: Measured d-axis current (A)
            iq_meas: Measured q-axis current (A)
            speed_meas: Measured mechanical speed (rad/s)
            theta: Electrical angle (rad)
            dt: Time step (s)
            
        Returns:
            Tuple of (vd, vq) voltages (V)
        """
        # Speed controller (if in speed mode)
        if self._mode == "speed":
            speed_error = self._speed_ref - speed_meas
            self._integral_speed += speed_error * dt
            
            # Anti-windup
            self._integral_speed = max(-100.0, min(100.0, self._integral_speed))
            
            # q-axis current reference from speed controller
            iq_ref = (self.params.Kp_speed * speed_error + 
                     self.params.Ki_speed * self._integral_speed)
            
            # Limit q-axis current reference
            iq_ref = max(-self.params.max_current, 
                        min(self.params.max_current, iq_ref))
        else:
            iq_ref = self._iq_ref
        
        # d-axis current controller
        id_error = self._id_ref - id_meas
        self._integral_d += id_error * dt
        
        # Anti-windup
        self._integral_d = max(-self.params.max_voltage, 
                              min(self.params.max_voltage, self._integral_d))
        
        vd = self.params.Kp_d * id_error + self.params.Ki_d * self._integral_d
        
        # q-axis current controller
        iq_error = iq_ref - iq_meas
        self._integral_q += iq_error * dt
        
        # Anti-windup
        self._integral_q = max(-self.params.max_voltage, 
                              min(self.params.max_voltage, self._integral_q))
        
        vq = self.params.Kp_q * iq_error + self.params.Ki_q * self._integral_q
        
        # Limit voltages
        vd = max(-self.params.max_voltage, min(self.params.max_voltage, vd))
        vq = max(-self.params.max_voltage, min(self.params.max_voltage, vq))
        
        return vd, vq
    
    def reset(self):
        """Reset controller state."""
        self._integral_d = 0.0
        self._integral_q = 0.0
        self._integral_speed = 0.0
    
    def get_state(self) -> Dict[str, Any]:
        """Get controller state.
        
        Returns:
            Dictionary of controller state
        """
        return {
            'mode': self._mode,
            'id_ref': self._id_ref,
            'iq_ref': self._iq_ref,
            'speed_ref': self._speed_ref,
            'integral_d': self._integral_d,
            'integral_q': self._integral_q,
            'integral_speed': self._integral_speed,
        }
