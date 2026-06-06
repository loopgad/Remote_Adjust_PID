"""PMSM dq-axis lumped-parameter model (L2 fidelity).

Suitable for: FOC control design, HIL simulation, real-time use.
Not suitable for: detailed torque ripple, cogging torque, magnetic saturation.

Security:
  - CWE-369: Zero-divide guard on Ld, Lq, J
  - CWE-754: NaN/Inf guards on all inputs and state transitions
"""

import math
from typing import Any, Dict, Optional, Tuple
from param_id_gui.core.numeric_utils import guard_numeric as _guard_numeric, cached_cos_sin as _cached_cos_sin

_MOTOR_EPS_L = 1e-12   # minimum inductance [H]
_MOTOR_EPS_J = 1e-15   # minimum inertia [kg·m²]


class PMSMdqModel:
    """PMSM dq-axis model with lumped parameters.

    Security: All input paths guarded against NaN/Inf (CWE-754).
    Zero-divide on Ld/Lq/J prevented (CWE-369).
    """

    def __init__(self, *, Rs: float, Ld: float, Lq: float,
                 flux_pm: float, J: float, B: float = 0.0,
                 Pp: int = 4, dt_ns: int = 50000):
        """Initialize PMSM dq model.

        Args:
            Rs: Stator resistance [Ω]
            Ld: d-axis inductance [H]
            Lq: q-axis inductance [H]
            flux_pm: Permanent magnet flux linkage [Wb]
            J: Moment of inertia [kg·m²]
            B: Viscous friction coefficient [N·m·s/rad]
            Pp: Number of pole pairs
            dt_ns: Default time step [ns]
        """
        self.Rs = _guard_numeric(Rs, 0.1)
        self.Ld = max(_guard_numeric(Ld, 5e-4), _MOTOR_EPS_L)
        self.Lq = max(_guard_numeric(Lq, 1e-3), _MOTOR_EPS_L)
        self.flux_pm = _guard_numeric(flux_pm, 0.03)
        self.J = max(_guard_numeric(J, 1e-3), _MOTOR_EPS_J)
        self.B = _guard_numeric(B, 0.0)
        self.Pp = max(1, int(Pp))
        self.dt = max(_guard_numeric(dt_ns / 1e9, 50e-6), 1e-12)

        self.id = 0.0
        self.iq = 0.0
        self.omega_m = 0.0
        self.theta_e = 0.0
        self.torque = 0.0
        self.ia = self.ib = self.ic = 0.0

    @property
    def omega_e(self) -> float:
        """Electrical angular velocity [rad/s]."""
        return self.Pp * self.omega_m

    @property
    def torque_em(self) -> float:
        """Electromagnetic torque [N·m]."""
        id_s = _guard_numeric(self.id, 0.0)
        iq_s = _guard_numeric(self.iq, 0.0)
        return 1.5 * self.Pp * (
            self.flux_pm * iq_s +
            (self.Ld - self.Lq) * id_s * iq_s
        )

    def step_dq(self, vd: float, vq: float, tl: float = 0.0,
             dt: Optional[float] = None) -> None:
        """Forward Euler integration with NaN/Inf and zero-divide guards.

        Args:
            vd: d-axis voltage [V].
            vq: q-axis voltage [V].
            tl: Load torque [N·m].
            dt: Time step [s], uses default if None.
        """
        # SECURITY: Guard inputs (CWE-754)
        vd = _guard_numeric(vd, 0.0)
        vq = _guard_numeric(vq, 0.0)
        tl = _guard_numeric(tl, 0.0)
        if dt is None:
            dt = self.dt
        else:
            dt = max(_guard_numeric(dt, self.dt), 1e-12)

        we = self.omega_e
        id_p, iq_p = self.id, self.iq

        # Electrical dynamics with zero-divide guard (CWE-369)
        did = (vd - self.Rs * id_p + we * self.Lq * iq_p) / self.Ld
        diq = (vq - self.Rs * iq_p - we * (self.Ld * id_p + self.flux_pm)) / self.Lq

        # Guard derivatives (CWE-754)
        did = _guard_numeric(did, 0.0)
        diq = _guard_numeric(diq, 0.0)

        self.id += did * dt
        self.iq += diq * dt

        # Guard state variables (CWE-754)
        self.id = _guard_numeric(self.id, 0.0)
        self.iq = _guard_numeric(self.iq, 0.0)

        # Mechanical dynamics with zero-divide guard
        self.torque = self.torque_em
        self.torque = _guard_numeric(self.torque, 0.0)
        dw = (self.torque - tl - self.B * self.omega_m) / self.J
        dw = _guard_numeric(dw, 0.0)
        self.omega_m += dw * dt
        self.omega_m = _guard_numeric(self.omega_m, 0.0)
        self.theta_e += self.Pp * self.omega_m * dt

        # Wrap theta_e to [0, 2π)
        self.theta_e = self.theta_e % (2 * math.pi)

    def step(self, inputs: dict, dt_ns: int = 50000) -> Dict[str, float]:
        """Protocol-compliant step method (ModelProtocol).

        Args:
            inputs: Dictionary with keys 'vd', 'vq', 'tl'.
            dt_ns: Time step in nanoseconds.

        Returns:
            Current state dictionary.
        """
        vd = inputs.get("vd", 0.0)
        vq = inputs.get("vq", 0.0)
        tl = inputs.get("tl", 0.0)
        dt = dt_ns / 1e9
        self.step_dq(vd, vq, tl, dt)
        self.update_abc_currents()
        return self.get_state()

    def update_abc_currents(self) -> Tuple[float, float, float]:
        """Compute three-phase currents from dq currents.

        Returns:
            Tuple of (ia, ib, ic) currents [A]
        """
        cos_t, sin_t = _cached_cos_sin(self.theta_e)

        ia_alpha = self.id * cos_t - self.iq * sin_t
        ia_beta = self.id * sin_t + self.iq * cos_t

        self.ia = _guard_numeric(ia_alpha, 0.0)
        self.ib = _guard_numeric(-0.5 * ia_alpha + math.sqrt(3) / 2 * ia_beta, 0.0)
        self.ic = _guard_numeric(-0.5 * ia_alpha - math.sqrt(3) / 2 * ia_beta, 0.0)
        return self.ia, self.ib, self.ic

    def step_abc(self, va: float, vb: float, vc: float, tl: float = 0.0,
                 dt: float = None) -> None:
        """Step with three-phase voltage inputs.

        Args:
            va: Phase a voltage [V]
            vb: Phase b voltage [V]
            vc: Phase c voltage [V]
            tl: Load torque [N·m]
            dt: Time step [s]
        """
        va = _guard_numeric(va, 0.0)
        vb = _guard_numeric(vb, 0.0)
        vc = _guard_numeric(vc, 0.0)
        v_alpha = va
        v_beta = (va + 2 * vb) / math.sqrt(3)
        cos_t, sin_t = _cached_cos_sin(self.theta_e)
        vd = v_alpha * cos_t + v_beta * sin_t
        vq = -v_alpha * sin_t + v_beta * cos_t
        self.step_dq(vd, vq, tl, dt)

    def reset(self) -> None:
        """Reset model state to initial values."""
        self.id = 0.0
        self.iq = 0.0
        self.omega_m = 0.0
        self.theta_e = 0.0
        self.torque = 0.0
        self.ia = self.ib = self.ic = 0.0

    def get_default_inputs(self) -> Dict[str, float]:
        """Get default inputs for PMSM model."""
        return {"vd": 0.0, "vq": 0.0, "tl": 0.0}

    def configure(self, params: Dict[str, Any]) -> None:
        """Apply parameter dict to update model attributes.

        Args:
            params: Dict with keys matching __init__ kwargs (Rs, Ld, Lq, flux_pm, J, B, Pp)
        """
        for key, value in params.items():
            if key == "Pp":
                value = max(1, int(value))
            elif key in ("Ld", "Lq"):
                value = max(_guard_numeric(value, 5e-4), _MOTOR_EPS_L)
            elif key == "J":
                value = max(_guard_numeric(value, 1e-3), _MOTOR_EPS_J)
            elif key in ("Rs", "flux_pm", "B"):
                value = _guard_numeric(value, getattr(self, key, 0.0))
            if hasattr(self, key):
                setattr(self, key, value)

    def get_state(self) -> Dict[str, float]:
        """Get current model state.

        Returns:
            Dictionary of state variables
        """
        return {
            "id": self.id, "iq": self.iq,
            "omega_m": self.omega_m, "theta_e": self.theta_e,
            "torque": self.torque,
            "ia": self.ia, "ib": self.ib, "ic": self.ic,
            "omega_e": self.omega_e,
            "speed": self.omega_m,
        }

    def get_output_ports(self) -> list:
        """Get output variable names for waveform display."""
        return ["ia", "ib", "ic", "va", "vb", "vc", "speed"]

