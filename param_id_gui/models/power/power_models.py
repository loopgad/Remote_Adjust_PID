"""Power electronics models — battery and inverter.

Security:
  - CWE-754: NaN/Inf guards on all model inputs and outputs
"""

import math


def _guard_num(value: float, fallback: float = 0.0) -> float:
    """Guard against NaN/Inf."""
    if math.isnan(value) or math.isinf(value):
        return fallback
    return value


class IdealBattery:
    """L0: Ideal voltage source."""

    def __init__(self, v_nom: float = 48.0):
        """Initialize ideal battery.

        Args:
            v_nom: Nominal voltage [V]
        """
        self.v_nom = _guard_num(v_nom, 48.0)
        self.v = self.v_nom

    def step(self, i_load: float = 0.0) -> float:
        """Get battery voltage.

        Args:
            i_load: Load current [A] (unused for ideal battery)

        Returns:
            Battery voltage [V]
        """
        return self.v

    def reset(self) -> None:
        """Reset battery state."""
        self.v = self.v_nom


class RintBattery:
    """L1: Battery with internal resistance (OCV + Rint)."""

    def __init__(self, v_oc: float = 48.0, r_int: float = 0.05):
        """Initialize battery with internal resistance.

        Args:
            v_oc: Open circuit voltage [V]
            r_int: Internal resistance [Ω]
        """
        self.v_oc = _guard_num(v_oc, 48.0)
        self.r_int = max(_guard_num(r_int, 0.05), 1e-9)
        self.v = self.v_oc

    def step(self, i_load: float = 0.0) -> float:
        """Get battery voltage under load.

        Args:
            i_load: Load current [A]

        Returns:
            Battery voltage [V]
        """
        i_load = _guard_num(i_load, 0.0)
        self.v = max(0.0, self.v_oc - i_load * self.r_int)
        self.v = _guard_num(self.v, self.v_oc)
        return self.v

    def reset(self) -> None:
        """Reset battery state."""
        self.v = self.v_oc


class AverageInverter:
    """L2: Three-phase inverter averaged model.

    Converts duty cycles and DC bus voltage to phase voltages.
    """

    def __init__(self, v_bus: float = 48.0, dead_time_ns: float = 200.0):
        """Initialize average inverter model.

        Args:
            v_bus: DC bus voltage [V]
            dead_time_ns: Dead time [ns]
        """
        self.v_bus = _guard_num(v_bus, 48.0)
        self.dead_time_ns = _guard_num(dead_time_ns, 200.0)

    def step(self, duty_a: float, duty_b: float, duty_c: float,
             v_bus: float = None, ia: float = 0.0, ib: float = 0.0,
             ic: float = 0.0) -> tuple:
        """Compute three-phase output voltages with NaN/Inf guards.

        Args:
            duty_a: Phase a duty cycle [0, 1]
            duty_b: Phase b duty cycle [0, 1]
            duty_c: Phase c duty cycle [0, 1]
            v_bus: DC bus voltage [V] (optional, uses default if None)
            ia: Phase a current [A] (unused in average model)
            ib: Phase b current [A] (unused in average model)
            ic: Phase c current [A] (unused in average model)

        Returns:
            Tuple of (va, vb, vc) phase voltages [V]
        """
        # Guard duty cycles (already in [0,1] from svpwm, but be safe)
        da = max(0.0, min(1.0, _guard_num(duty_a, 0.5)))
        db = max(0.0, min(1.0, _guard_num(duty_b, 0.5)))
        dc = max(0.0, min(1.0, _guard_num(duty_c, 0.5)))

        if v_bus is None:
            v_bus = self.v_bus
        else:
            self.v_bus = max(0.0, _guard_num(v_bus, 48.0))

        v_bus = max(0.0, _guard_num(v_bus, 48.0))

        va = v_bus * (da - 0.5)
        vb = v_bus * (db - 0.5)
        vc = v_bus * (dc - 0.5)

        return (_guard_num(va, 0.0), _guard_num(vb, 0.0), _guard_num(vc, 0.0))

    def reset(self) -> None:
        """Reset inverter state."""
        pass  # No state to reset for average model


# ── DC-DC Converter Models ────────────────────────────────────

from dataclasses import dataclass as _dataclass
from typing import Dict as _Dict, Any as _Any, Optional as _Optional


@_dataclass
class BuckConverterParameters:
    """Buck converter parameters."""
    Vin: float = 12.0      # Input voltage (V)
    L: float = 0.001       # Inductance (H)
    C: float = 0.0001      # Capacitance (F)
    R: float = 0.01        # ESR of capacitor (Ohm)
    Rl: float = 0.05       # Inductor resistance (Ohm)
    f_sw: float = 100000   # Switching frequency (Hz)


@_dataclass
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

    def __init__(self, params: _Optional[BuckConverterParameters] = None):
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

    def get_state(self) -> _Dict[str, float]:
        """Get current model state.

        Returns:
            Dictionary of state variables
        """
        return self.state.copy()

    def update(self, dt: float) -> _Dict[str, float]:
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

    def __init__(self, params: _Optional[BoostConverterParameters] = None):
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

    def get_state(self) -> _Dict[str, float]:
        """Get current model state.

        Returns:
            Dictionary of state variables
        """
        return self.state.copy()

    def update(self, dt: float) -> _Dict[str, float]:
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
