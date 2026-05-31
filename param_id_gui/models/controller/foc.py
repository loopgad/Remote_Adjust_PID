"""FOC (Field-Oriented Control) and PID controllers.

Implements: Clarke/Park transforms, PI current loop, PI speed loop,
SVPWM modulation, anti-windup.

Security:
  - CWE-754: NaN/Inf guards on all numeric entry points
  - CWE-369: Zero-divide guard in svpwm (v_bus near-zero)
  - CWE-20: Input validation on PI update
"""

import math
import numpy as np

_PWM_EPS_V = 1e-12  # minimum bus voltage [V]


def _guard_numeric(value: float, fallback: float = 0.0) -> float:
    """Guard against NaN/Inf."""
    if math.isnan(value) or math.isinf(value):
        return fallback
    return value


# ── Coordinate Transforms (pure math: safe by construction) ──

def clarke_transform(ia: float, ib: float, ic: float) -> tuple:
    """Clarke: abc → αβ.

    Args:
        ia: Phase a current [A]
        ib: Phase b current [A]
        ic: Phase c current [A]

    Returns:
        Tuple of (i_alpha, i_beta) [A]
    """
    i_alpha = _guard_numeric(ia, 0.0)
    i_beta = (_guard_numeric(ia, 0.0) + 2 * _guard_numeric(ib, 0.0)) / math.sqrt(3)
    return i_alpha, i_beta


def park_transform(i_alpha: float, i_beta: float, theta: float) -> tuple:
    """Park: αβ → dq.

    Args:
        i_alpha: Alpha-axis current [A]
        i_beta: Beta-axis current [A]
        theta: Electrical angle [rad]

    Returns:
        Tuple of (id, iq) [A]
    """
    i_alpha = _guard_numeric(i_alpha, 0.0)
    i_beta = _guard_numeric(i_beta, 0.0)
    cos_t = math.cos(_guard_numeric(theta, 0.0))
    sin_t = math.sin(_guard_numeric(theta, 0.0))
    id_val = i_alpha * cos_t + i_beta * sin_t
    iq_val = -i_alpha * sin_t + i_beta * cos_t
    return id_val, iq_val


def inverse_park(vd: float, vq: float, theta: float) -> tuple:
    """Inverse Park: dq → αβ.

    Args:
        vd: d-axis voltage [V]
        vq: q-axis voltage [V]
        theta: Electrical angle [rad]

    Returns:
        Tuple of (v_alpha, v_beta) [V]
    """
    vd = _guard_numeric(vd, 0.0)
    vq = _guard_numeric(vq, 0.0)
    cos_t = math.cos(_guard_numeric(theta, 0.0))
    sin_t = math.sin(_guard_numeric(theta, 0.0))
    v_alpha = vd * cos_t - vq * sin_t
    v_beta = vd * sin_t + vq * cos_t
    return v_alpha, v_beta


# ── SVPWM ────────────────────────────────────────────────────

def svpwm(v_alpha: float, v_beta: float, v_bus: float) -> tuple:
    """Space Vector PWM — αβ voltages → 3-phase duty cycles.

    SECURITY (CWE-754): NaN/Inf guards, v_bus near-zero guard (CWE-369).
    Safe fallback: 50% duty on all phases = zero voltage output.

    Args:
        v_alpha: Alpha-axis voltage [V]
        v_beta: Beta-axis voltage [V]
        v_bus: DC bus voltage [V]

    Returns:
        Tuple of (da, db, dc) duty cycles in [0, 1]
    """
    v_alpha = _guard_numeric(v_alpha, 0.0)
    v_beta = _guard_numeric(v_beta, 0.0)
    v_bus = _guard_numeric(v_bus, 0.0)

    # SECURITY: v_bus near-zero → cannot modulate (CWE-369)
    if abs(v_bus) < _PWM_EPS_V:
        return (0.5, 0.5, 0.5)

    # Inverse Clarke
    va = v_alpha
    vb = -0.5 * v_alpha + math.sqrt(3) / 2 * v_beta
    vc = -0.5 * v_alpha - math.sqrt(3) / 2 * v_beta

    v_mid = v_bus / 2.0
    da = (va + v_mid) / v_bus
    db = (vb + v_mid) / v_bus
    dc = (vc + v_mid) / v_bus

    # Overmodulation
    v_min = min(da, db, dc)
    v_max = max(da, db, dc)
    diff = v_max - v_min
    if diff > 1.0:
        if diff > _PWM_EPS_V:
            scale = 1.0 / diff
            mid = (v_max + v_min) / 2
            da = (da - mid) * scale + 0.5
            db = (db - mid) * scale + 0.5
            dc = (dc - mid) * scale + 0.5

    # Clamp to [0, 1] with NaN guard
    da = _guard_numeric(da, 0.5)
    db = _guard_numeric(db, 0.5)
    dc = _guard_numeric(dc, 0.5)
    da = max(0.0, min(1.0, da))
    db = max(0.0, min(1.0, db))
    dc = max(0.0, min(1.0, dc))

    return da, db, dc


# ── PI Controller with Anti-Windup ───────────────────────────

class PIController:
    """Discrete-time PI controller with anti-windup.

    SECURITY (CWE-20): NaN/Inf guard on inputs (CWE-754).
    """

    def __init__(self, *, kp: float, ki: float, ts: float,
                 out_min: float = -float("inf"), out_max: float = float("inf"),
                 k_aw: float = None):
        """Initialize PI controller.

        Args:
            kp: Proportional gain
            ki: Integral gain
            ts: Sample time [s]
            out_min: Minimum output
            out_max: Maximum output
            k_aw: Anti-windup gain (default: ki/kp)
        """
        self.kp = _guard_numeric(kp, 1.0)
        self.ki = _guard_numeric(ki, 10.0)
        self.ts = max(_guard_numeric(ts, 1e-6), 1e-12)

        # Ensure out_min < out_max
        if out_min > out_max:
            out_min, out_max = out_max, out_min
        self.out_min = out_min if math.isfinite(out_min) else -1e6
        self.out_max = out_max if math.isfinite(out_max) else 1e6

        # Anti-windup gain: guard against kp=0 (CWE-369)
        if k_aw is not None:
            self.k_aw = _guard_numeric(k_aw, 1.0)
        else:
            self.k_aw = self.ki / self.kp if abs(self.kp) > 1e-12 else 1.0

        self.reset()

    def reset(self) -> None:
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_output = 0.0
        self.saturated = False

    def update(self, setpoint: float, measurement: float) -> float:
        """Compute control output with NaN/Inf guards.

        Args:
            setpoint: Reference value.
            measurement: Measured value.

        Returns:
            Control output, clamped to [out_min, out_max].
        """
        # SECURITY: Guard inputs (CWE-754)
        setpoint = _guard_numeric(setpoint, 0.0)
        measurement = _guard_numeric(measurement, 0.0)

        error = setpoint - measurement
        # Guard error
        error = _guard_numeric(error, 0.0)

        p_term = self.kp * error
        i_term = self.integral + self.ki * self.ts * error

        # Guard integral (CWE-754)
        i_term = _guard_numeric(i_term, self.integral)

        u_pre = p_term + i_term
        u = max(self.out_min, min(self.out_max, u_pre))
        self.saturated = (u != u_pre)

        # Back-calculation anti-windup
        if self.saturated:
            self.integral = u - p_term
            self.integral = max(self.out_min, min(self.out_max, self.integral))
        else:
            self.integral = i_term

        self.integral = _guard_numeric(self.integral, 0.0)
        self.prev_error = error
        self.prev_output = u
        return u


# ── FOC Current Controller ──────────────────────────────────

class FOCController:
    """Field-Oriented Control with dual PI current loops + SVPWM.

    SECURITY: NaN/Inf guards on all inputs.
    """

    def __init__(self, *, kp_id: float = 5.0, ki_id: float = 500.0,
                 kp_iq: float = 5.0, ki_iq: float = 500.0,
                 ts: float = 50e-6, v_bus: float = 48.0,
                 id_max: float = 100.0, iq_max: float = 200.0):
        """Initialize FOC controller.

        Args:
            kp_id: d-axis current PI proportional gain
            ki_id: d-axis current PI integral gain
            kp_iq: q-axis current PI proportional gain
            ki_iq: q-axis current PI integral gain
            ts: Sample time [s]
            v_bus: DC bus voltage [V]
            id_max: Maximum d-axis current [A]
            iq_max: Maximum q-axis current [A]
        """
        # Guard initialization parameters
        kp_id = _guard_numeric(kp_id, 5.0)
        ki_id = _guard_numeric(ki_id, 500.0)
        kp_iq = _guard_numeric(kp_iq, 5.0)
        ki_iq = _guard_numeric(ki_iq, 500.0)
        ts = max(_guard_numeric(ts, 50e-6), 1e-12)
        v_bus = max(_guard_numeric(v_bus, 48.0), 1.0)

        self.pi_id = PIController(kp=kp_id, ki=ki_id, ts=ts,
                                  out_min=-v_bus, out_max=v_bus)
        self.pi_iq = PIController(kp=kp_iq, ki=ki_iq, ts=ts,
                                  out_min=-v_bus, out_max=v_bus)
        self.v_bus = v_bus
        self.id_ref = 0.0
        self.iq_ref = 0.0
        self.vd_ref = 0.0
        self.vq_ref = 0.0
        self.duty_a = self.duty_b = self.duty_c = 0.5

    def update(self, ia: float, ib: float, ic: float, theta_e: float,
               id_ref: float, iq_ref: float) -> tuple:
        """Compute SVPWM duty cycles with input guarding.

        Args:
            ia: Phase a current [A]
            ib: Phase b current [A]
            ic: Phase c current [A]
            theta_e: Electrical angle [rad]
            id_ref: d-axis current reference [A]
            iq_ref: q-axis current reference [A]

        Returns:
            Tuple of (da, db, dc) duty cycles
        """
        # SECURITY: Guard inputs (CWE-754)
        ia = _guard_numeric(ia, 0.0)
        ib = _guard_numeric(ib, 0.0)
        ic = _guard_numeric(ic, 0.0)
        theta_e = _guard_numeric(theta_e, 0.0)
        id_ref = _guard_numeric(id_ref, 0.0)
        iq_ref = _guard_numeric(iq_ref, 0.0)

        self.id_ref = id_ref
        self.iq_ref = iq_ref

        i_alpha, i_beta = clarke_transform(ia, ib, ic)
        id_meas, iq_meas = park_transform(i_alpha, i_beta, theta_e)

        self.vd_ref = self.pi_id.update(id_ref, id_meas)
        self.vq_ref = self.pi_iq.update(iq_ref, iq_meas)

        v_alpha, v_beta = inverse_park(self.vd_ref, self.vq_ref, theta_e)
        self.duty_a, self.duty_b, self.duty_c = svpwm(v_alpha, v_beta, self.v_bus)

        return self.duty_a, self.duty_b, self.duty_c

    def reset(self) -> None:
        """Reset controller state."""
        self.pi_id.reset()
        self.pi_iq.reset()
        self.vd_ref = 0.0
        self.vq_ref = 0.0
        self.duty_a = self.duty_b = self.duty_c = 0.5


# ── Speed PI Controller ─────────────────────────────────────

class SpeedController:
    """Outer-loop PI speed controller producing iq_ref."""

    def __init__(self, *, kp: float, ki: float, ts: float,
                 iq_min: float = -200.0, iq_max: float = 200.0):
        """Initialize speed controller.

        Args:
            kp: Proportional gain
            ki: Integral gain
            ts: Sample time [s]
            iq_min: Minimum q-axis current reference [A]
            iq_max: Maximum q-axis current reference [A]
        """
        self.pi = PIController(kp=_guard_numeric(kp, 0.05),
                               ki=_guard_numeric(ki, 0.5),
                               ts=max(_guard_numeric(ts, 1e-3), 1e-12),
                               out_min=_guard_numeric(iq_min, -200.0),
                               out_max=_guard_numeric(iq_max, 200.0))

    def update(self, speed_ref: float, speed_meas: float) -> float:
        """Compute q-axis current reference.

        Args:
            speed_ref: Speed reference [rad/s]
            speed_meas: Measured speed [rad/s]

        Returns:
            q-axis current reference [A]
        """
        return self.pi.update(speed_ref, speed_meas)

    def reset(self) -> None:
        """Reset controller state."""
        self.pi.reset()


# ── Legacy compatibility ──────────────────────────────────────

from dataclasses import dataclass as _dataclass
from typing import Dict as _Dict, Any as _Any, Optional as _Optional


@_dataclass
class FOCParameters:
    """FOC controller parameters (legacy compatibility)."""
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


class FOCControllerLegacy:
    """Field-Oriented Control (FOC) controller (legacy compatibility wrapper).

    This class wraps FOCController for backward compatibility with
    the original interface.
    """

    def __init__(self, params: _Optional[FOCParameters] = None):
        """Initialize FOC controller.

        Args:
            params: FOC parameters (uses defaults if None)
        """
        self.params = params or FOCParameters()

        # Create wrapped FOC controller
        self._foc = FOCController(
            kp_id=self.params.Kp_d, ki_id=self.params.Ki_d,
            kp_iq=self.params.Kp_q, ki_iq=self.params.Ki_q,
            ts=50e-6, v_bus=self.params.max_voltage,
        )

        # PI controller states (for legacy interface)
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
        return clarke_transform(ia, ib, ic)

    def park_transform(self, ialpha: float, ibeta: float, theta: float) -> tuple:
        """Perform Park transformation (alpha-beta -> dq).

        Args:
            ialpha: Alpha-axis current (A)
            ibeta: Beta-axis current (A)
            theta: Electrical angle (rad)

        Returns:
            Tuple of (id, iq) currents (A)
        """
        return park_transform(ialpha, ibeta, theta)

    def inverse_park_transform(self, vd: float, vq: float, theta: float) -> tuple:
        """Perform inverse Park transformation (dq -> alpha-beta).

        Args:
            vd: d-axis voltage (V)
            vq: q-axis voltage (V)
            theta: Electrical angle (rad)

        Returns:
            Tuple of (valpha, vbeta) voltages (V)
        """
        return inverse_park(vd, vq, theta)

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

    def get_state(self) -> _Dict[str, _Any]:
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
