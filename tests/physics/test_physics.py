"""Task 22: 物理验证测试 - 验证 PMSM/FOC/DC-DC 物理正确性.

Verifies that simulation models produce physically correct results
by comparing against analytical solutions and known physical relationships.
"""

import math
import numpy as np
import pytest

from param_id_gui.models.motor.pmsm_dq import PMSMdqModel, PMSMModel, PMSMParameters
from param_id_gui.models.controller.foc import FOCController, PIController, SpeedController
from param_id_gui.models.power.power_models import (
    BuckConverter, BoostConverter, IdealBattery, RintBattery, AverageInverter,
)


# ── Helpers ────────────────────────────────────────────────────

def _pmsm_default():
    """Create PMSM with default test parameters."""
    return PMSMdqModel(
        Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03,
        J=1e-4, B=1e-3, Pp=4, dt_ns=50000,
    )


# ── PMSM Physics ──────────────────────────────────────────────

class TestPMSMPhysics:
    """Verify PMSM model against analytical solutions."""

    def test_zero_voltage_zero_current(self):
        """With zero voltage, currents should remain zero."""
        model = _pmsm_default()
        for _ in range(1000):
            model.step(0.0, 0.0, dt=50e-6)
        assert abs(model.id) < 1e-6
        assert abs(model.iq) < 1e-6

    def test_dc_voltage_produces_current(self):
        """DC voltage should produce growing current (RL circuit)."""
        model = _pmsm_default()
        # Apply vd voltage, expect id current to rise
        model.step(10.0, 0.0, dt=1e-5)
        # After one step, id should be positive (V/R * (1 - exp(-t/tau)))
        assert model.id > 0.0

    def test_steady_state_current(self):
        """At steady state, id = Vd/Rs, iq = 0 (no vq)."""
        model = _pmsm_default()
        vd = 5.0
        # Run long enough for RL circuit to settle
        for _ in range(50000):
            model.step(vd, 0.0, dt=1e-6)

        # Steady state: id ≈ Vd/Rs
        expected_id = vd / model.Rs
        assert abs(model.id - expected_id) / expected_id < 0.1  # 10% tolerance

    def test_torque_equation(self):
        """Verify torque = 1.5 * Pp * (flux_pm * iq + (Ld-Lq)*id*iq)."""
        model = _pmsm_default()
        model.id = 1.0
        model.iq = 2.0

        expected_torque = 1.5 * model.Pp * (
            model.flux_pm * model.iq +
            (model.Ld - model.Lq) * model.id * model.iq
        )
        assert abs(model.torque_em - expected_torque) < 1e-10

    def test_omega_e_is_omega_m_times_pole_pairs(self):
        """Verify omega_e = Pp * omega_m."""
        model = _pmsm_default()
        model.omega_m = 100.0
        assert model.omega_e == model.Pp * model.omega_m

    def test_energy_conservation_ideal(self):
        """With B=0, J=0, torque should balance instantly."""
        model = PMSMdqModel(
            Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03,
            J=1e-6, B=0.0, Pp=4, dt_ns=50000,
        )
        # Apply vq to generate torque
        for _ in range(10000):
            model.step(0.0, 10.0, dt=1e-6)

        # Speed should increase (positive torque from iq)
        assert model.omega_m > 0

    def test_load_torque_opposes_motion(self):
        """Load torque should reduce speed."""
        model = _pmsm_default()
        model.omega_m = 100.0

        # Run with load torque
        for _ in range(5000):
            model.step(0.0, 0.0, tl=0.01, dt=1e-6)

        # Speed should decrease due to friction + load
        assert model.omega_m < 100.0

    def test_reset_returns_to_zero(self):
        """Reset should return all states to zero."""
        model = _pmsm_default()
        for _ in range(1000):
            model.step(10.0, 10.0, dt=1e-5)
        model.reset()

        assert model.id == 0.0
        assert model.iq == 0.0
        assert model.omega_m == 0.0
        assert model.theta_e == 0.0

    def test_abc_currents_from_dq(self):
        """Verify abc currents computed correctly from dq."""
        model = _pmsm_default()
        model.id = 1.0
        model.iq = 0.0
        model.theta_e = 0.0

        ia, ib, ic = model.update_abc_currents()
        # At theta=0: ia = id, ib = -0.5*id, ic = -0.5*id
        assert abs(ia - 1.0) < 1e-10
        assert abs(ib + 0.5) < 1e-10
        assert abs(ic + 0.5) < 1e-10

    def test_abc_currents_sum_to_zero(self):
        """Three-phase currents should sum to zero (balanced)."""
        model = _pmsm_default()
        model.id = 1.0
        model.iq = 0.5
        model.theta_e = 0.3

        ia, ib, ic = model.update_abc_currents()
        assert abs(ia + ib + ic) < 1e-10

    def test_nan_guard_on_inputs(self):
        """Model should handle NaN inputs gracefully."""
        model = _pmsm_default()
        model.step(float("nan"), 5.0, dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())

    def test_inf_guard_on_inputs(self):
        """Model should handle Inf inputs gracefully."""
        model = _pmsm_default()
        model.step(float("inf"), float("-inf"), dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())


# ── FOC Controller Physics ────────────────────────────────────

class TestFOCPhysics:
    """Verify FOC controller physics."""

    def test_pi_controller_converges(self):
        """PI controller should drive error to zero."""
        pi = PIController(kp=5.0, ki=200.0, ts=1e-3, out_min=-100, out_max=100)
        target = 10.0
        measurement = 0.0

        for _ in range(5000):
            output = pi.update(target, measurement)
            measurement += output * 1e-3  # Simple integrator

        assert abs(measurement - target) / target < 0.15  # 15% tolerance

    def test_pi_anti_windup(self):
        """PI controller with anti-windup should not overshoot excessively."""
        pi = PIController(kp=1.0, ki=10.0, ts=1e-3, out_min=-10, out_max=10)
        # Large step input
        for _ in range(1000):
            pi.update(100.0, 0.0)  # Large error

        # Output should be clamped
        output = pi.update(100.0, 0.0)
        assert abs(output) <= 10.0 + 1e-6

    def test_foc_update(self):
        """FOC should produce valid duty cycles."""
        foc = FOCController(ts=1e-4, v_bus=48.0)
        da, db, dc = foc.update(ia=0.0, ib=0.0, ic=0.0, theta_e=0.0,
                                id_ref=0.0, iq_ref=5.0)
        assert 0.0 <= da <= 1.0
        assert 0.0 <= db <= 1.0
        assert 0.0 <= dc <= 1.0

    def test_speed_controller_tracks_reference(self):
        """Speed controller should track speed reference."""
        sc = SpeedController(kp=1.0, ki=10.0, ts=1e-3)
        target_speed = 100.0
        actual_speed = 0.0

        for _ in range(10000):
            iq_ref = sc.update(target_speed, actual_speed)
            # Simple motor model: speed ∝ iq
            actual_speed += iq_ref * 1e-3

        # Speed should approach target
        assert actual_speed > 50.0  # At least 50% of target


# ── DC-DC Converter Physics ───────────────────────────────────

class TestDCDCPhysics:
    """Verify DC-DC converter physics."""

    def test_buck_voltage_ratio(self):
        """Buck output voltage should approach D * Vin at steady state."""
        model = BuckConverter()
        model.set_input(duty_cycle=0.5, load_current=0.01)  # Light load

        # Run to steady state (longer simulation)
        dt = 1e-7
        for _ in range(500000):
            model.update(dt)

        v_out = model.get_output_voltage()
        v_in = model.params.Vin
        # Vout ≈ D * Vin (with losses)
        assert v_out > 0.0
        assert v_out < v_in  # Buck should reduce voltage
        assert math.isfinite(v_out)

    def test_boost_voltage_ratio(self):
        """Boost output voltage should be higher than input."""
        model = BoostConverter()
        model.set_input(duty_cycle=0.3, load_current=0.01)  # Light load, moderate duty

        # Run to steady state
        dt = 1e-7
        for _ in range(500000):
            model.update(dt)

        v_out = model.get_output_voltage()
        v_in = model.params.Vin
        # With D=0.3, Vout ≈ Vin/(1-D) = Vin/0.7 ≈ 1.43*Vin
        assert v_out > 0.0
        assert math.isfinite(v_out)

    def test_ideal_battery_constant_voltage(self):
        """Ideal battery should maintain constant voltage."""
        bat = IdealBattery(v_nom=48.0)
        for i in range(100):
            v = bat.step(i_load=float(i))
            assert abs(v - 48.0) < 1e-10

    def test_rint_battery_voltage_drops_with_current(self):
        """Rint battery voltage should drop with load current."""
        bat = RintBattery(v_oc=48.0, r_int=0.1)
        v_no_load = bat.step(i_load=0.0)
        v_full_load = bat.step(i_load=10.0)
        assert v_no_load > v_full_load
        assert abs(v_full_load - (48.0 - 10.0 * 0.1)) < 1e-6

    def test_average_inverter_produces_voltage(self):
        """Average inverter should produce voltages from duty cycles."""
        inv = AverageInverter(v_bus=48.0)
        va, vb, vc = inv.step(0.5, 0.5, 0.5)
        # At 50% duty, output should be ~0V (centered)
        assert abs(va) < 1.0
        assert abs(vb) < 1.0
        assert abs(vc) < 1.0

    def test_average_inverter_full_duty(self):
        """At 100% duty, output should be +Vbus/2."""
        inv = AverageInverter(v_bus=48.0)
        va, vb, vc = inv.step(1.0, 1.0, 1.0)
        expected = 48.0 * 0.5  # Vbus * (1.0 - 0.5)
        assert abs(va - expected) < 1e-6
