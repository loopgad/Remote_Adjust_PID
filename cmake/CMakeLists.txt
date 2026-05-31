cmake_minimum_required(VERSION 3.15...3.27)

# Detect if we are being called from scikit-build-core
if(SKBUILD)
  # Scikit-build-core sets SKBUILD=1
  message(STATUS "Building with scikit-build-core")
endif()

# Find Python
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

# Find nanobind
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE
  OUTPUT_VARIABLE nanobind_DIR
)
find_package(nanobind CONFIG REQUIRED)

# Add the ODE solver library
nanobind_add_module(
  _core
  STABLE_ABI
  ../param_id_gui/cpp/src/bindings.cpp
  ../param_id_gui/cpp/src/ode_solver.cpp
)

# Install the module
install(
  TARGETS _core
  DESTINATION param_id_gui
)
