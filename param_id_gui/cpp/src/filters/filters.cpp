/**
 * @file filters.cpp
 * @brief 滤波器层实现
 */

#include "../../include/filters/filters.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace param_id {
namespace filters {

// ============================================================================
// FilterBase实现
// ============================================================================

std::vector<double> FilterBase::process(const std::vector<double>& input) {
    std::vector<double> output(input.size());
    for (size_t i = 0; i < input.size(); ++i) {
        output[i] = process(input[i]);
    }
    return output;
}

// ============================================================================
// FirstOrderBPF实现 (从 filter 项目提取)
// ============================================================================

FirstOrderBPF::FirstOrderBPF(double fc, double bw, double fs)
    : fc_(fc), bw_(bw), fs_(fs) {
    if (fs <= 0 || fc <= 0 || bw <= 0) {
        throw std::invalid_argument("Invalid filter parameters");
    }
    calculate_coefficients();
}

void FirstOrderBPF::calculate_coefficients() {
    double Wn = 2.0 * M_PI * (fc_ - bw_ / 2.0) / fs_;
    double Wd = 2.0 * M_PI * (fc_ + bw_ / 2.0) / fs_;
    a0_ = Wn / (Wn + 1.0);
    a1_ = 1.0 / (1.0 + Wd);
}

double FirstOrderBPF::process(double input) {
    double output1 = a0_ * input + (1.0 - a0_) * last_input_;
    double output2 = a1_ * (input - last_input_) + a1_ * last_output_;
    double feedback = -output1 + output2;
    last_output_ = feedback;
    last_input_ = input;
    return feedback;
}

void FirstOrderBPF::reset() {
    last_input_ = 0.0;
    last_output_ = 0.0;
}

// ============================================================================
// MeanFilter实现 (从 filter 项目提取)
// ============================================================================

MeanFilter::MeanFilter(int window_size) : window_size_(window_size) {
    if (window_size <= 0) throw std::invalid_argument("Window size must be positive");
}

double MeanFilter::process(double input) {
    buffer_.push_back(input);
    sum_ += input;
    if (buffer_.size() > static_cast<size_t>(window_size_)) {
        sum_ -= buffer_.front();
        buffer_.pop_front();
    }
    return sum_ / buffer_.size();
}

std::vector<double> MeanFilter::process(const std::vector<double>& input) {
    reset();
    std::vector<double> output(input.size());
    for (size_t i = 0; i < input.size(); ++i) {
        output[i] = process(input[i]);
    }
    return output;
}

void MeanFilter::reset() {
    buffer_.clear();
    sum_ = 0.0;
}

// ============================================================================
// MedianFilter实现 (从 filter 项目提取)
// ============================================================================

MedianFilter::MedianFilter(int window_size) : window_size_(window_size) {
    if (window_size <= 0) throw std::invalid_argument("Window size must be positive");
    if (window_size % 2 == 0) window_size_++; // 确保奇数
}

double MedianFilter::process(double input) {
    buffer_.push_back(input);
    if (buffer_.size() > static_cast<size_t>(window_size_)) {
        buffer_.pop_front();
    }
    // 复制并排序
    std::vector<double> sorted(buffer_.begin(), buffer_.end());
    std::sort(sorted.begin(), sorted.end());
    return sorted[sorted.size() / 2];
}

std::vector<double> MedianFilter::process(const std::vector<double>& input) {
    reset();
    std::vector<double> output(input.size());
    for (size_t i = 0; i < input.size(); ++i) {
        output[i] = process(input[i]);
    }
    return output;
}

void MedianFilter::reset() {
    buffer_.clear();
}

// ============================================================================
// KalmanFilter实现 (从 filter 项目提取)
// ============================================================================

KalmanFilter::KalmanFilter(double process_noise, double measurement_noise,
                           double initial_estimate, double initial_error)
    : process_noise_(process_noise), measurement_noise_(measurement_noise),
      estimate_(initial_estimate), error_covariance_(initial_error) {}

double KalmanFilter::process(double input) {
    predict();
    update(input);
    return estimate_;
}

void KalmanFilter::reset() {
    estimate_ = 0.0;
    error_covariance_ = 1.0;
    kalman_gain_ = 0.0;
}

void KalmanFilter::predict() {
    // 状态预测: x_pred = x_est (假设状态转移矩阵为单位阵)
    // 误差协方差预测: P_pred = P + Q
    error_covariance_ += process_noise_;
}

void KalmanFilter::update(double measurement) {
    // 卡尔曼增益: K = P_pred / (P_pred + R)
    kalman_gain_ = error_covariance_ / (error_covariance_ + measurement_noise_);
    // 状态更新: x_est = x_pred + K * (z - x_pred)
    estimate_ += kalman_gain_ * (measurement - estimate_);
    // 误差协方差更新: P = (1 - K) * P_pred
    error_covariance_ *= (1.0 - kalman_gain_);
}

// ============================================================================
// ButterworthFilter实现
// ============================================================================

ButterworthFilter::ButterworthFilter(double cutoff_freq, double fs, int order)
    : cutoff_freq_(cutoff_freq), fs_(fs), order_(order) {
    if (cutoff_freq <= 0 || fs <= 0) {
        throw std::invalid_argument("Invalid filter parameters");
    }
    if (order < 1 || order > 4) {
        throw std::invalid_argument("Order must be 1-4");
    }
    calculate_coefficients();
}

void ButterworthFilter::calculate_coefficients() {
    // 双线性变换设计二阶Butterworth低通滤波器
    double fc = cutoff_freq_ / fs_;
    double wc = std::tan(M_PI * fc);
    double wc2 = wc * wc;
    double sqrt2 = std::sqrt(2.0);
    double denom = 1.0 + sqrt2 * wc + wc2;

    b0_ = wc2 / denom;
    b1_ = 2.0 * b0_;
    b2_ = b0_;
    a1_ = 2.0 * (wc2 - 1.0) / denom;
    a2_ = (1.0 - sqrt2 * wc + wc2) / denom;
}

double ButterworthFilter::process(double input) {
    // Direct Form I实现
    double output = b0_ * input + b1_ * x1_ + b2_ * x2_ - a1_ * y1_ - a2_ * y2_;

    // 更新状态
    x2_ = x1_;
    x1_ = input;
    y2_ = y1_;
    y1_ = output;

    return output;
}

void ButterworthFilter::reset() {
    x1_ = x2_ = 0.0;
    y1_ = y2_ = 0.0;
}

// ============================================================================
// SlidingWindowFilter实现
// ============================================================================

SlidingWindowFilter::SlidingWindowFilter(int window_size) : window_size_(window_size) {
    if (window_size <= 0) throw std::invalid_argument("Window size must be positive");
}

void SlidingWindowFilter::push(double value) {
    buffer_.push_back(value);
    if (buffer_.size() > static_cast<size_t>(window_size_)) {
        buffer_.pop_front();
    }
}

double SlidingWindowFilter::mean() const {
    if (buffer_.empty()) return 0.0;
    double sum = std::accumulate(buffer_.begin(), buffer_.end(), 0.0);
    return sum / buffer_.size();
}

double SlidingWindowFilter::median() const {
    if (buffer_.empty()) return 0.0;
    std::vector<double> sorted(buffer_.begin(), buffer_.end());
    std::sort(sorted.begin(), sorted.end());
    return sorted[sorted.size() / 2];
}

double SlidingWindowFilter::std_dev() const {
    if (buffer_.size() < 2) return 0.0;
    double m = mean();
    double sum_sq = 0.0;
    for (double v : buffer_) sum_sq += (v - m) * (v - m);
    return std::sqrt(sum_sq / (buffer_.size() - 1));
}

double SlidingWindowFilter::max() const {
    if (buffer_.empty()) return 0.0;
    return *std::max_element(buffer_.begin(), buffer_.end());
}

double SlidingWindowFilter::min() const {
    if (buffer_.empty()) return 0.0;
    return *std::min_element(buffer_.begin(), buffer_.end());
}

void SlidingWindowFilter::clear() {
    buffer_.clear();
}

// ============================================================================
// 工厂方法
// ============================================================================

std::unique_ptr<FilterBase> create_filter(FilterType type, double param1, double param2, double param3) {
    switch (type) {
        case FilterType::BPF:
            return std::make_unique<FirstOrderBPF>(param1, param2, param3);
        case FilterType::MEAN:
            return std::make_unique<MeanFilter>(static_cast<int>(param1));
        case FilterType::MEDIAN:
            return std::make_unique<MedianFilter>(static_cast<int>(param1));
        case FilterType::KALMAN:
            return std::make_unique<KalmanFilter>(param1, param2);
        case FilterType::BUTTERWORTH:
            return std::make_unique<ButterworthFilter>(param1, param2, static_cast<int>(param3));
        default:
            throw std::invalid_argument("Unknown filter type");
    }
}

} // namespace filters
} // namespace param_id
