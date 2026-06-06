"""End-to-end integration tests for disconnect fix.

Tests the complete workflow:
- C++ compatibility layer
- SimulationController lifecycle
- DataBus bridge
- GUI signal connections
- End-to-end simulation workflow
"""

import pytest
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCoreCompat:
    """Test C++ compatibility layer."""
    
    def test_get_core_returns_module_or_none(self):
        """Test get_core() returns module or None."""
        from param_id_gui.core._core_compat import get_core
        core = get_core()
        # Should return module or None, never raise
        assert core is None or hasattr(core, '__name__')
    
    def test_get_solver_returns_solver_or_none(self):
        """Test get_solver() returns solver or None."""
        from param_id_gui.core._core_compat import get_solver
        solver = get_solver(1e-4)
        # Should return solver or None, never raise
        assert solver is None or hasattr(solver, 'solve')
    
    def test_get_filters_returns_module_or_none(self):
        """Test get_filters() returns filters module or None."""
        from param_id_gui.core._core_compat import get_filters
        filters = get_filters()
        # Should return module or None, never raise
        assert filters is None or hasattr(filters, '__name__')
    
    def test_core_compat_import_error_handling(self):
        """Test that import errors are handled gracefully."""
        from param_id_gui.core import _core_compat
        # Reset cached state to test import error handling
        _core_compat._core_module = None
        _core_compat._core_available = None
        
        # Should not raise even if C++ module is unavailable
        core = _core_compat.get_core()
        assert core is None or hasattr(core, '__name__')


class TestSimulationController:
    """Test SimulationController lifecycle."""
    
    @pytest.fixture
    def controller(self):
        """Create a SimulationController instance."""
        from param_id_gui.core.orchestrator import Orchestrator
        from param_id_gui.core.data_bus import DataBus
        from param_id_gui.core.model_registry import ModelRegistry
        from param_id_gui.core.simulation_controller import SimulationController
        
        orch = Orchestrator()
        db = DataBus()
        reg = ModelRegistry()
        return SimulationController(orch, db, reg)
    
    def test_controller_creation(self, controller):
        """Test controller can be created."""
        assert controller is not None
        assert hasattr(controller, 'start_simulation')
        assert hasattr(controller, 'pause_simulation')
        assert hasattr(controller, 'stop_simulation')
        assert hasattr(controller, 'reset_simulation')
    
    def test_controller_initial_state(self, controller):
        """Test controller initial state."""
        assert controller.get_current_model_name() is None
        assert controller.get_current_params() is None
    
    def test_controller_get_latest_data(self, controller):
        """Test get_latest_data returns dict."""
        data = controller.get_latest_data()
        assert isinstance(data, dict)
    
    def test_controller_state_changed_signal(self, controller):
        """Test state_changed signal is emitted."""
        states = []
        controller.state_changed.connect(lambda s: states.append(s))
        
        # Reset should emit 'idle'
        controller.reset_simulation()
        assert 'idle' in states


class TestDataBus:
    """Test DataBus functionality."""
    
    @pytest.fixture
    def data_bus(self):
        """Create a DataBus instance."""
        from param_id_gui.core.data_bus import DataBus
        return DataBus()
    
    def test_data_bus_creation(self, data_bus):
        """Test DataBus can be created."""
        assert data_bus is not None
    
    def test_publish_scalar(self, data_bus):
        """Test publish_scalar works."""
        from param_id_gui.core.data_bus import Signal
        sig = data_bus.publish_scalar("test/topic", 1.0, "V", module_id="test")
        assert sig is not None
        assert sig.value == 1.0
    
    def test_read_latest(self, data_bus):
        """Test read_latest returns published value."""
        data_bus.publish_scalar("test/topic", 42.0, "A", module_id="test")
        sig = data_bus.read_latest("test/topic")
        assert sig is not None
        assert sig.value == 42.0
    
    def test_subscribe_callback(self, data_bus):
        """Test subscribe callback is called."""
        received = []
        data_bus.subscribe("test/topic", lambda s: received.append(s.value))
        data_bus.publish_scalar("test/topic", 99.0, "V", module_id="test")
        assert 99.0 in received
    


class TestOrchestrator:
    """Test Orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create an Orchestrator instance."""
        from param_id_gui.core.orchestrator import Orchestrator
        return Orchestrator()
    
    def test_orchestrator_creation(self, orchestrator):
        """Test Orchestrator can be created."""
        assert orchestrator is not None
    
    def test_orchestrator_initial_state(self, orchestrator):
        """Test Orchestrator initial state."""
        state = orchestrator.get_state()
        assert state.name == "IDLE"
        assert state.value == "idle"
    
    def test_orchestrator_register_stepper(self, orchestrator):
        """Test register_stepper works."""
        def dummy_step():
            pass
        orchestrator.register_stepper("test", dummy_step)
        assert "test" in orchestrator._steppers


class TestModelRegistry:
    """Test ModelRegistry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create a ModelRegistry instance."""
        from param_id_gui.core.model_registry import ModelRegistry
        return ModelRegistry()
    
    def test_registry_creation(self, registry):
        """Test ModelRegistry can be created."""
        assert registry is not None
    
    def test_registry_register_and_get(self, registry):
        """Test register and get work."""
        from param_id_gui.core.model_registry import ModelMetadata, Domain, FidelityLevel
        
        class DummyModel:
            pass
        
        model = DummyModel()
        meta = ModelMetadata(
            model_id="test_model",
            model_name="Test Model",
            domain=Domain.MOTOR,
            fidelity=FidelityLevel.L0_STUB,
            version="1.0.0",
            sim_step_ns=1000
        )
        registry.register(model, meta)
        assert registry.get("test_model") is model
    
    def test_registry_get_nonexistent(self, registry):
        """Test get raises KeyError for nonexistent model."""
        with pytest.raises(KeyError):
            registry.get("nonexistent")


class TestGUIComponents:
    """Test GUI components import and basic functionality."""
    
    def test_simulation_panel_import(self):
        """Test SimulationPanel can be imported."""
        from param_id_gui.gui.panels.simulation import SimulationPanel
        assert SimulationPanel is not None
    
    def test_main_window_import(self):
        """Test MainWindow can be imported."""
        from param_id_gui.gui.main_window import MainWindow
        assert MainWindow is not None
    
    def test_simulation_panel_has_set_controller(self):
        """Test SimulationPanel has set_controller method."""
        from param_id_gui.gui.panels.simulation import SimulationPanel
        assert hasattr(SimulationPanel, 'set_controller')
    
    def test_main_window_has_set_controller(self):
        """Test MainWindow has set_controller method."""
        from param_id_gui.gui.main_window import MainWindow
        assert hasattr(MainWindow, 'set_controller')


class TestEndToEnd:
    """Test end-to-end workflow."""
    
    def test_full_import_chain(self):
        """Test full import chain works."""
        from param_id_gui.core._core_compat import get_core
        from param_id_gui.core.orchestrator import Orchestrator
        from param_id_gui.core.data_bus import DataBus
        from param_id_gui.core.model_registry import ModelRegistry
        from param_id_gui.core.simulation_controller import SimulationController
        from param_id_gui.gui.main_window import MainWindow
        
        # All imports should succeed
        assert get_core is not None
        assert Orchestrator is not None
        assert DataBus is not None
        assert ModelRegistry is not None
        assert SimulationController is not None
        assert MainWindow is not None
    
    def test_controller_data_bus_integration(self):
        """Test controller and data bus work together."""
        from param_id_gui.core.orchestrator import Orchestrator
        from param_id_gui.core.data_bus import DataBus
        from param_id_gui.core.model_registry import ModelRegistry
        from param_id_gui.core.simulation_controller import SimulationController
        
        orch = Orchestrator()
        db = DataBus()
        reg = ModelRegistry()
        ctrl = SimulationController(orch, db, reg)
        
        # Publish data via data bus
        db.publish_scalar("test/value", 123.456, "V", module_id="test")
        
        # Read via data bus
        sig = db.read_latest("test/value")
        assert sig is not None
        assert abs(sig.value - 123.456) < 0.001
    
    def test_orchestrator_simulation_run(self):
        """Test orchestrator can run a simulation."""
        from param_id_gui.core.orchestrator import Orchestrator, StepResult
        
        orch = Orchestrator()
        
        results = []
        def step_fn(step_ns: int) -> StepResult:
            results.append(orch.get_time())
            return StepResult(solver_id="test", converged=True, error_estimate=0.0)
        
        orch.register_stepper("test", step_fn)
        orch.run(step_ns=1000000, duration_s=0.01)
        
        assert len(results) > 0
        # Use name comparison to avoid cross-module enum mismatch
        assert orch.get_state().name == "IDLE"
