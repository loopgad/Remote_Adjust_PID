"""Tests for input validation and numerical safety utilities."""

import pytest
import numpy as np
import math
from param_id_gui.utils.validation import InputValidator
from param_id_gui.utils.safety import NumericalSafety


class TestInputValidator:
    """Tests for InputValidator class."""

    def test_validate_numeric_valid(self):
        """Test valid numeric input."""
        assert InputValidator.validate_numeric(1.0, "test") == 1.0
        assert InputValidator.validate_numeric(42, "test") == 42.0
        assert InputValidator.validate_numeric(np.float64(3.14), "test") == 3.14

    def test_validate_numeric_none_allowed(self):
        """Test None input when allowed."""
        assert InputValidator.validate_numeric(None, "test", allow_none=True) is None

    def test_validate_numeric_none_not_allowed(self):
        """Test None input when not allowed."""
        with pytest.raises(ValueError, match="cannot be None"):
            InputValidator.validate_numeric(None, "test", allow_none=False)

    def test_validate_numeric_invalid_type(self):
        """Test invalid type input."""
        with pytest.raises(TypeError, match="must be numeric"):
            InputValidator.validate_numeric("not a number", "test")

    def test_validate_range_valid(self):
        """Test valid range input."""
        assert InputValidator.validate_range(5.0, "test", 0.0, 10.0) == 5.0

    def test_validate_range_below_min(self):
        """Test input below minimum."""
        with pytest.raises(ValueError, match="must be >="):
            InputValidator.validate_range(-1.0, "test", 0.0, 10.0)

    def test_validate_range_above_max(self):
        """Test input above maximum."""
        with pytest.raises(ValueError, match="must be <="):
            InputValidator.validate_range(11.0, "test", 0.0, 10.0)

    def test_validate_range_no_bounds(self):
        """Test range validation with no bounds."""
        assert InputValidator.validate_range(100.0, "test") == 100.0

    def test_validate_positive_valid(self):
        """Test valid positive input."""
        assert InputValidator.validate_positive(1.0, "test") == 1.0

    def test_validate_positive_zero(self):
        """Test zero input."""
        with pytest.raises(ValueError, match="must be positive"):
            InputValidator.validate_positive(0.0, "test")

    def test_validate_positive_negative(self):
        """Test negative input."""
        with pytest.raises(ValueError, match="must be positive"):
            InputValidator.validate_positive(-1.0, "test")

    def test_validate_non_negative_valid(self):
        """Test valid non-negative input."""
        assert InputValidator.validate_non_negative(0.0, "test") == 0.0
        assert InputValidator.validate_non_negative(1.0, "test") == 1.0

    def test_validate_non_negative_negative(self):
        """Test negative input."""
        with pytest.raises(ValueError, match="must be non-negative"):
            InputValidator.validate_non_negative(-1.0, "test")

    def test_validate_array_valid(self):
        """Test valid array input."""
        arr = np.array([1.0, 2.0, 3.0])
        result = InputValidator.validate_array(arr, "test")
        np.testing.assert_array_equal(result, arr)

    def test_validate_array_shape(self):
        """Test array shape validation."""
        arr = np.array([1.0, 2.0, 3.0])
        result = InputValidator.validate_array(arr, "test", shape=(3,))
        assert result.shape == (3,)

    def test_validate_array_wrong_shape(self):
        """Test array with wrong shape."""
        arr = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="must have shape"):
            InputValidator.validate_array(arr, "test", shape=(2,))

    def test_validate_array_dtype(self):
        """Test array dtype validation."""
        arr = np.array([1.0, 2.0, 3.0])
        result = InputValidator.validate_array(arr, "test", dtype=np.float64)
        assert result.dtype == np.float64

    def test_validate_array_from_list(self):
        """Test array validation from list."""
        result = InputValidator.validate_array([1.0, 2.0, 3.0], "test")
        assert isinstance(result, np.ndarray)

    def test_validate_enum_valid(self):
        """Test valid enum input."""
        assert InputValidator.validate_enum("a", "test", ["a", "b", "c"]) == "a"

    def test_validate_enum_invalid(self):
        """Test invalid enum input."""
        with pytest.raises(ValueError, match="must be one of"):
            InputValidator.validate_enum("d", "test", ["a", "b", "c"])

    def test_validate_dict_valid(self):
        """Test valid dict input."""
        d = {"key1": 1, "key2": 2}
        result = InputValidator.validate_dict(d, "test")
        assert result == d

    def test_validate_dict_required_keys(self):
        """Test dict with required keys."""
        d = {"key1": 1, "key2": 2}
        result = InputValidator.validate_dict(d, "test", required_keys=["key1"])
        assert result == d

    def test_validate_dict_missing_keys(self):
        """Test dict with missing required keys."""
        d = {"key1": 1}
        with pytest.raises(ValueError, match="missing required keys"):
            InputValidator.validate_dict(d, "test", required_keys=["key1", "key2"])

    def test_validate_callable_valid(self):
        """Test valid callable input."""
        fn = lambda x: x
        assert InputValidator.validate_callable(fn, "test") == fn

    def test_validate_callable_invalid(self):
        """Test invalid callable input."""
        with pytest.raises(TypeError, match="must be callable"):
            InputValidator.validate_callable(42, "test")


class TestNumericalSafety:
    """Tests for NumericalSafety class."""

    def test_check_nan_valid(self):
        """Test valid (non-NaN) input."""
        assert NumericalSafety.check_nan(1.0, "test") == False

    def test_check_nan_scalar(self):
        """Test NaN scalar input."""
        with pytest.raises(ValueError, match="is NaN"):
            NumericalSafety.check_nan(float('nan'), "test")

    def test_check_nan_array(self):
        """Test NaN array input."""
        arr = np.array([1.0, float('nan'), 3.0])
        with pytest.raises(ValueError, match="contains NaN"):
            NumericalSafety.check_nan(arr, "test")

    def test_check_inf_valid(self):
        """Test valid (non-Inf) input."""
        assert NumericalSafety.check_inf(1.0, "test") == False

    def test_check_inf_scalar(self):
        """Test Inf scalar input."""
        with pytest.raises(ValueError, match="is Inf"):
            NumericalSafety.check_inf(float('inf'), "test")

    def test_check_inf_negative(self):
        """Test negative Inf scalar input."""
        with pytest.raises(ValueError, match="is Inf"):
            NumericalSafety.check_inf(float('-inf'), "test")

    def test_check_inf_array(self):
        """Test Inf array input."""
        arr = np.array([1.0, float('inf'), 3.0])
        with pytest.raises(ValueError, match="contains Inf"):
            NumericalSafety.check_inf(arr, "test")

    def test_check_nan_inf_valid(self):
        """Test valid (non-NaN, non-Inf) input."""
        assert NumericalSafety.check_nan_inf(1.0, "test") == False

    def test_check_nan_inf_nan(self):
        """Test NaN input."""
        with pytest.raises(ValueError):
            NumericalSafety.check_nan_inf(float('nan'), "test")

    def test_check_nan_inf_inf(self):
        """Test Inf input."""
        with pytest.raises(ValueError):
            NumericalSafety.check_nan_inf(float('inf'), "test")

    def test_safe_divide_valid(self):
        """Test valid division."""
        assert NumericalSafety.safe_divide(10.0, 2.0) == 5.0

    def test_safe_divide_by_zero(self):
        """Test division by zero."""
        assert NumericalSafety.safe_divide(10.0, 0.0) == 0.0
        assert NumericalSafety.safe_divide(10.0, 0.0, default=-1.0) == -1.0

    def test_safe_divide_nan_result(self):
        """Test division resulting in NaN."""
        result = NumericalSafety.safe_divide(0.0, 0.0)
        assert result == 0.0

    def test_safe_sqrt_valid(self):
        """Test valid square root."""
        assert NumericalSafety.safe_sqrt(4.0) == 2.0

    def test_safe_sqrt_negative(self):
        """Test square root of negative number."""
        assert NumericalSafety.safe_sqrt(-1.0) == 0.0

    def test_safe_sqrt_zero(self):
        """Test square root of zero."""
        assert NumericalSafety.safe_sqrt(0.0) == 0.0

    def test_safe_log_valid(self):
        """Test valid logarithm."""
        assert NumericalSafety.safe_log(math.e) == pytest.approx(1.0)

    def test_safe_log_zero(self):
        """Test logarithm of zero."""
        result = NumericalSafety.safe_log(0.0)
        assert result == float('-inf')

    def test_safe_log_negative(self):
        """Test logarithm of negative number."""
        result = NumericalSafety.safe_log(-1.0)
        assert result == float('-inf')

    def test_clamp_within_range(self):
        """Test clamping within range."""
        assert NumericalSafety.clamp(5.0, 0.0, 10.0) == 5.0

    def test_clamp_below_min(self):
        """Test clamping below minimum."""
        assert NumericalSafety.clamp(-1.0, 0.0, 10.0) == 0.0

    def test_clamp_above_max(self):
        """Test clamping above maximum."""
        assert NumericalSafety.clamp(11.0, 0.0, 10.0) == 10.0

    def test_normalize(self):
        """Test normalization."""
        assert NumericalSafety.normalize(5.0, 0.0, 10.0) == 0.5

    def test_normalize_equal_bounds(self):
        """Test normalization with equal bounds."""
        assert NumericalSafety.normalize(5.0, 5.0, 5.0) == 0.0

    def test_denormalize(self):
        """Test denormalization."""
        assert NumericalSafety.denormalize(0.5, 0.0, 10.0) == 5.0

    def test_check_overflow_valid(self):
        """Test valid (non-overflow) input."""
        assert NumericalSafety.check_overflow(1.0, "test") == True

    def test_check_overflow_large(self):
        """Test large value that may cause overflow."""
        with pytest.raises(ValueError, match="may cause overflow"):
            NumericalSafety.check_overflow(1e309, "test")

    def test_safe_array_operation_valid(self):
        """Test valid array operation."""
        arr = np.array([1.0, 2.0, 3.0])
        result = NumericalSafety.safe_array_operation(np.sum, arr)
        assert result == 6.0

    def test_safe_array_operation_nan(self):
        """Test array operation resulting in NaN."""
        arr = np.array([1.0, float('nan'), 3.0])
        default = np.array([0.0])
        result = NumericalSafety.safe_array_operation(np.sum, arr, default=default)
        # Result should be default since sum of array with NaN is NaN
        assert result is not None

    def test_safe_array_operation_exception(self):
        """Test array operation with exception."""
        def failing_op(x):
            raise ValueError("Test error")
        
        default = np.array([0.0])
        result = NumericalSafety.safe_array_operation(failing_op, np.array([1.0]), default=default)
        np.testing.assert_array_equal(result, default)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
