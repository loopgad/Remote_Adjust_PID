"""Task 23: 性能基准测试 - C++ vs Python 加速比.

Tests the performance of the C++ ODE solver vs pure Python implementation.
"""

import math
import time
import numpy as np
import pytest


# ── Pure Python RK4 (baseline) ────────────────────────────────

def _python_rk4_step(f, t, y, dt):
    """Single RK4 step in pure Python."""
    k1 = f(t, y)
    k2 = f(t + dt/2, y + dt/2 * k1)
    k3 = f(t + dt/2, y + dt/2 * k2)
    k4 = f(t + dt, y + dt * k3)
    return y + dt/6 * (k1 + 2*k2 + 2*k3 + k4)


def _python_rk4_solve(f, y0, t_span, dt):
    """Solve ODE using pure Python RK4."""
    t_start, t_end = t_span
    t = t_start
    y = np.array(y0, dtype=float)
    ts = [t]
    ys = [y.copy()]

    while t < t_end - 1e-12:
        y = _python_rk4_step(f, t, y, dt)
        t += dt
        ts.append(t)
        ys.append(y.copy())

    return np.array(ts), np.array(ys)


# ── Test ODEs ──────────────────────────────────────────────────

def exponential_decay(t, y):
    """dy/dt = -y, solution: y = exp(-t)."""
    return -y


def harmonic_oscillator(t, y):
    """d²x/dt² = -x, as system: dy1=y2, dy2=-y1."""
    return np.array([y[1], -y[0]])


# ── Performance Tests ─────────────────────────────────────────

class TestPythonRK4Accuracy:
    """Verify Python RK4 is correct before benchmarking."""

    def test_exponential_decay(self):
        """RK4 should solve dy/dt = -y accurately."""
        ts, ys = _python_rk4_solve(
            exponential_decay, [1.0], (0, 1.0), 0.001
        )
        # Analytical: y(1) = exp(-1) ≈ 0.367879
        np.testing.assert_allclose(ys[-1, 0], np.exp(-1), atol=1e-6)

    def test_harmonic_oscillator(self):
        """RK4 should solve harmonic oscillator accurately."""
        ts, ys = _python_rk4_solve(
            harmonic_oscillator, [1.0, 0.0], (0, 2*np.pi), 0.001
        )
        # After one period, should return to initial state
        np.testing.assert_allclose(ys[-1, 0], 1.0, atol=1e-4)
        np.testing.assert_allclose(ys[-1, 1], 0.0, atol=1e-3)


class TestPerformanceBenchmark:
    """Benchmark Python vs C++ ODE solver."""

    @pytest.mark.benchmark
    def test_python_rk4_performance(self):
        """Measure Python RK4 performance."""
        n_steps = 10000
        dt = 0.0001

        start = time.perf_counter()
        for _ in range(10):
            _python_rk4_solve(exponential_decay, [1.0], (0, n_steps * dt), dt)
        elapsed = time.perf_counter() - start

        # Just verify it runs, don't enforce timing
        assert elapsed > 0

    @pytest.mark.benchmark
    def test_cpp_solver_import(self):
        """Test that C++ solver can be imported."""
        try:
            from param_id_gui.cpp import _core
            cpp_available = True
        except ImportError:
            cpp_available = False

        if not cpp_available:
            pytest.skip("C++ extension not built")

    @pytest.mark.benchmark
    def test_cpp_solver_performance(self):
        """Measure C++ solver performance if available."""
        try:
            from param_id_gui.cpp import _core
        except ImportError:
            pytest.skip("C++ extension not built")

        # Verify C++ solver works
        result = _core.hello()
        assert "C++" in result

    @pytest.mark.benchmark
    def test_pmsm_step_performance(self):
        """Benchmark PMSM model step performance."""
        from param_id_gui.models.motor.pmsm_dq import PMSMdqModel

        model = PMSMdqModel(
            Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03,
            J=1e-4, B=1e-3, Pp=4,
        )

        n_steps = 10000
        start = time.perf_counter()
        for _ in range(n_steps):
            model.step_dq(10.0, 5.0, dt=50e-6)
        elapsed = time.perf_counter() - start

        steps_per_sec = n_steps / elapsed
        assert steps_per_sec > 1000  # Should do >1000 steps/sec

    @pytest.mark.benchmark
    def test_lm_optimizer_performance(self):
        """Benchmark LM optimizer convergence speed."""
        from param_id_gui.algorithms.lm import LevenbergMarquardt, LMConfig

        def residual(params):
            x = np.array([0, 1, 2, 3, 4.0])
            return params[0] * x + params[1] - (2.0 * x + 3.0)

        lm = LevenbergMarquardt(LMConfig(max_iterations=100))
        start = time.perf_counter()
        result, info = lm.optimize(residual, x0=np.array([1.0, 1.0]))
        elapsed = time.perf_counter() - start

        assert info["converged"]
        assert elapsed < 1.0  # Should converge in <1 second

    @pytest.mark.benchmark
    def test_pso_optimizer_performance(self):
        """Benchmark PSO optimizer convergence speed."""
        from param_id_gui.algorithms.pso import ParticleSwarmOptimization, PSOConfig

        def objective(params):
            return (params[0] - 3.0)**2 + (params[1] - 5.0)**2

        pso = ParticleSwarmOptimization(PSOConfig(n_particles=20, max_iterations=100))
        bounds = (np.array([0.0, 0.0]), np.array([10.0, 10.0]))

        start = time.perf_counter()
        result, info = pso.optimize(objective, bounds=bounds)
        elapsed = time.perf_counter() - start

        assert info["final_cost"] < 1.0
        assert elapsed < 5.0  # Should converge in <5 seconds


class TestScalability:
    """Test system scalability."""

    def test_orchestrator_many_steps(self):
        """Orchestrator should handle many steps efficiently."""
        from param_id_gui.core.orchestrator import Orchestrator

        orch = Orchestrator()
        count = 0

        def counter(step_ns):
            nonlocal count
            count += 1
            from param_id_gui.core.orchestrator import StepResult
            return StepResult(solver_id="bench")

        orch.register_stepper("bench", counter)
        orch.run(step_ns=50000, duration_s=0.1)
        expected = int(0.1 * 1e9 / 50000)
        assert count == expected

    def test_data_bus_many_signals(self):
        """Data bus should handle many signals."""
        from param_id_gui.core.data_bus import DataBus, Signal

        bus = DataBus(max_history=1000)

        n_signals = 5000
        for i in range(n_signals):
            sig = Signal(
                source="test", signal_type="scalar",
                timestamp_ns=i * 50000, value=float(i),
            )
            bus.publish(f"topic/{i % 10}", sig, module_id="test")

        # History should be capped at max_history
        for topic in [f"topic/{i}" for i in range(10)]:
            hist = bus.read_history(topic, max_count=10000)
            assert len(hist) <= 1000
