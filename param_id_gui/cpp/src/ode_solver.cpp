// ODE Solver implementation in C++
// This file implements a Runge-Kutta 4th order ODE solver

#include <vector>
#include <functional>
#include <stdexcept>

namespace ode_solver {

// Type alias for ODE function: dy/dt = f(t, y)
using ODEFunction = std::function<std::vector<double>(double, const std::vector<double>&)>;

// Runge-Kutta 4th order solver
class RK4Solver {
public:
    RK4Solver() = default;
    ~RK4Solver() = default;

    // Solve ODE from t0 to t1 with initial condition y0
    std::vector<std::vector<double>> solve(
        const ODEFunction& f,
        double t0,
        double t1,
        const std::vector<double>& y0,
        double dt
    ) {
        if (dt <= 0) {
            throw std::invalid_argument("Time step must be positive");
        }

        if (t1 <= t0) {
            throw std::invalid_argument("End time must be after start time");
        }

        std::vector<std::vector<double>> result;
        result.push_back(y0);

        double t = t0;
        std::vector<double> y = y0;

        while (t < t1) {
            // Adjust last step if needed
            double current_dt = dt;
            if (t + dt > t1) {
                current_dt = t1 - t;
            }

            // RK4 steps
            std::vector<double> k1 = f(t, y);
            
            std::vector<double> y_temp(y.size());
            for (size_t i = 0; i < y.size(); ++i) {
                y_temp[i] = y[i] + 0.5 * current_dt * k1[i];
            }
            std::vector<double> k2 = f(t + 0.5 * current_dt, y_temp);

            for (size_t i = 0; i < y.size(); ++i) {
                y_temp[i] = y[i] + 0.5 * current_dt * k2[i];
            }
            std::vector<double> k3 = f(t + 0.5 * current_dt, y_temp);

            for (size_t i = 0; i < y.size(); ++i) {
                y_temp[i] = y[i] + current_dt * k3[i];
            }
            std::vector<double> k4 = f(t + current_dt, y_temp);

            // Update state
            for (size_t i = 0; i < y.size(); ++i) {
                y[i] += (current_dt / 6.0) * (k1[i] + 2.0*k2[i] + 2.0*k3[i] + k4[i]);
            }

            t += current_dt;
            result.push_back(y);
        }

        return result;
    }

    // Solve ODE and return only final state
    std::vector<double> solve_final(
        const ODEFunction& f,
        double t0,
        double t1,
        const std::vector<double>& y0,
        double dt
    ) {
        auto result = solve(f, t0, t1, y0, dt);
        return result.back();
    }
};

} // namespace ode_solver
