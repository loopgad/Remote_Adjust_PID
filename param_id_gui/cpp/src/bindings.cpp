// nanobind bindings for ODE solver
// This file exposes the C++ ODE solver to Python

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/function.h>
#include "ode_solver.cpp"

namespace nb = nanobind;
using namespace ode_solver;

NB_MODULE(_core, m) {
    m.doc() = "C++ accelerated ODE solver for high-precision simulation";

    // Expose RK4Solver class
    nb::class_<RK4Solver>(m, "RK4Solver")
        .def(nb::init<>())
        .def("solve", &RK4Solver::solve,
             "Solve ODE from t0 to t1 with initial condition y0",
             nb::arg("f"),
             nb::arg("t0"),
             nb::arg("t1"),
             nb::arg("y0"),
             nb::arg("dt"))
        .def("solve_final", &RK4Solver::solve_final,
             "Solve ODE and return only final state",
             nb::arg("f"),
             nb::arg("t0"),
             nb::arg("t1"),
             nb::arg("y0"),
             nb::arg("dt"));

    // Convenience function
    m.def("hello", []() { return "Hello from C++!"; },
          "Test function to verify C++ module is loaded");
}
