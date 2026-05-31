/**
 * @file ode_solvers.cpp
 * @brief ODE求解器层实现
 */

#include "../../include/solvers/ode_solvers.h"
#include <cmath>
#include <algorithm>
#include <numeric>

namespace param_id {
namespace solvers {

// ============================================================================
// RK4实现 (增强版)
// ============================================================================

SolveResult RK4Solver::solve(const ODEFunction& f, double t0, double t1,
                             const std::vector<double>& y0) {
    SolveResult result;
    double dt = config_.dt_initial;
    double t = t0;
    std::vector<double> y = y0;

    result.t.push_back(t);
    result.y.push_back(y);

    while (t < t1 - 1e-15 * std::abs(t1)) {
        if (result.steps_taken >= config_.max_steps) {
            result.converged = false;
            result.error_message = "Max steps exceeded";
            break;
        }

        double current_dt = std::min(dt, t1 - t);
        y = step(f, t, y, current_dt);
        t += current_dt;
        result.steps_taken++;
        result.function_evals += 4;

        result.t.push_back(t);
        result.y.push_back(y);
    }

    return result;
}

std::vector<double> RK4Solver::step(const ODEFunction& f, double t,
                                    const std::vector<double>& y, double dt) {
    size_t n = y.size();
    double half_dt = 0.5 * dt;

    auto k1 = f(t, y);

    std::vector<double> y_temp(n);
    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + half_dt * k1[i];
    auto k2 = f(t + half_dt, y_temp);

    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + half_dt * k2[i];
    auto k3 = f(t + half_dt, y_temp);

    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + dt * k3[i];
    auto k4 = f(t + dt, y_temp);

    std::vector<double> result(n);
    for (size_t i = 0; i < n; ++i) {
        result[i] = y[i] + dt / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
    }
    return result;
}

// ============================================================================
// RK45实现 (自适应步长)
// ============================================================================

SolveResult RK45Solver::solve(const ODEFunction& f, double t0, double t1,
                              const std::vector<double>& y0) {
    SolveResult result;
    double dt = config_.dt_initial;
    double t = t0;
    std::vector<double> y = y0;

    result.t.push_back(t);
    result.y.push_back(y);

    while (t < t1 - 1e-15 * std::abs(t1)) {
        if (result.steps_taken >= config_.max_steps) {
            result.converged = false;
            result.error_message = "Max steps exceeded";
            break;
        }

        double current_dt = std::min(dt, t1 - t);

        // Fehlberg 4(5) Butcher tableau - correct coefficients
        size_t n = y.size();
        auto k1 = f(t, y);

        std::vector<double> y_temp(n);
        for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + current_dt * (1.0/4.0) * k1[i];
        auto k2 = f(t + current_dt * a2, y_temp);

        for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + current_dt * (3.0/32.0 * k1[i] + 9.0/32.0 * k2[i]);
        auto k3 = f(t + current_dt * a3, y_temp);

        for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + current_dt * (1932.0/2197.0 * k1[i] - 7200.0/2197.0 * k2[i] + 7296.0/2197.0 * k3[i]);
        auto k4 = f(t + current_dt * a4, y_temp);

        for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + current_dt * (439.0/216.0 * k1[i] - 8.0 * k2[i] + 3680.0/513.0 * k3[i] - 845.0/4104.0 * k4[i]);
        auto k5 = f(t + current_dt * a5, y_temp);

        for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + current_dt * (-8.0/27.0 * k1[i] + 2.0 * k2[i] - 3544.0/2565.0 * k3[i] + 1859.0/4104.0 * k4[i] - 11.0/40.0 * k5[i]);
        auto k6 = f(t + current_dt * a6, y_temp);

        // 4th order solution
        std::vector<double> y4(n);
        for (size_t i = 0; i < n; ++i) {
            y4[i] = y[i] + current_dt * (b4_1 * k1[i] + b4_3 * k3[i] + b4_4 * k4[i] + b4_5 * k5[i]);
        }

        // 5th order solution
        std::vector<double> y5(n);
        for (size_t i = 0; i < n; ++i) {
            y5[i] = y[i] + current_dt * (b5_1 * k1[i] + b5_3 * k3[i] + b5_4 * k4[i] + b5_5 * k5[i] + b5_6 * k6[i]);
        }

        // Error estimate
        double error = estimate_error(y4, y5, config_.rtol, config_.atol);
        result.function_evals += 6;

        // 步长调整
        if (error < 1.0) {
            // 接受步长
            t += current_dt;
            y = y5;  // 使用5阶解
            result.steps_taken++;
            result.t.push_back(t);
            result.y.push_back(y);

            // 增大步长
            double safety = 0.9;
            double factor = safety * std::pow(1.0 / error, 0.2);
            factor = std::min(factor, 2.0);  // 最多增大2倍
            dt = std::min(dt * factor, config_.dt_max);
        } else {
            // 拒绝步长，减小步长
            double safety = 0.9;
            double factor = safety * std::pow(1.0 / error, 0.25);
            factor = std::max(factor, 0.1);  // 最多缩小10倍
            dt = std::max(dt * factor, config_.dt_min);

            if (dt <= config_.dt_min) {
                result.converged = false;
                result.error_message = "Step size too small";
                break;
            }
        }
    }

    return result;
}

std::vector<double> RK45Solver::step(const ODEFunction& f, double t,
                                     const std::vector<double>& y, double dt) {
    // 简化版：直接使用RK4
    size_t n = y.size();
    double half_dt = 0.5 * dt;

    auto k1 = f(t, y);
    std::vector<double> y_temp(n);
    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + half_dt * k1[i];
    auto k2 = f(t + half_dt, y_temp);

    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + half_dt * k2[i];
    auto k3 = f(t + half_dt, y_temp);

    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + dt * k3[i];
    auto k4 = f(t + dt, y_temp);

    std::vector<double> result(n);
    for (size_t i = 0; i < n; ++i) {
        result[i] = y[i] + dt / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
    }
    return result;
}

double RK45Solver::estimate_error(const std::vector<double>& y4,
                                  const std::vector<double>& y5,
                                  double rtol, double atol) const {
    double error = 0.0;
    for (size_t i = 0; i < y4.size(); ++i) {
        double scale = atol + rtol * std::max(std::abs(y4[i]), std::abs(y5[i]));
        error += std::pow((y5[i] - y4[i]) / scale, 2);
    }
    return std::sqrt(error / y4.size());
}

// ============================================================================
// RK23实现
// ============================================================================

SolveResult RK23Solver::solve(const ODEFunction& f, double t0, double t1,
                              const std::vector<double>& y0) {
    SolveResult result;
    double dt = config_.dt_initial;
    double t = t0;
    std::vector<double> y = y0;

    result.t.push_back(t);
    result.y.push_back(y);

    while (t < t1 - 1e-15 * std::abs(t1)) {
        if (result.steps_taken >= config_.max_steps) {
            result.converged = false;
            result.error_message = "Max steps exceeded";
            break;
        }

        double current_dt = std::min(dt, t1 - t);
        y = step(f, t, y, current_dt);
        t += current_dt;
        result.steps_taken++;
        result.function_evals += 4;

        result.t.push_back(t);
        result.y.push_back(y);
    }

    return result;
}

std::vector<double> RK23Solver::step(const ODEFunction& f, double t,
                                     const std::vector<double>& y, double dt) {
    // Bogacki-Shampine 2/3阶方法
    size_t n = y.size();

    auto k1 = f(t, y);

    std::vector<double> y_temp(n);
    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + 0.5 * dt * k1[i];
    auto k2 = f(t + 0.5 * dt, y_temp);

    for (size_t i = 0; i < n; ++i) y_temp[i] = y[i] + 0.75 * dt * k2[i];
    auto k3 = f(t + 0.75 * dt, y_temp);

    // 3阶解
    std::vector<double> result(n);
    for (size_t i = 0; i < n; ++i) {
        result[i] = y[i] + dt / 9.0 * (2.0 * k1[i] + 3.0 * k2[i] + 4.0 * k3[i]);
    }
    return result;
}

// ============================================================================
// ImplicitEuler实现
// ============================================================================

SolveResult ImplicitEulerSolver::solve(const ODEFunction& f, double t0, double t1,
                                       const std::vector<double>& y0) {
    SolveResult result;
    double dt = config_.dt_initial;
    double t = t0;
    std::vector<double> y = y0;

    result.t.push_back(t);
    result.y.push_back(y);

    while (t < t1 - 1e-15 * std::abs(t1)) {
        if (result.steps_taken >= config_.max_steps) {
            result.converged = false;
            result.error_message = "Max steps exceeded";
            break;
        }

        double current_dt = std::min(dt, t1 - t);
        y = step(f, t, y, current_dt);
        t += current_dt;
        result.steps_taken++;

        result.t.push_back(t);
        result.y.push_back(y);
    }

    return result;
}

std::vector<double> ImplicitEulerSolver::step(const ODEFunction& f, double t,
                                               const std::vector<double>& y, double dt) {
    // 隐式欧拉: y_{n+1} = y_n + dt * f(t_{n+1}, y_{n+1})
    // 使用牛顿迭代求解
    return newton_solve(f, t, dt, y, y);  // 初始猜测为当前值
}

std::vector<double> ImplicitEulerSolver::newton_solve(const ODEFunction& f, double t, double dt,
                                                       const std::vector<double>& y_old,
                                                       const std::vector<double>& y_guess) {
    std::vector<double> y = y_guess;
    size_t n = y.size();

    for (int iter = 0; iter < 50; ++iter) {
        // 计算残差: g(y) = y - y_old - dt * f(t + dt, y)
        auto f_val = f(t + dt, y);
        std::vector<double> g(n);
        for (size_t i = 0; i < n; ++i) {
            g[i] = y[i] - y_old[i] - dt * f_val[i];
        }

        // 检查收敛
        double norm = 0.0;
        for (size_t i = 0; i < n; ++i) norm += g[i] * g[i];
        if (std::sqrt(norm) < 1e-10) break;

        // 计算雅可比: J = I - dt * df/dy
        std::vector<std::vector<double>> J;
        if (jacobian_) {
            J = jacobian_(t + dt, y);
            for (size_t i = 0; i < n; ++i) {
                for (size_t j = 0; j < n; ++j) {
                    J[i][j] = (i == j ? 1.0 : 0.0) - dt * J[i][j];
                }
            }
        } else {
            J = numerical_jacobian(f, t + dt, y);
            for (size_t i = 0; i < n; ++i) {
                for (size_t j = 0; j < n; ++j) {
                    J[i][j] = (i == j ? 1.0 : 0.0) - dt * J[i][j];
                }
            }
        }

        // 求解 J * delta = -g
        // 简化：使用Gauss-Seidel迭代
        std::vector<double> delta(n, 0.0);
        for (int sweep = 0; sweep < 10; ++sweep) {
            for (size_t i = 0; i < n; ++i) {
                double sum = -g[i];
                for (size_t j = 0; j < n; ++j) {
                    if (j != i) sum -= J[i][j] * delta[j];
                }
                if (std::abs(J[i][i]) > 1e-15) delta[i] = sum / J[i][i];
            }
        }

        // 更新
        for (size_t i = 0; i < n; ++i) y[i] += delta[i];
    }

    return y;
}

std::vector<std::vector<double>> ImplicitEulerSolver::numerical_jacobian(
    const ODEFunction& f, double t, const std::vector<double>& y) {
    size_t n = y.size();
    double eps = 1e-7;
    auto f0 = f(t, y);
    std::vector<std::vector<double>> J(n, std::vector<double>(n));

    for (size_t j = 0; j < n; ++j) {
        std::vector<double> y_pert = y;
        y_pert[j] += eps;
        auto f_pert = f(t, y_pert);
        for (size_t i = 0; i < n; ++i) {
            J[i][j] = (f_pert[i] - f0[i]) / eps;
        }
    }
    return J;
}

// ============================================================================
// 工厂方法
// ============================================================================

std::unique_ptr<ODESolverBase> create_solver(SolverType type) {
    switch (type) {
        case SolverType::RK4: return std::make_unique<RK4Solver>();
        case SolverType::RK45: return std::make_unique<RK45Solver>();
        case SolverType::RK23: return std::make_unique<RK23Solver>();
        case SolverType::IMPLICIT_EULER: return std::make_unique<ImplicitEulerSolver>();
        default: throw std::invalid_argument("Unknown solver type");
    }
}

std::unique_ptr<ODESolverBase> create_solver(SolverType type, const SolverConfig& config) {
    auto solver = create_solver(type);
    solver->set_config(config);
    return solver;
}

} // namespace solvers
} // namespace param_id
