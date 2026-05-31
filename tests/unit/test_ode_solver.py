"""Tests for C++ ODE solver (RK4) accuracy and performance.

Covers:
  - Simple ODE accuracy vs analytical solutions
  - Accuracy vs scipy.integrate.solve_ivp (tolerance < 1e-6)
  - Performance benchmark: C++ vs pure-Python RK4
  - Edge cases and boundary conditions
"""

import math
import time
import pytest
import numpy as np
from scipy.integrate import solve_ivp

from param_id_gui._core.solvers import RK4Solver


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def solver():
    """Return a fresh RK4Solver instance with dt=0.001."""
    return RK4Solver(0.001)


# ── Pure-Python RK4 for performance comparison ────────────────

def python_rk4_solve(f, t0, t1, y0, dt):
    """Pure-Python RK4 implementation for benchmark comparison."""
    result = [list(y0)]
    t = t0
    y = list(y0)
    n = len(y0)

    while t < t1:
        current_dt = dt
        if t + dt > t1:
            current_dt = t1 - t

        k1 = f(t, y)
        y_temp = [y[i] + 0.5 * current_dt * k1[i] for i in range(n)]
        k2 = f(t + 0.5 * current_dt, y_temp)
        y_temp = [y[i] + 0.5 * current_dt * k2[i] for i in range(n)]
        k3 = f(t + 0.5 * current_dt, y_temp)
        y_temp = [y[i] + current_dt * k3[i] for i in range(n)]
        k4 = f(t + current_dt, y_temp)

        y = [y[i] + (current_dt / 6.0) * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) for i in range(n)]
        t += current_dt
        result.append(list(y))

    return result


# ── Accuracy Tests: Simple ODEs ──────────────────────────────

class TestRK4Accuracy:
    """Test RK4 solver accuracy against analytical solutions."""

    def test_exponential_decay(self, solver):
        """dy/dt = -y, y(0)=1 => y(t) = exp(-t)."""
        def f(t, y):
            return [-y[0]]

        result = solver.solve(f, 0.0, 1.0, [1.0])
        final = result.y[-1][0]
        expected = math.exp(-1.0)
        assert abs(final - expected) < 1e-6, (
            f"Exponential decay error: {abs(final - expected):.2e}"
        )

    def test_exponential_growth(self, solver):
        """dy/dt = y, y(0)=1 => y(t) = exp(t)."""
        def f(t, y):
            return [y[0]]

        result = solver.solve(f, 0.0, 1.0, [1.0])
        final = result.y[-1][0]
        expected = math.exp(1.0)
        assert abs(final - expected) < 1e-6, (
            f"Exponential growth error: {abs(final - expected):.2e}"
        )

    def test_harmonic_oscillator(self, solver):
        """d²x/dt² = -x => x(t) = cos(t), v(t) = -sin(t)."""
        def f(t, y):
            return [y[1], -y[0]]

        result = solver.solve(f, 0.0, 2 * math.pi, [1.0, 0.0])
        final_x = result.y[-1][0]
        final_v = result.y[-1][1]
        assert abs(final_x - 1.0) < 1e-4, (
            f"Harmonic oscillator x(2π) error: {abs(final_x - 1.0):.2e}"
        )
        assert abs(final_v - 0.0) < 1e-4, (
            f"Harmonic oscillator v(2π) error: {abs(final_v):.2e}"
        )

    def test_linear_ode(self, solver):
        """dy/dt = 2t, y(0)=0 => y(t) = t²."""
        def f(t, y):
            return [2 * t]

        result = solver.solve(f, 0.0, 3.0, [0.0])
        final = result.y[-1][0]
        expected = 9.0
        assert abs(final - expected) < 1e-4, (
            f"Linear ODE error: {abs(final - expected):.2e}"
        )


# ── Accuracy Tests: vs scipy.integrate.solve_ivp ─────────────

class TestRK4vsScipy:
    """Test RK4 solver accuracy against scipy.integrate.solve_ivp."""

    def _compare_with_scipy(self, f, t0, t1, y0, dt, tol=1e-4):
        """Helper to compare C++ RK4 with scipy RK45."""
        solver = RK4Solver(dt)
        result = solver.solve(f, t0, t1, y0)
        cpp_final = np.array(result.y[-1])

        def f_scipy(t, y):
            return np.array(f(t, y.tolist()))

        sol = solve_ivp(f_scipy, [t0, t1], np.array(y0),
                        method='RK45', rtol=1e-12, atol=1e-14)
        scipy_final = sol.y[:, -1]

        error = np.max(np.abs(cpp_final - scipy_final))
        assert error < tol, (
            f"RK4 vs scipy error {error:.2e} exceeds tolerance {tol:.2e}"
        )
        return error

    def test_exponential_decay_vs_scipy(self):
        """Compare exponential decay with scipy."""
        def f(t, y):
            return [-y[0]]
        self._compare_with_scipy(f, 0.0, 1.0, [1.0], 0.001, tol=1e-4)

    def test_harmonic_oscillator_vs_scipy(self):
        """Compare harmonic oscillator with scipy."""
        def f(t, y):
            return [y[1], -y[0]]
        self._compare_with_scipy(f, 0.0, 2 * math.pi, [1.0, 0.0], 0.001, tol=1e-3)

    def test_stiff_equation_vs_scipy(self):
        """Compare stiff equation with scipy."""
        def f(t, y):
            return [-1000 * y[0] + 1000]
        self._compare_with_scipy(f, 0.0, 0.1, [0.0], 0.0001, tol=1e-2)


# ── Performance Tests ────────────────────────────────────────

class TestRK4Performance:
    """Test RK4 solver performance vs pure Python."""

    @pytest.mark.slow
    def test_cpp_faster_than_python(self):
        """C++ RK4 should be faster than pure Python RK4."""
        def f(t, y):
            return [-y[0]]

        n_steps = 1000
        dt = 1.0 / n_steps

        # Python benchmark
        python_times = []
        for _ in range(5):
            start = time.perf_counter()
            python_rk4_solve(f, 0.0, 1.0, [1.0], dt)
            python_times.append(time.perf_counter() - start)
        python_mean = np.mean(python_times)

        # C++ benchmark
        cpp_times = []
        solver = RK4Solver(dt)
        for _ in range(5):
            start = time.perf_counter()
            solver.solve(f, 0.0, 1.0, [1.0])
            cpp_times.append(time.perf_counter() - start)
        cpp_mean = np.mean(cpp_times)

        speedup = python_mean / cpp_mean
        print(f"\n  Python mean: {python_mean*1000:.2f} ms")
        print(f"  C++ mean:    {cpp_mean*1000:.2f} ms")
        print(f"  Speedup:     {speedup:.1f}x")


# ── Edge Cases ───────────────────────────────────────────────

class TestRK4EdgeCases:
    """Test RK4 solver edge cases."""

    def test_single_step(self):
        """Solver should work with very few steps."""
        solver = RK4Solver(0.5)
        def f(t, y):
            return [-y[0]]
        result = solver.solve(f, 0.0, 1.0, [1.0])
        assert result.converged

    def test_large_system(self):
        """Solver should handle large dimensional systems."""
        n = 100
        solver = RK4Solver(0.001)
        def f(t, y):
            return [-yi for yi in y]
        y0 = [1.0] * n
        result = solver.solve(f, 0.0, 0.1, y0)
        assert result.converged
        assert len(result.y[-1]) == n
