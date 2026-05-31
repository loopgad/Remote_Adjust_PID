"""Task 24: 安全攻击测试 - 输入验证绕过、NaN/Inf 攻击.

Tests that security guards properly handle adversarial inputs including
NaN, Inf, overflow, boundary conditions, and injection attempts.
"""

import math
import numpy as np
import pytest

from param_id_gui.utils.validation import InputValidator
from param_id_gui.utils.safety import NumericalSafety
from param_id_gui.models.motor.pmsm_dq import PMSMdqModel, _guard_numeric
from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
from param_id_gui.core.orchestrator import Orchestrator
from param_id_gui.core.data_bus import DataBus, Signal


# ── Input Validation Attack Tests ─────────────────────────────

class TestInputValidationAttacks:
    """Test InputValidator against adversarial inputs."""

    def test_reject_non_numeric_string(self):
        """String input should be rejected."""
        with pytest.raises(TypeError, match="numeric"):
            InputValidator.validate_numeric("abc", "param")

    def test_reject_non_numeric_list(self):
        """List input should be rejected."""
        with pytest.raises(TypeError, match="numeric"):
            InputValidator.validate_numeric([1, 2, 3], "param")

    def test_reject_non_numeric_dict(self):
        """Dict input should be rejected."""
        with pytest.raises(TypeError, match="numeric"):
            InputValidator.validate_numeric({"a": 1}, "param")

    def test_reject_none_when_not_allowed(self):
        """None should be rejected when allow_none=False."""
        with pytest.raises(ValueError, match="cannot be None"):
            InputValidator.validate_numeric(None, "param")

    def test_accept_none_when_allowed(self):
        """None should be accepted when allow_none=True."""
        result = InputValidator.validate_numeric(None, "param", allow_none=True)
        assert result is None

    def test_accept_int(self):
        """Integer should be accepted."""
        result = InputValidator.validate_numeric(42, "param")
        assert result == 42.0

    def test_accept_float(self):
        """Float should be accepted."""
        result = InputValidator.validate_numeric(3.14, "param")
        assert result == 3.14

    def test_accept_numpy_types(self):
        """Numpy numeric types should be accepted."""
        assert InputValidator.validate_numeric(np.int64(42), "param") == 42.0
        assert InputValidator.validate_numeric(np.float64(3.14), "param") == 3.14

    def test_range_below_min(self):
        """Value below minimum should be rejected."""
        with pytest.raises(ValueError, match=">="):
            InputValidator.validate_range(-1.0, "param", min_value=0.0)

    def test_range_above_max(self):
        """Value above maximum should be rejected."""
        with pytest.raises(ValueError, match="<="):
            InputValidator.validate_range(101.0, "param", max_value=100.0)

    def test_range_within_bounds(self):
        """Value within bounds should be accepted."""
        result = InputValidator.validate_range(50.0, "param", min_value=0.0, max_value=100.0)
        assert result == 50.0

    def test_positive_rejects_zero(self):
        """Zero should be rejected for positive validation."""
        with pytest.raises(ValueError, match="positive"):
            InputValidator.validate_positive(0.0, "param")

    def test_positive_rejects_negative(self):
        """Negative should be rejected for positive validation."""
        with pytest.raises(ValueError, match="positive"):
            InputValidator.validate_positive(-1.0, "param")

    def test_non_negative_rejects_negative(self):
        """Negative should be rejected for non-negative validation."""
        with pytest.raises(ValueError, match="non-negative"):
            InputValidator.validate_non_negative(-0.001, "param")

    def test_array_shape_mismatch(self):
        """Wrong array shape should be rejected."""
        with pytest.raises(ValueError, match="shape"):
            InputValidator.validate_array([1, 2, 3], "param", shape=(2,))

    def test_enum_rejects_invalid(self):
        """Invalid enum value should be rejected."""
        with pytest.raises(ValueError, match="one of"):
            InputValidator.validate_enum("invalid", "param", ["a", "b", "c"])

    def test_dict_missing_required_keys(self):
        """Missing required keys should be rejected."""
        with pytest.raises(ValueError, match="missing required"):
            InputValidator.validate_dict({"a": 1}, "param", required_keys=["a", "b"])

    def test_callable_rejects_non_callable(self):
        """Non-callable should be rejected."""
        with pytest.raises(TypeError, match="callable"):
            InputValidator.validate_callable(42, "param")


# ── Numerical Safety Attack Tests ─────────────────────────────

class TestNumericalSafetyAttacks:
    """Test NumericalSafety against adversarial numerical inputs."""

    def test_nan_detection_scalar(self):
        """NaN scalar should be detected."""
        with pytest.raises(ValueError, match="NaN"):
            NumericalSafety.check_nan(float("nan"), "test")

    def test_nan_detection_array(self):
        """NaN in array should be detected."""
        with pytest.raises(ValueError, match="NaN"):
            NumericalSafety.check_nan(np.array([1.0, float("nan"), 3.0]), "test")

    def test_inf_detection_scalar(self):
        """Inf scalar should be detected."""
        with pytest.raises(ValueError, match="Inf"):
            NumericalSafety.check_inf(float("inf"), "test")

    def test_inf_detection_negative(self):
        """-Inf should be detected."""
        with pytest.raises(ValueError, match="Inf"):
            NumericalSafety.check_inf(float("-inf"), "test")

    def test_inf_detection_array(self):
        """Inf in array should be detected."""
        with pytest.raises(ValueError, match="Inf"):
            NumericalSafety.check_inf(np.array([1.0, float("inf")]), "test")

    def test_combined_nan_inf_detection(self):
        """Combined check should catch both."""
        with pytest.raises(ValueError):
            NumericalSafety.check_nan_inf(float("nan"), "test")
        with pytest.raises(ValueError):
            NumericalSafety.check_nan_inf(float("inf"), "test")

    def test_safe_divide_by_zero(self):
        """Division by zero should return default."""
        result = NumericalSafety.safe_divide(1.0, 0.0, default=999.0)
        assert result == 999.0

    def test_safe_divide_normal(self):
        """Normal division should work."""
        result = NumericalSafety.safe_divide(10.0, 2.0)
        assert result == 5.0

    def test_safe_sqrt_negative(self):
        """Square root of negative should return 0."""
        result = NumericalSafety.safe_sqrt(-1.0)
        assert result == 0.0

    def test_safe_log_zero(self):
        """Log of zero should return -inf."""
        result = NumericalSafety.safe_log(0.0)
        assert result == float("-inf")

    def test_safe_log_negative(self):
        """Log of negative should return -inf."""
        result = NumericalSafety.safe_log(-5.0)
        assert result == float("-inf")

    def test_clamp_above_max(self):
        """Value above max should be clamped."""
        assert NumericalSafety.clamp(100.0, 0.0, 50.0) == 50.0

    def test_clamp_below_min(self):
        """Value below min should be clamped."""
        assert NumericalSafety.clamp(-10.0, 0.0, 50.0) == 0.0

    def test_overflow_detection(self):
        """Very large value should trigger overflow warning."""
        with pytest.raises(ValueError, match="overflow"):
            NumericalSafety.check_overflow(1e309, "test", max_value=1e308)

    def test_safe_array_operation_nan_result(self):
        """Operation producing NaN should return default."""
        def bad_op():
            return np.array([float("nan")])

        result = NumericalSafety.safe_array_operation(bad_op, default=np.array([0.0]))
        np.testing.assert_array_equal(result, [0.0])

    def test_safe_array_operation_inf_result(self):
        """Operation producing Inf should return default."""
        def bad_op():
            return np.array([float("inf")])

        result = NumericalSafety.safe_array_operation(bad_op, default=np.array([0.0]))
        np.testing.assert_array_equal(result, [0.0])

    def test_safe_array_operation_exception(self):
        """Operation raising exception should return default."""
        def bad_op():
            raise RuntimeError("boom")

        result = NumericalSafety.safe_array_operation(bad_op, default=np.array([-1.0]))
        np.testing.assert_array_equal(result, [-1.0])


# ── Model-Level Attack Tests ──────────────────────────────────

class TestModelSecurityAttacks:
    """Test that models resist adversarial inputs."""

    def test_pmsm_nan_voltage(self):
        """PMSM should handle NaN voltage inputs."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step(float("nan"), 0.0, dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"NaN leaked: {state}"

    def test_pmsm_inf_voltage(self):
        """PMSM should handle Inf voltage inputs."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step(float("inf"), float("-inf"), dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"Inf leaked: {state}"

    def test_pmsm_extreme_voltage(self):
        """PMSM should handle extreme voltage values."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step(1e10, -1e10, dt=1e-5)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values()), f"Extreme leaked: {state}"

    def test_pmsm_zero_dt(self):
        """PMSM should handle zero dt."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step(10.0, 5.0, dt=0.0)
        state = model.get_state()
        assert all(math.isfinite(v) for v in state.values())

    def test_pmsm_negative_dt(self):
        """PMSM should handle negative dt."""
        model = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, B=1e-3, Pp=4)
        model.step(10.0, 5.0, dt=-1e-5)
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

    def test_unregistered_module_cannot_publish(self):
        """Unregistered module should not be able to publish to restricted topic."""
        bus = DataBus()
        bus.register_module("authorized")
        bus.restrict_topic("secure/topic", ["authorized"])

        sig = Signal(source="attacker", signal_type="data", value=1.0)

        # Unregistered module should raise PermissionError
        with pytest.raises(PermissionError):
            bus.publish("secure/topic", sig, module_id="unauthorized")

    def test_registered_module_can_publish(self):
        """Registered module should be able to publish."""
        bus = DataBus()
        bus.register_module("authorized")
        bus.restrict_topic("secure/topic", ["authorized"])

        sig = Signal(source="authorized", signal_type="data", value=42.0)
        bus.publish("secure/topic", sig, module_id="module://authorized")

        latest = bus.read_latest("secure/topic")
        assert latest is not None
        assert latest.value == 42.0

    def test_acl_blocks_wrong_module(self):
        """ACL should block modules not in the allowed list."""
        bus = DataBus()
        bus.register_module("mod_a")
        bus.register_module("mod_b")
        bus.restrict_topic("topic", ["mod_a"])

        sig = Signal(source="mod_b", signal_type="data", value=1.0)
        # mod_b not in ACL → silently dropped (no error)
        bus.publish("topic", sig, module_id="module://mod_b")

        # mod_b not in ACL, should be blocked
        latest = bus.read_latest("topic")
        assert latest is None

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
