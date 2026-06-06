"""Security attack tests - NaN/Inf attacks, ACL bypass, guard functions.

Tests that security guards properly handle adversarial inputs including
NaN, Inf, overflow, boundary conditions, and injection attempts.
"""

import math
import numpy as np
import pytest

from param_id_gui.models.motor.pmsm_dq import PMSMdqModel, _guard_numeric
from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
from param_id_gui.core.data_bus import DataBus, Signal


# ── Model-Level Attack Tests ──────────────────────────────────

class TestModelSecurityAttacks:
    """Test that models resist adversarial inputs."""

    def test_pmsm_nan_voltage(self):
        """PMSM should handle NaN voltage inputs."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step_dq(float("nan"), 0.0, dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"NaN leaked: {state}"

    def test_pmsm_inf_voltage(self):
        """PMSM should handle Inf voltage inputs."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step_dq(float("inf"), float("-inf"), dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"Inf leaked: {state}"

    def test_pmsm_extreme_voltage(self):
        """PMSM should handle extreme voltage values."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step_dq(1e10, -1e10, dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"Extreme leaked: {state}"

    def test_pmsm_zero_dt(self):
        """PMSM should handle zero dt."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step_dq(10.0, 5.0, dt=0.0)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())

    def test_pmsm_negative_dt(self):
        """PMSM should handle negative dt."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step_dq(10.0, 5.0, dt=-1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())

    def test_buck_extreme_duty(self):
        """Buck converter should clamp extreme duty cycles."""
        model = BuckConverter()
        model.set_input(duty_cycle=100.0)  # Way out of range
        assert 0.0 <= model._duty_cycle <= 1.0

    def test_buck_negative_duty(self):
        """Buck converter should clamp negative duty cycle."""
        model = BuckConverter()
        model.set_input(duty_cycle=-100.0)
        assert model._duty_cycle >= 0.0

    def test_boost_extreme_duty(self):
        """Boost converter should clamp extreme duty cycles."""
        model = BoostConverter()
        model.set_input(duty_cycle=100.0)
        assert 0.0 <= model._duty_cycle <= 1.0


# ── Data Bus Attack Tests ─────────────────────────────────────

class TestDataBusSecurityAttacks:
    """Test data bus security against adversarial inputs."""

    def test_signal_source_normalized(self):
        """Signal source without '://' should be normalized."""
        sig = Signal(source="test_source", signal_type="data", value=1.0)
        assert "://" in sig.source

    def test_signal_negative_timestamp(self):
        """Signal with negative timestamp should log warning but not crash."""
        sig = Signal(source="test://source", signal_type="data",
                     timestamp_ns=-1, value=1.0)
        # Should not raise, just warn
        assert sig.timestamp_ns == -1


# ── Guard Function Tests ──────────────────────────────────────

class TestGuardFunctions:
    """Test _guard_numeric and similar safety functions."""

    def test_guard_numeric_normal(self):
        """Normal value should pass through."""
        assert _guard_numeric(42.0) == 42.0

    def test_guard_numeric_nan(self):
        """NaN should return fallback."""
        assert _guard_numeric(float("nan"), fallback=0.0) == 0.0

    def test_guard_numeric_inf(self):
        """Inf should return fallback."""
        assert _guard_numeric(float("inf"), fallback=99.0) == 99.0

    def test_guard_numeric_negative_inf(self):
        """-Inf should return fallback."""
        assert _guard_numeric(float("-inf"), fallback=-1.0) == -1.0

    def test_guard_numeric_zero(self):
        """Zero is valid, should return zero."""
        assert _guard_numeric(0.0) == 0.0
