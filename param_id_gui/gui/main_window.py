"""PySide6 main window for the parameter identification application."""

import json
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QLabel, QToolBar,
    QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QCloseEvent

from param_id_gui.gui.panels import (
    ModelConfigPanel,
    SimulationPanel,
    ParamIDPanel,
    ResultsPanel,
)

if TYPE_CHECKING:
    from param_id_gui.core.simulation_controller import SimulationController

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window for the parameter identification application."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._controller: Optional['SimulationController'] = None
        self._project_path: Optional[str] = None
        self._last_dir: str = ""

        self.setWindowTitle("High-Precision Parameter Identification")
        self.setMinimumSize(1200, 800)

        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        self._layout = QVBoxLayout(self._central_widget)

        self._tab_widget = QTabWidget()
        self._layout.addWidget(self._tab_widget)

        self._setup_panels()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

        self._show_welcome()

    # ── Public API ──────────────────────────────────────────────

    def set_controller(self, controller: 'SimulationController') -> None:
        self._controller = controller
        self._simulation_panel.set_controller(controller)
        self._connect_actions()
        self._model_config_panel.params_changed.connect(self._on_params_changed)
        self._param_id_panel.identification_started.connect(self._on_identification_started)
        self._param_id_panel.identification_finished.connect(self._on_identification_finished)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._status_timer.stop()
        if self._controller:
            self._controller.stop_simulation()
        event.accept()
        self._status_label.setText("Ready — configure model in Model Configuration tab")
        self._status_label.setObjectName("statusIdle")

    # ── Slots ───────────────────────────────────────────────────

    def _on_params_changed(self, model_name: str, params: dict) -> None:
        if self._controller:
            self._controller.update_params(model_name, params)

    def _on_identification_started(self, algorithm: str, params: dict) -> None:
        self._status_label.setText(f"Identification running ({algorithm})...")
        self._status_label.setObjectName("statusRunning")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _on_identification_finished(self, results: dict) -> None:
        converged = results.get("converged", False)
        if converged:
            self._status_label.setText("Identification converged ✓")
            self._status_label.setObjectName("statusRunning")
        else:
            self._status_label.setText("Identification did not converge")
            self._status_label.setObjectName("statusWarning")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    # ── File Operations ─────────────────────────────────────────

    def _new_project(self):
        if self._controller and self._controller.get_state().value == "running":
            QMessageBox.warning(self, "Warning", "Stop the simulation before creating a new project.")
            return
        if self._controller:
            self._controller.reset_simulation()
        self._model_config_panel.reset_to_defaults()
        self._project_path = None
        self.setWindowTitle("High-Precision Parameter Identification — New Project")
        self._status_label.setText("New project created")
        logger.info("New project created")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", self._last_dir, "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        self._last_dir = str(Path(path).parent)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            model_name = data.get("model_name", "PMSM")
            params = data.get("params", {})
            self._model_config_panel.load_params(model_name, params)
            if self._controller:
                self._controller.update_params(model_name, params)
            self._project_path = path
            self.setWindowTitle(f"High-Precision Parameter Identification — {path}")
            self._status_label.setText(f"Opened: {path}")
            logger.info("Opened project: %s", path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")

    def _save_project(self):
        if self._project_path:
            self._save_to_path(self._project_path)
        else:
            self._save_project_as()

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", self._last_dir, "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        self._last_dir = str(Path(path).parent)
        self._save_to_path(path)
        self._project_path = path
        self.setWindowTitle(f"High-Precision Parameter Identification — {path}")

    def _save_to_path(self, path: str):
        try:
            model_name = self._model_config_panel.get_model_name()
            params = self._model_config_panel.get_params()
            data = {"model_name": model_name, "params": params}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._status_label.setText(f"Saved: {path}")
            logger.info("Saved project: %s", path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")

    def _export_results(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", self._last_dir, "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        self._last_dir = str(Path(path).parent)
        try:
            if self._controller:
                data = self._controller.get_latest_data()
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("key,value\n")
                    for k, v in data.items():
                        f.write(f"{k},{v}\n")
                self._status_label.setText(f"Exported: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")

    def _show_about(self):
        QMessageBox.about(
            self, "About",
            "<h3>High-Precision Parameter Identification</h3>"
            "<p>Version 0.1.0</p>"
            "<p>PMSM motor parameter identification and PID tuning tool "
            "with PySide6 GUI and C++ acceleration.</p>"
            "<p><b>Shortcuts:</b></p>"
            "<ul>"
            "<li>Ctrl+N — New Project</li>"
            "<li>Ctrl+O — Open Project</li>"
            "<li>Ctrl+S — Save Project</li>"
            "<li>F5 — Start Simulation</li>"
            "<li>F6 — Pause/Resume</li>"
            "<li>F7 — Stop Simulation</li>"
            "</ul>"
        )

    # ── Action Wiring ───────────────────────────────────────────

    def _connect_actions(self) -> None:
        if not self._controller:
            return

        # Disconnect previous connections to avoid duplicates
        for action in (self._start_action, self._pause_action, self._stop_action,
                        self._toolbar_start, self._toolbar_pause, self._toolbar_stop):
            try:
                action.triggered.disconnect()
            except (RuntimeError, TypeError):
                pass

        def _start_sim():
            if not self._controller:
                return
            model_name = self._controller.get_current_model_name() or "PMSM"
            params = self._controller.get_current_params() or {}
            self._controller.start_simulation(model_name, params)

        self._start_action.triggered.connect(_start_sim)
        self._pause_action.triggered.connect(
            lambda: self._controller.pause_simulation() if self._controller else None)
        self._stop_action.triggered.connect(
            lambda: self._controller.stop_simulation() if self._controller else None)

        # Toolbar buttons mirror menu actions
        self._toolbar_start.triggered.connect(_start_sim)
        self._toolbar_pause.triggered.connect(
            lambda: self._controller.pause_simulation() if self._controller else None)
        self._toolbar_stop.triggered.connect(
            lambda: self._controller.stop_simulation() if self._controller else None)

    # ── UI Setup ────────────────────────────────────────────────

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        a = QAction("&New Project", self)
        a.setShortcut(QKeySequence("Ctrl+N"))
        a.setToolTip("Create a new project (Ctrl+N)")
        a.triggered.connect(self._new_project)
        file_menu.addAction(a)

        a = QAction("&Open Project...", self)
        a.setShortcut(QKeySequence("Ctrl+O"))
        a.setToolTip("Open a saved project file (Ctrl+O)")
        a.triggered.connect(self._open_project)
        file_menu.addAction(a)

        a = QAction("&Save Project", self)
        a.setShortcut(QKeySequence("Ctrl+S"))
        a.setToolTip("Save current project (Ctrl+S)")
        a.triggered.connect(self._save_project)
        file_menu.addAction(a)

        a = QAction("Save Project &As...", self)
        a.setShortcut(QKeySequence("Ctrl+Shift+S"))
        a.triggered.connect(self._save_project_as)
        file_menu.addAction(a)

        file_menu.addSeparator()

        a = QAction("&Export Results...", self)
        a.setShortcut(QKeySequence("Ctrl+E"))
        a.setToolTip("Export simulation results to CSV")
        a.triggered.connect(self._export_results)
        file_menu.addAction(a)

        file_menu.addSeparator()

        a = QAction("E&xit", self)
        a.setShortcut(QKeySequence("Alt+F4"))
        a.triggered.connect(self.close)
        file_menu.addAction(a)

        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")

        self._start_action = QAction("&Start", self)
        self._start_action.setShortcut(QKeySequence("F5"))
        self._start_action.setToolTip("Start simulation (F5)")
        sim_menu.addAction(self._start_action)

        self._pause_action = QAction("&Pause/Resume", self)
        self._pause_action.setShortcut(QKeySequence("F6"))
        self._pause_action.setToolTip("Pause or resume simulation (F6)")
        sim_menu.addAction(self._pause_action)

        self._stop_action = QAction("S&top", self)
        self._stop_action.setShortcut(QKeySequence("F7"))
        self._stop_action.setToolTip("Stop simulation (F7)")
        sim_menu.addAction(self._stop_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        a = QAction("&About", self)
        a.triggered.connect(self._show_about)
        help_menu.addAction(a)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolTip("Main application toolbar")
        self.addToolBar(toolbar)

        a = QAction("New", self)
        a.setToolTip("Create new project (Ctrl+N)")
        a.triggered.connect(self._new_project)
        toolbar.addAction(a)

        a = QAction("Open", self)
        a.setToolTip("Open project file (Ctrl+O)")
        a.triggered.connect(self._open_project)
        toolbar.addAction(a)

        a = QAction("Save", self)
        a.setToolTip("Save project (Ctrl+S)")
        a.triggered.connect(self._save_project)
        toolbar.addAction(a)

        toolbar.addSeparator()

        self._toolbar_start = QAction("Start", self)
        self._toolbar_start.setToolTip("Start simulation (F5)")
        toolbar.addAction(self._toolbar_start)

        self._toolbar_pause = QAction("Pause", self)
        self._toolbar_pause.setToolTip("Pause/Resume simulation (F6)")
        toolbar.addAction(self._toolbar_pause)

        self._toolbar_stop = QAction("Stop", self)
        self._toolbar_stop.setToolTip("Stop simulation (F7)")
        toolbar.addAction(self._toolbar_stop)

    def _setup_status_bar(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)

        self._time_label = QLabel("Time: 0.000 s")
        self._status_bar.addPermanentWidget(self._time_label)

    def _setup_panels(self):
        self._model_config_panel = ModelConfigPanel()
        self._tab_widget.addTab(self._model_config_panel, "Model Configuration")

        self._simulation_panel = SimulationPanel()
        self._tab_widget.addTab(self._simulation_panel, "Simulation")

        self._param_id_panel = ParamIDPanel()
        self._tab_widget.addTab(self._param_id_panel, "Parameter Identification")

        self._results_panel = ResultsPanel()
        self._tab_widget.addTab(self._results_panel, "Results")

        # Tab tooltips
        self._tab_widget.setTabToolTip(0, "Configure model parameters and presets")
        self._tab_widget.setTabToolTip(1, "Run simulation and view waveforms")
        self._tab_widget.setTabToolTip(2, "Identify parameters using LM or PSO")
        self._tab_widget.setTabToolTip(3, "View and analyze results")

    def _show_welcome(self):
        self._status_label.setText(
            "Welcome! Start by selecting a model in the 'Model Configuration' tab, then go to 'Simulation' to run.")

    def _update_status(self):
        if not self._controller:
            return

        data = self._controller.get_latest_data()

        sim_time = data.get("time", 0.0)
        if sim_time is None:
            sim_time = 0.0
        self._time_label.setText(f"Time: {sim_time:.3f} s")

        state = data.get("state", "idle")
        if state == "running":
            self._status_label.setText("Simulation Running")
            self._status_label.setObjectName("statusRunning")
        elif state == "paused":
            self._status_label.setText("Simulation Paused — press F6 to resume")
            self._status_label.setObjectName("statusWarning")
        elif state == "error":
            self._status_label.setText("Simulation Error — check parameters and try again")
            self._status_label.setObjectName("statusError")
        elif self._status_label.text().startswith("Simulation"):
            self._status_label.setText("Ready")
            self._status_label.setObjectName("")
