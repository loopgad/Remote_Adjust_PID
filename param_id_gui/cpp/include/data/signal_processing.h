#pragma once
/**
 * @file signal_processing.h
 * @brief 数据处理层 - 信号分析与处理
 *
 * 提供信号处理功能：
 * - FFT/IFFT
 * - 功率谱密度
 * - 频谱分析
 * - 数据插值
 * - 统计分析
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <complex>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace param_id {
namespace data {

// ============================================================================
// 类型定义
// ============================================================================

using Complex = std::complex<double>;
using ComplexVector = std::vector<Complex>;

// ============================================================================
// FFT变换
// ============================================================================

/**
 * @brief 快速傅里叶变换 (FFT)
 *
 * 实现Cooley-Tukey基2 FFT算法。
 * 输入长度必须为2的幂。
 */
class FFT {
public:
    /**
     * @brief 执行FFT
     * @param input 输入信号（实数）
     * @return 频域表示（复数）
     */
    static ComplexVector fft(const std::vector<double>& input);

    /**
     * @brief 执行逆FFT
     * @param input 频域信号（复数）
     * @return 时域信号（实数）
     */
    static std::vector<double> ifft(const ComplexVector& input);

    /**
     * @brief 计算幅度谱
     * @param input 输入信号
     * @return 幅度谱
     */
    static std::vector<double> magnitude_spectrum(const std::vector<double>& input);

    /**
     * @brief 计算功率谱密度
     * @param input 输入信号
     * @param fs 采样频率
     * @return PSD (dB/Hz)
     */
    static std::vector<double> power_spectral_density(const std::vector<double>& input, double fs);

    /**
     * @brief 计算频率轴
     * @param n 信号长度
     * @param fs 采样频率
     * @return 频率数组
     */
    static std::vector<double> freq_axis(size_t n, double fs);

private:
    /**
     * @brief 递归FFT实现
     */
    static ComplexVector fft_recursive(const ComplexVector& x);

    /**
     * @brief 补齐到2的幂
     */
    static size_t next_power_of_2(size_t n);
};

// ============================================================================
// 频谱分析
// ============================================================================

/**
 * @brief 频谱分析结果
 */
struct SpectrumResult {
    std::vector<double> frequencies;   // 频率轴 (Hz)
    std::vector<double> magnitudes;    // 幅度谱
    std::vector<double> phases;        // 相位谱 (rad)
    std::vector<double> psd;           // 功率谱密度 (dB/Hz)
    double dominant_frequency = 0.0;   // 主频率 (Hz)
    double thd = 0.0;                  // 总谐波失真 (%)
};

/**
 * @brief 频谱分析器
 */
class SpectrumAnalyzer {
public:
    /**
     * @brief 分析信号频谱
     * @param signal 输入信号
     * @param fs 采样频率
     * @return 频谱分析结果
     */
    static SpectrumResult analyze(const std::vector<double>& signal, double fs);

    /**
     * @brief 计算THD (总谐波失真)
     * @param signal 输入信号
     * @param fs 采样频率
     * @param fundamental 基波频率
     * @return THD (%)
     */
    static double calc_thd(const std::vector<double>& signal, double fs, double fundamental);

    /**
     * @brief 计算SNR (信噪比)
     * @param signal 信号
     * @param noise 噪声
     * @return SNR (dB)
     */
    static double calc_snr(const std::vector<double>& signal, const std::vector<double>& noise);
};

// ============================================================================
// 数据插值
// ============================================================================

/**
 * @brief 插值方法
 */
enum class InterpMethod {
    LINEAR,     // 线性插值
    CUBIC,      // 三次插值
    SPLINE      // 三次样条插值
};

/**
 * @brief 数据插值器
 */
class Interpolator {
public:
    /**
     * @brief 构造插值器
     * @param x 已知数据点的x坐标（必须单调递增）
     * @param y 已知数据点的y坐标
     * @param method 插值方法
     */
    Interpolator(const std::vector<double>& x, const std::vector<double>& y,
                 InterpMethod method = InterpMethod::LINEAR);

    /**
     * @brief 计算插值
     * @param xi 查询点
     * @return 插值结果
     */
    double interpolate(double xi) const;

    /**
     * @brief 批量插值
     * @param xi 查询点数组
     * @return 插值结果数组
     */
    std::vector<double> interpolate(const std::vector<double>& xi) const;

private:
    std::vector<double> x_, y_;
    InterpMethod method_;
    std::vector<double> h_, a_, b_, c_, d_;  // 样条系数

    void compute_spline_coefficients();
    double cubic_spline(double xi) const;
};

// ============================================================================
// 统计分析
// ============================================================================

/**
 * @brief 统计分析结果
 */
struct StatsResult {
    double mean = 0.0;       // 均值
    double median = 0.0;     // 中位数
    double std_dev = 0.0;    // 标准差
    double variance = 0.0;   // 方差
    double min = 0.0;        // 最小值
    double max = 0.0;        // 最大值
    double range = 0.0;      // 范围
    double skewness = 0.0;   // 偏度
    double kurtosis = 0.0;   // 峰度
    double rms = 0.0;        // 均方根
    double crest_factor = 0.0; // 峰值因子
};

/**
 * @brief 统计分析器
 */
class Statistics {
public:
    /**
     * @brief 计算统计量
     */
    static StatsResult analyze(const std::vector<double>& data);

    /**
     * @brief 计算均值
     */
    static double mean(const std::vector<double>& data);

    /**
     * @brief 计算标准差
     */
    static double std_dev(const std::vector<double>& data);

    /**
     * @brief 计算RMS
     */
    static double rms(const std::vector<double>& data);

    /**
     * @brief 计算相关系数
     */
    static double correlation(const std::vector<double>& x, const std::vector<double>& y);

    /**
     * @brief 计算协方差
     */
    static double covariance(const std::vector<double>& x, const std::vector<double>& y);

    /**
     * @brief 直方图
     * @param data 输入数据
     * @param bins 分箱数
     * @return (bin_edges, counts)
     */
    static std::pair<std::vector<double>, std::vector<int>> histogram(
        const std::vector<double>& data, int bins = 10);
};

// ============================================================================
// 数据预处理
// ============================================================================

/**
 * @brief 数据预处理工具
 */
class DataPreprocessor {
public:
    /**
     * @brief 标准化 (z-score)
     */
    static std::vector<double> standardize(const std::vector<double>& data);

    /**
     * @brief 归一化 (min-max)
     */
    static std::vector<double> normalize(const std::vector<double>& data,
                                         double min_val = 0.0, double max_val = 1.0);

    /**
     * @brief 去趋势
     */
    static std::vector<double> detrend(const std::vector<double>& data);

    /**
     * @brief 重采样
     * @param data 原始数据
     * @param original_fs 原始采样率
     * @param target_fs 目标采样率
     * @return 重采样后的数据
     */
    static std::vector<double> resample(const std::vector<double>& data,
                                        double original_fs, double target_fs);
};

} // namespace data
} // namespace param_id
