"""Results Visualization and Comparison GUI Panel.

Provides interface for visualizing simulation results, comparing different
runs, and exporting data.
"""

from typing import Optional, Dict, Any, List
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QComboBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSplitter, QMessageBox, QFileDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import h5py
    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False

import csv


class ResultsPanel(QWidget):
    """Results visualization and comparison panel.
    
    Provides interface for visualizing simulation results, comparing different
    runs, and exporting data.
    """
    
    # Signals
    data_loaded = Signal(str)  # filename
    data_exported = Signal(str, str)  # filename, format
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize results panel."""
        super().__init__(parent)
        
        self._data: Dict[str, np.ndarray] = {}
        self._comparison_data: Dict[str, Dict[str, np.ndarray]] = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for controls and plots
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Data loading
        load_group = QGroupBox("Data Loading")
        load_layout = QVBoxLayout(load_group)
        
        load_button_layout = QHBoxLayout()
        
        self._load_hdf5_btn = QPushButton("Load HDF5")
        self._load_hdf5_btn.clicked.connect(self._load_hdf5)
        load_button_layout.addWidget(self._load_hdf5_btn)
        
        self._load_csv_btn = QPushButton("Load CSV")
        self._load_csv_btn.clicked.connect(self._load_csv)
        load_button_layout.addWidget(self._load_csv_btn)
        
        load_layout.addLayout(load_button_layout)
        
        # Data list
        self._data_list = QListWidget()
        self._data_list.setSelectionMode(QListWidget.MultiSelection)
        self._data_list.itemSelectionChanged.connect(self._on_selection_changed)
        load_layout.addWidget(self._data_list)
        
        control_layout.addWidget(load_group)
        
        # Plot configuration
        plot_group = QGroupBox("Plot Configuration")
        plot_layout = QFormLayout(plot_group)
        
        self._x_combo = QComboBox()
        self._x_combo.currentTextChanged.connect(self._update_plot)
        plot_layout.addRow("X Axis:", self._x_combo)
        
        self._y_combo = QComboBox()
        self._y_combo.currentTextChanged.connect(self._update_plot)
        plot_layout.addRow("Y Axis:", self._y_combo)
        
        self._plot_type_combo = QComboBox()
        self._plot_type_combo.addItems(["Line", "Scatter", "Bar"])
        self._plot_type_combo.currentTextChanged.connect(self._update_plot)
        plot_layout.addRow("Plot Type:", self._plot_type_combo)
        
        self._show_grid_check = QCheckBox("Show Grid")
        self._show_grid_check.setChecked(True)
        self._show_grid_check.stateChanged.connect(self._update_plot)
        plot_layout.addRow("", self._show_grid_check)
        
        self._show_legend_check = QCheckBox("Show Legend")
        self._show_legend_check.setChecked(True)
        self._show_legend_check.stateChanged.connect(self._update_plot)
        plot_layout.addRow("", self._show_legend_check)
        
        control_layout.addWidget(plot_group)
        
        # Comparison
        comparison_group = QGroupBox("Comparison")
        comparison_layout = QVBoxLayout(comparison_group)
        
        self._add_comparison_btn = QPushButton("Add to Comparison")
        self._add_comparison_btn.clicked.connect(self._add_comparison)
        comparison_layout.addWidget(self._add_comparison_btn)
        
        self._clear_comparison_btn = QPushButton("Clear Comparison")
        self._clear_comparison_btn.clicked.connect(self._clear_comparison)
        comparison_layout.addWidget(self._clear_comparison_btn)
        
        self._comparison_list = QListWidget()
        comparison_layout.addWidget(self._comparison_list)
        
        control_layout.addWidget(comparison_group)
        
        # Export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        export_button_layout = QHBoxLayout()
        
        self._export_csv_btn = QPushButton("Export CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        export_button_layout.addWidget(self._export_csv_btn)
        
        self._export_hdf5_btn = QPushButton("Export HDF5")
        self._export_hdf5_btn.clicked.connect(self._export_hdf5)
        export_button_layout.addWidget(self._export_hdf5_btn)
        
        self._export_plot_btn = QPushButton("Export Plot")
        self._export_plot_btn.clicked.connect(self._export_plot)
        export_button_layout.addWidget(self._export_plot_btn)
        
        export_layout.addLayout(export_button_layout)
        
        control_layout.addWidget(export_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self._mean_label = QLabel("N/A")
        stats_layout.addRow("Mean:", self._mean_label)
        
        self._std_label = QLabel("N/A")
        stats_layout.addRow("Std Dev:", self._std_label)
        
        self._min_label = QLabel("N/A")
        stats_layout.addRow("Min:", self._min_label)
        
        self._max_label = QLabel("N/A")
        stats_layout.addRow("Max:", self._max_label)
        
        control_layout.addWidget(stats_group)
        
        control_layout.addStretch()
        
        splitter.addWidget(control_widget)
        
        # Right panel - Plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        if MATPLOTLIB_AVAILABLE:
            self._figure = Figure(figsize=(10, 6))
            self._canvas = FigureCanvas(self._figure)
            self._ax = self._figure.add_subplot(111)
            self._ax.set_title("Simulation Results")
            self._ax.set_xlabel("X")
            self._ax.set_ylabel("Y")
            self._ax.grid(True)
            plot_layout.addWidget(self._canvas)
        else:
            self._placeholder = QLabel("Matplotlib not available for plotting")
            self._placeholder.setAlignment(Qt.AlignCenter)
            plot_layout.addWidget(self._placeholder)
        
        # Data table
        self._data_table = QTableWidget()
        self._data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        plot_layout.addWidget(self._data_table)
        
        splitter.addWidget(plot_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
    
    def _load_hdf5(self):
        """Load data from HDF5 file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load HDF5 File", "", "HDF5 Files (*.h5 *.hdf5)"
        )
        
        if not filename:
            return
        
        try:
            with h5py.File(filename, 'r') as f:
                self._data.clear()
                self._data_list.clear()
                self._x_combo.clear()
                self._y_combo.clear()
                
                for key in f.keys():
                    if isinstance(f[key], h5py.Dataset):
                        data = f[key][:]
                        self._data[key] = data
                        self._data_list.addItem(key)
                        self._x_combo.addItem(key)
                        self._y_combo.addItem(key)
                
                self.data_loaded.emit(filename)
                self._update_data_table()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {e}")
    
    def _load_csv(self):
        """Load data from CSV file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load CSV File", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
                self._data.clear()
                self._data_list.clear()
                self._x_combo.clear()
                self._y_combo.clear()
                
                # Initialize data arrays
                for header in headers:
                    self._data[header] = []
                
                # Read data
                for row in reader:
                    for i, value in enumerate(row):
                        if i < len(headers):
                            try:
                                self._data[headers[i]].append(float(value))
                            except ValueError:
                                pass
                
                # Convert to numpy arrays
                for header in headers:
                    if self._data[header]:
                        self._data[header] = np.array(self._data[header])
                        self._data_list.addItem(header)
                        self._x_combo.addItem(header)
                        self._y_combo.addItem(header)
                
                self.data_loaded.emit(filename)
                self._update_data_table()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV file: {e}")
    
    def _on_selection_changed(self):
        """Handle data list selection change."""
        selected_items = self._data_list.selectedItems()
        if selected_items:
            # Update plot with selected data
            self._update_plot()
    
    def _update_plot(self):
        """Update the plot."""
        if not MATPLOTLIB_AVAILABLE or not self._data:
            return
        
        x_key = self._x_combo.currentText()
        y_key = self._y_combo.currentText()
        
        if not x_key or not y_key:
            return
        
        if x_key not in self._data or y_key not in self._data:
            return
        
        self._ax.clear()
        
        x_data = self._data[x_key]
        y_data = self._data[y_key]
        
        # Ensure same length
        min_len = min(len(x_data), len(y_data))
        x_data = x_data[:min_len]
        y_data = y_data[:min_len]
        
        plot_type = self._plot_type_combo.currentText()
        
        if plot_type == "Line":
            self._ax.plot(x_data, y_data, label=y_key)
        elif plot_type == "Scatter":
            self._ax.scatter(x_data, y_data, label=y_key)
        elif plot_type == "Bar":
            self._ax.bar(x_data, y_data, label=y_key)
        
        # Add comparison data
        for comp_name, comp_data in self._comparison_data.items():
            if x_key in comp_data and y_key in comp_data:
                comp_x = comp_data[x_key]
                comp_y = comp_data[y_key]
                min_len = min(len(comp_x), len(comp_y))
                self._ax.plot(comp_x[:min_len], comp_y[:min_len], '--', label=comp_name)
        
        self._ax.set_xlabel(x_key)
        self._ax.set_ylabel(y_key)
        self._ax.set_title(f"{y_key} vs {x_key}")
        
        if self._show_grid_check.isChecked():
            self._ax.grid(True)
        
        if self._show_legend_check.isChecked():
            self._ax.legend()
        
        self._canvas.draw()
        
        # Update statistics
        self._update_statistics(y_data)
    
    def _update_statistics(self, data: np.ndarray):
        """Update statistics display."""
        if len(data) == 0:
            return
        
        self._mean_label.setText(f"{np.mean(data):.6f}")
        self._std_label.setText(f"{np.std(data):.6f}")
        self._min_label.setText(f"{np.min(data):.6f}")
        self._max_label.setText(f"{np.max(data):.6f}")
    
    def _update_data_table(self):
        """Update data table."""
        if not self._data:
            return
        
        # Get all keys
        keys = list(self._data.keys())
        if not keys:
            return
        
        # Get max length
        max_len = max(len(self._data[k]) for k in keys)
        
        # Set table size
        self._data_table.setRowCount(min(max_len, 100))  # Limit to 100 rows
        self._data_table.setColumnCount(len(keys))
        self._data_table.setHorizontalHeaderLabels(keys)
        
        # Fill table
        for col, key in enumerate(keys):
            data = self._data[key]
            for row in range(min(len(data), 100)):
                self._data_table.setItem(row, col, QTableWidgetItem(f"{data[row]:.6f}"))
    
    def _add_comparison(self):
        """Add current data to comparison."""
        if not self._data:
            return
        
        name = f"Dataset {len(self._comparison_data) + 1}"
        self._comparison_data[name] = self._data.copy()
        self._comparison_list.addItem(name)
        self._update_plot()
    
    def _clear_comparison(self):
        """Clear all comparison data."""
        self._comparison_data.clear()
        self._comparison_list.clear()
        self._update_plot()
    
    def _export_csv(self):
        """Export data to CSV file."""
        if not self._data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write headers
                headers = list(self._data.keys())
                writer.writerow(headers)
                
                # Write data
                max_len = max(len(self._data[k]) for k in headers)
                for i in range(max_len):
                    row = []
                    for header in headers:
                        if i < len(self._data[header]):
                            row.append(self._data[header][i])
                        else:
                            row.append("")
                    writer.writerow(row)
                
                self.data_exported.emit(filename, "CSV")
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {e}")
    
    def _export_hdf5(self):
        """Export data to HDF5 file."""
        if not self._data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        if not HDF5_AVAILABLE:
            QMessageBox.warning(self, "Warning", "h5py not available")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export HDF5", "", "HDF5 Files (*.h5)"
        )
        
        if not filename:
            return
        
        try:
            with h5py.File(filename, 'w') as f:
                for key, data in self._data.items():
                    f.create_dataset(key, data=data)
            
            self.data_exported.emit(filename, "HDF5")
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export HDF5: {e}")
    
    def _export_plot(self):
        """Export plot to image file."""
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Warning", "Matplotlib not available")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Plot", "",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        
        if not filename:
            return
        
        try:
            self._figure.savefig(filename, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Plot exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export plot: {e}")
    
    def load_data(self, data: Dict[str, np.ndarray]):
        """Load data directly.
        
        Args:
            data: Dictionary of data arrays
        """
        self._data = data
        self._data_list.clear()
        self._x_combo.clear()
        self._y_combo.clear()
        
        for key in data.keys():
            self._data_list.addItem(key)
            self._x_combo.addItem(key)
            self._y_combo.addItem(key)
        
        self._update_data_table()
    
    def get_data(self) -> Dict[str, np.ndarray]:
        """Get current data."""
        return self._data
