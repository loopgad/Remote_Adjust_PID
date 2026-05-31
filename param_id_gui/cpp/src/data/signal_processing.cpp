/**
 * @file signal_processing.cpp
 * @brief 数据处理层实现
 */

#include "../../include/data/signal_processing.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace param_id {
namespace data {

// ============================================================================
// FFT实现
// ============================================================================

ComplexVector FFT::fft(const std::vector<double>& input) {
    size_t n = next_power_of_2(input.size());
    ComplexVector x(n);
    for (size_t i = 0; i < input.size(); ++i) x[i] = input[i];
    for (size_t i = input.size(); i < n; ++i) x[i] = 0.0;
    return fft_recursive(x);
}

std::vector<double> FFT::ifft(const ComplexVector& input) {
    size_t n = input.size();
    ComplexVector x(n);
    for (size_t i = 0; i < n; ++i) x[i] = std::conj(input[i]);
    x = fft_recursive(x);
    std::vector<double> result(n);
    for (size_t i = 0; i < n; ++i) result[i] = x[i].real() / n;
    return result;
}

std::vector<double> FFT::magnitude_spectrum(const std::vector<double>& input) {
    auto spectrum = fft(input);
    size_t n = spectrum.size();
    std::vector<double> magnitude(n / 2);
    for (size_t i = 0; i < n / 2; ++i) {
        magnitude[i] = std::abs(spectrum[i]) / n;
    }
    return magnitude;
}

std::vector<double> FFT::power_spectral_density(const std::vector<double>& input, double fs) {
    auto magnitude = magnitude_spectrum(input);
    size_t n = magnitude.size();
    std::vector<double> psd(n);
    for (size_t i = 0; i < n; ++i) {
        double power = magnitude[i] * magnitude[i];
        psd[i] = 10.0 * std::log10(power + 1e-20);  // dB
    }
    return psd;
}

std::vector<double> FFT::freq_axis(size_t n, double fs) {
    std::vector<double> freqs(n / 2);
    for (size_t i = 0; i < n / 2; ++i) {
        freqs[i] = i * fs / n;
    }
    return freqs;
}

ComplexVector FFT::fft_recursive(const ComplexVector& x) {
    size_t n = x.size();
    if (n <= 1) return x;

    // 分治
    ComplexVector even(n / 2), odd(n / 2);
    for (size_t i = 0; i < n / 2; ++i) {
        even[i] = x[2 * i];
        odd[i] = x[2 * i + 1];
    }

    ComplexVector fft_even = fft_recursive(even);
    ComplexVector fft_odd = fft_recursive(odd);

    ComplexVector result(n);
    for (size_t k = 0; k < n / 2; ++k) {
        Complex w = std::polar(1.0, -2.0 * M_PI * k / n);
        result[k] = fft_even[k] + w * fft_odd[k];
        result[k + n / 2] = fft_even[k] - w * fft_odd[k];
    }
    return result;
}

size_t FFT::next_power_of_2(size_t n) {
    size_t power = 1;
    while (power < n) power <<= 1;
    return power;
}

// ============================================================================
// SpectrumAnalyzer实现
// ============================================================================

SpectrumResult SpectrumAnalyzer::analyze(const std::vector<double>& signal, double fs) {
    SpectrumResult result;

    // FFT
    auto spectrum = FFT::fft(signal);
    size_t n = spectrum.size();

    // 频率轴
    result.frequencies = FFT::freq_axis(n, fs);

    // 幅度谱和相位谱
    result.magnitudes.resize(n / 2);
    result.phases.resize(n / 2);
    for (size_t i = 0; i < n / 2; ++i) {
        result.magnitudes[i] = 2.0 * std::abs(spectrum[i]) / n;
        result.phases[i] = std::arg(spectrum[i]);
    }

    // 功率谱密度
    result.psd = FFT::power_spectral_density(signal, fs);

    // 主频率
    auto max_it = std::max_element(result.magnitudes.begin() + 1, result.magnitudes.end());
    size_t max_idx = std::distance(result.magnitudes.begin(), max_it);
    result.dominant_frequency = result.frequencies[max_idx];

    // THD
    result.thd = calc_thd(signal, fs, result.dominant_frequency);

    return result;
}

double SpectrumAnalyzer::calc_thd(const std::vector<double>& signal, double fs, double fundamental) {
    auto spectrum = FFT::fft(signal);
    size_t n = spectrum.size();

    // 找到基波位置
    int fund_idx = static_cast<int>(fundamental * n / fs);
    if (fund_idx <= 0 || fund_idx >= n / 2) return 0.0;

    double fund_amp = std::abs(spectrum[fund_idx]);
    if (fund_amp < 1e-10) return 0.0;

    // 计算谐波
    double harmonic_power = 0.0;
    for (int h = 2; h * fund_idx < n / 2; ++h) {
        double amp = std::abs(spectrum[h * fund_idx]);
        harmonic_power += amp * amp;
    }

    return 100.0 * std::sqrt(harmonic_power) / fund_amp;
}

double SpectrumAnalyzer::calc_snr(const std::vector<double>& signal, const std::vector<double>& noise) {
    if (signal.size() != noise.size()) throw std::invalid_argument("Size mismatch");

    double signal_power = 0.0, noise_power = 0.0;
    for (size_t i = 0; i < signal.size(); ++i) {
        signal_power += signal[i] * signal[i];
        noise_power += noise[i] * noise[i];
    }

    if (noise_power < 1e-20) return 100.0;  // 无噪声
    return 10.0 * std::log10(signal_power / noise_power);
}

// ============================================================================
// Interpolator实现
// ============================================================================

Interpolator::Interpolator(const std::vector<double>& x, const std::vector<double>& y,
                           InterpMethod method)
    : x_(x), y_(y), method_(method) {
    if (x.size() != y.size()) throw std::invalid_argument("Size mismatch");
    if (x.size() < 2) throw std::invalid_argument("Need at least 2 points");

    // 检查单调性
    for (size_t i = 1; i < x.size(); ++i) {
        if (x[i] <= x[i-1]) throw std::invalid_argument("x must be monotonically increasing");
    }

    if (method == InterpMethod::SPLINE) {
        compute_spline_coefficients();
    }
}

double Interpolator::interpolate(double xi) const {
    if (xi < x_.front() || xi > x_.back()) {
        throw std::out_of_range("Interpolation point out of range");
    }

    // 找到区间
    auto it = std::lower_bound(x_.begin(), x_.end(), xi);
    size_t idx = std::distance(x_.begin(), it);
    if (idx > 0) idx--;

    switch (method_) {
        case InterpMethod::LINEAR: {
            double t = (xi - x_[idx]) / (x_[idx + 1] - x_[idx]);
            return y_[idx] + t * (y_[idx + 1] - y_[idx]);
        }
        case InterpMethod::CUBIC: {
            // 简化的三次插值
            double t = (xi - x_[idx]) / (x_[idx + 1] - x_[idx]);
            double t2 = t * t, t3 = t2 * t;
            return (2*t3 - 3*t2 + 1) * y_[idx] + (t3 - 2*t2 + t) * (y_[idx+1] - y_[idx]) * (x_[idx+1] - x_[idx])
                 + (-2*t3 + 3*t2) * y_[idx+1] + (t3 - t2) * (y_[idx+1] - y_[idx]) * (x_[idx+1] - x_[idx]);
        }
        case InterpMethod::SPLINE:
            return cubic_spline(xi);
        default:
            throw std::invalid_argument("Unknown interpolation method");
    }
}

std::vector<double> Interpolator::interpolate(const std::vector<double>& xi) const {
    std::vector<double> result(xi.size());
    for (size_t i = 0; i < xi.size(); ++i) {
        result[i] = interpolate(xi[i]);
    }
    return result;
}

void Interpolator::compute_spline_coefficients() {
    size_t n = x_.size() - 1;
    h_.resize(n);
    a_ = y_;
    b_.resize(n);
    c_.resize(n + 1);
    d_.resize(n);

    for (size_t i = 0; i < n; ++i) h_[i] = x_[i + 1] - x_[i];

    // Thomas算法求解三对角方程组
    std::vector<double> alpha(n);
    for (size_t i = 1; i < n; ++i) {
        alpha[i] = 3.0 / h_[i] * (a_[i + 1] - a_[i]) - 3.0 / h_[i - 1] * (a_[i] - a_[i - 1]);
    }

    std::vector<double> l(n + 1), mu(n + 1), z(n + 1);
    l[0] = 1.0;
    for (size_t i = 1; i < n; ++i) {
        l[i] = 2.0 * (x_[i + 1] - x_[i - 1]) - h_[i - 1] * mu[i - 1];
        mu[i] = h_[i] / l[i];
        z[i] = (alpha[i] - h_[i - 1] * z[i - 1]) / l[i];
    }
    l[n] = 1.0;

    for (size_t j = n - 1; j > 0; --j) {
        c_[j] = z[j] - mu[j] * c_[j + 1];
        b_[j] = (a_[j + 1] - a_[j]) / h_[j] - h_[j] * (c_[j + 1] + 2.0 * c_[j]) / 3.0;
        d_[j] = (c_[j + 1] - c_[j]) / (3.0 * h_[j]);
    }
}

double Interpolator::cubic_spline(double xi) const {
    size_t n = x_.size() - 1;
    size_t idx = 0;
    for (size_t i = 0; i < n; ++i) {
        if (xi >= x_[i] && xi <= x_[i + 1]) {
            idx = i;
            break;
        }
    }

    double dx = xi - x_[idx];
    return a_[idx] + b_[idx] * dx + c_[idx] * dx * dx + d_[idx] * dx * dx * dx;
}

// ============================================================================
// Statistics实现
// ============================================================================

StatsResult Statistics::analyze(const std::vector<double>& data) {
    StatsResult result;
    if (data.empty()) return result;

    result.mean = mean(data);
    result.variance = 0.0;
    for (double v : data) result.variance += (v - result.mean) * (v - result.mean);
    result.variance /= data.size();
    result.std_dev = std::sqrt(result.variance);

    auto minmax = std::minmax_element(data.begin(), data.end());
    result.min = *minmax.first;
    result.max = *minmax.second;
    result.range = result.max - result.min;

    result.rms = rms(data);
    result.crest_factor = (result.rms > 0) ? result.max / result.rms : 0.0;

    // 偏度和峰度
    double skew = 0.0, kurt = 0.0;
    for (double v : data) {
        double z = (v - result.mean) / (result.std_dev + 1e-10);
        skew += z * z * z;
        kurt += z * z * z * z;
    }
    result.skewness = skew / data.size();
    result.kurtosis = kurt / data.size() - 3.0;

    // 中位数
    std::vector<double> sorted = data;
    std::sort(sorted.begin(), sorted.end());
    result.median = (sorted.size() % 2 == 0) ?
        (sorted[sorted.size()/2 - 1] + sorted[sorted.size()/2]) / 2.0 :
        sorted[sorted.size()/2];

    return result;
}

double Statistics::mean(const std::vector<double>& data) {
    if (data.empty()) return 0.0;
    return std::accumulate(data.begin(), data.end(), 0.0) / data.size();
}

double Statistics::std_dev(const std::vector<double>& data) {
    if (data.size() < 2) return 0.0;
    double m = mean(data);
    double sum_sq = 0.0;
    for (double v : data) sum_sq += (v - m) * (v - m);
    return std::sqrt(sum_sq / (data.size() - 1));
}

double Statistics::rms(const std::vector<double>& data) {
    if (data.empty()) return 0.0;
    double sum_sq = 0.0;
    for (double v : data) sum_sq += v * v;
    return std::sqrt(sum_sq / data.size());
}

double Statistics::correlation(const std::vector<double>& x, const std::vector<double>& y) {
    if (x.size() != y.size()) throw std::invalid_argument("Size mismatch");
    double mx = mean(x), my = mean(y);
    double cov = 0.0, sx = 0.0, sy = 0.0;
    for (size_t i = 0; i < x.size(); ++i) {
        cov += (x[i] - mx) * (y[i] - my);
        sx += (x[i] - mx) * (x[i] - mx);
        sy += (y[i] - my) * (y[i] - my);
    }
    return cov / (std::sqrt(sx * sy) + 1e-10);
}

double Statistics::covariance(const std::vector<double>& x, const std::vector<double>& y) {
    if (x.size() != y.size()) throw std::invalid_argument("Size mismatch");
    double mx = mean(x), my = mean(y);
    double cov = 0.0;
    for (size_t i = 0; i < x.size(); ++i) {
        cov += (x[i] - mx) * (y[i] - my);
    }
    return cov / x.size();
}

std::pair<std::vector<double>, std::vector<int>> Statistics::histogram(
    const std::vector<double>& data, int bins) {
    auto minmax = std::minmax_element(data.begin(), data.end());
    double min_val = *minmax.first, max_val = *minmax.second;
    double bin_width = (max_val - min_val) / bins;

    std::vector<double> edges(bins + 1);
    for (int i = 0; i <= bins; ++i) edges[i] = min_val + i * bin_width;

    std::vector<int> counts(bins, 0);
    for (double v : data) {
        int bin = std::min(static_cast<int>((v - min_val) / bin_width), bins - 1);
        counts[bin]++;
    }

    return {edges, counts};
}

// ============================================================================
// DataPreprocessor实现
// ============================================================================

std::vector<double> DataPreprocessor::standardize(const std::vector<double>& data) {
    double m = Statistics::mean(data);
    double s = Statistics::std_dev(data);
    std::vector<double> result(data.size());
    for (size_t i = 0; i < data.size(); ++i) {
        result[i] = (data[i] - m) / (s + 1e-10);
    }
    return result;
}

std::vector<double> DataPreprocessor::normalize(const std::vector<double>& data,
                                                 double min_val, double max_val) {
    auto minmax = std::minmax_element(data.begin(), data.end());
    double d_min = *minmax.first, d_max = *minmax.second;
    double scale = (max_val - min_val) / (d_max - d_min + 1e-10);

    std::vector<double> result(data.size());
    for (size_t i = 0; i < data.size(); ++i) {
        result[i] = min_val + (data[i] - d_min) * scale;
    }
    return result;
}

std::vector<double> DataPreprocessor::detrend(const std::vector<double>& data) {
    size_t n = data.size();
    double x_mean = (n - 1) / 2.0;
    double y_mean = Statistics::mean(data);

    double num = 0.0, den = 0.0;
    for (size_t i = 0; i < n; ++i) {
        num += (i - x_mean) * (data[i] - y_mean);
        den += (i - x_mean) * (i - x_mean);
    }
    double slope = num / (den + 1e-10);
    double intercept = y_mean - slope * x_mean;

    std::vector<double> result(n);
    for (size_t i = 0; i < n; ++i) {
        result[i] = data[i] - (slope * i + intercept);
    }
    return result;
}

std::vector<double> DataPreprocessor::resample(const std::vector<double>& data,
                                                double original_fs, double target_fs) {
    if (original_fs <= 0 || target_fs <= 0) throw std::invalid_argument("Invalid sample rate");

    double ratio = target_fs / original_fs;
    size_t new_size = static_cast<size_t>(data.size() * ratio);
    std::vector<double> result(new_size);

    for (size_t i = 0; i < new_size; ++i) {
        double src_idx = i / ratio;
        size_t idx = static_cast<size_t>(src_idx);
        double frac = src_idx - idx;

        if (idx + 1 < data.size()) {
            result[i] = data[idx] * (1.0 - frac) + data[idx + 1] * frac;
        } else {
            result[i] = data.back();
        }
    }

    return result;
}

} // namespace data
} // namespace param_id
