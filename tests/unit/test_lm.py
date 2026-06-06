"""Tests for Levenberg-Marquardt optimization algorithm.

验证 LM 算法在标准测试函数上的精度、收敛性和边界约束。
测试函数：线性拟合、Rosenbrock、指数衰减
"""

import time
import pytest
import numpy as np
from typing import Tuple

from param_id_gui.algorithms.lm import LMConfig, LevenbergMarquardt


@pytest.fixture(autouse=True)
def _isolate_random():
    """Save and restore numpy global random state to prevent cross-test pollution."""
    state = np.random.get_state()
    yield
    np.random.set_state(state)


# ── 测试函数定义 ───────────────────────────────────────────────

def linear_residuals(params: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """线性拟合残差: y = a*x + b"""
    a, b = params
    return a * x + b - y


def linear_jacobian(params: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """线性拟合雅可比矩阵"""
    n = len(x)
    J = np.zeros((n, 2))
    J[:, 0] = x  # d/da
    J[:, 1] = 1.0  # d/db
    return J


def rosenbrock_residuals(params: np.ndarray) -> np.ndarray:
    """Rosenbrock 函数残差形式: f(x,y) = (1-x)^2 + 100*(y-x^2)^2"""
    x, y = params
    return np.array([1 - x, 10 * (y - x**2)])


def rosenbrock_jacobian(params: np.ndarray) -> np.ndarray:
    """Rosenbrock 雅可比矩阵"""
    x, y = params
    J = np.zeros((2, 2))
    J[0, 0] = -1
    J[0, 1] = 0
    J[1, 0] = -20 * x
    J[1, 1] = 10
    return J


def exponential_residuals(params: np.ndarray, t: np.ndarray, y: np.ndarray) -> np.ndarray:
    """指数衰减残差: y = A * exp(-lambda * t)"""
    A, lam = params
    return A * np.exp(-lam * t) - y


# ── 辅助函数 ───────────────────────────────────────────────────

def compute_relative_error(found: np.ndarray, expected: np.ndarray) -> float:
    """计算参数相对误差"""
    diff_norm = np.linalg.norm(found - expected)
    expected_norm = np.linalg.norm(expected)
    if expected_norm < 1e-6:
        return diff_norm
    return diff_norm / expected_norm


# ── 测试类 ─────────────────────────────────────────────────────

class TestLMConfig:
    """LM 配置测试"""

    def test_default_config(self):
        """默认配置值正确"""
        config = LMConfig()
        assert config.max_iterations == 1000
        assert config.tolerance == 1e-6
        assert config.lambda_init == 1e-3
        assert config.lambda_factor == 10.0

    def test_custom_config(self):
        """自定义配置"""
        config = LMConfig(max_iterations=500, tolerance=1e-8)
        assert config.max_iterations == 500
        assert config.tolerance == 1e-8


class TestLMLinearFitting:
    """线性拟合测试"""

    def test_perfect_linear_data(self):
        """完美线性数据: y = 2x + 1"""
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            jacobian_func=lambda p: linear_jacobian(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )

        error = compute_relative_error(result, np.array([2.0, 1.0]))
        assert error < 0.05, f"Linear fitting error {error:.4f} > 5%"
        assert info['converged']

    def test_noisy_linear_data(self):
        """带噪声的线性数据"""
        rng = np.random.default_rng(42)
        x_data = np.linspace(0, 10, 100)
        y_data = 3 * x_data - 2 + rng.normal(0, 0.1, 100)

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )

        # 允许更大误差因为有噪声
        error = compute_relative_error(result, np.array([3.0, -2.0]))
        assert error < 0.1, f"Noisy linear fitting error {error:.4f} > 10%"

    def test_with_bounds(self):
        """带参数边界约束"""
        x_data = np.linspace(0, 5, 30)
        y_data = 1.5 * x_data + 0.5

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0]),
            bounds=(np.array([0.0, 0.0]), np.array([5.0, 5.0]))
        )

        assert result[0] >= 0.0 and result[0] <= 5.0
        assert result[1] >= 0.0 and result[1] <= 5.0


class TestLMRosenbrock:
    """Rosenbrock 函数测试"""

    def test_rosenbrock_convergence(self):
        """Rosenbrock 函数收敛到 (1, 1)"""
        lm = LevenbergMarquardt(LMConfig(max_iterations=2000))
        result, info = lm.optimize(
            residual_func=rosenbrock_residuals,
            jacobian_func=rosenbrock_jacobian,
            x0=np.array([-1.0, -1.0])
        )

        error = compute_relative_error(result, np.array([1.0, 1.0]))
        assert error < 0.1, f"Rosenbrock error {error:.4f} > 10%"

    def test_rosenbrock_from_different_starts(self):
        """从不同起点收敛"""
        starts = [np.array([0.0, 0.0]), np.array([2.0, 2.0]), np.array([-2.0, 2.0])]

        for x0 in starts:
            lm = LevenbergMarquardt(LMConfig(max_iterations=2000))
            result, info = lm.optimize(
                residual_func=rosenbrock_residuals,
                jacobian_func=rosenbrock_jacobian,
                x0=x0
            )
            error = compute_relative_error(result, np.array([1.0, 1.0]))
            assert error < 0.2, f"Rosenbrock from {x0}: error {error:.4f}"


class TestLMExponentialDecay:
    """指数衰减测试"""

    def test_exponential_decay_fitting(self):
        """拟合指数衰减: y = 2 * exp(-0.5 * t)"""
        t_data = np.linspace(0, 5, 50)
        A_true, lam_true = 2.0, 0.5
        y_data = A_true * np.exp(-lam_true * t_data)

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: exponential_residuals(p, t_data, y_data),
            x0=np.array([1.0, 1.0])
        )

        error = compute_relative_error(result, np.array([A_true, lam_true]))
        assert error < 0.05, f"Exponential decay error {error:.4f} > 5%"


class TestLMConvergence:
    """收敛性测试"""

    def test_convergence_history(self):
        """验证收敛历史记录"""
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )

        history = lm.get_history()
        assert len(history) > 0
        # 成本应该单调递减
        for i in range(1, len(history)):
            assert history[i] <= history[i-1] + 1e-10

    def test_iteration_count(self):
        """验证迭代次数合理"""
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )

        iterations = lm.get_iterations()
        assert iterations > 0
        assert iterations < 1000  # 不应该用完所有迭代

    def test_final_cost_near_zero(self):
        """最终成本应该接近零"""
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )

        assert info['final_cost'] < 1e-10


class TestLMEdgeCases:
    """边界条件测试"""

    def test_already_at_optimum(self):
        """初始值已在最优点"""
        x_data = np.linspace(0, 10, 50)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([2.0, 1.0])
        )

        error = compute_relative_error(result, np.array([2.0, 1.0]))
        assert error < 1e-6

    def test_single_parameter(self):
        """单参数优化: y = a*x"""
        x_data = np.linspace(0, 10, 50)
        y_data = 3 * x_data

        lm = LevenbergMarquardt()
        result, info = lm.optimize(
            residual_func=lambda p: p[0] * x_data - y_data,
            x0=np.array([0.0])
        )

        assert abs(result[0] - 3.0) < 0.05

    def test_x0_none_raises(self, lm_config):
        lm = LevenbergMarquardt(config=lm_config)
        with pytest.raises(ValueError, match="x0"):
            lm.optimize(residual_func=lambda x: np.array([0.0]), x0=None)


class TestLMPerformance:
    """性能测试"""

    def test_convergence_time(self):
        """收敛时间合理"""
        x_data = np.linspace(0, 10, 100)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt()
        start = time.perf_counter()
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0])
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Convergence took {elapsed:.2f}s > 1s"


class TestLMProgressCallback:
    """进度回调测试（Bug #1+#2 附带功能）"""

    def test_callback_called(self):
        """回调被调用"""
        x_data = np.linspace(0, 10, 20)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt(LMConfig(max_iterations=50))
        call_log = []

        def callback(iteration, cost, params):
            call_log.append((iteration, cost))
            return True

        lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0]),
            progress_callback=callback
        )

        assert len(call_log) > 0
        assert call_log[0][0] == 1  # First iteration is 1

    def test_callback_returns_false_terminates(self):
        """回调返回 False 提前终止"""
        x_data = np.linspace(0, 10, 20)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt(LMConfig(max_iterations=1000))
        call_count = 0

        def callback(iteration, cost, params):
            nonlocal call_count
            call_count += 1
            return call_count < 2  # Stop after 2 calls

        lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0]),
            progress_callback=callback
        )

        assert call_count == 2

    def test_callback_none_no_error(self):
        """不传回调无异常"""
        x_data = np.linspace(0, 10, 20)
        y_data = 2 * x_data + 1

        lm = LevenbergMarquardt(LMConfig(max_iterations=10))
        result, info = lm.optimize(
            residual_func=lambda p: linear_residuals(p, x_data, y_data),
            x0=np.array([0.0, 0.0]),
            progress_callback=None
        )
        assert info['iterations'] > 0


class TestLMConvergenceCorrectness:
    """收敛检查正确性（C-3）"""

    def test_convergence_only_on_accepted_steps(self):
        """拒绝步不触发虚假收敛"""
        # Use a residual function that will cause rejections near the optimum
        # by having a very flat region
        def flat_residuals(params):
            x = params[0]
            if abs(x) < 0.1:
                # Very small residual near zero → small gradient → likely rejection
                return np.array([x * 1e-10])
            return np.array([x])

        lm = LevenbergMarquardt(LMConfig(
            max_iterations=50, tolerance=1e-12, lambda_init=1.0
        ))
        result, info = lm.optimize(
            residual_func=flat_residuals,
            x0=np.array([5.0])
        )

        # Should converge to near zero
        assert abs(result[0]) < 1.0, f"Didn't converge: x={result[0]}"
        # Cost history should be monotonically non-increasing
        history = info['cost_history']
        for i in range(1, len(history)):
            assert history[i] <= history[i-1] + 1e-15, (
                f"Cost increased at step {i}: {history[i-1]} -> {history[i]}"
            )


class TestLMNumericalStability:
    """数值稳定性测试（H-1/H-2/H-3）"""

    def test_singular_hessian_no_crash(self):
        """Hessian 对角线为零时阻尼矩阵不失效"""
        def zero_diag_residual(params):
            return np.array([params[1], params[1]])

        lm = LevenbergMarquardt(LMConfig(max_iterations=50))
        result, info = lm.optimize(
            residual_func=zero_diag_residual,
            x0=np.array([1.0, 1.0])
        )
        assert np.isfinite(result).all()
        assert abs(result[1]) < 0.5, f"x[1] didn't converge: {result[1]}"

    def test_adaptive_eps_different_scales(self):
        """不同量级参数精度合理"""
        x_data = np.linspace(0, 10, 50)
        true_a, true_b = 1e-3, 1e6
        y_data = true_a * x_data + true_b

        def residuals(params):
            return params[0] * x_data + params[1] - y_data

        lm = LevenbergMarquardt(LMConfig(max_iterations=200, tolerance=1e-12))
        result, info = lm.optimize(
            residual_func=residuals,
            x0=np.array([0.0, 0.0])
        )

        assert abs(result[0] - true_a) / max(abs(true_a), 1e-15) < 0.01, (
            f"a: expected {true_a}, got {result[0]}"
        )
        assert abs(result[1] - true_b) / max(abs(true_b), 1e-15) < 0.01, (
            f"b: expected {true_b}, got {result[1]}"
        )

    def test_zero_predicted_reduction_no_crash(self):
        """predicted_reduction 接近零时除法不溢出"""
        def flat_residual(params):
            return np.array([params[0] * 1e-15])

        lm = LevenbergMarquardt(LMConfig(max_iterations=10))
        result, info = lm.optimize(
            residual_func=flat_residual,
            x0=np.array([1.0])
        )
        assert np.isfinite(result).all()
