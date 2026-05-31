/**
 * @file bindings.cpp
 * @brief nanobind绑定层 - 将C++模块暴露给Python
 *
 * 绑定7层C++架构：
 * 1. math/ - 矩阵/向量运算
 * 2. filters/ - 信号滤波器
 * 3. solvers/ - ODE求解器
 * 4. models/ - 物理模型
 * 5. optim/ - 优化算法
 * 6. data/ - 信号处理
 * 7. (本文件) - Python接口
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/pair.h>

// 包含各层头文件
#include "../include/math/matrix.h"
#include "../include/filters/filters.h"
#include "../include/solvers/ode_solvers.h"
#include "../include/models/physics_models.h"
#include "../include/optim/optimizers.h"
#include "../include/data/signal_processing.h"

namespace nb = nanobind;
using namespace param_id;

NB_MODULE(_core, m) {
    m.doc() = "C++ accelerated core for parameter identification GUI\n"
              "Provides 7 layers: math, filters, solvers, models, optim, data, bindings";

    // ========================================================================
    // Layer 1: Math - 向量和矩阵运算
    // ========================================================================

    auto math_mod = m.def_submodule("math", "Math core - vectors and matrices");

    nb::class_<math::Vector>(math_mod, "Vector")
        .def(nb::init<>())
        .def("__init__", [](math::Vector* v, int n, double val) { new (v) math::Vector(static_cast<size_t>(n), val); }, nb::arg("n"), nb::arg("val") = 0.0)
        .def(nb::init<std::vector<double>>())
        .def("__getitem__", [](const math::Vector& v, size_t i) { return v[i]; })
        .def("__setitem__", [](math::Vector& v, size_t i, double val) { v[i] = val; })
        .def("__len__", &math::Vector::size)
        .def("size", &math::Vector::size)
        .def("norm", &math::Vector::norm)
        .def("norm_sq", &math::Vector::norm_sq)
        .def("sum", &math::Vector::sum)
        .def("mean", &math::Vector::mean)
        .def("dot", &math::Vector::dot)
        .def("to_std", [](const math::Vector& v) { return v.to_std(); })
        .def_static("zeros", &math::Vector::zeros)
        .def_static("ones", &math::Vector::ones)
        .def_static("linspace", &math::Vector::linspace)
        .def_static("range", &math::Vector::range)
        .def("__add__", &math::Vector::operator+)
        .def("__sub__", &math::Vector::operator-)
        .def("__mul__", &math::Vector::operator*)
        .def("__truediv__", &math::Vector::operator/);

    nb::class_<math::Matrix>(math_mod, "Matrix")
        .def(nb::init<size_t, size_t, double>(), nb::arg("rows"), nb::arg("cols"), nb::arg("val") = 0.0)
        .def("rows", &math::Matrix::rows)
        .def("cols", &math::Matrix::cols)
        .def("transpose", &math::Matrix::transpose)
        .def("determinant", &math::Matrix::determinant)
        .def("inverse", &math::Matrix::inverse)
        .def_static("identity", &math::Matrix::identity)
        .def_static("zeros", &math::Matrix::zeros)
        .def("__mul__", nb::overload_cast<const math::Matrix&>(&math::Matrix::operator*, nb::const_))
        .def("__mul__", nb::overload_cast<const math::Vector&>(&math::Matrix::operator*, nb::const_));

    math_mod.def("solve", &math::linalg::solve, "Solve Ax = b");
    math_mod.def("lstsq", &math::linalg::lstsq, "Least squares solve");

    // ========================================================================
    // Layer 2: Filters - 信号滤波器
    // ========================================================================

    auto filter_mod = m.def_submodule("filters", "Signal processing filters");

    nb::enum_<filters::FilterType>(filter_mod, "FilterType")
        .value("BPF", filters::FilterType::BPF)
        .value("MEAN", filters::FilterType::MEAN)
        .value("MEDIAN", filters::FilterType::MEDIAN)
        .value("KALMAN", filters::FilterType::KALMAN)
        .value("BUTTERWORTH", filters::FilterType::BUTTERWORTH);

    nb::class_<filters::FirstOrderBPF>(filter_mod, "FirstOrderBPF")
        .def(nb::init<double, double, double>(), nb::arg("fc"), nb::arg("bw"), nb::arg("fs"))
        .def("process", nb::overload_cast<double>(&filters::FirstOrderBPF::process))
        .def("process_array", [](filters::FirstOrderBPF& f, const std::vector<double>& v) {
            std::vector<double> result;
            result.reserve(v.size());
            for (double x : v) result.push_back(f.process(x));
            return result;
        })
        .def("reset", &filters::FirstOrderBPF::reset);

    nb::class_<filters::MeanFilter>(filter_mod, "MeanFilter")
        .def(nb::init<int>(), nb::arg("window_size"))
        .def("process", nb::overload_cast<double>(&filters::MeanFilter::process))
        .def("process_array", [](filters::MeanFilter& f, const std::vector<double>& v) { return f.process(v); })
        .def("reset", &filters::MeanFilter::reset);

    nb::class_<filters::MedianFilter>(filter_mod, "MedianFilter")
        .def(nb::init<int>(), nb::arg("window_size"))
        .def("process", nb::overload_cast<double>(&filters::MedianFilter::process))
        .def("process_array", [](filters::MedianFilter& f, const std::vector<double>& v) { return f.process(v); })
        .def("reset", &filters::MedianFilter::reset);

    nb::class_<filters::KalmanFilter>(filter_mod, "KalmanFilter")
        .def(nb::init<double, double, double, double>(),
             nb::arg("process_noise"), nb::arg("measurement_noise"),
             nb::arg("initial_estimate") = 0.0, nb::arg("initial_error") = 1.0)
        .def("process", nb::overload_cast<double>(&filters::KalmanFilter::process))
        .def("process_array", [](filters::KalmanFilter& f, const std::vector<double>& v) {
            std::vector<double> result;
            result.reserve(v.size());
            for (double x : v) result.push_back(f.process(x));
            return result;
        })
        .def("reset", &filters::KalmanFilter::reset)
        .def("estimate", &filters::KalmanFilter::estimate)
        .def("error_covariance", &filters::KalmanFilter::error_covariance)
        .def("kalman_gain", &filters::KalmanFilter::kalman_gain);

    nb::class_<filters::ButterworthFilter>(filter_mod, "ButterworthFilter")
        .def(nb::init<double, double, int>(), nb::arg("cutoff_freq"), nb::arg("fs"), nb::arg("order") = 2)
        .def("process", nb::overload_cast<double>(&filters::ButterworthFilter::process))
        .def("reset", &filters::ButterworthFilter::reset);

    nb::class_<filters::SlidingWindowFilter>(filter_mod, "SlidingWindowFilter")
        .def(nb::init<int>(), nb::arg("window_size"))
        .def("push", &filters::SlidingWindowFilter::push)
        .def("mean", &filters::SlidingWindowFilter::mean)
        .def("median", &filters::SlidingWindowFilter::median)
        .def("std_dev", &filters::SlidingWindowFilter::std_dev)
        .def("max", &filters::SlidingWindowFilter::max)
        .def("min", &filters::SlidingWindowFilter::min)
        .def("clear", &filters::SlidingWindowFilter::clear);

    filter_mod.def("create_filter", &filters::create_filter, "Create filter instance");

    // ========================================================================
    // Layer 3: Solvers - ODE求解器
    // ========================================================================

    auto solver_mod = m.def_submodule("solvers", "ODE solvers");

    nb::enum_<solvers::SolverType>(solver_mod, "SolverType")
        .value("RK4", solvers::SolverType::RK4)
        .value("RK45", solvers::SolverType::RK45)
        .value("RK23", solvers::SolverType::RK23)
        .value("IMPLICIT_EULER", solvers::SolverType::IMPLICIT_EULER);

    nb::class_<solvers::SolveResult>(solver_mod, "SolveResult")
        .def_ro("t", &solvers::SolveResult::t)
        .def_ro("y", &solvers::SolveResult::y)
        .def_ro("steps_taken", &solvers::SolveResult::steps_taken)
        .def_ro("converged", &solvers::SolveResult::converged);

    nb::class_<solvers::RK4Solver>(solver_mod, "RK4Solver")
        .def(nb::init<>())
        .def("solve", &solvers::RK4Solver::solve)
        .def("step", &solvers::RK4Solver::step);

    nb::class_<solvers::RK45Solver>(solver_mod, "RK45Solver")
        .def(nb::init<>())
        .def("solve", &solvers::RK45Solver::solve)
        .def("step", &solvers::RK45Solver::step);

    nb::class_<solvers::ImplicitEulerSolver>(solver_mod, "ImplicitEulerSolver")
        .def(nb::init<>())
        .def("solve", &solvers::ImplicitEulerSolver::solve)
        .def("step", &solvers::ImplicitEulerSolver::step);

    solver_mod.def("create_solver", nb::overload_cast<solvers::SolverType>(&solvers::create_solver));

    // ========================================================================
    // Layer 4: Models - 物理模型
    // ========================================================================

    auto model_mod = m.def_submodule("models", "Physics models");

    nb::class_<models::ModelOutput>(model_mod, "ModelOutput")
        .def_ro("states", &models::ModelOutput::states)
        .def_ro("outputs", &models::ModelOutput::outputs)
        .def_ro("power_loss", &models::ModelOutput::power_loss)
        .def_ro("efficiency", &models::ModelOutput::efficiency);

    // PMSM模型
    nb::class_<models::PMSMModel>(model_mod, "PMSMModel")
        .def(nb::init<>(), "Create PMSM model with default parameters")
        .def("step", &models::PMSMModel::step)
        .def("reset", &models::PMSMModel::reset)
        .def("get_state", &models::PMSMModel::get_state)
        .def("set_state", &models::PMSMModel::set_state)
        .def("calc_torque", &models::PMSMModel::calc_torque);

    // FOC控制器
    nb::class_<models::PIController>(model_mod, "PIController")
        .def(nb::init<>())
        .def("update", &models::PIController::update)
        .def("reset", &models::PIController::reset);

    nb::class_<models::FOCController>(model_mod, "FOCController")
        .def(nb::init<>())
        .def("step", &models::FOCController::step)
        .def("reset", &models::FOCController::reset)
        .def_static("clarke_transform", &models::FOCController::clarke_transform)
        .def_static("park_transform", &models::FOCController::park_transform)
        .def_static("inv_clarke_transform", &models::FOCController::inv_clarke_transform)
        .def_static("inv_park_transform", &models::FOCController::inv_park_transform)
        .def_static("svpwm", &models::FOCController::svpwm);

    // Buck变换器
    nb::class_<models::BuckConverter>(model_mod, "BuckConverter")
        .def(nb::init<>())
        .def("step", &models::BuckConverter::step)
        .def("reset", &models::BuckConverter::reset)
        .def("get_state", &models::BuckConverter::get_state);

    // Boost变换器
    nb::class_<models::BoostConverter>(model_mod, "BoostConverter")
        .def(nb::init<>())
        .def("step", &models::BoostConverter::step)
        .def("reset", &models::BoostConverter::reset)
        .def("get_state", &models::BoostConverter::get_state);

    // 电池模型
    nb::class_<models::BatteryModel>(model_mod, "BatteryModel")
        .def(nb::init<>())
        .def("step", &models::BatteryModel::step)
        .def("reset", &models::BatteryModel::reset)
        .def("get_state", &models::BatteryModel::get_state);

    // ========================================================================
    // Layer 5: Optimizers - 优化算法
    // ========================================================================

    auto optim_mod = m.def_submodule("optim", "Optimization algorithms");

    nb::enum_<optim::OptimizerType>(optim_mod, "OptimizerType")
        .value("LM", optim::OptimizerType::LM)
        .value("PSO", optim::OptimizerType::PSO)
        .value("SGD", optim::OptimizerType::SGD)
        .value("ADAM", optim::OptimizerType::ADAM);

    nb::class_<optim::OptResult>(optim_mod, "OptResult")
        .def_ro("best_params", &optim::OptResult::best_params)
        .def_ro("best_cost", &optim::OptResult::best_cost)
        .def_ro("iterations", &optim::OptResult::iterations)
        .def_ro("converged", &optim::OptResult::converged)
        .def_ro("cost_history", &optim::OptResult::cost_history);

    nb::class_<optim::LevenbergMarquardt>(optim_mod, "LevenbergMarquardt")
        .def(nb::init<>())
        .def("minimize", &optim::LevenbergMarquardt::minimize);

    nb::class_<optim::ParticleSwarmOptimization>(optim_mod, "ParticleSwarmOptimization")
        .def(nb::init<>())
        .def("minimize", &optim::ParticleSwarmOptimization::minimize);

    nb::class_<optim::GradientDescent>(optim_mod, "GradientDescent")
        .def(nb::init<>())
        .def("minimize", &optim::GradientDescent::minimize);

    optim_mod.def("create_optimizer", &optim::create_optimizer);

    // ========================================================================
    // Layer 6: Data - 信号处理
    // ========================================================================

    auto data_mod = m.def_submodule("data", "Signal processing and data analysis");

    nb::class_<data::SpectrumResult>(data_mod, "SpectrumResult")
        .def_ro("frequencies", &data::SpectrumResult::frequencies)
        .def_ro("magnitudes", &data::SpectrumResult::magnitudes)
        .def_ro("phases", &data::SpectrumResult::phases)
        .def_ro("psd", &data::SpectrumResult::psd)
        .def_ro("dominant_frequency", &data::SpectrumResult::dominant_frequency)
        .def_ro("thd", &data::SpectrumResult::thd);

    nb::class_<data::StatsResult>(data_mod, "StatsResult")
        .def_ro("mean", &data::StatsResult::mean)
        .def_ro("std_dev", &data::StatsResult::std_dev)
        .def_ro("min", &data::StatsResult::min)
        .def_ro("max", &data::StatsResult::max)
        .def_ro("rms", &data::StatsResult::rms);

    data_mod.def("fft", &data::FFT::fft, "Fast Fourier Transform");
    data_mod.def("ifft", &data::FFT::ifft, "Inverse FFT");
    data_mod.def("magnitude_spectrum", &data::FFT::magnitude_spectrum);
    data_mod.def("power_spectral_density", &data::FFT::power_spectral_density);

    data_mod.def("analyze_spectrum", &data::SpectrumAnalyzer::analyze);
    data_mod.def("calc_thd", &data::SpectrumAnalyzer::calc_thd);
    data_mod.def("calc_snr", &data::SpectrumAnalyzer::calc_snr);

    data_mod.def("statistics", &data::Statistics::analyze);
    data_mod.def("correlation", &data::Statistics::correlation);

    data_mod.def("standardize", &data::DataPreprocessor::standardize);
    data_mod.def("normalize", &data::DataPreprocessor::normalize);
    data_mod.def("detrend", &data::DataPreprocessor::detrend);
    data_mod.def("resample", &data::DataPreprocessor::resample);

    // ========================================================================
    // 便利函数
    // ========================================================================

    m.def("hello", []() { return "Hello from C++ accelerated core!"; },
          "Test function to verify C++ module is loaded");

    m.def("version", []() { return "2.0.0"; },
          "Get C++ core version");
}
