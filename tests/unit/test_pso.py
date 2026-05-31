"""Tests for Particle Swarm Optimization algorithm.

验证 PSO 算法在标准测试函数上的精度、收敛性和边界约束。
测试函数：Sphere、Rosenbrock、Rastrigin
"""

import time
import pytest
import numpy as np
from typing import Tuple

from param_id_gui.algorithms.pso import PSOConfig, ParticleSwarmOptimization


# ── 测试函数定义 ───────────────────────────────────────────────

def sphere(x: np.ndarray) -> float:
    """Sphere 函数: f(x) = sum(x_i^2)，全局最优 x* = [0, 0, ...]，f* = 0."""
    return float(np.sum(x ** 2))


def rosenbrock(x: np.ndarray) -> float:
    """Rosenbrock 函数: 全局最优 x* = [1, 1, ...]，f* = 0."""
    return float(np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2))


def rastrigin(x: np.ndarray) -> float:
    """Rastrigin 函数: 全局最优 x* = [0, 0, ...]，f* = 0."""
    n = len(x)
    return float(10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x)))


def shifted_sphere(x: np.ndarray) -> float:
    """平移 Sphere 函数: 全局最优 x* = [2, -1, 3]，f* = 0."""
    target = np.array([2.0, -1.0, 3.0])
    return float(np.sum((x - target) ** 2))


# ── 辅助函数 ───────────────────────────────────────────────────

def compute_relative_error(found: np.ndarray, expected: np.ndarray) -> float:
    """计算参数相对误差（归一化 L2 误差）。

    当期望值接近零时，使用绝对误差与参数范围归一化；
    否则使用相对于期望值幅度的归一化误差。
    """
    diff_norm = np.linalg.norm(found - expected)
    expected_norm = np.linalg.norm(expected)
    # 当期望值接近零时，使用绝对误差（以搜索空间尺度 1.0 为参考）
    if expected_norm < 1e-6:
        return float(diff_norm)
    return float(diff_norm / expected_norm)


def run_pso_optimize(
    objective_func,
    bounds: Tuple[np.ndarray, np.ndarray],
    config: PSOConfig | None = None,
    seed: int = 42,
) -> Tuple[np.ndarray, dict]:
    """以固定随机种子运行 PSO，确保结果可复现。"""
    np.random.seed(seed)
    pso = ParticleSwarmOptimization(config)
    return pso.optimize(objective_func, bounds)


# ── 精度验证测试 ────────────────────────────────────────────────

class TestPSOAccuracy:
    """PSO 算法在标准测试函数上的精度验证。"""

    def test_sphere_2d_accuracy(self):
        """Sphere 2D: 验证 PSO 找到全局最优 x*=[0,0]，绝对误差 < 0.5。"""
        bounds = (np.array([-10.0, -10.0]), np.array([10.0, 10.0]))
        config = PSOConfig(n_particles=80, max_iterations=800, tolerance=1e-10)
        result, info = run_pso_optimize(sphere, bounds, config)

        # expected 为零向量，使用绝对误差
        rel_error = compute_relative_error(result, np.array([0.0, 0.0]))
        assert rel_error < 0.5, (
            f"Sphere 2D 精度不足: 绝对误差 {rel_error:.6f} >= 0.5, "
            f"结果={result}, 期望=[0,0]"
        )
        assert info["final_cost"] < 0.25, (
            f"Sphere 2D 目标函数值过高: {info['final_cost']:.6f}"
        )

    def test_sphere_5d_accuracy(self):
        """Sphere 5D: 验证 PSO 在高维空间的精度，绝对误差 < 1.5。"""
        dim = 5
        bounds = (np.full(dim, -10.0), np.full(dim, 10.0))
        config = PSOConfig(n_particles=100, max_iterations=1000, tolerance=1e-10)
        result, info = run_pso_optimize(sphere, bounds, config, seed=123)

        expected = np.zeros(dim)
        rel_error = compute_relative_error(result, expected)
        assert rel_error < 1.5, (
            f"Sphere 5D 精度不足: 绝对误差 {rel_error:.6f} >= 1.5, "
            f"结果={result}"
        )

    def test_rosenbrock_2d_accuracy(self):
        """Rosenbrock 2D: 验证 PSO 找到 x*=[1,1]，相对误差 < 50%。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        config = PSOConfig(n_particles=80, max_iterations=2000, tolerance=1e-10)
        result, info = run_pso_optimize(rosenbrock, bounds, config, seed=456)

        expected = np.array([1.0, 1.0])
        rel_error = compute_relative_error(result, expected)
        assert rel_error < 0.50, (
            f"Rosenbrock 2D 精度不足: 相对误差 {rel_error:.6f} >= 50%, "
            f"结果={result}, 期望=[1,1]"
        )

    def test_rastrigin_2d_accuracy(self):
        """Rastrigin 2D: 验证 PSO 在多模态函数上的精度，绝对误差 < 1.0。"""
        bounds = (np.array([-5.12, -5.12]), np.array([5.12, 5.12]))
        config = PSOConfig(n_particles=100, max_iterations=2000, tolerance=1e-10)
        result, info = run_pso_optimize(rastrigin, bounds, config, seed=789)

        expected = np.array([0.0, 0.0])
        rel_error = compute_relative_error(result, expected)
        assert rel_error < 1.0, (
            f"Rastrigin 2D 精度不足: 绝对误差 {rel_error:.6f} >= 1.0, "
            f"结果={result}, 期望=[0,0]"
        )

    def test_shifted_sphere_accuracy(self):
        """平移 Sphere: 验证 PSO 识别非零最优参数，相对误差 < 10%。"""
        bounds = (np.array([-10.0, -10.0, -10.0]), np.array([10.0, 10.0, 10.0]))
        config = PSOConfig(n_particles=80, max_iterations=1000, tolerance=1e-10)
        result, info = run_pso_optimize(shifted_sphere, bounds, config, seed=321)

        expected = np.array([2.0, -1.0, 3.0])
        rel_error = compute_relative_error(result, expected)
        assert rel_error < 0.10, (
            f"Shifted Sphere 精度不足: 相对误差 {rel_error:.6f} >= 10%, "
            f"结果={result}, 期望=[2,-1,3]"
        )

    def test_final_cost_near_zero(self):
        """验证最终目标函数值接近理论最优（Sphere f*=0）。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        config = PSOConfig(n_particles=80, max_iterations=800, tolerance=1e-10)
        _, info = run_pso_optimize(sphere, bounds, config, seed=654)

        assert info["final_cost"] < 0.01, (
            f"最终目标函数值过高: {info['final_cost']:.8f}, 期望 < 0.01"
        )


# ── 收敛性测试 ──────────────────────────────────────────────────

class TestPSOConvergence:
    """PSO 算法收敛性测试。"""

    def test_convergence_on_sphere(self):
        """验证 PSO 在 Sphere 函数上收敛。"""
        bounds = (np.array([-10.0, -10.0]), np.array([10.0, 10.0]))
        config = PSOConfig(n_particles=50, max_iterations=500, tolerance=1e-8)
        _, info = run_pso_optimize(sphere, bounds, config, seed=111)

        assert info["converged"] is True, "PSO 未在最大迭代次数内收敛"
        assert info["iterations"] < config.max_iterations, (
            f"迭代次数 {info['iterations']} 达到上限 {config.max_iterations}"
        )

    def test_cost_history_decreasing(self):
        """验证代价函数历史单调非递增（全局最优不会变差）。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        config = PSOConfig(n_particles=50, max_iterations=300, tolerance=1e-8)
        _, info = run_pso_optimize(sphere, bounds, config, seed=222)

        history = info["cost_history"]
        assert len(history) > 1, "代价历史为空"
        for i in range(1, len(history)):
            assert history[i] <= history[i - 1] + 1e-12, (
                f"代价在迭代 {i} 处增加: {history[i-1]:.8e} -> {history[i]:.8e}"
            )

    def test_more_particles_faster_convergence(self):
        """验证增加粒子数减少迭代次数（在合理范围内）。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))

        # 使用相同随机种子，比较不同粒子数的迭代次数
        np.random.seed(42)
        config_few = PSOConfig(n_particles=20, max_iterations=500, tolerance=1e-6)
        pso_few = ParticleSwarmOptimization(config_few)
        _, info_few = pso_few.optimize(sphere, bounds)

        np.random.seed(42)
        config_many = PSOConfig(n_particles=80, max_iterations=500, tolerance=1e-6)
        pso_many = ParticleSwarmOptimization(config_many)
        _, info_many = pso_many.optimize(sphere, bounds)

        # 更多粒子应该达到更低的最终代价
        assert info_many["final_cost"] <= info_few["final_cost"] * 1.1, (
            f"更多粒子({config_many.n_particles})的代价 {info_many['final_cost']:.6e} "
            f"未优于更少粒子({config_few.n_particles})的代价 {info_few['final_cost']:.6e}"
        )

    def test_convergence_time_reasonable(self):
        """验证 PSO 收敛时间在合理范围内（< 30秒）。"""
        bounds = (np.array([-10.0, -10.0]), np.array([10.0, 10.0]))
        config = PSOConfig(n_particles=50, max_iterations=500, tolerance=1e-6)

        np.random.seed(333)
        pso = ParticleSwarmOptimization(config)
        start_time = time.time()
        _, info = pso.optimize(sphere, bounds)
        elapsed = time.time() - start_time

        assert elapsed < 30.0, f"收敛时间过长: {elapsed:.2f}秒 >= 30秒"
        assert info["iterations"] > 0, "迭代次数为 0"

    def test_high_tolerance_fewer_iterations(self):
        """验证高容差（宽松）比低容差（严格）需要更少迭代。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))

        np.random.seed(444)
        config_loose = PSOConfig(n_particles=50, max_iterations=500, tolerance=1e-2)
        pso_loose = ParticleSwarmOptimization(config_loose)
        _, info_loose = pso_loose.optimize(sphere, bounds)

        np.random.seed(444)
        config_tight = PSOConfig(n_particles=50, max_iterations=500, tolerance=1e-8)
        pso_tight = ParticleSwarmOptimization(config_tight)
        _, info_tight = pso_tight.optimize(sphere, bounds)

        assert info_loose["iterations"] <= info_tight["iterations"], (
            f"宽松容差迭代 {info_loose['iterations']} > 严格容差迭代 {info_tight['iterations']}"
        )


# ── 边界约束测试 ────────────────────────────────────────────────

class TestPSOBounds:
    """PSO 参数边界约束验证。"""

    def test_result_within_bounds(self):
        """验证优化结果严格在边界范围内。"""
        lower = np.array([-3.0, -3.0])
        upper = np.array([3.0, 3.0])
        bounds = (lower, upper)
        config = PSOConfig(n_particles=50, max_iterations=500)
        result, _ = run_pso_optimize(sphere, bounds, config)

        assert np.all(result >= lower), (
            f"结果 {result} 低于下界 {lower}"
        )
        assert np.all(result <= upper), (
            f"结果 {result} 超过上界 {upper}"
        )

    def test_asymmetric_bounds(self):
        """验证非对称边界下 PSO 正确工作。"""
        lower = np.array([-1.0, 0.0, 2.0])
        upper = np.array([5.0, 3.0, 8.0])
        bounds = (lower, upper)
        config = PSOConfig(n_particles=60, max_iterations=500, tolerance=1e-8)

        # 最优解 [2, -1, 3] 中 -1 超出下界，所以裁剪后最优在 [2, 0, 3]
        result, info = run_pso_optimize(shifted_sphere, bounds, config, seed=555)

        assert np.all(result >= lower), (
            f"结果 {result} 低于下界 {lower}"
        )
        assert np.all(result <= upper), (
            f"结果 {result} 超过上界 {upper}"
        )

    def test_tight_bounds(self):
        """验证紧缩边界下 PSO 仍能找到最优解。"""
        # 真实最优在 [0, 0]，给很紧的边界
        lower = np.array([-0.5, -0.5])
        upper = np.array([0.5, 0.5])
        bounds = (lower, upper)
        config = PSOConfig(n_particles=50, max_iterations=300, tolerance=1e-8)
        result, info = run_pso_optimize(sphere, bounds, config, seed=666)

        assert np.all(result >= lower) and np.all(result <= upper), (
            f"结果 {result} 超出边界 [{lower}, {upper}]"
        )
        assert info["final_cost"] < 0.01, (
            f"紧缩边界下代价过高: {info['final_cost']:.6f}"
        )

    def test_narrow_bounds_convergence(self):
        """验证窄边界下算法仍然收敛。"""
        lower = np.array([-1.0, -1.0])
        upper = np.array([1.0, 1.0])
        bounds = (lower, upper)
        config = PSOConfig(n_particles=30, max_iterations=300, tolerance=1e-6)
        _, info = run_pso_optimize(sphere, bounds, config, seed=777)

        assert info["converged"] is True or info["final_cost"] < 0.01, (
            f"窄边界下未收敛: converged={info['converged']}, "
            f"final_cost={info['final_cost']:.6e}"
        )


# ── 配置与接口测试 ──────────────────────────────────────────────

class TestPSOConfig:
    """PSO 配置和接口测试。"""

    def test_default_config(self):
        """验证默认配置值。"""
        config = PSOConfig()
        assert config.n_particles == 50
        assert config.max_iterations == 1000
        assert config.tolerance == 1e-6
        assert config.w == 0.7298
        assert config.c1 == 1.4962
        assert config.c2 == 1.4962
        assert config.w_decay == 0.99

    def test_custom_config(self):
        """验证自定义配置。"""
        config = PSOConfig(n_particles=30, max_iterations=200, w=0.5, c1=2.0, c2=2.0)
        assert config.n_particles == 30
        assert config.max_iterations == 200
        assert config.w == 0.5
        assert config.c1 == 2.0
        assert config.c2 == 2.0

    def test_get_history(self):
        """验证 get_history() 返回完整历史。"""
        np.random.seed(888)
        config = PSOConfig(n_particles=30, max_iterations=100, tolerance=1e-6)
        pso = ParticleSwarmOptimization(config)
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        pso.optimize(sphere, bounds)

        history = pso.get_history()
        assert len(history) > 0, "历史记录为空"
        assert len(history) <= config.max_iterations + 1, (
            f"历史长度 {len(history)} 超过最大迭代+1"
        )

    def test_get_iterations(self):
        """验证 get_iterations() 返回正确迭代次数。"""
        np.random.seed(999)
        config = PSOConfig(n_particles=30, max_iterations=100, tolerance=1e-6)
        pso = ParticleSwarmOptimization(config)
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        _, info = pso.optimize(sphere, bounds)

        assert pso.get_iterations() == info["iterations"], (
            f"get_iterations()={pso.get_iterations()} != "
            f"info['iterations']={info['iterations']}"
        )

    def test_x0_initialization(self):
        """验证 x0 参数被用作第一个粒子的初始位置。"""
        np.random.seed(101)
        config = PSOConfig(n_particles=10, max_iterations=50)
        pso = ParticleSwarmOptimization(config)
        bounds = (np.array([-10.0, -10.0]), np.array([10.0, 10.0]))

        # 提供接近最优的 x0 应该得到更好的结果
        x0 = np.array([0.1, 0.1])
        result, info = pso.optimize(sphere, bounds, x0=x0)

        assert info["final_cost"] < 1.0, (
            f"使用接近最优的 x0 后代价仍为 {info['final_cost']:.6f}"
        )


# ── 稳定性测试 ──────────────────────────────────────────────────

class TestPSOStability:
    """PSO 算法多次运行的稳定性测试。"""

    def test_multiple_runs_consistency(self):
        """多次运行 PSO 验证精度一致性（成功率 > 60%）。"""
        bounds = (np.array([-5.0, -5.0]), np.array([5.0, 5.0]))
        config = PSOConfig(n_particles=80, max_iterations=800, tolerance=1e-10)
        n_runs = 10
        success_count = 0

        for i in range(n_runs):
            np.random.seed(i * 100 + 42)
            pso = ParticleSwarmOptimization(config)
            result, info = pso.optimize(sphere, bounds)
            # expected 为零向量，使用绝对误差
            rel_error = compute_relative_error(result, np.array([0.0, 0.0]))
            if rel_error < 0.5:
                success_count += 1

        success_rate = success_count / n_runs
        assert success_rate >= 0.6, (
            f"成功率 {success_rate:.0%} < 60% ({success_count}/{n_runs} 次达标)"
        )

    def test_no_nan_in_result(self):
        """验证结果中不包含 NaN 或 Inf。"""
        bounds = (np.array([-10.0, -10.0]), np.array([10.0, 10.0]))
        config = PSOConfig(n_particles=50, max_iterations=300)
        result, info = run_pso_optimize(sphere, bounds, config, seed=1111)

        assert not np.any(np.isnan(result)), f"结果包含 NaN: {result}"
        assert not np.any(np.isinf(result)), f"结果包含 Inf: {result}"
        assert not np.isnan(info["final_cost"]), "最终代价为 NaN"
        assert not np.isinf(info["final_cost"]), "最终代价为 Inf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
