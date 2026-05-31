cmake_minimum_required(VERSION 3.15...3.27)

# Detect if we are being called from scikit-build-core
if(SKBUILD)
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

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fix MSVC C4819 encoding warning (non-ASCII characters in source files)
# This is the root cause of 100+ cascading compilation errors
if(MSVC)
  add_compile_options(/utf-8)
endif()

# Source files - 7-layer architecture
set(SOURCES
  # Layer 1: Math core
  ../param_id_gui/cpp/src/math/matrix.cpp

  # Layer 2: Filters
  ../param_id_gui/cpp/src/filters/filters.cpp

  # Layer 3: ODE solvers
  ../param_id_gui/cpp/src/solvers/ode_solvers.cpp

  # Layer 4: Physics models
  ../param_id_gui/cpp/src/models/physics_models.cpp

  # Layer 5: Optimizers
  ../param_id_gui/cpp/src/optim/optimizers.cpp

  # Layer 6: Data processing
  ../param_id_gui/cpp/src/data/signal_processing.cpp

  # Layer 7: Bindings
  ../param_id_gui/cpp/src/bindings.cpp
)

# Include directories
set(INCLUDE_DIRS
  ../param_id_gui/cpp/include/math
  ../param_id_gui/cpp/include/filters
  ../param_id_gui/cpp/include/solvers
  ../param_id_gui/cpp/include/models
  ../param_id_gui/cpp/include/optim
  ../param_id_gui/cpp/include/data
)

# Create nanobind module
nanobind_add_module(
  _core
  STABLE_ABI
  ${SOURCES}
)

# Include directories
target_include_directories(_core PRIVATE ${INCLUDE_DIRS})

# Install the module
install(
  TARGETS _core
  DESTINATION param_id_gui
)
