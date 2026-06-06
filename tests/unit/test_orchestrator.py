"""Tests for Simulation Orchestrator.

验证仿真编排器的功能：生命周期管理、故障注入、能量审计、自动步长调整。
"""

import time
import threading
import pytest
import numpy as np
from unittest.mock import MagicMock

from param_id_gui.core.orchestrator import (
    GlobalClock, StepResult, ConvergenceAudit, OrchestratorConfig,
    Orchestrator, SimulationState
)


# ── GlobalClock 测试 ─────────────────────────────────────────

class TestGlobalClock:
    """GlobalClock 测试"""

    def test_initial_state(self):
        """初始状态正确"""
        clock = GlobalClock(dt_ns=50000)
        assert clock.dt_ns == 50000
        assert clock.sim_time_ns == 0
        assert clock.step_count == 0
        assert not clock.diverged

    def test_properties(self):
        """属性转换正确"""
        clock = GlobalClock(dt_ns=50000)
        assert clock.dt_s == pytest.approx(5e-5)
        assert clock.sim_time_s == pytest.approx(0.0)

    def test_advance(self):
        """时钟推进正确"""
        clock = GlobalClock(dt_ns=50000)
        clock.advance(50000)
        assert clock.sim_time_ns == 50000
        assert clock.step_count == 1
        assert clock.sim_time_s == pytest.approx(5e-5)

    def test_multiple_advance(self):
        """多次推进"""
        clock = GlobalClock(dt_ns=50000)
        for _ in range(100):
            clock.advance(50000)
        assert clock.step_count == 100
        assert clock.sim_time_ns == 5000000

    def test_divergence(self):
        """发散标记"""
        clock = GlobalClock()
        assert not clock.diverged
        clock.mark_diverged()
        assert clock.diverged

    def test_reset(self):
        """重置正确"""
        clock = GlobalClock()
        clock.advance(100000)
        clock.mark_diverged()
        clock.reset()
        assert clock.sim_time_ns == 0
        assert clock.step_count == 0
        assert not clock.diverged


# ── StepResult 测试 ──────────────────────────────────────────

class TestStepResult:
    """StepResult 测试"""

    def test_default_values(self):
        """默认值正确"""
        result = StepResult(solver_id="test")
        assert result.solver_id == "test"
        assert result.converged is True
        assert result.error_estimate == 0.0
        assert result.computation_ns == 0

    def test_custom_values(self):
        """自定义值"""
        result = StepResult(
            solver_id="solver1",
            converged=False,
            error_estimate=0.05,
            computation_ns=1000
        )
        assert result.solver_id == "solver1"
        assert not result.converged
        assert result.error_estimate == 0.05
        assert result.computation_ns == 1000


# ── ConvergenceAudit 测试 ──────────────────────────────────────

class TestConvergenceAudit:
    """ConvergenceAudit 测试"""

    def test_default_values(self):
        """默认值正确"""
        audit = ConvergenceAudit()
        assert audit.max_error == 0.0
        assert audit.avg_error == 0.0
        assert audit.sample_count == 0

    def test_convergence_pct_no_error(self):
        """无误差时收敛度100%"""
        audit = ConvergenceAudit(max_error=0.0)
        assert audit.convergence_pct == pytest.approx(100.0)

    def test_convergence_pct_with_error(self):
        """有误差时收敛度正确计算"""
        audit = ConvergenceAudit(max_error=0.5, avg_error=0.2, sample_count=100)
        assert audit.convergence_pct == pytest.approx(50.0)

    def test_convergence_pct_full_divergence(self):
        """误差≥1时收敛度为0"""
        audit = ConvergenceAudit(max_error=1.0)
        assert audit.convergence_pct == pytest.approx(0.0)
        audit2 = ConvergenceAudit(max_error=2.0)
        assert audit2.convergence_pct == pytest.approx(0.0)


# ── OrchestratorConfig 测试 ──────────────────────────────────

class TestOrchestratorConfig:
    """OrchestratorConfig 测试"""

    def test_default_config(self):
        """默认配置正确"""
        config = OrchestratorConfig()
        assert config.dt_ns == 50000
        assert config.enable_energy_audit is True
        assert config.energy_audit_period_steps == 1000
        assert config.auto_step_halving is True

    def test_custom_config(self):
        """自定义配置"""
        config = OrchestratorConfig(dt_ns=100000, enable_energy_audit=False)
        assert config.dt_ns == 100000
        assert config.enable_energy_audit is False


# ── Orchestrator 测试 ────────────────────────────────────────

class TestOrchestratorInit:
    """Orchestrator 初始化测试"""

    def test_initial_state(self):
        """初始状态正确"""
        orch = Orchestrator()
        assert orch.state == SimulationState.IDLE
        assert len(orch._steppers) == 0
        assert len(orch._initializers) == 0

    def test_custom_config(self):
        """自定义配置"""
        config = OrchestratorConfig(dt_ns=100000)
        orch = Orchestrator(cfg=config)
        assert orch.cfg.dt_ns == 100000


class TestOrchestratorRegistration:
    """模型注册测试"""

    def test_register_stepper(self):
        """注册 stepper"""
        orch = Orchestrator()
        mock_stepper = MagicMock(return_value=StepResult(solver_id="test"))
        orch.register_stepper("test", mock_stepper)
        assert "test" in orch._steppers

    def test_register_initializer(self):
        """注册 initializer"""
        orch = Orchestrator()
        mock_init = MagicMock()
        orch.register_initializer("test", mock_init)
        assert "test" in orch._initializers

    def test_multiple_registrations(self):
        """多个模型注册"""
        orch = Orchestrator()
        orch.register_stepper("s1", MagicMock())
        orch.register_stepper("s2", MagicMock())
        orch.register_initializer("s1", MagicMock())
        assert len(orch._steppers) == 2
        assert len(orch._initializers) == 1


class TestOrchestratorRun:
    """仿真运行测试"""

    def test_basic_run(self):
        """基本运行"""
        orch = Orchestrator()

        # Mock stepper that always converges
        def mock_stepper(step_ns):
            return StepResult(solver_id="test", converged=True)

        orch.register_stepper("test", mock_stepper)
        orch.register_initializer("test", MagicMock())

        # Run for 1ms with 50μs step
        audits = orch.run(step_ns=50000, duration_s=0.001)
        assert orch.clock.step_count == 20  # 1ms / 50μs = 20 steps

    def test_run_with_progress(self):
        """带进度回调的运行"""
        orch = Orchestrator()
        progress_values = []

        def mock_stepper(step_ns):
            return StepResult(solver_id="test")

        def progress_callback(progress):
            progress_values.append(progress)

        orch.register_stepper("test", mock_stepper)
        # Run longer to get multiple progress updates
        orch.run(step_ns=50000, duration_s=0.01, progress_callback=progress_callback)

        assert len(progress_values) > 0
        assert progress_values[-1] >= 0.9

    def test_run_invalid_step(self):
        """无效步长抛出异常"""
        orch = Orchestrator()
        with pytest.raises(ValueError, match="Invalid step_ns"):
            orch.run(step_ns=0, duration_s=1.0)

    def test_run_invalid_duration(self):
        """无效时长抛出异常"""
        orch = Orchestrator()
        with pytest.raises(ValueError, match="Invalid duration_s"):
            orch.run(step_ns=50000, duration_s=-1.0)

    def test_run_with_nan_step(self):
        """NaN 步长抛出异常"""
        orch = Orchestrator()
        with pytest.raises(ValueError, match="Invalid step_ns"):
            orch.run(step_ns=float('nan'), duration_s=1.0)


class TestOrchestratorDivergence:
    """发散处理测试"""

    def test_divergence_detection(self):
        """发散检测 — 当 auto_step_halving 启用且所有步都发散时应触发 diverged"""
        orch = Orchestrator(OrchestratorConfig(auto_step_halving=True, max_step_halving=2))

        call_count = 0
        def diverging_stepper(step_ns):
            nonlocal call_count
            call_count += 1
            return StepResult(solver_id="test", converged=False, error_estimate=0.5)

        orch.register_stepper("test", diverging_stepper)
        orch.run(step_ns=50000, duration_s=0.001)

        # After max_step_halving exhausted, simulation should mark diverged
        assert orch.clock.diverged

    def test_auto_step_halving(self):
        """自动步长减半"""
        config = OrchestratorConfig(auto_step_halving=True, max_step_halving=3)
        orch = Orchestrator(config)

        def diverging_stepper(step_ns):
            return StepResult(solver_id="test", converged=False)

        orch.register_stepper("test", diverging_stepper)
        orch.run(step_ns=50000, duration_s=0.001)

        # Should have attempted step halving
        assert orch.clock.diverged


class TestOrchestratorFaultInjection:
    """故障注入测试"""

    def test_schedule_fault(self):
        """调度故障"""
        orch = Orchestrator()
        fault_fn = MagicMock()
        orch.schedule_fault(0.001, fault_fn)  # 1ms

        assert len(orch._fault_queue) == 1

    def test_fault_execution(self):
        """故障执行"""
        orch = Orchestrator()
        fault_fn = MagicMock()
        orch.schedule_fault(0.0005, fault_fn)  # 0.5ms

        def mock_stepper(step_ns):
            return StepResult(solver_id="test")

        orch.register_stepper("test", mock_stepper)
        orch.run(step_ns=50000, duration_s=0.001)

        fault_fn.assert_called_once()

    def test_invalid_fault_time(self):
        """无效故障时间被忽略"""
        orch = Orchestrator()
        orch.schedule_fault(float('nan'), MagicMock())
        orch.schedule_fault(float('inf'), MagicMock())
        orch.schedule_fault(-1.0, MagicMock())
        assert len(orch._fault_queue) == 0


class TestOrchestratorStopCondition:
    """停止条件测试"""

    def test_stop_condition_breaks_outer_loop(self):
        """停止条件触发后外层仿真循环应终止"""
        orch = Orchestrator()
        # Stop when sim_time reaches 500us (10 steps at 50us each)
        orch.add_stop_condition(lambda: orch.clock.sim_time_ns >= 500000)

        def mock_stepper(step_ns):
            return StepResult(solver_id="test")

        orch.register_stepper("test", mock_stepper)
        orch.run(step_ns=50000, duration_s=0.01)  # 200 steps total

        # Simulation should stop early at ~10 steps, not run all 200
        assert orch.clock.step_count <= 12, (
            f"Stop condition didn't break outer loop: {orch.clock.step_count} steps"
        )
        assert orch.clock.step_count >= 9, "Simulation didn't run enough before stop"

    def test_stop_condition_no_hooks_no_early_stop(self):
        """无停止条件时仿真正常完成全部步数"""
        orch = Orchestrator()

        def mock_stepper(step_ns):
            return StepResult(solver_id="test")

        orch.register_stepper("test", mock_stepper)
        orch.run(step_ns=50000, duration_s=0.001)  # 20 steps

        assert orch.clock.step_count == 20


class TestOrchestratorPauseResume:
    """Pause/Resume 测试（Bug #6）"""

    def test_pause_actually_pauses(self):
        """暂停后仿真停止推进，恢复后继续"""
        orch = Orchestrator()

        def step_fn(step_ns):
            return StepResult(solver_id="test")

        orch.register_stepper("test", step_fn)
        thread = threading.Thread(target=lambda: orch.run(step_ns=50000, duration_s=60.0), daemon=True)
        thread.start()

        # Wait for simulation to start
        deadline = time.monotonic() + 2.0
        while orch.clock.step_count < 10:
            if time.monotonic() >= deadline:
                break
            time.sleep(0.01)
        assert orch.clock.step_count >= 10, "Simulation didn't start"

        # Pause and wait for it to stabilize
        orch.pause()
        time.sleep(0.5)
        count_a = orch.clock.step_count
        time.sleep(0.3)
        count_b = orch.clock.step_count
        assert count_a == count_b, (
            f"Step count still growing after pause stabilization: {count_a} -> {count_b}"
        )

        # Resume
        orch.set_state(SimulationState.RUNNING)
        time.sleep(0.2)
        count_after = orch.clock.step_count
        assert count_after > count_b, (
            f"Step count didn't increase after resume: {count_b} -> {count_after}"
        )

        orch.stop()


class TestOrchestratorStepBounds:
    """步数边界测试（Bug #7）"""

    def test_zero_steps_raises(self):
        """零步数抛出异常"""
        orch = Orchestrator()
        orch.register_stepper("test", MagicMock(return_value=StepResult(solver_id="test")))
        with pytest.raises(ValueError, match="0 steps"):
            orch.run(step_ns=1_000_000_000, duration_s=0.001)

    def test_huge_steps_raises(self):
        """超大步数抛出异常"""
        orch = Orchestrator()
        orch.register_stepper("test", MagicMock(return_value=StepResult(solver_id="test")))
        with pytest.raises(ValueError, match="10M steps"):
            orch.run(step_ns=1, duration_s=1.0)


class TestOrchestratorStepHalving:
    """步长减半测试"""

    def test_step_halving_minimum(self):
        """步长减半不会降到 0 导致死循环"""
        orch = Orchestrator(OrchestratorConfig(
            auto_step_halving=True, max_step_halving=100
        ))

        call_count = [0]

        def diverging_stepper(step_ns):
            call_count[0] += 1
            # Always report non-converged to trigger halving
            return StepResult(solver_id="test", converged=False, error_estimate=1.0)

        orch.register_stepper("test", diverging_stepper)
        orch.run(step_ns=1, duration_s=1e-9)  # 1 step

        # Should complete (not hang) even with aggressive halving
        assert call_count[0] >= 1


class TestOrchestratorEnergyAudit:
    """能量审计测试"""

    def test_energy_audit_enabled(self):
        """启用能量审计"""
        config = OrchestratorConfig(
            enable_energy_audit=True, energy_audit_period_steps=10,
            auto_step_halving=False,
        )
        orch = Orchestrator(config)

        step_idx = 0
        def mock_stepper(step_ns):
            nonlocal step_idx
            step_idx += 1
            # Every 5th step reports non-convergence with a small error
            if step_idx % 5 == 0:
                return StepResult(solver_id="test", converged=False, error_estimate=0.01)
            return StepResult(solver_id="test")

        orch.register_stepper("test", mock_stepper)
        orch.run(step_ns=50000, duration_s=0.001)

        # Energy audits should be collected
        assert len(orch._energy_audits) > 0
        # Each audit should have valid data
        for audit in orch._energy_audits:
            assert isinstance(audit.max_error, float)
            assert isinstance(audit.avg_error, float)
        # At least one audit should have sampled error data
        assert any(a.sample_count > 0 for a in orch._energy_audits)

    def test_energy_audit_disabled(self):
        """禁用能量审计"""
        config = OrchestratorConfig(enable_energy_audit=False)
        orch = Orchestrator(config)

        def mock_stepper(step_ns):
            return StepResult(solver_id="test")

        orch.register_stepper("test", mock_stepper)
        orch.run(step_ns=50000, duration_s=0.001)

        assert len(orch._energy_audits) == 0


class TestOrchestratorIntegration:
    """集成测试"""

    def test_full_simulation_cycle(self):
        """完整仿真周期"""
        orch = Orchestrator()

        # Mock PMSM-like stepper
        state = {'id': 0.0, 'iq': 0.0}

        def pmsm_stepper(step_ns):
            dt = step_ns / 1e9
            # Simple integration
            state['id'] += 0.1 * dt
            state['iq'] += 0.2 * dt
            return StepResult(solver_id="pmsm", converged=True)

        def pmsm_init():
            state['id'] = 0.0
            state['iq'] = 0.0

        orch.register_stepper("pmsm", pmsm_stepper)
        orch.register_initializer("pmsm", pmsm_init)

        # Run for 10ms
        orch.run(step_ns=50000, duration_s=0.01)

        assert orch.clock.step_count == 200  # 10ms / 50μs
        assert state['id'] > 0
        assert state['iq'] > 0

    def test_multiple_solvers(self):
        """多求解器协同"""
        orch = Orchestrator()

        results = {'s1': [], 's2': []}

        def stepper1(step_ns):
            results['s1'].append(orch.clock.sim_time_ns)
            return StepResult(solver_id="s1")

        def stepper2(step_ns):
            results['s2'].append(orch.clock.sim_time_ns)
            return StepResult(solver_id="s2")

        orch.register_stepper("s1", stepper1)
        orch.register_stepper("s2", stepper2)

        orch.run(step_ns=50000, duration_s=0.001)

        # Both solvers should have run for all 20 steps
        assert len(results['s1']) == 20
        assert len(results['s2']) == 20
        assert len(results['s1']) == len(results['s2'])



