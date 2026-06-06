"""Test project structure and imports."""

import pytest
from pathlib import Path


def test_project_structure():
    """Test that project directory structure exists."""
    project_root = Path(__file__).parent.parent.parent
    
    # Check main package exists
    assert (project_root / "param_id_gui").is_dir()
    assert (project_root / "param_id_gui" / "__init__.py").is_file()
    
    # Check core modules
    assert (project_root / "param_id_gui" / "core").is_dir()
    assert (project_root / "param_id_gui" / "core" / "__init__.py").is_file()
    assert (project_root / "param_id_gui" / "core" / "orchestrator.py").is_file()
    assert (project_root / "param_id_gui" / "core" / "data_bus.py").is_file()
    assert (project_root / "param_id_gui" / "core" / "model_registry.py").is_file()
    
    # Check models
    assert (project_root / "param_id_gui" / "models").is_dir()
    assert (project_root / "param_id_gui" / "models" / "motor").is_dir()
    assert (project_root / "param_id_gui" / "models" / "power").is_dir()
    assert (project_root / "param_id_gui" / "models" / "controller").is_dir()
    
    # Check algorithms
    assert (project_root / "param_id_gui" / "algorithms").is_dir()
    assert (project_root / "param_id_gui" / "algorithms" / "__init__.py").is_file()
    assert (project_root / "param_id_gui" / "algorithms" / "lm.py").is_file()
    assert (project_root / "param_id_gui" / "algorithms" / "pso.py").is_file()
    
    # Check GUI
    assert (project_root / "param_id_gui" / "gui").is_dir()
    assert (project_root / "param_id_gui" / "gui" / "main_window.py").is_file()
    assert (project_root / "param_id_gui" / "gui" / "panels").is_dir()
    
    # Check C++ module
    assert (project_root / "param_id_gui" / "cpp").is_dir()
    assert (project_root / "param_id_gui" / "cpp" / "src").is_dir()
    
    # Check data module
    assert (project_root / "param_id_gui" / "data").is_dir()
    assert (project_root / "param_id_gui" / "data" / "hdf5_handler.py").is_file()
    
    # Check tests
    assert (project_root / "tests").is_dir()
    assert (project_root / "tests" / "__init__.py").is_file()
    assert (project_root / "tests" / "conftest.py").is_file()
    assert (project_root / "tests" / "unit").is_dir()
    assert (project_root / "tests" / "integration").is_dir()
    assert (project_root / "tests" / "physics").is_dir()
    assert (project_root / "tests" / "security").is_dir()


def test_config_files():
    """Test that configuration files exist."""
    project_root = Path(__file__).parent.parent.parent
    
    assert (project_root / "pyproject.toml").is_file()
    assert (project_root / ".gitignore").is_file()


def test_core_imports():
    """Test that core modules can be imported."""
    from param_id_gui.core.orchestrator import Orchestrator, SimulationState
    from param_id_gui.core.data_bus import DataBus
    from param_id_gui.core.model_registry import ModelRegistry
    
    # Test basic instantiation
    orchestrator = Orchestrator()
    assert orchestrator.get_state() == SimulationState.IDLE
    
    data_bus = DataBus()
    assert data_bus.read_latest("nonexistent") is None
    
    registry = ModelRegistry()
    assert registry.list_models() == []


def test_model_imports():
    """Test that model modules can be imported."""
    from param_id_gui.models.motor.pmsm_dq import PMSMdqModel
    from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
    from param_id_gui.models.controller.foc import FOCController
    
    # Test basic instantiation
    pmsm = PMSMdqModel(Rs=0.5, Ld=5e-4, Lq=1e-3, flux_pm=0.03, J=1e-4)
    assert pmsm.Rs == 0.5
    
    buck = BuckConverter()
    assert buck.params.Vin == 12.0
    
    boost = BoostConverter()
    assert boost.params.Vin == 5.0
    
    foc = FOCController()
    assert foc.pi_id.kp == 5.0


def test_algorithm_imports():
    """Test that algorithm modules can be imported."""
    from param_id_gui.algorithms.lm import LevenbergMarquardt
    from param_id_gui.algorithms.pso import ParticleSwarmOptimization
    
    # Test basic instantiation
    lm = LevenbergMarquardt()
    assert lm.config.max_iterations == 1000
    
    pso = ParticleSwarmOptimization()
    assert pso.config.n_particles == 50


def test_data_imports():
    """Test that data modules can be imported."""
    pytest.importorskip("h5py")
    from param_id_gui.data.hdf5_handler import HDF5Handler
    
    # Test basic instantiation
    handler = HDF5Handler("test.h5")
    assert handler.filename == "test.h5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
