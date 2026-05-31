/**
 * @file optimizers.cpp
 * @brief 优化算法层实现
 */

#include "../../include/optim/optimizers.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <iostream>

namespace param_id {
namespace optim {

// ============================================================================
// ParamBounds实现
// ============================================================================

std::vector<double> ParamBounds::clip(const std::vector<double>& params) const {
    std::vector<double> result = params;
    for (size_t i = 0; i < result.size(); ++i) {
        result[i] = std::max(lower[i], std::min(upper[i], result[i]));
    }
    return result;
}

// ============================================================================
// LevenbergMarquardt实现
// ============================================================================

OptResult LevenbergMarquardt::minimize(const ObjectiveFunction& objective,
                                        const std::vector<double>& initial_params) {
    OptResult result;
    std::vector<double> params = initial_params;
    size_t n = params.size();

    double lambda = lm_config_.lambda_init;
    auto residuals = objective(params);
    result.function_evals++;
    double cost = compute_cost(residuals);
    result.cost_history.push_back(cost);

    for (int iter = 0; iter < config_.max_iterations; ++iter) {
        result.iterations = iter + 1;

        // 计算雅可比矩阵
        auto J = jacobian_ ? jacobian_(params) : compute_jacobian(objective, params, residuals);
        result.function_evals += n;

        // 计算梯度和Hessian近似
        std::vector<double> gradient(n, 0.0);
        std::vector<std::vector<double>> H(n, std::vector<double>(n, 0.0));
        for (size_t i = 0; i < n; ++i) {
            for (size_t k = 0; k < residuals.size(); ++k) {
                gradient[i] += J[k][i] * residuals[k];
            }
            for (size_t j = 0; j < n; ++j) {
                for (size_t k = 0; k < residuals.size(); ++k) {
                    H[i][j] += J[k][i] * J[k][j];
                }
            }
        }

        // 检查梯度收敛
        double grad_norm = 0.0;
        for (size_t i = 0; i < n; ++i) grad_norm += gradient[i] * gradient[i];
        if (std::sqrt(grad_norm) < config_.tol_gradient) {
            result.converged = true;
            result.message = "Gradient converged";
            break;
        }

        // LM步: (H + lambda * I) * delta = -gradient
        std::vector<double> delta = solve_normal_equations(J, residuals, lambda);

        // 试探新参数
        std::vector<double> new_params(n);
        for (size_t i = 0; i < n; ++i) new_params[i] = params[i] + delta[i];

        // 边界裁剪
        if (bounds_.is_valid()) new_params = bounds_.clip(new_params);

        auto new_residuals = objective(new_params);
        result.function_evals++;
        double new_cost = compute_cost(new_residuals);

        // 增益比
        double actual_reduction = cost - new_cost;
        double predicted_reduction = 0.0;
        for (size_t i = 0; i < n; ++i) {
            predicted_reduction += delta[i] * (lambda * delta[i] + gradient[i]);
        }
        double gain_ratio = (predicted_reduction > 0) ? actual_reduction / predicted_reduction : 0.0;

        if (gain_ratio > lm_config_.gain_ratio_min) {
            // 接受步长
            params = new_params;
            residuals = new_residuals;
            cost = new_cost;
            result.cost_history.push_back(cost);

            // 减小lambda
            lambda = std::max(lambda / lm_config_.lambda_factor, lm_config_.lambda_min);

            // 检查收敛
            if (actual_reduction < config_.tol * (1.0 + cost)) {
                result.converged = true;
                result.message = "Cost converged";
                break;
            }
        } else {
            // 拒绝步长，增大lambda
            lambda = std::min(lambda * lm_config_.lambda_factor, lm_config_.lambda_max);
        }
    }

    result.best_params = params;
    result.best_cost = cost;
    return result;
}

std::vector<std::vector<double>> LevenbergMarquardt::compute_jacobian(
    const ObjectiveFunction& objective,
    const std::vector<double>& params,
    const std::vector<double>& residuals) {
    size_t n = params.size();
    size_t m = residuals.size();
    double h = lm_config_.finite_diff_step;

    std::vector<std::vector<double>> J(m, std::vector<double>(n));
    for (size_t j = 0; j < n; ++j) {
        std::vector<double> params_p = params;
        params_p[j] += h;
        auto residuals_p = objective(params_p);
        for (size_t i = 0; i < m; ++i) {
            J[i][j] = (residuals_p[i] - residuals[i]) / h;
        }
    }
    return J;
}

double LevenbergMarquardt::compute_cost(const std::vector<double>& residuals) const {
    double cost = 0.0;
    for (double r : residuals) cost += r * r;
    return 0.5 * cost;
}

std::vector<double> LevenbergMarquardt::solve_normal_equations(
    const std::vector<std::vector<double>>& J,
    const std::vector<double>& residuals,
    double lambda) {
    size_t n = J[0].size();
    size_t m = J.size();

    // 计算 J^T * J + lambda * diag(J^T * J)
    std::vector<std::vector<double>> H(n, std::vector<double>(n, 0.0));
    std::vector<double> g(n, 0.0);

    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            for (size_t k = 0; k < m; ++k) {
                H[i][j] += J[k][i] * J[k][j];
            }
        }
        // 阻尼
        H[i][i] += lambda * H[i][i];
        if (H[i][i] < 1e-10) H[i][i] = lambda;

        // 梯度
        for (size_t k = 0; k < m; ++k) {
            g[i] += J[k][i] * residuals[k];
        }
    }

    // 求解 H * delta = -g (Gauss-Seidel)
    std::vector<double> delta(n, 0.0);
    for (int iter = 0; iter < 50; ++iter) {
        for (size_t i = 0; i < n; ++i) {
            double sum = -g[i];
            for (size_t j = 0; j < n; ++j) {
                if (j != i) sum -= H[i][j] * delta[j];
            }
            delta[i] = sum / H[i][i];
        }
    }

    return delta;
}

// ============================================================================
// ParticleSwarmOptimization实现
// ============================================================================

OptResult ParticleSwarmOptimization::minimize(const ObjectiveFunction& objective,
                                               const std::vector<double>& initial_params) {
    // 转换为代价函数
    CostFunction cost_func = [&](const std::vector<double>& p) {
        auto res = objective(p);
        double cost = 0.0;
        for (double r : res) cost += r * r;
        return cost;
    };
    return minimize_cost(cost_func, initial_params);
}

OptResult ParticleSwarmOptimization::minimize_cost(const CostFunction& cost_function,
                                                    const std::vector<double>& initial_params) {
    OptResult result;
    size_t dim = initial_params.size();

    // 初始化粒子群
    auto swarm = init_swarm(dim, bounds_);

    // 全局最优
    std::vector<double> global_best = initial_params;
    double global_best_cost = cost_function(initial_params);
    result.function_evals++;

    // 初始粒子位置设为initial_params附近
    for (auto& p : swarm) {
        for (size_t i = 0; i < dim; ++i) {
            p.position[i] = initial_params[i] + (p.position[i] - 0.5) * 0.1;
        }
        if (bounds_.is_valid()) p.position = bounds_.clip(p.position);
    }

    double w = pso_config_.w;

    for (int iter = 0; iter < config_.max_iterations; ++iter) {
        result.iterations = iter + 1;

        for (auto& p : swarm) {
            // 计算代价
            double cost = cost_function(p.position);
            result.function_evals++;

            // 更新个体最优
            if (cost < p.best_cost) {
                p.best_cost = cost;
                p.best_position = p.position;
            }

            // 更新全局最优
            if (cost < global_best_cost) {
                global_best_cost = cost;
                global_best = p.position;
            }
        }

        // 更新粒子
        for (auto& p : swarm) {
            update_particle(p, global_best, w, bounds_);
        }

        // 惯性衰减
        w *= pso_config_.w_decay;

        result.cost_history.push_back(global_best_cost);

        // 收敛检查
        if (result.cost_history.size() > 10) {
            double recent_change = std::abs(result.cost_history.back() -
                                            result.cost_history[result.cost_history.size() - 10]);
            if (recent_change < config_.tol) {
                result.converged = true;
                result.message = "Cost converged";
                break;
            }
        }
    }

    result.best_params = global_best;
    result.best_cost = global_best_cost;
    return result;
}

std::vector<ParticleSwarmOptimization::Particle> ParticleSwarmOptimization::init_swarm(
    size_t dim, const ParamBounds& bounds) {
    std::mt19937 rng(pso_config_.seed);
    std::vector<Particle> swarm(pso_config_.swarm_size);

    for (auto& p : swarm) {
        p.position.resize(dim);
        p.velocity.resize(dim);
        p.best_position.resize(dim);

        for (size_t i = 0; i < dim; ++i) {
            if (bounds.is_valid()) {
                std::uniform_real_distribution<double> dist(bounds.lower[i], bounds.upper[i]);
                p.position[i] = dist(rng);
                p.velocity[i] = (dist(rng) - dist(rng)) * pso_config_.v_max;
            } else {
                std::uniform_real_distribution<double> dist(-1.0, 1.0);
                p.position[i] = dist(rng);
                p.velocity[i] = dist(rng) * pso_config_.v_max;
            }
            p.best_position[i] = p.position[i];
        }
    }
    return swarm;
}

void ParticleSwarmOptimization::update_particle(Particle& p, const std::vector<double>& global_best,
                                                 double w, const ParamBounds& bounds) {
    std::mt19937 rng(std::random_device{}());
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    for (size_t i = 0; i < p.position.size(); ++i) {
        double r1 = dist(rng), r2 = dist(rng);
        p.velocity[i] = w * p.velocity[i]
                       + pso_config_.c1 * r1 * (p.best_position[i] - p.position[i])
                       + pso_config_.c2 * r2 * (global_best[i] - p.position[i]);

        // 速度限制
        double v_max = (bounds.is_valid()) ?
            (bounds.upper[i] - bounds.lower[i]) * pso_config_.v_max : pso_config_.v_max;
        p.velocity[i] = std::max(-v_max, std::min(v_max, p.velocity[i]));

        p.position[i] += p.velocity[i];

        // 边界处理
        if (bounds.is_valid()) {
            if (p.position[i] < bounds.lower[i]) {
                p.position[i] = bounds.lower[i];
                p.velocity[i] *= -0.5;
            }
            if (p.position[i] > bounds.upper[i]) {
                p.position[i] = bounds.upper[i];
                p.velocity[i] *= -0.5;
            }
        }
    }
}

double ParticleSwarmOptimization::compute_cost(const std::vector<double>& residuals) const {
    double cost = 0.0;
    for (double r : residuals) cost += r * r;
    return cost;
}

// ============================================================================
// GradientDescent实现
// ============================================================================

OptResult GradientDescent::minimize(const ObjectiveFunction& objective,
                                     const std::vector<double>& initial_params) {
    OptResult result;
    std::vector<double> params = initial_params;
    size_t n = params.size();

    // Adam状态
    std::vector<double> m(n, 0.0), v(n, 0.0);
    int t = 0;

    auto residuals = objective(params);
    result.function_evals++;
    double cost = 0.0;
    for (double r : residuals) cost += r * r;
    result.cost_history.push_back(cost);

    for (int iter = 0; iter < config_.max_iterations; ++iter) {
        result.iterations = iter + 1;

        // 计算梯度
        std::vector<double> grad;
        if (gradient_) {
            grad = gradient_(params);
        } else {
            grad = compute_gradient(objective, params);
            result.function_evals += n;
        }

        t++;

        if (gd_config_.method == Method::ADAM) {
            // Adam更新
            for (size_t i = 0; i < n; ++i) {
                m[i] = gd_config_.beta1 * m[i] + (1.0 - gd_config_.beta1) * grad[i];
                v[i] = gd_config_.beta2 * v[i] + (1.0 - gd_config_.beta2) * grad[i] * grad[i];
                double m_hat = m[i] / (1.0 - std::pow(gd_config_.beta1, t));
                double v_hat = v[i] / (1.0 - std::pow(gd_config_.beta2, t));
                params[i] -= gd_config_.learning_rate * m_hat / (std::sqrt(v_hat) + gd_config_.epsilon);
            }
        } else {
            // SGD with momentum
            for (size_t i = 0; i < n; ++i) {
                m[i] = gd_config_.momentum * m[i] - gd_config_.learning_rate * grad[i];
                params[i] += m[i];
            }
        }

        // 边界裁剪
        if (bounds_.is_valid()) params = bounds_.clip(params);

        // 计算新代价
        residuals = objective(params);
        result.function_evals++;
        cost = 0.0;
        for (double r : residuals) cost += r * r;
        result.cost_history.push_back(cost);

        // 收敛检查
        double grad_norm = 0.0;
        for (double g : grad) grad_norm += g * g;
        if (std::sqrt(grad_norm) < config_.tol_gradient) {
            result.converged = true;
            result.message = "Gradient converged";
            break;
        }
    }

    result.best_params = params;
    result.best_cost = cost;
    return result;
}

std::vector<double> GradientDescent::compute_gradient(
    const ObjectiveFunction& objective,
    const std::vector<double>& params) {
    size_t n = params.size();
    double h = 1e-7;
    std::vector<double> grad(n);

    auto f0 = objective(params);
    double cost0 = 0.0;
    for (double r : f0) cost0 += r * r;

    for (size_t i = 0; i < n; ++i) {
        std::vector<double> params_p = params;
        params_p[i] += h;
        auto f_p = objective(params_p);
        double cost_p = 0.0;
        for (double r : f_p) cost_p += r * r;
        grad[i] = (cost_p - cost0) / h;
    }

    return grad;
}

// ============================================================================
// 工厂方法
// ============================================================================

std::unique_ptr<OptimizerBase> create_optimizer(OptimizerType type) {
    switch (type) {
        case OptimizerType::LM: return std::make_unique<LevenbergMarquardt>();
        case OptimizerType::PSO: return std::make_unique<ParticleSwarmOptimization>();
        case OptimizerType::SGD: {
            auto gd = std::make_unique<GradientDescent>();
            GradientDescent::GDConfig config;
            config.method = GradientDescent::Method::SGD;
            gd->set_gd_config(config);
            return gd;
        }
        case OptimizerType::ADAM: {
            auto gd = std::make_unique<GradientDescent>();
            GradientDescent::GDConfig config;
            config.method = GradientDescent::Method::ADAM;
            gd->set_gd_config(config);
            return gd;
        }
        default: throw std::invalid_argument("Unknown optimizer type");
    }
}

} // namespace optim
} // namespace param_id
