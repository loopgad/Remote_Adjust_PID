"""Simulation GUI Panel with real-time waveform display.

Provides interface for simulation control, real-time waveform visualization,
and simulation status monitoring.
"""

from typing import Optional, Dict, Any, List
import numpy as np
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QComboBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

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
            self._ax.plot([], [], label=name, color=color)
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
        """Update the matplotlib plot."""
        if not self._time_data:
            return
        
        self._ax.clear()
        self._ax.set_title(self._title)
        self._ax.set_xlabel("Time (s)")
        self._ax.set_ylabel("Value")
        self._ax.grid(True)
        
        time_array = np.array(self._time_data)
        
        for name, data in self._data.items():
            if data:
                self._ax.plot(time_array[-len(data):], list(data), label=name)
        
        self._ax.legend()
        self._canvas.draw()
    
    def clear(self):
        """Clear all data."""
        self._time_data.clear()
        for data in self._data.values():
            data.clear()
        
        if MATPLOTLIB_AVAILABLE:
            self._ax.clear()
            self._ax.set_title(self._title)
            self._ax.grid(True)
            self._canvas.draw()


class SimulationPanel(QWidget):
    """Simulation control panel.
    
    Provides interface for simulation control, real-time waveform display,
    and simulation status monitoring.
    """
    
    # Signals
    simulation_started = Signal()
    simulation_paused = Signal()
    simulation_stopped = Signal()
    simulation_reset = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize simulation panel."""
        super().__init__(parent)
        
        self._is_running = False
        self._is_paused = False
        self._simulation_time = 0.0
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        
        self._setup_ui()
    
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
        self._start_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self._start_btn.clicked.connect(self._on_start)
        button_layout.addWidget(self._start_btn)
        
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setStyleSheet("background-color: #FF9800; color: white;")
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setEnabled(False)
        button_layout.addWidget(self._pause_btn)
        
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        button_layout.addWidget(self._stop_btn)
        
        self._reset_btn = QPushButton("Reset")
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
        self._model_combo.addItems(["PMSM", "Buck Converter", "Boost Converter"])
        params_layout.addRow("Model:", self._model_combo)
        
        control_layout.addWidget(params_group)
        
        # Status display
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)
        
        self._time_label = QLabel("0.000 s")
        status_layout.addRow("Simulation Time:", self._time_label)
        
        self._status_label = QLabel("Stopped")
        self._status_label.setStyleSheet("color: gray;")
        status_layout.addRow("Status:", self._status_label)
        
        self._step_count_label = QLabel("0")
        status_layout.addRow("Step Count:", self._step_count_label)
        
        control_layout.addWidget(status_group)
        
        # Data table
        data_group = QGroupBox("Current Values")
        data_layout = QVBoxLayout(data_group)
        
        self._data_table = QTableWidget(4, 2)
        self._data_table.setHorizontalHeaderLabels(["Variable", "Value"])
        self._data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._data_table.verticalHeader().setVisible(False)
        
        # Initialize with default variables
        variables = ["Time", "ia", "ib", "ic"]
        for i, var in enumerate(variables):
            self._data_table.setItem(i, 0, QTableWidgetItem(var))
            self._data_table.setItem(i, 1, QTableWidgetItem("0.0"))
        
        data_layout.addWidget(self._data_table)
        control_layout.addWidget(data_group)
        
        control_layout.addStretch()
        
        splitter.addWidget(control_widget)
        
        # Right panel - Waveforms
        waveform_widget = QWidget()
        waveform_layout = QVBoxLayout(waveform_widget)
        
        # Current waveform
        self._current_waveform = WaveformWidget("Phase Currents")
        self._current_waveform.add_series("ia", "red")
        self._current_waveform.add_series("ib", "green")
        self._current_waveform.add_series("ic", "blue")
        waveform_layout.addWidget(self._current_waveform)
        
        # Voltage waveform
        self._voltage_waveform = WaveformWidget("Voltages")
        self._voltage_waveform.add_series("va", "red")
        self._voltage_waveform.add_series("vb", "green")
        self._voltage_waveform.add_series("vc", "blue")
        waveform_layout.addWidget(self._voltage_waveform)
        
        # Speed waveform
        self._speed_waveform = WaveformWidget("Speed")
        self._speed_waveform.add_series("speed", "purple")
        waveform_layout.addWidget(self._speed_waveform)
        
        splitter.addWidget(waveform_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
    
    def _on_start(self):
        """Handle start button click."""
        if not self._is_running:
            self._is_running = True
            self._is_paused = False
            
            self._start_btn.setEnabled(False)
            self._pause_btn.setEnabled(True)
            self._stop_btn.setEnabled(True)
            
            self._status_label.setText("Running")
            self._status_label.setStyleSheet("color: green;")
            
            # Start update timer
            self._update_timer.start(50)  # 20 FPS
            
            self.simulation_started.emit()
    
    def _on_pause(self):
        """Handle pause button click."""
        if self._is_running:
            if self._is_paused:
                # Resume
                self._is_paused = False
                self._pause_btn.setText("Pause")
                self._status_label.setText("Running")
                self._status_label.setStyleSheet("color: green;")
                self._update_timer.start(50)
            else:
                # Pause
                self._is_paused = True
                self._pause_btn.setText("Resume")
                self._status_label.setText("Paused")
                self._status_label.setStyleSheet("color: orange;")
                self._update_timer.stop()
            
            self.simulation_paused.emit()
    
    def _on_stop(self):
        """Handle stop button click."""
        self._is_running = False
        self._is_paused = False
        
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._pause_btn.setText("Pause")
        
        self._status_label.setText("Stopped")
        self._status_label.setStyleSheet("color: gray;")
        
        self._update_timer.stop()
        
        self.simulation_stopped.emit()
    
    def _on_reset(self):
        """Handle reset button click."""
        self._on_stop()
        
        self._simulation_time = 0.0
        self._time_label.setText("0.000 s")
        self._step_count_label.setText("0")
        self._progress_bar.setValue(0)
        
        # Clear waveforms
        self._current_waveform.clear()
        self._voltage_waveform.clear()
        self._speed_waveform.clear()
        
        # Reset data table
        for i in range(self._data_table.rowCount()):
            self._data_table.item(i, 1).setText("0.0")
        
        self.simulation_reset.emit()
    
    def _update_display(self):
        """Update display with current simulation data."""
        # This will be connected to the orchestrator
        pass
    
    def update_waveforms(self, time: float, data: Dict[str, float]):
        """Update waveform displays.
        
        Args:
            time: Current simulation time
            data: Dictionary of data values
        """
        self._simulation_time = time
        self._time_label.setText(f"{time:.3f} s")
        
        # Update current waveforms
        current_data = {}
        for key in ["ia", "ib", "ic"]:
            if key in data:
                current_data[key] = data[key]
        if current_data:
            self._current_waveform.update_data(time, current_data)
        
        # Update voltage waveforms
        voltage_data = {}
        for key in ["va", "vb", "vc"]:
            if key in data:
                voltage_data[key] = data[key]
        if voltage_data:
            self._voltage_waveform.update_data(time, voltage_data)
        
        # Update speed waveform
        if "speed" in data:
            self._speed_waveform.update_data(time, {"speed": data["speed"]})
        
        # Update data table
        self._update_data_table(time, data)
    
    def _update_data_table(self, time: float, data: Dict[str, float]):
        """Update data table with current values."""
        # Update time
        time_item = self._data_table.item(0, 1)
        if time_item:
            time_item.setText(f"{time:.6f}")
        
        # Update other variables
        row = 1
        for key in ["ia", "ib", "ic"]:
            if key in data and row < self._data_table.rowCount():
                value_item = self._data_table.item(row, 1)
                if value_item:
                    value_item.setText(f"{data[key]:.6f}")
                row += 1
    
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
