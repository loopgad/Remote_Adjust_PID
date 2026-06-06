"""Tests for core.simulation_controller and core.simulation_engine."""

import pytest
from unittest.mock import MagicMock, patch
from param_id_gui.core.simulation_controller import SimulationController
from param_id_gui.core.simulation_engine import SimulationEngine
from param_id_gui.core.types import SimulationState


class TestSimulationEngine:
    """Test SimulationEngine (pure Python, no Qt)."""

    def test_initial_state(self):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()

        engine = SimulationEngine(orch, bus, reg)
        assert engine.get_current_model_name() is None
        assert engine.get_current_params() is None

    def test_update_params(self):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()

        engine = SimulationEngine(orch, bus, reg)
        engine.update_params("PMSM", {"Rs": 0.5})
        assert engine.get_current_model_name() == "PMSM"
        assert engine.get_current_params() == {"Rs": 0.5}

    def test_start_returns_false_if_model_not_found(self):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()
        orch.get_state.return_value = SimulationState.IDLE
        reg.get.side_effect = KeyError("not found")

        engine = SimulationEngine(orch, bus, reg)
        result = engine.start("NonExistent", {})
        assert result is False

    def test_start_returns_false_if_already_running(self):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()
        orch.get_state.return_value = SimulationState.RUNNING

        engine = SimulationEngine(orch, bus, reg)
        result = engine.start("PMSM", {})
        assert result is False


class TestSimulationController:
    """Test SimulationController lifecycle."""

    def test_initial_state(self, qtbot):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()
        reg.list_models.return_value = ["PMSM"]
        reg.get.return_value = MagicMock()

        ctrl = SimulationController(orch, bus, reg)
        assert ctrl.get_current_model_name() is None
        assert ctrl.get_current_params() is None

    def test_update_params(self, qtbot):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()

        ctrl = SimulationController(orch, bus, reg)
        ctrl.update_params("PMSM", {"Rs": 0.5})
        assert ctrl.get_current_model_name() == "PMSM"
        assert ctrl.get_current_params() == {"Rs": 0.5}

    def test_reset_clears_state(self, qtbot):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()

        ctrl = SimulationController(orch, bus, reg)
        ctrl.update_params("PMSM", {"Rs": 0.5})
        ctrl.reset_simulation()
        assert ctrl.get_current_model_name() is None
        assert ctrl.get_current_params() is None

    def test_start_simulation_calls_orchestrator(self, qtbot):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()
        orch.get_state.return_value = SimulationState.IDLE

        ctrl = SimulationController(orch, bus, reg)
        ctrl.update_params("PMSM", {"Rs": 0.5})

        with patch('param_id_gui.core.simulation_controller.QThread') as mock_qthread, \
             patch('param_id_gui.core.simulation_controller._SimulationWorker') as mock_worker_cls:
            mock_thread_instance = MagicMock()
            mock_qthread.return_value = mock_thread_instance
            mock_worker_instance = MagicMock()
            mock_worker_cls.return_value = mock_worker_instance

            ctrl.start_simulation("PMSM", {"Rs": 0.5})

            orch.reset.assert_called_once()
            # State is now set by orchestrator.run() inside the engine, not by controller
            mock_worker_instance.moveToThread.assert_called_once_with(mock_thread_instance)
            mock_thread_instance.start.assert_called_once()

    def test_stop_simulation_calls_engine(self, qtbot):
        orch = MagicMock()
        bus = MagicMock()
        reg = MagicMock()

        ctrl = SimulationController(orch, bus, reg)
        ctrl.stop_simulation()
        orch.stop.assert_called_once()
