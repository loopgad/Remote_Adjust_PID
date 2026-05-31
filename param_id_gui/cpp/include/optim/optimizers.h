#pragma once
/**
 * @file optimizers.h
 * @brief 优化算法层 - 参数识别算法
 *
 * 提供参数识别所需的优化算法：
 * - Levenberg-Marquardt (LM): 非线性最小二乘
 * - PSO: 粒子群优化
 * - 梯度下降: 基础优化
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <functional>
#include <random>
#include <limits>
#include <string>
#include <algorithm>
#include <cmath>
#include <memory>

namespace param_id {
namespace optim {

// ============================================================================
// 类型定义
// ============================================================================

/** @brief 目标函数类型: f(params) -> residuals */
using ObjectiveFunction = std::function<std::vector<double>(const std::vector<double>&)>;

/** @brief 代价函数类型: f(params) -> cost */
using CostFunction = std::function<double(const std::vector<double>&)>;

/** @brief 雅可比矩阵函数 */
using JacobianFunction = std::function<std::vector<std::vector<double>>(const std::vector<double>&)>;

/** @brief 参数边界 */
struct ParamBounds {
    std::vector<double> lower;
    std::vector<double> upper;

    bool is_valid() const { return lower.size() == upper.size(); }
    size_t dim() const { return lower.size(); }

    /**
     * @brief 将参数裁剪到边界内
     */
    std::vector<double> clip(const std::vector<double>& params) const;
};

/** @brief 优化结果 */
struct OptResult {
    std::vector<double> best_params;   // 最优参数
    double best_cost = 0.0;            // 最优代价
    int iterations = 0;                // 迭代次数
    int function_evals = 0;            // 函数评估次数
    bool converged = false;            // 是否收敛
    std::string message;               // 终止信息
    std::vector<double> cost_history;  // 代价历史
};

/** @brief 优化器配置 */
struct OptConfig {
    int max_iterations = 1000;         // 最大迭代次数
    double tol = 1e-8;                 // 收敛容差
    double tol_gradient = 1e-6;        // 梯度容差
    bool verbose = false;              // 是否输出详细信息
    int log_interval = 100;            // 日志间隔
};

// ============================================================================
// 优化器基类
// ============================================================================

/**
 * @brief 优化器基类
 */
class OptimizerBase {
public:
    virtual ~OptimizerBase() = default;

    /**
     * @brief 最小化目标函数
     * @param objective 目标函数 (返回残差向量)
     * @param initial_params 初始参数
     * @return 优化结果
     */
    virtual OptResult minimize(const ObjectiveFunction& objective,
                               const std::vector<double>& initial_params) = 0;

    /**
     * @brief 设置配置
     */
    virtual void set_config(const OptConfig& config) { config_ = config; }

    /**
     * @brief 设置参数边界
     */
    virtual void set_bounds(const ParamBounds& bounds) { bounds_ = bounds; }

    /**
     * @brief 获取优化器名称
     */
    virtual std::string name() const = 0;

protected:
    OptConfig config_;
    ParamBounds bounds_;
};

// ============================================================================
// Levenberg-Marquardt算法
// ============================================================================

/**
 * @brief Levenberg-Marquardt非线性最小二乘优化
 *
 * 结合梯度下降和高斯-牛顿法的优点：
 * - 远离最优解时表现如梯度下降（稳定）
 * - 接近最优解时表现如高斯-牛顿（快速）
 *
 * 适用于参数识别、曲线拟合等问题。
 */
class LevenbergMarquardt : public OptimizerBase {
public:
    struct LMConfig {
        double lambda_init = 1e-3;     // 初始阻尼因子
        double lambda_factor = 10.0;   // 阻尼因子调整倍数
        double lambda_min = 1e-10;     // 最小阻尼因子
        double lambda_max = 1e10;      // 最大阻尼因子
        double gain_ratio_min = 0.25;  // 最小增益比
        bool use_finite_diff = true;   // 使用有限差分计算雅可比
        double finite_diff_step = 1e-7;// 有限差分步长
    };

    LevenbergMarquardt() = default;
    explicit LevenbergMarquardt(const LMConfig& lm_config) : lm_config_(lm_config) {}

    OptResult minimize(const ObjectiveFunction& objective,
                       const std::vector<double>& initial_params) override;

    /**
     * @brief 设置雅可比矩阵函数（可选，否则使用有限差分）
     */
    void set_jacobian(const JacobianFunction& jac) { jacobian_ = jac; }

    std::string name() const override { return "Levenberg-Marquardt"; }

    void set_lm_config(const LMConfig& config) { lm_config_ = config; }

private:
    LMConfig lm_config_;
    JacobianFunction jacobian_;

    // 计算雅可比矩阵（有限差分）
    std::vector<std::vector<double>> compute_jacobian(
        const ObjectiveFunction& objective,
        const std::vector<double>& params,
        const std::vector<double>& residuals);

    // 计算残差平方和
    double compute_cost(const std::vector<double>& residuals) const;

    // 求解正规方程
    std::vector<double> solve_normal_equations(
        const std::vector<std::vector<double>>& J,
        const std::vector<double>& residuals,
        double lambda);
};

// ============================================================================
// 粒子群优化 (PSO)
// ============================================================================

/**
 * @brief 粒子群优化算法
 *
 * 群体智能优化算法，适用于全局搜索、多模态问题。
 * 不需要梯度信息，适合黑盒优化。
 */
class ParticleSwarmOptimization : public OptimizerBase {
public:
    struct PSOConfig {
        int swarm_size = 50;           // 粒子数量
        double w = 0.7;                // 惯性权重
        double c1 = 1.5;               // 个体学习因子
        double c2 = 1.5;               // 社会学习因子
        double w_decay = 0.99;         // 惯性衰减率
        double v_max = 0.5;            // 最大速度（相对于搜索范围）
        bool use_bounds = true;        // 是否使用边界约束
        unsigned int seed = 42;        // 随机种子
    };

    ParticleSwarmOptimization() = default;
    explicit ParticleSwarmOptimization(const PSOConfig& pso_config) : pso_config_(pso_config) {}

    OptResult minimize(const ObjectiveFunction& objective,
                       const std::vector<double>& initial_params) override;

    /**
     * @brief 使用代价函数直接优化（不返回残差向量）
     */
    OptResult minimize_cost(const CostFunction& cost_function,
                            const std::vector<double>& initial_params);

    std::string name() const override { return "PSO"; }

    void set_pso_config(const PSOConfig& config) { pso_config_ = config; }

private:
    PSOConfig pso_config_;

    struct Particle {
        std::vector<double> position;
        std::vector<double> velocity;
        std::vector<double> best_position;
        double best_cost = std::numeric_limits<double>::max();
    };

    // 初始化粒子群
    std::vector<Particle> init_swarm(size_t dim, const ParamBounds& bounds);

    // 更新粒子
    void update_particle(Particle& p, const std::vector<double>& global_best,
                         double w, const ParamBounds& bounds);

    // 计算代价
    double compute_cost(const std::vector<double>& residuals) const;
};

// ============================================================================
// 梯度下降优化器
// ============================================================================

/**
 * @brief 梯度下降优化器
 *
 * 基础优化算法，支持：
 * - 固定学习率
 * - 自适应学习率（Adam）
 */
class GradientDescent : public OptimizerBase {
public:
    enum class Method {
        SGD,    // 随机梯度下降
        ADAM    // Adam自适应学习率
    };

    struct GDConfig {
        Method method = Method::ADAM;
        double learning_rate = 0.001;  // 学习率
        double beta1 = 0.9;            // Adam一阶矩衰减率
        double beta2 = 0.999;          // Adam二阶矩衰减率
        double epsilon = 1e-8;         // Adam数值稳定项
        double momentum = 0.9;         // SGD动量
        int batch_size = -1;           // 批大小 (-1表示全批量)
    };

    GradientDescent() = default;
    explicit GradientDescent(const GDConfig& gd_config) : gd_config_(gd_config) {}

    OptResult minimize(const ObjectiveFunction& objective,
                       const std::vector<double>& initial_params) override;

    /**
     * @brief 设置梯度函数（可选，否则使用有限差分）
     */
    void set_gradient(const std::function<std::vector<double>(const std::vector<double>&)>& grad) {
        gradient_ = grad;
    }

    std::string name() const override { return "GradientDescent"; }

    void set_gd_config(const GDConfig& config) { gd_config_ = config; }

private:
    GDConfig gd_config_;
    std::function<std::vector<double>(const std::vector<double>&)> gradient_;

    // 数值梯度计算
    std::vector<double> compute_gradient(
        const ObjectiveFunction& objective,
        const std::vector<double>& params);
};

// ============================================================================
// 优化器工厂
// ============================================================================

enum class OptimizerType {
    LM,     // Levenberg-Marquardt
    PSO,    // 粒子群优化
    SGD,    // 随机梯度下降
    ADAM    // Adam
};

/**
 * @brief 创建优化器实例
 */
std::unique_ptr<OptimizerBase> create_optimizer(OptimizerType type);

} // namespace optim
} // namespace param_id
