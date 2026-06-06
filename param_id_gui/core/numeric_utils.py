"""Numeric utility functions for NaN/Inf guards.

Shared across models and controllers to avoid duplication.
"""

import math
import functools


def guard_numeric(value: float, fallback: float = 0.0) -> float:
    """Guard against NaN/Inf, return fallback."""
    if math.isnan(value) or math.isinf(value):
        return fallback
    return value


@functools.lru_cache(maxsize=256)
def cached_cos_sin(theta: float) -> tuple:
    """Cached cos/sin for repeated theta values."""
    return math.cos(theta), math.sin(theta)


# Keep old names as aliases for backward compatibility
_guard_numeric = guard_numeric
_guard_num = guard_numeric
