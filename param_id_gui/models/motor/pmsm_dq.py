"""PMSM dq-axis lumped-parameter model (L2 fidelity).

Suitable for: FOC control design, HIL simulation, real-time use.
Not suitable for: detailed torque ripple, cogging torque, magnetic saturation.

Security:
  - CWE-369: Zero-divide guard on Ld, Lq, J
  - CWE-754: NaN/Inf guards on all inputs and state transitions
"""

import math
import numpy as np

_MOTOR_EPS_L = 1e-12   # minimum inductance [H]
_MOTOR_EPS_J = 1e-15   # minimum inertia [kg·m²]


def _guard_numeric(value: float, fallback: float = 0.0) -> float:
    """Guard against NaN/Inf, return fallback."""
    if math.isnan(value) or math.isinf(value):
        return fallback
    return value


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

    def step(self, vd: float, vq: float, tl: float = 0.0,
             dt: float = None) -> None:
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

    def update_abc_currents(self) -> tuple:
        """Compute three-phase currents from dq currents.

        Returns:
            Tuple of (ia, ib, ic) currents [A]
        """
        theta = self.theta_e
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

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
        cos_t = math.cos(self.theta_e)
        sin_t = math.sin(self.theta_e)
        vd = v_alpha * cos_t + v_beta * sin_t
        vq = -v_alpha * sin_t + v_beta * cos_t
        self.step(vd, vq, tl, dt)

    def reset(self) -> None:
        """Reset model state to initial values."""
        self.id = 0.0
        self.iq = 0.0
        self.omega_m = 0.0
        self.theta_e = 0.0
        self.torque = 0.0
        self.ia = self.ib = self.ic = 0.0

    def get_state(self) -> dict:
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
        }


# ── Legacy compatibility ──────────────────────────────────────

# Keep PMSMParameters and PMSMModel for backward compatibility
from dataclasses import dataclass as _dataclass
from typing import Dict as _Dict, Any as _Any, Optional as _Optional


@_dataclass
class PMSMParameters:
    """PMSM model parameters (legacy compatibility)."""
    Rs: float = 0.5      # Stator resistance (Ohm)
    Ld: float = 0.005    # d-axis inductance (H)
    Lq: float = 0.005    # q-axis inductance (H)
    psi_f: float = 0.1   # Permanent magnet flux linkage (Wb)
    p: int = 4           # Number of pole pairs
    J: float = 0.001     # Moment of inertia (kg·m²)
    B: float = 0.001     # Viscous friction coefficient (N·m·s/rad)


class PMSMModel:
    """PMSM dq-axis model (legacy compatibility wrapper).

    This class wraps PMSMdqModel for backward compatibility with
    the original interface.
    """

    def __init__(self, params: _Optional[PMSMParameters] = None):
        """Initialize PMSM model.

        Args:
            params: PMSM parameters (uses defaults if None)
        """
        p = params or PMSMParameters()
        self._model = PMSMdqModel(
            Rs=p.Rs, Ld=p.Ld, Lq=p.Lq,
            flux_pm=p.psi_f, J=p.J, B=p.B, Pp=p.p
        )
        self.params = p
        self.state = {
            'id': 0.0, 'iq': 0.0,
            'omega': 0.0, 'theta': 0.0,
        }
        self._input = {
            'vd': 0.0, 'vq': 0.0, 'tl': 0.0,
        }

    def set_input(self, **kwargs):
        """Set model inputs."""
        self._input.update(kwargs)

    def get_state(self) -> _Dict[str, float]:
        """Get current model state."""
        s = self._model.get_state()
        return {
            'id': s['id'], 'iq': s['iq'],
            'omega': s['omega_m'], 'theta': s['theta_e'],
        }

    def update(self, dt: float) -> _Dict[str, float]:
        """Update model state for one time step."""
        self._model.step(
            self._input['vd'], self._input['vq'],
            self._input['tl'], dt
        )
        return self.get_state()

    def reset(self):
        """Reset model state to initial values."""
        self._model.reset()
        self.state = {
            'id': 0.0, 'iq': 0.0,
            'omega': 0.0, 'theta': 0.0,
        }
        self._input = {
            'vd': 0.0, 'vq': 0.0, 'tl': 0.0,
        }

    def get_torque(self) -> float:
        """Calculate electromagnetic torque."""
        return self._model.torque_em
