#pragma once
/**
 * @file physics_models.h
 * @brief 物理模型层 - 电机、变换器、控制器模型
 *
 * 提供高精度物理模型的C++实现：
 * - PMSM dq轴模型
 * - FOC控制器
 * - Buck/Boost变换器
 * - 电池模型
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <cmath>
#include <array>
#include <string>
#include <stdexcept>
#include <functional>

namespace param_id {
namespace models {

// ============================================================================
// 类型定义
// ============================================================================

/** @brief 模型参数类型 */
using ParamVector = std::vector<double>;

/** @brief 状态向量类型 */
using StateVector = std::vector<double>;

/** @brief 模型输出 */
struct ModelOutput {
    std::vector<double> states;      // 状态变量
    std::vector<double> outputs;     // 输出变量
    double power_loss = 0.0;         // 功率损耗
    double efficiency = 1.0;         // 效率
};

// ============================================================================
// 模型基类
// ============================================================================

/**
 * @brief 物理模型基类
 */
class PhysicsModelBase {
public:
    virtual ~PhysicsModelBase() = default;

    /**
     * @brief 模型步进
     * @param inputs 输入向量
     * @param dt 时间步长
     * @return 模型输出
     */
    virtual ModelOutput step(const std::vector<double>& inputs, double dt) = 0;

    /**
     * @brief 重置模型状态
     */
    virtual void reset() = 0;

    /**
     * @brief 获取状态向量
     */
    virtual StateVector get_state() const = 0;

    /**
     * @brief 设置状态向量
     */
    virtual void set_state(const StateVector& state) = 0;

    /**
     * @brief 获取模型名称
     */
    virtual std::string name() const = 0;

    /**
     * @brief 获取状态维度
     */
    virtual int state_dim() const = 0;

    /**
     * @brief 获取输入维度
     */
    virtual int input_dim() const = 0;

    /**
     * @brief 获取输出维度
     */
    virtual int output_dim() const = 0;
};

// ============================================================================
// PMSM dq轴模型
// ============================================================================

/**
 * @brief PMSM dq轴集总参数模型
 *
 * 状态方程:
 *   Ld * did/dt = vd - Rs*id + we*Lq*iq
 *   Lq * diq/dt = vq - Rs*iq - we*Ld*id - we*lambda_m
 *   J * dwe/dt = Te - Tl - B*we
 *
 * 参考: sim_platform/models/motor/pmsm_dq.py
 */
class PMSMModel : public PhysicsModelBase {
public:
    /**
     * @brief PMSM参数结构
     */
    struct Params {
        double Rs = 0.5;        // 定子电阻 (Ohm)
        double Ld = 0.005;      // d轴电感 (H)
        double Lq = 0.008;      // q轴电感 (H)
        double lambda_m = 0.1;  // 永磁体磁链 (Wb)
        double J = 0.001;       // 转动惯量 (kg*m^2)
        double B = 0.001;       // 粘滞摩擦系数 (N*m*s/rad)
        int p = 4;              // 极对数
    };

    PMSMModel();
    explicit PMSMModel(const Params& params);

    ModelOutput step(const std::vector<double>& inputs, double dt) override;
    void reset() override;
    StateVector get_state() const override;
    void set_state(const StateVector& state) override;
    std::string name() const override { return "PMSM_dq"; }
    int state_dim() const override { return 3; }  // id, iq, we
    int input_dim() const override { return 3; }   // vd, vq, Tl
    int output_dim() const override { return 5; }  // id, iq, we, Te, Ploss

    // 设置参数
    void set_params(const Params& params) { params_ = params; }
    const Params& get_params() const { return params_; }

    // 计算电磁转矩
    double calc_torque(double id, double iq) const;

    // 计算功率损耗
    double calc_power_loss(double id, double iq, double vd, double vq) const;

private:
    Params params_;
    double id_ = 0.0, iq_ = 0.0, we_ = 0.0;  // 状态: d轴电流, q轴电流, 电角速度

    // 状态方程
    std::array<double, 3> state_equations(double vd, double vq, double Tl) const;
};

// ============================================================================
// FOC控制器
// ============================================================================

/**
 * @brief PI控制器 (带Anti-Windup)
 */
class PIController {
public:
    struct Params {
        double Kp = 1.0;       // 比例增益
        double Ki = 0.1;       // 积分增益
        double out_min = -100; // 输出下限
        double out_max = 100;  // 输出上限
    };

    PIController();
    explicit PIController(const Params& params);

    double update(double setpoint, double measurement, double dt);
    void reset();

    void set_params(const Params& p) { params_ = p; }

private:
    Params params_;
    double integral_ = 0.0;
    double prev_error_ = 0.0;
};

/**
 * @brief FOC控制器
 *
 * 实现Clarke/Park变换、SVPWM、PI电流环、速度环。
 * 参考: sim_platform/models/controller/foc.py
 */
class FOCController : public PhysicsModelBase {
public:
    struct Params {
        // 电流环PI参数
        PIController::Params current_d{10.0, 100.0, -100, 100};
        PIController::Params current_q{10.0, 100.0, -100, 100};
        // 速度环PI参数
        PIController::Params speed{1.0, 0.1, -50, 50};
        // 限幅
        double vd_max = 100.0;
        double vq_max = 100.0;
        int p = 4;  // 极对数
    };

    FOCController();
    explicit FOCController(const Params& params);

    ModelOutput step(const std::vector<double>& inputs, double dt) override;
    void reset() override;
    StateVector get_state() const override;
    void set_state(const StateVector& state) override;
    std::string name() const override { return "FOC"; }
    int state_dim() const override { return 0; }  // 无状态（PI控制器内部状态）
    int input_dim() const override { return 4; }   // id_ref, iq_ref, id_meas, iq_meas
    int output_dim() const override { return 2; }  // vd, vq

    // Clarke/Park变换
    static std::array<double, 2> clarke_transform(double ia, double ib, double ic);
    static std::array<double, 2> park_transform(double i_alpha, double i_beta, double theta);
    static std::array<double, 3> inv_clarke_transform(double v_alpha, double v_beta);
    static std::array<double, 2> inv_park_transform(double vd, double vq, double theta);

    // SVPWM
    static std::array<double, 3> svpwm(double v_alpha, double v_beta, double v_dc);

    void set_params(const Params& p) { params_ = p; }

private:
    Params params_;
    PIController pi_d_, pi_q_, pi_speed_;
};

// ============================================================================
// DC-DC Buck变换器
// ============================================================================

/**
 * @brief Buck变换器CCM模型
 *
 * 状态方程:
 *   L * diL/dt = D*vin - vout - iL*R_L
 *   C * dvout/dt = iL - vout/R_load
 *
 * 参考: param_id_gui/models/power_models.py
 */
class BuckConverter : public PhysicsModelBase {
public:
    struct Params {
        double L = 100e-6;     // 电感 (H)
        double C = 100e-6;     // 电容 (F)
        double R_L = 0.01;     // 电感电阻 (Ohm)
        double R_C = 0.01;     // 电容ESR (Ohm)
        double R_on = 0.01;    // MOSFET导通电阻 (Ohm)
        double V_f = 0.7;      // 二极管正向压降 (V)
    };

    BuckConverter();
    explicit BuckConverter(const Params& params);

    ModelOutput step(const std::vector<double>& inputs, double dt) override;
    void reset() override;
    StateVector get_state() const override;
    void set_state(const StateVector& state) override;
    std::string name() const override { return "Buck"; }
    int state_dim() const override { return 2; }  // iL, vout
    int input_dim() const override { return 3; }   // vin, duty, R_load
    int output_dim() const override { return 3; }  // iL, vout, Ploss

    void set_params(const Params& p) { params_ = p; }

private:
    Params params_;
    double iL_ = 0.0, vout_ = 0.0;  // 状态: 电感电流, 输出电压
};

// ============================================================================
// DC-DC Boost变换器
// ============================================================================

/**
 * @brief Boost变换器CCM模型
 *
 * 状态方程:
 *   L * diL/dt = vin - (1-D)*vout - iL*R_L
 *   C * dvout/dt = (1-D)*iL - vout/R_load
 */
class BoostConverter : public PhysicsModelBase {
public:
    struct Params {
        double L = 100e-6;     // 电感 (H)
        double C = 100e-6;     // 电容 (F)
        double R_L = 0.01;     // 电感电阻 (Ohm)
        double R_C = 0.01;     // 电容ESR (Ohm)
        double R_on = 0.01;    // MOSFET导通电阻 (Ohm)
        double V_f = 0.7;      // 二极管正向压降 (V)
    };

    BoostConverter();
    explicit BoostConverter(const Params& params);

    ModelOutput step(const std::vector<double>& inputs, double dt) override;
    void reset() override;
    StateVector get_state() const override;
    void set_state(const StateVector& state) override;
    std::string name() const override { return "Boost"; }
    int state_dim() const override { return 2; }  // iL, vout
    int input_dim() const override { return 3; }   // vin, duty, R_load
    int output_dim() const override { return 3; }  // iL, vout, Ploss

    void set_params(const Params& p) { params_ = p; }

private:
    Params params_;
    double iL_ = 0.0, vout_ = 0.0;
};

// ============================================================================
// 电池模型
// ============================================================================

/**
 * @brief Rint电池模型
 *
 * V_terminal = OCV(SOC) - I * R_internal
 */
class BatteryModel : public PhysicsModelBase {
public:
    struct Params {
        double capacity = 10.0;      // 容量 (Ah)
        double R_internal = 0.01;    // 内阻 (Ohm)
        double V_full = 4.2;         // 满充电压 (V)
        double V_empty = 3.0;        // 放空电压 (V)
    };

    BatteryModel();
    explicit BatteryModel(const Params& params);

    ModelOutput step(const std::vector<double>& inputs, double dt) override;
    void reset() override;
    StateVector get_state() const override;
    void set_state(const StateVector& state) override;
    std::string name() const override { return "Battery_Rint"; }
    int state_dim() const override { return 1; }  // SOC
    int input_dim() const override { return 1; }   // I (电流)
    int output_dim() const override { return 2; }  // V_terminal, SOC

    // OCV-SOC曲线
    double ocv_from_soc(double soc) const;

    void set_params(const Params& p) { params_ = p; }

private:
    Params params_;
    double soc_ = 1.0;  // 状态: 荷电状态 (0-1)
};

} // namespace models
} // namespace param_id
