"""Tests for OptimizationService — core layer abstraction."""

import numpy as np
import pytest

from param_id_gui.core.optimization_service import OptimizationService
from param_id_gui.core.types import LMConfig, PSOConfig


def _linear_residual(x):
    """Residual for y = 2*x + 1 at x_data=[1,2,3], y_data=[3,5,7]."""
    x_data = np.array([1.0, 2.0, 3.0])
    y_data = np.array([3.0, 5.0, 7.0])
    return y_data - (x[0] * x_data + x[1])


def _sphere(x):
    """Sphere function: sum(x^2)."""
    return np.sum(x**2)


class TestOptimizationServiceLM:
    def test_basic_lm(self):
        config = LMConfig(max_iterations=200, tolerance=1e-10)
        x0 = np.array([0.0, 0.0])
        result, info = OptimizationService.run_lm(config, _linear_residual, x0)
        assert abs(result[0] - 2.0) < 0.05
        assert abs(result[1] - 1.0) < 0.05
        assert info["final_cost"] < 0.01

    def test_lm_with_bounds(self):
        config = LMConfig(max_iterations=100)
        x0 = np.array([0.5, 0.5])
        lower = np.array([0.0, -10.0])
        upper = np.array([10.0, 10.0])
        result, info = OptimizationService.run_lm(
            config, _linear_residual, x0, bounds=(lower, upper)
        )
        assert result[0] >= 0.0
        assert result[1] >= -10.0

    def test_lm_with_callback(self):
        iterations = []
        config = LMConfig(max_iterations=50)
        x0 = np.array([0.0, 0.0])

        def cb(it, cost, params):
            iterations.append(it)
            return True

        result, info = OptimizationService.run_lm(config, _linear_residual, x0, progress_callback=cb)
        assert len(iterations) > 0

    def test_lm_callback_terminates(self):
        config = LMConfig(max_iterations=500)
        x0 = np.array([0.0, 0.0])

        def cb(it, cost, params):
            return it < 5

        result, info = OptimizationService.run_lm(config, _linear_residual, x0, progress_callback=cb)
        assert info["iterations"] <= 6


class TestOptimizationServicePSO:
    def test_basic_pso(self):
        config = PSOConfig(n_particles=30, max_iterations=200)
        lower = np.array([-5.0, -5.0])
        upper = np.array([5.0, 5.0])
        result, info = OptimizationService.run_pso(config, _sphere, (lower, upper))
        assert np.linalg.norm(result) < 1.0
        assert info["final_cost"] < 1.0

    def test_pso_with_x0(self):
        config = PSOConfig(n_particles=20, max_iterations=100)
        lower = np.array([-5.0])
        upper = np.array([5.0])
        x0 = np.array([1.0])
        result, info = OptimizationService.run_pso(config, _sphere, (lower, upper), x0=x0)
        assert abs(result[0]) < 1.0

    def test_pso_with_callback(self):
        iterations = []
        config = PSOConfig(n_particles=30, max_iterations=200, tolerance=1e-30)
        lower = np.array([-100.0, -100.0, -100.0, -100.0, -100.0])
        upper = np.array([100.0, 100.0, 100.0, 100.0, 100.0])

        def cb(it, cost, params):
            iterations.append(it)
            return True

        result, info = OptimizationService.run_pso(
            config, _sphere, (lower, upper), progress_callback=cb
        )
        assert len(iterations) > 0

    def test_pso_callback_terminates(self):
        config = PSOConfig(n_particles=10, max_iterations=100)
        lower = np.array([-5.0])
        upper = np.array([5.0])

        def cb(it, cost, params):
            return it < 3

        result, info = OptimizationService.run_pso(
            config, _sphere, (lower, upper), progress_callback=cb
        )
        assert info["iterations"] <= 4

    def test_pso_nan_objective(self):
        def nan_sphere(x):
            return float("nan")

        config = PSOConfig(n_particles=10, max_iterations=10)
        lower = np.array([-5.0])
        upper = np.array([5.0])
        result, info = OptimizationService.run_pso(config, nan_sphere, (lower, upper))
        assert np.all(np.isfinite(result))
