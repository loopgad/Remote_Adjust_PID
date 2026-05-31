#pragma once
/**
 * @file filters.h
 * @brief 滤波器层 - 信号处理滤波器
 *
 * 从 filter/ 项目提取并扩展，支持：
 * - 一阶带通滤波器 (First_Order_BPF)
 * - 均值滤波器 (MeanFilter)
 * - 中值滤波器 (MedianFilter)
 * - 卡尔曼滤波器 (KalmanFilter)
 * - 巴特沃斯滤波器 (ButterworthFilter)
 * - 滑动窗口滤波器 (SlidingWindowFilter)
 *
 * 支持两种精度：
 * - float 版本用于嵌入式/实时场景
 * - double 版本用于高精度离线计算
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <deque>
#include <stdexcept>
#include <array>
#include <memory>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace param_id {
namespace filters {

// ============================================================================
// 滤波器基类
// ============================================================================

/**
 * @brief 滤波器基类 - 定义统一接口
 */
class FilterBase {
public:
    virtual ~FilterBase() = default;

    /**
     * @brief 处理单个采样点
     * @param input 输入值
     * @return 滤波后的值
     */
    virtual double process(double input) = 0;

    /**
     * @brief 处理数组
     * @param input 输入数组
     * @return 滤波后的数组
     */
    virtual std::vector<double> process(const std::vector<double>& input);

    /**
     * @brief 重置滤波器状态
     */
    virtual void reset() = 0;

    /**
     * @brief 获取滤波器延迟（采样点数）
     */
    virtual int delay() const = 0;
};

// ============================================================================
// 一阶带通滤波器 (从 filter 项目提取)
// ============================================================================

/**
 * @brief 一阶带通滤波器
 *
 * 实现一阶IIR带通滤波，适用于特定频率范围的信号提取。
 * 参考: filter/on_destop_device/filter.h
 */
class FirstOrderBPF : public FilterBase {
public:
    /**
     * @param fc 中心频率 (Hz)
     * @param bw 带宽 (Hz)
     * @param fs 采样频率 (Hz)
     */
    FirstOrderBPF(double fc, double bw, double fs);

    double process(double input) override;
    void reset() override;
    int delay() const override { return 1; }

    // 获取滤波器系数
    double a0() const { return a0_; }
    double a1() const { return a1_; }

private:
    double fc_, bw_, fs_;
    double a0_, a1_;
    double last_input_ = 0;
    double last_output_ = 0;

    void calculate_coefficients();
};

// ============================================================================
// 均值滤波器 (从 filter 项目提取)
// ============================================================================

/**
 * @brief 滑动均值滤波器
 *
 * 对窗口内的数据取平均值，用于平滑高频噪声。
 * 参考: filter/on_destop_device/library.h
 */
class MeanFilter : public FilterBase {
public:
    /**
     * @param window_size 窗口大小
     */
    explicit MeanFilter(int window_size);

    double process(double input) override;
    std::vector<double> process(const std::vector<double>& input) override;
    void reset() override;
    int delay() const override { return window_size_ / 2; }

    int window_size() const { return window_size_; }

private:
    int window_size_;
    std::deque<double> buffer_;
    double sum_ = 0.0;
};

// ============================================================================
// 中值滤波器 (从 filter 项目提取)
// ============================================================================

/**
 * @brief 滑动中值滤波器
 *
 * 对窗口内的数据取中值，能有效去除突发噪声（椒盐噪声）。
 * 参考: filter/on_destop_device/library.h
 */
class MedianFilter : public FilterBase {
public:
    /**
     * @param window_size 窗口大小（奇数）
     */
    explicit MedianFilter(int window_size);

    double process(double input) override;
    std::vector<double> process(const std::vector<double>& input) override;
    void reset() override;
    int delay() const override { return window_size_ / 2; }

    int window_size() const { return window_size_; }

private:
    int window_size_;
    std::deque<double> buffer_;
};

// ============================================================================
// 卡尔曼滤波器 (从 filter 项目提取)
// ============================================================================

/**
 * @brief 一维卡尔曼滤波器
 *
 * 适用于线性系统的最优状态估计。
 * 参考: filter/on_destop_device/library.h
 */
class KalmanFilter : public FilterBase {
public:
    /**
     * @param process_noise 过程噪声方差
     * @param measurement_noise 测量噪声方差
     * @param initial_estimate 初始估计值
     * @param initial_error 初始误差协方差
     */
    KalmanFilter(double process_noise, double measurement_noise,
                 double initial_estimate = 0.0, double initial_error = 1.0);

    double process(double input) override;
    void reset() override;
    int delay() const override { return 0; }

    // 获取内部状态
    double estimate() const { return estimate_; }
    double error_covariance() const { return error_covariance_; }
    double kalman_gain() const { return kalman_gain_; }

    // 更新噪声参数
    void set_process_noise(double q) { process_noise_ = q; }
    void set_measurement_noise(double r) { measurement_noise_ = r; }

private:
    double process_noise_;
    double measurement_noise_;
    double estimate_;
    double error_covariance_;
    double kalman_gain_;

    void predict();
    void update(double measurement);
};

// ============================================================================
// 巴特沃斯低通滤波器 (新增)
// ============================================================================

/**
 * @brief 二阶巴特沃斯低通滤波器
 *
 * 提供平坦的通带响应，广泛用于信号预处理。
 */
class ButterworthFilter : public FilterBase {
public:
    /**
     * @param cutoff_freq 截止频率 (Hz)
     * @param fs 采样频率 (Hz)
     * @param order 阶数 (1-4)
     */
    ButterworthFilter(double cutoff_freq, double fs, int order = 2);

    double process(double input) override;
    void reset() override;
    int delay() const override { return order_; }

private:
    double cutoff_freq_;
    double fs_;
    int order_;

    // 二阶IIR滤波器系数
    double b0_, b1_, b2_, a1_, a2_;

    // 状态变量
    double x1_ = 0, x2_ = 0;
    double y1_ = 0, y2_ = 0;

    void calculate_coefficients();
};

// ============================================================================
// 滑动窗口统计滤波器 (新增)
// ============================================================================

/**
 * @brief 滑动窗口统计滤波器
 *
 * 提供窗口内的统计量：均值、中值、标准差、最大值、最小值。
 */
class SlidingWindowFilter {
public:
    explicit SlidingWindowFilter(int window_size);

    // 添加新数据点
    void push(double value);

    // 获取统计量
    double mean() const;
    double median() const;
    double std_dev() const;
    double max() const;
    double min() const;
    double range() const { return max() - min(); }

    // 重置
    void clear();

    // 当前窗口大小
    size_t size() const { return buffer_.size(); }

private:
    int window_size_;
    std::deque<double> buffer_;
};

// ============================================================================
// 滤波器工厂
// ============================================================================

/**
 * @brief 滤波器类型枚举
 */
enum class FilterType {
    BPF,        // 带通滤波器
    MEAN,       // 均值滤波器
    MEDIAN,     // 中值滤波器
    KALMAN,     // 卡尔曼滤波器
    BUTTERWORTH // 巴特沃斯滤波器
};

/**
 * @brief 创建滤波器实例
 */
std::unique_ptr<FilterBase> create_filter(FilterType type, double param1, double param2 = 0.0, double param3 = 0.0);

} // namespace filters
} // namespace param_id
