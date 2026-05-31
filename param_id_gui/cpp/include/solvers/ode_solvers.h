#pragma once
/**
 * @file ode_solvers.h
 * @brief ODE求解器层 - 常微分方程数值求解
 *
 * 提供多种ODE求解方法：
 * - RK4: 经典四阶Runge-Kutta
 * - RK45: 自适应步长Runge-Kutta-Fehlberg
 * - RK23: 低阶自适应Runge-Kutta
 * - 隐式欧拉: 刚性系统求解
 * - 多步法: Adams-Bashforth
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <functional>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include <limits>
#include <memory>
#include <string>

namespace param_id {
namespace solvers {

// ============================================================================
// 类型定义
// ============================================================================

/** @brief ODE函数类型: dy/dt = f(t, y) */
using ODEFunction = std::function<std::vector<double>(double, const std::vector<double>&)>;

/** @brief 雅可比矩阵函数: J[i][j] = df_i/dy_j */
using JacobianFunction = std::function<std::vector<std::vector<double>>(double, const std::vector<double>&)>;

/** @brief 求解结果 */
struct SolveResult {
    std::vector<double> t;           // 时间点
    std::vector<std::vector<double>> y;  // 状态向量
    int steps_taken = 0;             // 实际步数
    int function_evals = 0;          // 函数评估次数
    bool converged = true;           // 是否收敛
    std::string error_message;       // 错误信息
};

/** @brief 求解器配置 */
struct SolverConfig {
    double dt_initial = 1e-6;       // 初始步长
    double dt_min = 1e-12;          // 最小步长
    double dt_max = 1e-3;           // 最大步长
    double rtol = 1e-6;             // 相对容差
    double atol = 1e-9;             // 绝对容差
    int max_steps = 1000000;        // 最大步数
    double max_time = 1.0;          // 最大仿真时间
    bool dense_output = false;      // 是否输出密集点
};

// ============================================================================
// 求解器基类
// ============================================================================

/**
 * @brief ODE求解器基类
 */
class ODESolverBase {
public:
    virtual ~ODESolverBase() = default;

    /**
     * @brief 求解ODE
     * @param f ODE函数
     * @param t0 起始时间
     * @param t1 结束时间
     * @param y0 初始状态
     * @return 求解结果
     */
    virtual SolveResult solve(const ODEFunction& f,
                              double t0, double t1,
                              const std::vector<double>& y0) = 0;

    /**
     * @brief 单步推进
     * @param f ODE函数
     * @param t 当前时间
     * @param y 当前状态
     * @param dt 步长
     * @return 新状态
     */
    virtual std::vector<double> step(const ODEFunction& f,
                                     double t,
                                     const std::vector<double>& y,
                                     double dt) = 0;

    /**
     * @brief 设置配置
     */
    virtual void set_config(const SolverConfig& config) { config_ = config; }

    /**
     * @brief 获取求解器名称
     */
    virtual std::string name() const = 0;

protected:
    SolverConfig config_;
};

// ============================================================================
// RK4: 经典四阶Runge-Kutta (已有，增强)
// ============================================================================

/**
 * @brief 经典四阶Runge-Kutta求解器
 *
 * 固定步长，适用于非刚性系统。
 * 精度: O(dt^4)
 */
class RK4Solver : public ODESolverBase {
public:
    RK4Solver() = default;
    explicit RK4Solver(double dt) { config_.dt_initial = dt; }

    SolveResult solve(const ODEFunction& f,
                      double t0, double t1,
                      const std::vector<double>& y0) override;

    std::vector<double> step(const ODEFunction& f,
                             double t,
                             const std::vector<double>& y,
                             double dt) override;

    std::string name() const override { return "RK4"; }
};

// ============================================================================
// RK45: 自适应步长Runge-Kutta-Fehlberg
// ============================================================================

/**
 * @brief Runge-Kutta-Fehlberg自适应步长求解器
 *
 * 使用4阶和5阶公式估计误差，自动调整步长。
 * 精度: O(dt^4) 误差估计: O(dt^5)
 */
class RK45Solver : public ODESolverBase {
public:
    RK45Solver() = default;

    SolveResult solve(const ODEFunction& f,
                      double t0, double t1,
                      const std::vector<double>& y0) override;

    std::vector<double> step(const ODEFunction& f,
                             double t,
                             const std::vector<double>& y,
                             double dt) override;

    std::string name() const override { return "RK45"; }

private:
    // Butcher表系数
    static constexpr double a2 = 1.0/4.0;
    static constexpr double a3 = 3.0/8.0;
    static constexpr double a4 = 12.0/13.0;
    static constexpr double a5 = 1.0;
    static constexpr double a6 = 1.0/2.0;

    // 4阶权重
    static constexpr double b4_1 = 25.0/216.0;
    static constexpr double b4_3 = 1408.0/2565.0;
    static constexpr double b4_4 = 2197.0/4104.0;
    static constexpr double b4_5 = -1.0/5.0;

    // 5阶权重
    static constexpr double b5_1 = 16.0/135.0;
    static constexpr double b5_3 = 6656.0/12825.0;
    static constexpr double b5_4 = 28561.0/56430.0;
    static constexpr double b5_5 = -9.0/50.0;
    static constexpr double b5_6 = 2.0/55.0;

    double estimate_error(const std::vector<double>& y4,
                          const std::vector<double>& y5,
                          double rtol, double atol) const;
};

// ============================================================================
// RK23: Bogacki-Shampine低阶自适应方法
// ============================================================================

/**
 * @brief Bogacki-Shampine 2/3阶自适应求解器
 *
 * 适用于精度要求不高的快速仿真。
 */
class RK23Solver : public ODESolverBase {
public:
    RK23Solver() = default;

    SolveResult solve(const ODEFunction& f,
                      double t0, double t1,
                      const std::vector<double>& y0) override;

    std::vector<double> step(const ODEFunction& f,
                             double t,
                             const std::vector<double>& y,
                             double dt) override;

    std::string name() const override { return "RK23"; }
};

// ============================================================================
// 隐式欧拉: 刚性系统求解
// ============================================================================

/**
 * @brief 隐式欧拉求解器（后向Euler）
 *
 * A-稳定，适用于刚性系统。
 * 需要提供雅可比矩阵或使用数值近似。
 */
class ImplicitEulerSolver : public ODESolverBase {
public:
    ImplicitEulerSolver() = default;

    /**
     * @brief 设置雅可比矩阵函数
     */
    void set_jacobian(const JacobianFunction& jac) { jacobian_ = jac; }

    SolveResult solve(const ODEFunction& f,
                      double t0, double t1,
                      const std::vector<double>& y0) override;

    std::vector<double> step(const ODEFunction& f,
                             double t,
                             const std::vector<double>& y,
                             double dt) override;

    std::string name() const override { return "ImplicitEuler"; }

private:
    JacobianFunction jacobian_;

    // 牛顿迭代求解隐式方程
    std::vector<double> newton_solve(const ODEFunction& f,
                                     double t, double dt,
                                     const std::vector<double>& y_old,
                                     const std::vector<double>& y_guess);

    // 数值雅可比近似
    std::vector<std::vector<double>> numerical_jacobian(
        const ODEFunction& f, double t, const std::vector<double>& y);
};

// ============================================================================
// 求解器工厂
// ============================================================================

/**
 * @brief 求解器类型枚举
 */
enum class SolverType {
    RK4,            // 经典四阶RK
    RK45,           // 自适应RK45
    RK23,           // 低阶自适应RK23
    IMPLICIT_EULER  // 隐式欧拉
};

/**
 * @brief 创建求解器实例
 */
std::unique_ptr<ODESolverBase> create_solver(SolverType type);

/**
 * @brief 创建求解器实例并配置
 */
std::unique_ptr<ODESolverBase> create_solver(SolverType type, const SolverConfig& config);

} // namespace solvers
} // namespace param_id
