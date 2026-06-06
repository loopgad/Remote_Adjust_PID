"""Power electronics models — battery and inverter.

Security:
  - CWE-754: NaN/Inf guards on all model inputs and outputs
"""

from typing import Any, Optional, Dict
from param_id_gui.core.numeric_utils import guard_numeric as _guard_num


class IdealBattery:
    """L0: Ideal voltage source."""

    def __init__(self, v_nom: float = 48.0):
        """Initialize ideal battery.

        Args:
            v_nom: Nominal voltage [V]
        """
        self.v_nom = _guard_num(v_nom, 48.0)
        self.v = self.v_nom

    def step(self, inputs: Dict[str, float] = None, dt_ns: int = 50000) -> Dict[str, float]:
        """Get battery voltage.

        Args:
            inputs: Input dictionary (i_load unused for ideal battery)
            dt_ns: Time step in nanoseconds

        Returns:
            Current state dictionary
        """
        return self.get_state()

    def reset(self) -> None:
        """Reset battery state."""
        self.v = self.v_nom

    def get_state(self) -> Dict[str, float]:
        """Get current battery state."""
        return {"voltage": self.v}

    def get_default_inputs(self) -> Dict[str, float]:
        """Get default inputs."""
        return {"i_load": 0.0}

    def get_output_ports(self) -> list:
        """Get output variable names for waveform display."""
        return ["voltage"]

    def configure(self, params: Dict[str, Any]) -> None:
        """Apply parameter dict to update model attributes."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, _guard_num(value, getattr(self, key, 0.0)))


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

    def step(self, inputs: Dict[str, float] = None, dt_ns: int = 50000) -> Dict[str, float]:
        """Get battery voltage under load.

        Args:
            inputs: Input dictionary with optional 'i_load' key
            dt_ns: Time step in nanoseconds

        Returns:
            Current state dictionary
        """
        i_load = (inputs or {}).get("i_load", 0.0)
        i_load = _guard_num(i_load, 0.0)
        self.v = max(0.0, self.v_oc - i_load * self.r_int)
        self.v = _guard_num(self.v, self.v_oc)
        return self.get_state()

    def reset(self) -> None:
        """Reset battery state."""
        self.v = self.v_oc

    def get_state(self) -> Dict[str, float]:
        """Get current battery state."""
        return {"voltage": self.v}

    def get_default_inputs(self) -> Dict[str, float]:
        """Get default inputs."""
        return {"i_load": 0.0}

    def get_output_ports(self) -> list:
        """Get output variable names for waveform display."""
        return ["voltage"]

    def configure(self, params: Dict[str, Any]) -> None:
        """Apply parameter dict to update model attributes."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, _guard_num(value, getattr(self, key, 0.0)))


class AverageInverter:
    """L2: Three-phase inverter averaged model.

    Converts duty cycles and DC bus voltage to phase voltages.
    """

    def __init__(self, v_bus: float = 48.0):
        """Initialize average inverter model.

        Args:
            v_bus: DC bus voltage [V]
        """
        self.v_bus = _guard_num(v_bus, 48.0)
        self._last_va = 0.0
        self._last_vb = 0.0
        self._last_vc = 0.0

    def step(self, inputs: Dict[str, float] = None, dt_ns: int = 50000) -> Dict[str, float]:
        """Compute three-phase output voltages with NaN/Inf guards.

        Args:
            inputs: Input dictionary with 'duty_a', 'duty_b', 'duty_c', optional 'v_bus'
            dt_ns: Time step in nanoseconds

        Returns:
            Current state dictionary
        """
        inp = inputs or {}
        da = max(0.0, min(1.0, _guard_num(inp.get("duty_a", 0.5), 0.5)))
        db = max(0.0, min(1.0, _guard_num(inp.get("duty_b", 0.5), 0.5)))
        dc = max(0.0, min(1.0, _guard_num(inp.get("duty_c", 0.5), 0.5)))

        v_bus = max(0.0, _guard_num(inp.get("v_bus", self.v_bus), 48.0))
        self.v_bus = v_bus

        self._last_va = _guard_num(v_bus * (da - 0.5), 0.0)
        self._last_vb = _guard_num(v_bus * (db - 0.5), 0.0)
        self._last_vc = _guard_num(v_bus * (dc - 0.5), 0.0)

        return self.get_state()

    def reset(self) -> None:
        """Reset inverter state."""
        self._last_va = 0.0
        self._last_vb = 0.0
        self._last_vc = 0.0

    def get_state(self) -> Dict[str, float]:
        """Get current inverter state."""
        return {
            "v_bus": self.v_bus,
            "va": self._last_va,
            "vb": self._last_vb,
            "vc": self._last_vc,
        }

    def get_default_inputs(self) -> Dict[str, float]:
        """Get default inputs."""
        return {"duty_a": 0.5, "duty_b": 0.5, "duty_c": 0.5, "v_bus": self.v_bus}

    def get_output_ports(self) -> list:
        """Get output variable names for waveform display."""
        return ["v_bus", "va", "vb", "vc"]

    def configure(self, params: Dict[str, Any]) -> None:
        """Apply parameter dict to update model attributes."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, _guard_num(value, getattr(self, key, 0.0)))


# ── DC-DC Converter Models ────────────────────────────────────


class _DCDCConverterBase:
    """Base class for DC-DC converter models (Buck/Boost).

    Subclasses implement `_compute_derivatives` with topology-specific equations.
    """

    def __init__(self, params):
        self.params = params
        self.state = {'iL': 0.0, 'vC': 0.0}
        self._duty_cycle = 0.5
        self._load_current = 0.0

    def set_input(self, duty_cycle: float, load_current: float = 0.0):
        self._duty_cycle = max(0.0, min(1.0, duty_cycle))
        self._load_current = load_current

    def get_state(self) -> Dict[str, float]:
        return self.state.copy()

    def get_default_inputs(self) -> Dict[str, float]:
        """Get default inputs for DC-DC converter."""
        return {"duty_cycle": 0.5, "load_current": 0.0}

    def get_output_ports(self) -> list:
        """Get output variable names for waveform display."""
        return ["iL", "vC"]

    def configure(self, params: Dict[str, Any]) -> None:
        """Apply parameter dict to update model attributes."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(self.params, key):
                setattr(self.params, key, value)

    def _compute_derivatives(self, iL: float, vC: float, d: float,
                             i_load: float, Vin: float, L: float,
                             C: float, R_load: float) -> tuple:
        raise NotImplementedError

    def update(self, dt: float) -> Dict[str, float]:
        Vin = self.params.Vin
        L = self.params.L
        C = self.params.C
        R_load = self.params.R_load

        iL = self.state['iL']
        vC = self.state['vC']
        d = self._duty_cycle
        i_load = self._load_current

        diL, dvC = self._compute_derivatives(iL, vC, d, i_load, Vin, L, C, R_load)

        self.state['iL'] = _guard_num(self.state['iL'] + diL * dt, 0.0)
        self.state['vC'] = _guard_num(self.state['vC'] + dvC * dt, 0.0)

        return self.get_state()

    def reset(self) -> None:
        self.state = {'iL': 0.0, 'vC': 0.0}
        self._duty_cycle = 0.5
        self._load_current = 0.0

    def get_output_voltage(self) -> float:
        return self.state['vC']

    def step(self, inputs: dict, dt_ns: int = 50000) -> dict:
        duty = inputs.get("duty_cycle", 0.5)
        load = inputs.get("load_current", 0.0)
        self.set_input(duty, load)
        dt = dt_ns / 1e9
        return self.update(dt)


class BuckConverter(_DCDCConverterBase):
    """Buck converter model for DC-DC power conversion."""

    def __init__(self, params: Optional['BuckConverterParams'] = None):
        from param_id_gui.core.types import BuckConverterParams
        super().__init__(params or BuckConverterParams())

    def _compute_derivatives(self, iL, vC, d, i_load, Vin, L, C, R_load):
        diL = (d * Vin - vC - R_load * iL) / L
        dvC = (iL - i_load - vC / R_load) / C
        return diL, dvC


class BoostConverter(_DCDCConverterBase):
    """Boost converter model for DC-DC power conversion."""

    def __init__(self, params: Optional['BoostConverterParams'] = None):
        from param_id_gui.core.types import BoostConverterParams
        super().__init__(params or BoostConverterParams())

    def _compute_derivatives(self, iL, vC, d, i_load, Vin, L, C, R_load):
        diL = (Vin - (1 - d) * vC - R_load * iL) / L
        dvC = ((1 - d) * iL - i_load - vC / R_load) / C
        return diL, dvC
