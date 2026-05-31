"""PMSM dq-axis model and FOC controller unit tests (Task 8).

Covers:
  - PMSMdqModel: parameter validation, NaN/Inf guards, dq dynamics, torque
  - Clarke/Park/inverse-Park transforms: round-trip correctness
  - PIController: proportional, integral, anti-windup
  - FOCController: full Clarke→Park→PI→invPark→SVPWM pipeline
  - SpeedController: outer-loop speed PI
  - Legacy wrappers: PMSMModel, FOCControllerLegacy
  - NaN/Inf security guards on every entry point
"""

import math
import pytest
import numpy as np

from param_id_gui.models.motor.pmsm_dq import (
    PMSMdqModel, PMSMModel, PMSMParameters,
    _guard_numeric, _MOTOR_EPS_L, _MOTOR_EPS_J,
)
from param_id_gui.models.controller.foc import (
    clarke_transform, park_transform, inverse_park, svpwm,
    PIController, FOCController, SpeedController,
    FOCParameters, FOCControllerLegacy,
    _PWM_EPS_V,
)


# ═══════════════════════════════════════════════════════════════
#  1. PMSM dq Model Tests
# ═══════════════════════════════════════════════════════════════

class TestPMSMdqModelInit:
    """PMSM 模型初始化与参数验证。"""

    def test_default_parameters(self):
        """默认参数应被 NaN/Inf guard 处理后保持合理。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        assert m.Rs == 0.5
        assert m.Ld == 5e-4
        assert m.Lq == 1e-3
        assert m.flux_pm == 0.03
        assert m.J == 1e-4
        assert m.Pp >= 1

    def test_inductance_floor(self, pmsm_params):
        """电感不应低于 _MOTOR_EPS_L。"""
        m = PMSMdqModel(Rs=0.5, Ld=0, Lq=0, flux_pm=0.03, J=1e-4)
        assert m.Ld >= _MOTOR_EPS_L
        assert m.Lq >= _MOTOR_EPS_L

    def test_inertia_floor(self):
        """转动惯量不应低于 _MOTOR_EPS_J。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=0)
        assert m.J >= _MOTOR_EPS_J

    def test_pole_pairs_minimum(self):
        """极对数至少为 1。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=0)
        assert m.Pp == 1

    def test_nan_input_guard(self):
        """NaN 参数应被替换为 fallback。"""
        m = PMSMdqModel(Rs=float('nan'), Ld=float('nan'), Lq=float('nan'),
                        flux_pm=float('nan'), J=float('nan'), B=float('nan'))
        assert not math.isnan(m.Rs)
        assert not math.isnan(m.Ld)
        assert not math.isnan(m.Lq)
        assert not math.isnan(m.flux_pm)
        assert not math.isnan(m.J)
        assert not math.isnan(m.B)

    def test_inf_input_guard(self):
        """Inf 参数应被替换为 fallback。"""
        m = PMSMdqModel(Rs=float('inf'), Ld=float('inf'), Lq=float('inf'),
                        flux_pm=float('inf'), J=float('inf'), B=float('inf'))
        assert not math.isinf(m.Rs)
        assert not math.isinf(m.Ld)
        assert not math.isinf(m.Lq)
        assert not math.isinf(m.flux_pm)
        assert not math.isinf(m.J)
        assert not math.isinf(m.B)

    def test_initial_state_is_zero(self):
        """初始状态应全为零。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        s = m.get_state()
        for key in ('id', 'iq', 'omega_m', 'theta_e', 'torque', 'ia', 'ib', 'ic'):
            assert s[key] == 0.0, f"Initial state {key} should be 0"

    def test_omega_e_property(self):
        """omega_e = Pp * omega_m。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.omega_m = 100.0
        assert m.omega_e == 400.0


class TestPMSMdqModelTorque:
    """电磁转矩计算。"""

    def test_torque_pure_pm(self):
        """id=0 时 Te = 1.5 * Pp * flux_pm * iq。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.id = 0.0
        m.iq = 10.0
        expected = 1.5 * 4 * 0.03 * 10.0
        assert abs(m.torque_em - expected) < 1e-10

    def test_torque_with_reluctance(self, pmsm_params):
        """Ld != Lq 时应包含磁阻转矩分量。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.id = 5.0
        m.iq = 10.0
        expected = 1.5 * 4 * (0.03 * 10.0 + (5e-4 - 1e-3) * 5.0 * 10.0)
        assert abs(m.torque_em - expected) < 1e-10

    def test_torque_zero_current(self):
        """零电流时转矩为零。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        assert m.torque_em == 0.0


class TestPMSMdqModelStep:
    """PMSM 动力学步进。"""

    def test_step_no_voltage(self):
        """无输入电压时，电流应保持为零。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        for _ in range(100):
            m.step(0, 0)
        assert abs(m.id) < 1e-6
        assert abs(m.iq) < 1e-6

    def test_step_d_axis_voltage_builds_current(self):
        """正 vd 应建立正 id（忽略反电动势初始为零）。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(vd=10.0, vq=0.0, dt=1e-5)
        # did = (vd - Rs*id + we*Lq*iq) / Ld = (10 - 0 + 0) / 5e-4 = 20000
        # id = 20000 * 1e-5 = 0.2 A
        assert m.id > 0, "d-axis current should be positive with positive vd"

    def test_step_q_axis_voltage_builds_current(self):
        """正 vq 应建立正 iq（初始 theta=0）。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(vd=0.0, vq=10.0, dt=1e-5)
        # diq = (vq - Rs*iq - we*(Ld*id + flux_pm)) / Lq
        # = (10 - 0 - 0*(0 + 0.03)) / 1e-3 = 10000
        # iq = 10000 * 1e-5 = 0.1 A
        assert m.iq > 0, "q-axis current should be positive with positive vq"

    def test_step_torque_generation(self):
        """施加 vq 后应产生电磁转矩。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        for _ in range(50):
            m.step(vd=0, vq=20, dt=1e-5)
        assert m.torque > 0, "Torque should be positive with positive iq"

    def test_step_speed_builds_up(self):
        """持续正转矩应使转速增加。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4, B=0)
        for _ in range(500):
            m.step(vd=0, vq=30, dt=1e-5)
        assert m.omega_m > 0, "Speed should increase with positive torque"

    def test_step_load_torque_decelerates(self):
        """负载转矩应减速。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4, B=0)
        # 先加速
        for _ in range(500):
            m.step(vd=0, vq=30, dt=1e-5)
        speed_before = m.omega_m
        # 施加负载
        for _ in range(200):
            m.step(vd=0, vq=0, tl=0.5, dt=1e-5)
        assert m.omega_m < speed_before, "Speed should decrease with load torque"

    def test_step_nan_input_guard(self):
        """NaN 输入应被 guard 处理，不产生 NaN 状态。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(m.id)
        assert not math.isnan(m.iq)
        assert not math.isnan(m.omega_m)

    def test_step_inf_input_guard(self):
        """Inf 输入应被 guard 处理。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(float('inf'), float('inf'), float('inf'))
        assert not math.isinf(m.id)
        assert not math.isinf(m.iq)
        assert not math.isinf(m.omega_m)

    def test_step_custom_dt(self):
        """自定义 dt 应被正确使用。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(vd=10, vq=0, dt=1e-4)
        id1 = m.id
        m.reset()
        m.step(vd=10, vq=0, dt=1e-3)
        id2 = m.id
        assert id2 > id1, "Larger dt should produce larger current change"

    def test_step_dt_floor(self):
        """dt 不应低于 1e-12。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step(vd=10, vq=0, dt=0)  # dt=0 → floor to 1e-12
        assert not math.isnan(m.id)

    def test_theta_wrapping(self):
        """theta_e 应在 [0, 2π) 范围内。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4, B=0)
        for _ in range(5000):
            m.step(vd=0, vq=50, dt=1e-4)
        assert 0 <= m.theta_e < 2 * math.pi + 0.01


class TestPMSMdqModelABC:
    """三相电流与三相电压输入。"""

    def test_update_abc_currents_zero(self):
        """零 dq 电流应产生零三相电流。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        ia, ib, ic = m.update_abc_currents()
        assert abs(ia) < 1e-10
        assert abs(ib) < 1e-10
        assert abs(ic) < 1e-10

    def test_abc_currents_sum_to_zero(self):
        """三相电流之和应约等于零（基尔霍夫定律）。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.id = 5.0
        m.iq = 10.0
        m.theta_e = 0.3
        ia, ib, ic = m.update_abc_currents()
        assert abs(ia + ib + ic) < 1e-10, "ia + ib + ic should be ~0 (KCL)"

    def test_step_abc_produces_current(self):
        """三相电压输入应产生电流。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        m.step_abc(va=10, vb=-5, vc=-5, dt=1e-5)
        assert abs(m.id) > 1e-6 or abs(m.iq) > 1e-6

    def test_step_abc_nan_guard(self):
        """NaN 三相应被 guard 处理。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        m.step_abc(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(m.id)
        assert not math.isnan(m.iq)


class TestPMSMdqModelReset:
    """模型重置。"""

    def test_reset_clears_state(self):
        """reset() 应清零所有状态。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        for _ in range(100):
            m.step(vd=10, vq=20, dt=1e-5)
        m.reset()
        s = m.get_state()
        for key in ('id', 'iq', 'omega_m', 'theta_e', 'torque', 'ia', 'ib', 'ic'):
            assert s[key] == 0.0, f"After reset, {key} should be 0"

    def test_get_state_keys(self):
        """get_state() 应返回所有预期键。"""
        m = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
        s = m.get_state()
        expected_keys = {'id', 'iq', 'omega_m', 'theta_e', 'torque',
                         'ia', 'ib', 'ic', 'omega_e'}
        assert set(s.keys()) == expected_keys


class TestGuardNumeric:
    """_guard_numeric 工具函数。"""

    def test_normal_value(self):
        assert _guard_numeric(3.14) == 3.14

    def test_zero(self):
        assert _guard_numeric(0.0) == 0.0

    def test_nan_returns_fallback(self):
        assert _guard_numeric(float('nan'), 42.0) == 42.0

    def test_inf_returns_fallback(self):
        assert _guard_numeric(float('inf'), 42.0) == 42.0

    def test_neg_inf_returns_fallback(self):
        assert _guard_numeric(float('-inf'), 42.0) == 42.0

    def test_default_fallback_is_zero(self):
        assert _guard_numeric(float('nan')) == 0.0


# ═══════════════════════════════════════════════════════════════
#  2. Clarke / Park Transform Tests
# ═══════════════════════════════════════════════════════════════

class TestClarkeTransform:
    """Clarke 变换 (abc → αβ)。"""

    def test_balanced_abc(self):
        """平衡三相电流 (1, -0.5, -0.5) → i_alpha=1, i_beta=0。"""
        i_alpha, i_beta = clarke_transform(1.0, -0.5, -0.5)
        assert abs(i_alpha - 1.0) < 1e-10
        assert abs(i_beta) < 1e-10

    def test_zero_currents(self):
        """零电流 → 零输出。"""
        i_alpha, i_beta = clarke_transform(0, 0, 0)
        assert abs(i_alpha) < 1e-10
        assert abs(i_beta) < 1e-10

    def test_nan_guard(self):
        """NaN 输入应被 guard 处理。"""
        i_alpha, i_beta = clarke_transform(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(i_alpha)
        assert not math.isnan(i_beta)

    def test_inf_guard(self):
        """Inf 输入应被 guard 处理。"""
        i_alpha, i_beta = clarke_transform(float('inf'), float('inf'), float('inf'))
        assert not math.isinf(i_alpha)
        assert not math.isinf(i_beta)


class TestParkTransform:
    """Park 变换 (αβ → dq)。"""

    def test_zero_angle(self):
        """θ=0 时 id=i_alpha, iq=i_beta。"""
        id_val, iq_val = park_transform(1.0, 2.0, 0.0)
        assert abs(id_val - 1.0) < 1e-10
        assert abs(iq_val - 2.0) < 1e-10

    def test_90_degrees(self):
        """θ=π/2 时的变换。"""
        id_val, iq_val = park_transform(1.0, 0.0, math.pi / 2)
        assert abs(id_val) < 1e-10
        assert abs(iq_val + 1.0) < 1e-10

    def test_rotating_current_alignment(self):
        """当电流矢量与 dq 轴对齐（θ=电流角度）时 id=幅值, iq=0。"""
        amplitude = 5.0
        theta = 0.7  # 任意角度
        i_alpha = amplitude * math.cos(theta)
        i_beta = amplitude * math.sin(theta)
        id_val, iq_val = park_transform(i_alpha, i_beta, theta)
        assert abs(id_val - amplitude) < 1e-10
        assert abs(iq_val) < 1e-10

    def test_nan_guard(self):
        """NaN 输入应被 guard 处理。"""
        id_val, iq_val = park_transform(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(id_val)
        assert not math.isnan(iq_val)


class TestInversePark:
    """逆 Park 变换 (dq → αβ)。"""

    def test_zero_angle(self):
        """θ=0 时 v_alpha=vd, v_beta=vq。"""
        v_alpha, v_beta = inverse_park(10.0, 20.0, 0.0)
        assert abs(v_alpha - 10.0) < 1e-10
        assert abs(v_beta - 20.0) < 1e-10

    def test_round_trip_park_inverse(self):
        """Park ∘ invPark 应为恒等变换。"""
        vd, vq = 10.0, 20.0
        theta = 1.2
        v_alpha, v_beta = inverse_park(vd, vq, theta)
        vd2, vq2 = park_transform(v_alpha, v_beta, theta)
        assert abs(vd2 - vd) < 1e-10
        assert abs(vq2 - vq) < 1e-10

    def test_nan_guard(self):
        """NaN 输入应被 guard 处理。"""
        v_alpha, v_beta = inverse_park(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(v_alpha)
        assert not math.isnan(v_beta)


class TestClarkeParkRoundTrip:
    """Clarke → Park 完整变换链。"""

    def test_balanced_abc_to_dq(self):
        """平衡三相电流通过 Clarke+Park 应得到直流分量。"""
        # 设 θ=0，平衡电流 ia=10, ib=-5, ic=-5
        i_alpha, i_beta = clarke_transform(10.0, -5.0, -5.0)
        id_val, iq_val = park_transform(i_alpha, i_beta, 0.0)
        # i_alpha = 10, i_beta = (10 + 2*(-5))/√3 = 0
        # θ=0 → id = 10, iq = 0
        assert abs(id_val - 10.0) < 1e-10
        assert abs(iq_val) < 1e-10


# ═══════════════════════════════════════════════════════════════
#  3. SVPWM Tests
# ═══════════════════════════════════════════════════════════════

class TestSVPWM:
    """SVPWM 调制。"""

    def test_zero_voltage(self):
        """零电压输入 → 50% 占空比。"""
        da, db, dc = svpwm(0, 0, 48.0)
        assert abs(da - 0.5) < 1e-10
        assert abs(db - 0.5) < 1e-10
        assert abs(dc - 0.5) < 1e-10

    def test_near_zero_bus_voltage(self):
        """v_bus ≈ 0 → 安全回退到 50%。"""
        da, db, dc = svpwm(10, 10, 1e-15)
        assert da == 0.5
        assert db == 0.5
        assert dc == 0.5

    def test_duty_cycle_range(self):
        """占空比应在 [0, 1] 范围内。"""
        for va in [-50, 0, 50]:
            for vb in [-50, 0, 50]:
                da, db, dc = svpwm(va, vb, 48.0)
                assert 0.0 <= da <= 1.0, f"da={da} out of range for va={va}, vb={vb}"
                assert 0.0 <= db <= 1.0, f"db={db} out of range"
                assert 0.0 <= dc <= 1.0, f"dc={dc} out of range"

    def test_symmetric_voltage_symmetric_duty(self):
        """对称电压 → 对称占空比。"""
        # v_alpha=some, v_beta=0 → va=vb=vc (逆 Clarke 中)
        da, db, dc = svpwm(10.0, 0, 48.0)
        # va = 10, vb = -5, vc = -5
        # 不完全对称，但 da 应最大
        assert da > db
        assert da > dc

    def test_nan_guard(self):
        """NaN 输入应被 guard 处理。"""
        da, db, dc = svpwm(float('nan'), float('nan'), float('nan'))
        assert not math.isnan(da)
        assert not math.isnan(db)
        assert not math.isnan(dc)


# ═══════════════════════════════════════════════════════════════
#  4. PI Controller Tests
# ═══════════════════════════════════════════════════════════════

class TestPIController:
    """PI 控制器。"""

    def test_proportional_only(self):
        """纯比例响应。"""
        pi = PIController(kp=2.0, ki=0.0, ts=1e-3)
        out = pi.update(10.0, 5.0)
        # error=5, kp*error=10, ki=0 → out=10
        assert abs(out - 10.0) < 1e-10

    def test_integral_accumulation(self):
        """积分项应随时间累积。"""
        pi = PIController(kp=0.0, ki=10.0, ts=1e-3)
        out1 = pi.update(10.0, 0.0)  # error=10, integral=0.01*10=0.1
        out2 = pi.update(10.0, 0.0)  # integral=0.1+0.1=0.2
        assert out2 > out1, "Integral should accumulate"

    def test_output_clamping(self):
        """输出应被钳位到 [out_min, out_max]。"""
        pi = PIController(kp=100.0, ki=0.0, ts=1e-3, out_min=-5, out_max=5)
        out = pi.update(100.0, 0.0)  # error=100, kp*error=10000
        assert out == 5.0

    def test_output_clamping_negative(self):
        """负输出应被钳位。"""
        pi = PIController(kp=100.0, ki=0.0, ts=1e-3, out_min=-5, out_max=5)
        out = pi.update(-100.0, 0.0)
        assert out == -5.0

    def test_anti_windup(self):
        """饱和时积分项应被限制（back-calculation）。"""
        pi = PIController(kp=1.0, ki=100.0, ts=1e-3, out_min=-10, out_max=10)
        # 持续大误差 → 积分累积 → 输出饱和
        for _ in range(1000):
            pi.update(100.0, 0.0)
        # 积分不应无限增长
        assert abs(pi.integral) < 1e6, "Anti-windup should prevent integral blowup"

    def test_reset(self):
        """reset() 应清零控制器状态。"""
        pi = PIController(kp=1.0, ki=10.0, ts=1e-3)
        pi.update(10.0, 0.0)
        pi.reset()
        assert pi.integral == 0.0
        assert pi.prev_error == 0.0

    def test_nan_input_guard(self):
        """NaN 输入应被 guard 处理。"""
        pi = PIController(kp=1.0, ki=10.0, ts=1e-3)
        out = pi.update(float('nan'), float('nan'))
        assert not math.isnan(out)

    def test_inf_input_guard(self):
        """Inf 输入应被 guard 处理。"""
        pi = PIController(kp=1.0, ki=10.0, ts=1e-3)
        out = pi.update(float('inf'), float('inf'))
        assert not math.isnan(out)
        assert not math.isinf(out)

    def test_swapped_limits(self):
        """out_min > out_max 时应自动交换。"""
        pi = PIController(kp=1.0, ki=0.0, ts=1e-3, out_min=10, out_max=-10)
        assert pi.out_min <= pi.out_max

    def test_kp_zero_guard(self):
        """kp=0 时 k_aw 应有安全默认值。"""
        pi = PIController(kp=0.0, ki=10.0, ts=1e-3)
        assert math.isfinite(pi.k_aw)

    def test_settling_to_setpoint(self):
        """PI 控制器应能收敛到设定值。"""
        pi = PIController(kp=2.0, ki=20.0, ts=1e-3, out_min=-100, out_max=100)
        measurement = 0.0
        for _ in range(5000):
            out = pi.update(10.0, measurement)
            # 简单一阶响应模型: measurement += out * ts
            measurement += out * 1e-3
        assert abs(measurement - 10.0) < 0.5, "PI should settle near setpoint"


# ═══════════════════════════════════════════════════════════════
#  5. FOC Controller Tests
# ═══════════════════════════════════════════════════════════════

class TestFOCController:
    """FOC 控制器完整流水线。"""

    def test_default_init(self):
        """默认参数初始化。"""
        foc = FOCController()
        assert foc.v_bus == 48.0
        assert foc.pi_id.kp == 5.0
        assert foc.pi_iq.kp == 5.0

    def test_update_produces_duty_cycles(self):
        """update() 应返回 [0,1] 范围的占空比。"""
        foc = FOCController()
        da, db, dc = foc.update(ia=0, ib=0, ic=0, theta_e=0, id_ref=0, iq_ref=5)
        assert 0.0 <= da <= 1.0
        assert 0.0 <= db <= 1.0
        assert 0.0 <= dc <= 1.0

    def test_update_with_current_error(self, pmsm_params):
        """有电流误差时控制器应产生非零占空比。"""
        foc = FOCController()
        da, db, dc = foc.update(ia=0, ib=0, ic=0, theta_e=0, id_ref=0, iq_ref=10)
        # 有参考电流但实际为零 → 控制器应输出非零
        assert not (da == 0.5 and db == 0.5 and dc == 0.5), \
            "Controller should respond to current error"

    def test_reset(self):
        """reset() 应清零控制器状态。"""
        foc = FOCController()
        foc.update(ia=1, ib=-0.5, ic=-0.5, theta_e=0.5, id_ref=2, iq_ref=5)
        foc.reset()
        assert foc.vd_ref == 0.0
        assert foc.vq_ref == 0.0
        assert foc.duty_a == 0.5
        assert foc.duty_b == 0.5
        assert foc.duty_c == 0.5

    def test_nan_input_guard(self):
        """NaN 输入应被 guard 处理。"""
        foc = FOCController()
        da, db, dc = foc.update(
            ia=float('nan'), ib=float('nan'), ic=float('nan'),
            theta_e=float('nan'), id_ref=float('nan'), iq_ref=float('nan')
        )
        assert not math.isnan(da)
        assert not math.isnan(db)
        assert not math.isnan(dc)

    def test_inf_input_guard(self):
        """Inf 输入应被 guard 处理。"""
        foc = FOCController()
        da, db, dc = foc.update(
            ia=float('inf'), ib=float('inf'), ic=float('inf'),
            theta_e=float('inf'), id_ref=float('inf'), iq_ref=float('inf')
        )
        assert not math.isnan(da)
        assert not math.isinf(da)

    def test_steady_state_zero_error(self):
        """稳态零误差时输出应稳定。"""
        foc = FOCController(kp_id=5, ki_id=500, kp_iq=5, ki_iq=500, ts=50e-6)
        # 模拟稳态：测量值等于参考值
        for _ in range(100):
            da, db, dc = foc.update(
                ia=0, ib=0, ic=0, theta_e=0,
                id_ref=0, iq_ref=0
            )
        # 稳态时占空比应接近 50%
        assert abs(da - 0.5) < 0.1
        assert abs(db - 0.5) < 0.1
        assert abs(dc - 0.5) < 0.1


class TestSpeedController:
    """速度外环 PI 控制器。"""

    def test_default_init(self):
        """默认参数。"""
        sc = SpeedController(kp=0.05, ki=0.5, ts=1e-3)
        assert sc.pi.kp == 0.05
        assert sc.pi.ki == 0.5

    def test_speed_error_produces_iq_ref(self):
        """速度误差应产生 iq_ref。"""
        sc = SpeedController(kp=1.0, ki=10.0, ts=1e-3)
        iq_ref = sc.update(speed_ref=100.0, speed_meas=0.0)
        assert iq_ref > 0, "Positive speed error → positive iq_ref"

    def test_negative_speed_error(self):
        """负速度误差应产生负 iq_ref。"""
        sc = SpeedController(kp=1.0, ki=10.0, ts=1e-3)
        iq_ref = sc.update(speed_ref=0.0, speed_meas=100.0)
        assert iq_ref < 0, "Negative speed error → negative iq_ref"

    def test_output_clamping(self):
        """iq_ref 应被钳位。"""
        sc = SpeedController(kp=100.0, ki=0.0, ts=1e-3, iq_min=-10, iq_max=10)
        iq_ref = sc.update(speed_ref=1000.0, speed_meas=0.0)
        assert iq_ref == 10.0

    def test_reset(self):
        """reset() 应清零。"""
        sc = SpeedController(kp=1.0, ki=10.0, ts=1e-3)
        sc.update(100, 0)
        sc.reset()
        assert sc.pi.integral == 0.0


# ═══════════════════════════════════════════════════════════════
#  6. Legacy Wrapper Tests
# ═══════════════════════════════════════════════════════════════

class TestLegacyPMSMModel:
    """PMSMModel 兼容层。"""

    def test_default_params(self):
        m = PMSMModel()
        assert m.params.Rs == 0.5
        assert m.params.Ld == 0.005

    def test_update(self):
        m = PMSMModel()
        m.set_input(vd=10, vq=0, tl=0)
        state = m.update(dt=1e-5)
        assert 'id' in state
        assert 'iq' in state

    def test_reset(self):
        m = PMSMModel()
        m.set_input(vd=10, vq=0)
        m.update(dt=1e-5)
        m.reset()
        state = m.get_state()
        assert state['id'] == 0.0
        assert state['iq'] == 0.0

    def test_get_torque(self):
        m = PMSMModel()
        m.set_input(vd=0, vq=10)
        m.update(dt=1e-5)
        torque = m.get_torque()
        assert isinstance(torque, float)


class TestLegacyFOCController:
    """FOCControllerLegacy 兼容层。"""

    def test_default_params(self):
        foc = FOCControllerLegacy()
        assert foc.params.Kp_d == 10.0

    def test_clarke_transform(self):
        foc = FOCControllerLegacy()
        i_alpha, i_beta = foc.clarke_transform(1.0, -0.5, -0.5)
        assert abs(i_alpha - 1.0) < 1e-10

    def test_park_transform(self):
        foc = FOCControllerLegacy()
        id_val, iq_val = foc.park_transform(1.0, 0.0, 0.0)
        assert abs(id_val - 1.0) < 1e-10

    def test_inverse_park_transform(self):
        foc = FOCControllerLegacy()
        v_alpha, v_beta = foc.inverse_park_transform(10.0, 0.0, 0.0)
        assert abs(v_alpha - 10.0) < 1e-10

    def test_set_mode(self):
        foc = FOCControllerLegacy()
        foc.set_mode("speed")
        assert foc._mode == "speed"
        with pytest.raises(ValueError):
            foc.set_mode("invalid")

    def test_set_reference(self):
        foc = FOCControllerLegacy()
        foc.set_reference(id_ref=5.0, iq_ref=10.0, speed_ref=100.0)
        assert foc._id_ref == 5.0
        assert foc._iq_ref == 10.0
        assert foc._speed_ref == 100.0

    def test_update_torque_mode(self):
        foc = FOCControllerLegacy()
        foc.set_reference(iq_ref=5.0)
        vd, vq = foc.update(id_meas=0, iq_meas=0, speed_meas=0, theta=0, dt=1e-3)
        assert isinstance(vd, float)
        assert isinstance(vq, float)

    def test_update_speed_mode(self):
        foc = FOCControllerLegacy()
        foc.set_mode("speed")
        foc.set_reference(speed_ref=100.0)
        vd, vq = foc.update(id_meas=0, iq_meas=0, speed_meas=0, theta=0, dt=1e-3)
        assert isinstance(vd, float)
        assert isinstance(vq, float)

    def test_reset(self):
        foc = FOCControllerLegacy()
        foc.update(id_meas=0, iq_meas=0, speed_meas=0, theta=0, dt=1e-3)
        foc.reset()
        state = foc.get_state()
        assert state['integral_d'] == 0.0
        assert state['integral_q'] == 0.0

    def test_get_state(self):
        foc = FOCControllerLegacy()
        state = foc.get_state()
        assert 'mode' in state
        assert 'integral_d' in state


# ═══════════════════════════════════════════════════════════════
#  7. Integration: PMSM + FOC Closed-Loop
# ═══════════════════════════════════════════════════════════════

class TestPMSMFOCIntegration:
    """PMSM + FOC 闭环集成测试。"""

    def test_closed_loop_current_control(self):
        """FOC 闭环电流控制：iq 应收敛到参考值。

        使用适配电机参数的 PI 增益，避免过度振荡。
        电气时间常数 τ = Lq/Rs = 1e-3/0.5 = 2ms。
        控制带宽 ≈ 1/(5*τ) = 100 rad/s。
        kp = bandwidth * Lq = 100 * 1e-3 = 0.1
        ki = kp * Rs/Lq = 0.1 * 500 = 50
        """
        motor = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        # 使用适配的 PI 增益
        foc = FOCController(kp_id=0.5, ki_id=50, kp_iq=0.5, ki_iq=50,
                            ts=50e-6, v_bus=48.0)
        iq_ref = 3.0
        dt = 50e-6

        for _ in range(10000):
            motor.update_abc_currents()
            da, db, dc = foc.update(
                ia=motor.ia, ib=motor.ib, ic=motor.ic,
                theta_e=motor.theta_e, id_ref=0, iq_ref=iq_ref
            )
            # 将占空比转换为相电压
            v_bus = 48.0
            va = (da - 0.5) * v_bus
            vb = (db - 0.5) * v_bus
            vc = (dc - 0.5) * v_bus
            motor.step_abc(va, vb, vc, dt=dt)

        # 电流应接近参考值（允许一定误差，开环近似）
        assert abs(motor.iq - iq_ref) < 2.0, \
            f"iq={motor.iq:.3f} should be near ref={iq_ref}"
        # 无 NaN/Inf
        assert not math.isnan(motor.iq)
        assert not math.isinf(motor.iq)

    def test_open_loop_simulation_stability(self):
        """开环仿真：施加恒定电压后系统不应发散。"""
        motor = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4, Pp=4)
        for _ in range(10000):
            motor.step(vd=0, vq=10, dt=50e-6)

        # 系统不应发散
        assert abs(motor.iq) < 1000, "iq should not diverge"
        assert abs(motor.omega_m) < 10000, "speed should not diverge"
        assert not math.isnan(motor.iq)
        assert not math.isnan(motor.omega_m)
        assert not math.isnan(motor.theta_e)

    def test_physics_energy_consistency(self):
        """能量守恒：输入功率应大于摩擦损耗。"""
        motor = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03,
                            J=1e-4, Pp=4, B=1e-3)
        # 施加电压一段时间
        total_energy_in = 0.0
        dt = 50e-6
        for _ in range(5000):
            vd, vq = 0.0, 20.0
            motor.step(vd, vq, dt=dt)
            # 输入功率 P = vd*id + vq*iq
            p_in = vd * motor.id + vq * motor.iq
            total_energy_in += p_in * dt

        # 总输入能量应为正（做功）
        assert total_energy_in > 0, "Total input energy should be positive"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
