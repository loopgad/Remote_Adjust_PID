/**
 * @file physics_models.cpp
 * @brief 物理模型层实现
 */

#define _USE_MATH_DEFINES
#include "../../include/models/physics_models.h"
#include <cmath>
#include <algorithm>

namespace param_id {
namespace models {

// ============================================================================
// PMSMModel实现
// ============================================================================

PMSMModel::PMSMModel(const Params& params) : params_(params) {}

ModelOutput PMSMModel::step(const std::vector<double>& inputs, double dt) {
    if (inputs.size() < 3) throw std::invalid_argument("PMSM requires 3 inputs: vd, vq, Tl");

    double vd = inputs[0], vq = inputs[1], Tl = inputs[2];

    // 状态方程
    auto derivs = state_equations(vd, vq, Tl);

    // 欧拉积分
    id_ += derivs[0] * dt;
    iq_ += derivs[1] * dt;
    we_ += derivs[2] * dt;

    // 输出
    double Te = calc_torque(id_, iq_);
    double Ploss = calc_power_loss(id_, iq_, vd, vq);

    return {{id_, iq_, we_}, {id_, iq_, we_, Te, Ploss}, Ploss, 1.0 - Ploss / (Te * we_ + 1e-10)};
}

void PMSMModel::reset() {
    id_ = iq_ = we_ = 0.0;
}

StateVector PMSMModel::get_state() const { return {id_, iq_, we_}; }

void PMSMModel::set_state(const StateVector& state) {
    if (state.size() < 3) throw std::invalid_argument("State size mismatch");
    id_ = state[0]; iq_ = state[1]; we_ = state[2];
}

double PMSMModel::calc_torque(double id, double iq) const {
    return 1.5 * params_.p * (params_.lambda_m * iq + (params_.Ld - params_.Lq) * id * iq);
}

double PMSMModel::calc_power_loss(double id, double iq, double vd, double vq) const {
    double copper_loss = 1.5 * params_.Rs * (id * id + iq * iq);
    double core_loss = 0.001 * we_ * we_;  // 简化铁损模型
    return copper_loss + core_loss;
}

std::array<double, 3> PMSMModel::state_equations(double vd, double vq, double Tl) const {
    double did = (vd - params_.Rs * id_ + params_.p * we_ * params_.Lq * iq_) / params_.Ld;
    double diq = (vq - params_.Rs * iq_ - params_.p * we_ * params_.Ld * id_ - params_.p * we_ * params_.lambda_m) / params_.Lq;
    double Te = calc_torque(id_, iq_);
    double dwe = (Te - Tl - params_.B * we_) / params_.J;
    return {did, diq, dwe};
}

// ============================================================================
// PIController实现
// ============================================================================

PIController::PIController(const Params& params) : params_(params) {}

double PIController::update(double setpoint, double measurement, double dt) {
    double error = setpoint - measurement;
    integral_ += error * dt;

    // Anti-Windup
    integral_ = std::max(params_.out_min / params_.Ki, std::min(params_.out_max / params_.Ki, integral_));

    double output = params_.Kp * error + params_.Ki * integral_;
    output = std::max(params_.out_min, std::min(params_.out_max, output));

    prev_error_ = error;
    return output;
}

void PIController::reset() {
    integral_ = 0.0;
    prev_error_ = 0.0;
}

// ============================================================================
// FOCController实现
// ============================================================================

FOCController::FOCController(const Params& params)
    : params_(params), pi_d_(params_.current_d), pi_q_(params_.current_q), pi_speed_(params_.speed) {}

ModelOutput FOCController::step(const std::vector<double>& inputs, double dt) {
    if (inputs.size() < 4) throw std::invalid_argument("FOC requires 4 inputs");

    double id_ref = inputs[0], iq_ref = inputs[1];
    double id_meas = inputs[2], iq_meas = inputs[3];

    double vd = pi_d_.update(id_ref, id_meas, dt);
    double vq = pi_q_.update(iq_ref, iq_meas, dt);

    // 限幅
    vd = std::max(-params_.vd_max, std::min(params_.vd_max, vd));
    vq = std::max(-params_.vq_max, std::min(params_.vq_max, vq));

    return {{}, {vd, vq}, 0.0, 1.0};
}

void FOCController::reset() {
    pi_d_.reset();
    pi_q_.reset();
    pi_speed_.reset();
}

StateVector FOCController::get_state() const { return {}; }
void FOCController::set_state(const StateVector& state) {}

std::array<double, 2> FOCController::clarke_transform(double ia, double ib, double ic) {
    double alpha = ia;
    double beta = (ia + 2.0 * ib) / std::sqrt(3.0);
    return {alpha, beta};
}

std::array<double, 2> FOCController::park_transform(double i_alpha, double i_beta, double theta) {
    double id = i_alpha * std::cos(theta) + i_beta * std::sin(theta);
    double iq = -i_alpha * std::sin(theta) + i_beta * std::cos(theta);
    return {id, iq};
}

std::array<double, 3> FOCController::inv_clarke_transform(double v_alpha, double v_beta) {
    double va = v_alpha;
    double vb = -0.5 * v_alpha + std::sqrt(3.0) / 2.0 * v_beta;
    double vc = -0.5 * v_alpha - std::sqrt(3.0) / 2.0 * v_beta;
    return {va, vb, vc};
}

std::array<double, 2> FOCController::inv_park_transform(double vd, double vq, double theta) {
    double v_alpha = vd * std::cos(theta) - vq * std::sin(theta);
    double v_beta = vd * std::sin(theta) + vq * std::cos(theta);
    return {v_alpha, v_beta};
}

std::array<double, 3> FOCController::svpwm(double v_alpha, double v_beta, double v_dc) {
    // 简化SVPWM实现
    double v_ref = std::sqrt(v_alpha * v_alpha + v_beta * v_beta);
    double angle = std::atan2(v_beta, v_alpha);

    // 扇区判断
    int sector = static_cast<int>(angle / (M_PI / 3.0)) + 1;
    if (sector > 6) sector = 6;

    // 占空比计算（简化）
    double duty_a = 0.5 + v_ref / v_dc * std::cos(angle);
    double duty_b = 0.5 + v_ref / v_dc * std::cos(angle - 2.0 * M_PI / 3.0);
    double duty_c = 0.5 + v_ref / v_dc * std::cos(angle + 2.0 * M_PI / 3.0);

    return {duty_a, duty_b, duty_c};
}

// ============================================================================
// BuckConverter实现
// ============================================================================

BuckConverter::BuckConverter(const Params& params) : params_(params) {}

ModelOutput BuckConverter::step(const std::vector<double>& inputs, double dt) {
    if (inputs.size() < 3) throw std::invalid_argument("Buck requires 3 inputs: vin, duty, R_load");

    double vin = inputs[0], duty = inputs[1], R_load = inputs[2];

    // 状态方程 (CCM)
    double diL = (duty * vin - vout_ - iL_ * params_.R_L) / params_.L;
    double dvout = (iL_ - vout_ / R_load) / params_.C;

    // 欧拉积分
    iL_ += diL * dt;
    vout_ += dvout * dt;

    // 功率损耗
    double P_cond = iL_ * iL_ * params_.R_on * duty;
    double P_switch = 0.5 * vin * iL_ * 1e-9 * 100e3;  // 开关损耗估算
    double Ploss = P_cond + P_switch;

    return {{iL_, vout_}, {iL_, vout_, Ploss}, Ploss, vout_ * iL_ / (vin * iL_ * duty + 1e-10)};
}

void BuckConverter::reset() { iL_ = vout_ = 0.0; }
StateVector BuckConverter::get_state() const { return {iL_, vout_}; }
void BuckConverter::set_state(const StateVector& state) {
    iL_ = state[0]; vout_ = state[1];
}

// ============================================================================
// BoostConverter实现
// ============================================================================

BoostConverter::BoostConverter(const Params& params) : params_(params) {}

ModelOutput BoostConverter::step(const std::vector<double>& inputs, double dt) {
    if (inputs.size() < 3) throw std::invalid_argument("Boost requires 3 inputs: vin, duty, R_load");

    double vin = inputs[0], duty = inputs[1], R_load = inputs[2];

    // 状态方程 (CCM)
    double diL = (vin - (1.0 - duty) * vout_ - iL_ * params_.R_L) / params_.L;
    double dvout = ((1.0 - duty) * iL_ - vout_ / R_load) / params_.C;

    // 欧拉积分
    iL_ += diL * dt;
    vout_ += dvout * dt;

    // 功率损耗
    double Ploss = iL_ * iL_ * params_.R_L + vout_ * vout_ / R_load * 0.01;

    return {{iL_, vout_}, {iL_, vout_, Ploss}, Ploss, vout_ * vout_ / R_load / (vin * iL_ + 1e-10)};
}

void BoostConverter::reset() { iL_ = vout_ = 0.0; }
StateVector BoostConverter::get_state() const { return {iL_, vout_}; }
void BoostConverter::set_state(const StateVector& state) {
    iL_ = state[0]; vout_ = state[1];
}

// ============================================================================
// BatteryModel实现
// ============================================================================

BatteryModel::BatteryModel(const Params& params) : params_(params) {}

ModelOutput BatteryModel::step(const std::vector<double>& inputs, double dt) {
    if (inputs.size() < 1) throw std::invalid_argument("Battery requires 1 input: I");

    double I = inputs[0];

    // SOC更新: dSOC = -I * dt / capacity
    double dSOC = -I * dt / (params_.capacity * 3600.0);  // 转换为秒
    soc_ += dSOC;
    soc_ = std::max(0.0, std::min(1.0, soc_));

    // 端电压
    double OCV = ocv_from_soc(soc_);
    double V_terminal = OCV - I * params_.R_internal;

    return {{soc_}, {V_terminal, soc_}, I * I * params_.R_internal, V_terminal / OCV};
}

void BatteryModel::reset() { soc_ = 1.0; }
StateVector BatteryModel::get_state() const { return {soc_}; }
void BatteryModel::set_state(const StateVector& state) {
    soc_ = std::max(0.0, std::min(1.0, state[0]));
}

double BatteryModel::ocv_from_soc(double soc) const {
    // 简化的OCV-SOC曲线 (线性近似)
    return params_.V_empty + (params_.V_full - params_.V_empty) * soc;
}

} // namespace models
} // namespace param_id
