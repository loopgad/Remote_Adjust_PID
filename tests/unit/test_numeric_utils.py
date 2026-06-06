"""Tests for core.numeric_utils module."""

import math
import pytest
from param_id_gui.core.numeric_utils import guard_numeric


class TestGuardNumeric:
    """Test guard_numeric NaN/Inf protection."""

    def test_normal_float(self):
        assert guard_numeric(1.5, 0.0) == 1.5

    def test_normal_int(self):
        assert guard_numeric(42, 0.0) == 42

    def test_zero(self):
        assert guard_numeric(0.0, 0.0) == 0.0

    def test_negative(self):
        assert guard_numeric(-3.14, 0.0) == -3.14

    def test_nan_returns_default(self):
        assert guard_numeric(float('nan'), 0.0) == 0.0

    def test_inf_returns_default(self):
        assert guard_numeric(float('inf'), 0.0) == 0.0

    def test_neg_inf_returns_default(self):
        assert guard_numeric(float('-inf'), 0.0) == 0.0

    def test_custom_default(self):
        assert guard_numeric(float('nan'), 42.0) == 42.0

    def test_custom_default_inf(self):
        assert guard_numeric(float('inf'), -1.0) == -1.0

    def test_very_large_number(self):
        assert guard_numeric(1e308, 0.0) == 1e308

    def test_very_small_number(self):
        assert guard_numeric(1e-308, 0.0) == 1e-308
