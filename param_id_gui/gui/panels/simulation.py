"""Simulation GUI Panel with real-time waveform display.

Provides interface for simulation control, real-time waveform visualization,
and simulation status monitoring.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
import numpy as np
from collections import deque

if TYPE_CHECKING:
    from param_id_gui.core.simulation_controller import SimulationController

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QComboBox,
    QDoubleSpinBox, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class WaveformWidget(QWidget):
    """Widget for real-time waveform display."""
    
    def __init__(self, title: str = "Waveform", max_points: int = 1000,
                 parent: Optional[QWidget] = None):
        """Initialize waveform widget.
        
        Args:
            title: Plot title
            max_points: Maximum number of points to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._title = title
        self._max_points = max_points
        self._data: Dict[str, deque] = {}
        self._time_data: deque = deque(maxlen=max_points)
        self._lines: Dict = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if MATPLOTLIB_AVAILABLE:
            self._figure = Figure(figsize=(8, 4))
            self._canvas = FigureCanvas(self._figure)
            self._ax = self._figure.add_subplot(111)
            self._ax.set_title(self._title)
            self._ax.set_xlabel("Time (s)")
            self._ax.set_ylabel("Value")
            self._ax.grid(True)
            layout.addWidget(self._canvas)
        else:
            self._placeholder = QLabel("Matplotlib not available for waveform display")
            self._placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(self._placeholder)
    
    def add_series(self, name: str, color: str = "blue"):
        """Add a data series.
        
        Args:
            name: Series name
            color: Line color
        """
        self._data[name] = deque(maxlen=self._max_points)
        
        if MATPLOTLIB_AVAILABLE:
            line, = self._ax.plot([], [], label=name, color=color)
            self._lines[name] = line
            self._ax.legend()
    
    def update_data(self, time: float, values: Dict[str, float]):
        """Update waveform data.
        
        Args:
            time: Current time
            values: Dictionary of values {name: value}
        """
        self._time_data.append(time)
        
        for name, value in values.items():
            if name in self._data:
                self._data[name].append(value)
        
        if MATPLOTLIB_AVAILABLE:
            self._update_plot()
    
    def _update_plot(self):
        """Update the matplotlib plot using incremental line updates."""
        if not self._time_data:
            return
        
        time_array = np.array(self._time_data)
        
        for name, data in self._data.items():
            if data and name in self._lines:
                self._lines[name].set_data(time_array[-len(data):], list(data))
        
        self._ax.relim()
        self._ax.autoscale_view()
        self._canvas.draw_idle()
    
    def clear(self):
        """Clear all data and reset plot lines."""
        self._time_data.clear()
        for data in self._data.values():
            data.clear()
        
        if MATPLOTLIB_AVAILABLE:
            self._ax.clear()
            self._ax.set_title(self._title)
            self._ax.grid(True)
            self._lines.clear()
            self._rebuild_lines()
            self._canvas.draw()
    
    def clear_series(self):
        """Remove all series and clear the plot."""
        self._data.clear()
        self._time_data.clear()
        self._lines.clear()
        if MATPLOTLIB_AVAILABLE:
            self._ax.clear()
            self._ax.set_title(self._title)
            self._ax.grid(True)
            self._canvas.draw()
    
    def set_series(self, names, colors=None):
        """Set series to display, removing any existing ones.
        
        Args:
            names: List of series names
            colors: Optional list of colors (cycles if shorter than names)
        """
        self.clear_series()
        if colors is None:
            default_colors = ["red", "green", "blue", "orange", "purple", "brown", "cyan", "magenta"]
            colors = default_colors
        for i, name in enumerate(names):
            color = colors[i % len(colors)]
            self.add_series(name, color)
    
    def _rebuild_lines(self):
        """Recreate matplotlib line objects after axes clear."""
        if not MATPLOTLIB_AVAILABLE:
            return
        colors = ["red", "green", "blue", "orange", "purple", "brown", "cyan", "magenta"]
        for i, name in enumerate(self._data.keys()):
            color = colors[i % len(colors)]
            line, = self._ax.plot([], [], label=name, color=color)
            self._lines[name] = line
        if self._lines:
            self._ax.legend()


class SimulationPanel(QWidget):
    """Simulation control panel.
    
    Provides interface for simulation control, real-time waveform display,
    and simulation status monitoring.
    """
    
    # Model output port definitions for waveform configuration
    _MODEL_OUTPUTS = {
        "PMSM": {
            "current": (["ia", "ib", "ic"], ["red", "green", "blue"]),
            "voltage": (["va", "vb", "vc"], ["red", "green", "blue"]),
            "speed": (["speed"], ["purple"]),
        },
        "Buck Converter": {
            "inductor": (["iL"], ["red"]),
            "capacitor": (["vC"], ["blue"]),
        },
        "Boost Converter": {
            "inductor": (["iL"], ["red"]),
            "capacitor": (["vC"], ["blue"]),
        },
        "FOC Controller": {
            "output": (["vd_ref", "vq_ref", "duty_a"], ["red", "green", "blue"]),
        },
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize simulation panel."""
        super().__init__(parent)
        
        self._controller: Optional['SimulationController'] = None
        self._is_running = False
        self._is_paused = False
        self._simulation_time = 0.0
        self._current_output_keys = []
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        
        self._setup_ui()
        self._configure_waveforms(self._model_combo.currentText())
    
    def set_controller(self, controller: 'SimulationController') -> None:
        """Set the simulation controller.
        
        Args:
            controller: SimulationController instance
        """
        # Disconnect old controller signals
        if self._controller:
            try:
                self._controller.state_changed.disconnect(self._on_state_changed)
                self._controller.step_completed.disconnect(self._on_step_completed)
                self._controller.error_occurred.disconnect(self._on_error)
            except (RuntimeError, TypeError):
                pass

        self._controller = controller
        
        # Connect controller signals
        self._controller.state_changed.connect(self._on_state_changed)
        self._controller.step_completed.connect(self._on_step_completed)
        self._controller.error_occurred.connect(self._on_error)
    
    def _configure_waveforms(self, model_name: str) -> None:
        """Reconfigure waveform widgets based on selected model."""
        # Clear existing waveform widgets
        for w in self._waveform_widgets:
            self._waveform_layout.removeWidget(w)
            w.deleteLater()
        self._waveform_widgets.clear()
        
        # Get output port definitions for this model
        outputs = self._MODEL_OUTPUTS.get(model_name, {})
        self._current_output_keys = []
        
        for group_name, (keys, colors) in outputs.items():
            title = group_name.replace("_", " ").title()
            widget = WaveformWidget(title)
            widget.set_series(keys, colors)
            self._waveform_layout.addWidget(widget)
            self._waveform_widgets.append(widget)
            self._current_output_keys.extend(keys)
        
        if not self._waveform_widgets:
            placeholder = QLabel("No waveform data for this model")
            placeholder.setAlignment(Qt.AlignCenter)
            self._waveform_layout.addWidget(placeholder)
            self._waveform_widgets.append(placeholder)
        
        self._waveform_layout.addStretch()
        
        # Update data table rows to match output keys
        display_keys = ["Time"] + self._current_output_keys
        self._data_table.setRowCount(len(display_keys))
        for i, key in enumerate(display_keys):
            item = self._data_table.item(i, 0)
            if item is None:
                self._data_table.setItem(i, 0, QTableWidgetItem(key))
                self._data_table.setItem(i, 1, QTableWidgetItem("0.0"))
            else:
                item.setText(key)
                val_item = self._data_table.item(i, 1)
                if val_item:
                    val_item.setText("0.0")
    
    def _on_state_changed(self, state: str) -> None:
        """Handle state change from controller."""
        if state == "running":
            self._is_running = True
            self._is_paused = False
            self._start_btn.setEnabled(False)
            self._pause_btn.setEnabled(True)
            self._stop_btn.setEnabled(True)
            self._status_label.setText("Running")
            self._set_status_style("statusRunning")
            self._update_timer.start(50)  # 20 FPS
        elif state == "paused":
            self._is_paused = True
            self._pause_btn.setText("Resume")
            self._status_label.setText("Paused")
            self._set_status_style("statusWarning")
            self._update_timer.stop()
        elif state == "idle":
            self._is_running = False
            self._is_paused = False
            self._start_btn.setEnabled(True)
            self._pause_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._pause_btn.setText("Pause")
            self._status_label.setText("Idle")
            self._set_status_style("statusIdle")
            self._update_timer.stop()
        elif state == "stopped":
            self._is_running = False
            self._is_paused = False
            self._start_btn.setEnabled(True)
            self._pause_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._pause_btn.setText("Pause")
            self._status_label.setText("Stopped")
            self._set_status_style("statusIdle")
            self._update_timer.stop()
        elif state == "error":
            self._is_running = False
            self._is_paused = False
            self._start_btn.setEnabled(True)
            self._pause_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._status_label.setText("Error")
            self._set_status_style("statusError")
            self._update_timer.stop()
    
    def _set_status_style(self, object_name: str) -> None:
        """Update status label style via objectName + QSS."""
        self._status_label.setObjectName(object_name)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
    
    def _on_step_completed(self, state: Dict[str, Any]) -> None:
        """Handle step completed from controller."""
        # Update step count
        if "step_count" in state:
            self._step_count_label.setText(str(state["step_count"]))
    
    def _on_error(self, error_msg: str) -> None:
        """Handle error from controller."""
        QMessageBox.critical(self, "Simulation Error", error_msg)
    
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for controls and waveforms
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Simulation controls
        control_group = QGroupBox("Simulation Control")
        control_group_layout = QVBoxLayout(control_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._start_btn = QPushButton("Start")
        self._start_btn.setObjectName("startButton")
        self._start_btn.setToolTip("Start simulation (F5)")
        self._start_btn.clicked.connect(self._on_start)
        button_layout.addWidget(self._start_btn)
        
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setToolTip("Pause or resume simulation (F6)")
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setEnabled(False)
        button_layout.addWidget(self._pause_btn)
        
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("dangerButton")
        self._stop_btn.setToolTip("Stop simulation (F7)")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        button_layout.addWidget(self._stop_btn)
        
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setToolTip("Reset simulation to initial state")
        self._reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self._reset_btn)
        
        control_group_layout.addLayout(button_layout)
        
        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        control_group_layout.addWidget(self._progress_bar)
        
        control_layout.addWidget(control_group)
        
        # Simulation parameters
        params_group = QGroupBox("Simulation Parameters")
        params_layout = QFormLayout(params_group)
        
        self._duration_spin = QDoubleSpinBox()
        self._duration_spin.setRange(0.001, 1000.0)
        self._duration_spin.setValue(1.0)
        self._duration_spin.setSuffix(" s")
        params_layout.addRow("Duration:", self._duration_spin)
        
        self._step_size_spin = QDoubleSpinBox()
        self._step_size_spin.setRange(1e-6, 1.0)
        self._step_size_spin.setValue(1e-4)
        self._step_size_spin.setDecimals(6)
        self._step_size_spin.setSuffix(" s")
        params_layout.addRow("Step Size:", self._step_size_spin)
        
        self._model_combo = QComboBox()
        self._model_combo.addItems(["PMSM", "Buck Converter", "Boost Converter", "FOC Controller"])
        self._model_combo.currentTextChanged.connect(self._configure_waveforms)
        params_layout.addRow("Model:", self._model_combo)
        
        control_layout.addWidget(params_group)
        
        # Status display
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)
        
        self._time_label = QLabel("0.000 s")
        status_layout.addRow("Simulation Time:", self._time_label)
        
        self._status_label = QLabel("Stopped")
        self._status_label.setObjectName("statusIdle")
        status_layout.addRow("Status:", self._status_label)
        
        self._step_count_label = QLabel("0")
        status_layout.addRow("Step Count:", self._step_count_label)
        
        control_layout.addWidget(status_group)
        
        # Data table
        data_group = QGroupBox("Current Values")
        data_layout = QVBoxLayout(data_group)
        
        self._data_table = QTableWidget(1, 2)
        self._data_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self._data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._data_table.verticalHeader().setVisible(False)
        self._data_table.setItem(0, 0, QTableWidgetItem("Time"))
        self._data_table.setItem(0, 1, QTableWidgetItem("0.0"))
        
        data_layout.addWidget(self._data_table)
        control_layout.addWidget(data_group)
        
        control_layout.addStretch()
        
        splitter.addWidget(control_widget)
        
        # Right panel - Waveforms (dynamically populated by _configure_waveforms)
        self._waveform_container = QWidget()
        self._waveform_layout = QVBoxLayout(self._waveform_container)
        self._waveform_layout.setContentsMargins(0, 0, 0, 0)
        self._waveform_widgets = []
        
        splitter.addWidget(self._waveform_container)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
    
    def _on_start(self):
        """Handle start button click."""
        if not self._is_running and self._controller:
            # Get simulation parameters
            model_name = self._model_combo.currentText()
            duration = self._duration_spin.value()
            step_size = self._step_size_spin.value()
            
            # Get model params from controller (set by ModelConfigPanel)
            params = self._controller.get_current_params() or {}
            
            # Start simulation via controller
            self._controller.start_simulation(model_name, params, duration, step_size)
    
    def _on_pause(self):
        """Handle pause button click."""
        if self._is_running and self._controller:
            if self._is_paused:
                # Resume - continue from where we left off
                self._controller.resume_simulation()
            else:
                # Pause
                self._controller.pause_simulation()
    
    def _on_stop(self):
        """Handle stop button click."""
        if self._controller:
            self._controller.stop_simulation()
    
    def _on_reset(self):
        """Handle reset button click."""
        if self._controller:
            self._controller.reset_simulation()
        
        # Clear all waveform widgets
        for w in self._waveform_widgets:
            if isinstance(w, WaveformWidget):
                w.clear()
        
        # Reset data table values
        for i in range(self._data_table.rowCount()):
            item = self._data_table.item(i, 1)
            if item is not None:
                item.setText("0.0")
    
    def _update_display(self):
        """Update display with current simulation data."""
        if not self._controller:
            return
        
        # Get latest data from controller
        data = self._controller.get_latest_data()
        
        # Update time display
        sim_time = data.get("time", 0.0)
        if sim_time is None:
            sim_time = 0.0
        self._time_label.setText(f"{sim_time:.3f} s")
        self._simulation_time = sim_time

        # Update progress bar
        duration = self._duration_spin.value()
        if duration > 0:
            pct = min(int(sim_time / duration * 100), 100)
            self._progress_bar.setValue(pct)
        
        # Update step count
        step_count = data.get("step_count", 0)
        self._step_count_label.setText(str(step_count))
        
        # Extract model-specific data using dynamic output keys
        waveform_data = {}
        for key in self._current_output_keys:
            if key in data:
                waveform_data[key] = data[key]
        
        if waveform_data:
            self.update_waveforms(sim_time, waveform_data)
    
    def update_waveforms(self, time: float, data: Dict[str, float]):
        """Update waveform displays.
        
        Args:
            time: Current simulation time
            data: Dictionary of data values
        """
        self._simulation_time = time
        self._time_label.setText(f"{time:.3f} s")
        
        # Distribute data to each waveform widget
        for widget in self._waveform_widgets:
            if isinstance(widget, WaveformWidget):
                # Find which keys this widget owns
                widget_data = {}
                for key in data:
                    if key in widget._data:
                        widget_data[key] = data[key]
                if widget_data:
                    widget.update_data(time, widget_data)
        
        # Update data table
        self._update_data_table(time, data)
    
    def _update_data_table(self, time: float, data: Dict[str, float]):
        """Update data table with current values."""
        # Update time (row 0)
        time_item = self._data_table.item(0, 1)
        if time_item:
            time_item.setText(f"{time:.6f}")
        
        # Update model output variables (rows 1..N)
        for i, key in enumerate(self._current_output_keys):
            row = i + 1
            if row < self._data_table.rowCount() and key in data:
                value_item = self._data_table.item(row, 1)
                if value_item:
                    value_item.setText(f"{data[key]:.6f}")
    
    def set_step_count(self, count: int):
        """Set step count display."""
        self._step_count_label.setText(str(count))
    
    def set_progress(self, percent: int):
        """Set progress bar value."""
        self._progress_bar.setValue(percent)
    
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self._is_running
    
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return self._is_paused
