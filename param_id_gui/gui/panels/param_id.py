"""Parameter Identification GUI Panel.

Provides interface for defining objective functions, selecting algorithms,
and displaying identification results.
"""

from typing import Optional, Dict, Any, Callable
import threading
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QComboBox,
    QDoubleSpinBox, QSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSplitter, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread


class OptimizationWorker(QThread):
    """Worker thread for running optimization."""
    
    progress_updated = Signal(int, float)  # iteration, cost
    optimization_finished = Signal(dict)  # results
    optimization_error = Signal(str)  # error message
    
    def __init__(self, algorithm: str, params: Dict[str, Any],
                 objective_fn: Callable, initial_guess: np.ndarray):
        """Initialize optimization worker.
        
        Args:
            algorithm: Algorithm name ("LM" or "PSO")
            params: Algorithm parameters
            objective_fn: Objective function
            initial_guess: Initial parameter guess
        """
        super().__init__()
        self._algorithm = algorithm
        self._params = params
        self._objective_fn = objective_fn
        self._initial_guess = initial_guess
        self._stop_event = threading.Event()
    
    def run(self):
        """Run optimization."""
        self._stop_event.clear()
        
        try:
            if self._algorithm == "LM":
                self._run_lm()
            elif self._algorithm == "PSO":
                self._run_pso()
            else:
                self.optimization_error.emit(f"Unknown algorithm: {self._algorithm}")
        except Exception as e:
            self.optimization_error.emit(str(e))
        finally:
            self._stop_event.set()
    
    def _run_lm(self):
        """Run Levenberg-Marquardt optimization."""
        from param_id_gui.core.optimization_service import OptimizationService
        from param_id_gui.core.types import LMConfig

        config = LMConfig(
            max_iterations=self._params.get("max_iter", 100),
            tolerance=self._params.get("tol", 1e-6),
            lambda_init=self._params.get("lambda_init", 0.001)
        )

        def callback(iteration, cost, params):
            self.progress_updated.emit(iteration, cost)
            return not self._stop_event.is_set()

        x, info = OptimizationService.run_lm(
            config=config,
            residual_fn=self._objective_fn,
            x0=self._initial_guess,
            progress_callback=callback,
        )
        
        self.optimization_finished.emit({
            "algorithm": "LM",
            "params": x.tolist(),
            "cost": info["final_cost"],
            "iterations": info["iterations"],
            "converged": info["converged"],
        })
    
    def _run_pso(self):
        """Run Particle Swarm Optimization."""
        from param_id_gui.core.optimization_service import OptimizationService
        from param_id_gui.core.types import PSOConfig

        config = PSOConfig(
            n_particles=self._params.get("n_particles", 30),
            max_iterations=self._params.get("max_iter", 100),
            w=self._params.get("w", 0.7),
            c1=self._params.get("c1", 1.5),
            c2=self._params.get("c2", 1.5)
        )

        def callback(iteration, cost, params):
            self.progress_updated.emit(iteration, cost)
            return not self._stop_event.is_set()

        bounds = self._params.get("bounds", None)
        if bounds is None:
            self.optimization_error.emit("PSO requires bounds")
            return
        
        bounds_arr = (
            np.array([b[0] for b in bounds]),
            np.array([b[1] for b in bounds]),
        )
        x, info = OptimizationService.run_pso(
            config=config,
            objective_fn=self._objective_fn,
            bounds=bounds_arr,
            x0=self._initial_guess,
            progress_callback=callback,
        )
        
        self.optimization_finished.emit({
            "algorithm": "PSO",
            "params": x.tolist(),
            "cost": info["final_cost"],
            "iterations": info["iterations"],
            "converged": info["converged"],
        })
    
    def stop(self):
        """Stop optimization."""
        self._stop_event.set()


class ParamIDPanel(QWidget):
    """Parameter identification panel.
    
    Provides interface for defining objective functions, selecting algorithms,
    and displaying identification results.
    """
    
    # Signals
    identification_started = Signal(str, dict)  # algorithm, params
    identification_finished = Signal(dict)  # results
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize parameter identification panel."""
        super().__init__(parent)
        
        self._worker: Optional[OptimizationWorker] = None
        self._objective_fn: Optional[Callable] = None
        self._results: Optional[Dict] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for config and results
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Configuration
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Algorithm selection
        algo_group = QGroupBox("Algorithm Selection")
        algo_layout = QFormLayout(algo_group)
        
        self._algo_combo = QComboBox()
        self._algo_combo.addItems(["LM (Levenberg-Marquardt)", "PSO (Particle Swarm)"])
        self._algo_combo.currentIndexChanged.connect(self._on_algorithm_changed)
        algo_layout.addRow("Algorithm:", self._algo_combo)
        
        config_layout.addWidget(algo_group)
        
        # Algorithm parameters
        self._algo_params_group = QGroupBox("Algorithm Parameters")
        self._algo_params_layout = QFormLayout(self._algo_params_group)
        
        # LM parameters
        self._max_iter_spin = QSpinBox()
        self._max_iter_spin.setRange(1, 10000)
        self._max_iter_spin.setValue(100)
        self._algo_params_layout.addRow("Max Iterations:", self._max_iter_spin)
        
        self._tol_spin = QDoubleSpinBox()
        self._tol_spin.setRange(1e-12, 1.0)
        self._tol_spin.setValue(1e-6)
        self._tol_spin.setDecimals(12)
        self._algo_params_layout.addRow("Tolerance:", self._tol_spin)
        
        self._lambda_spin = QDoubleSpinBox()
        self._lambda_spin.setRange(1e-10, 1000.0)
        self._lambda_spin.setValue(0.001)
        self._lambda_spin.setDecimals(10)
        self._algo_params_layout.addRow("Lambda (LM):", self._lambda_spin)
        
        # PSO parameters
        self._n_particles_spin = QSpinBox()
        self._n_particles_spin.setRange(5, 1000)
        self._n_particles_spin.setValue(30)
        self._algo_params_layout.addRow("Particles (PSO):", self._n_particles_spin)
        
        self._w_spin = QDoubleSpinBox()
        self._w_spin.setRange(0.0, 2.0)
        self._w_spin.setValue(0.7)
        self._w_spin.setDecimals(3)
        self._algo_params_layout.addRow("Inertia Weight:", self._w_spin)
        
        self._c1_spin = QDoubleSpinBox()
        self._c1_spin.setRange(0.0, 5.0)
        self._c1_spin.setValue(1.5)
        self._c1_spin.setDecimals(3)
        self._algo_params_layout.addRow("c1 (PSO):", self._c1_spin)
        
        self._c2_spin = QDoubleSpinBox()
        self._c2_spin.setRange(0.0, 5.0)
        self._c2_spin.setValue(1.5)
        self._c2_spin.setDecimals(3)
        self._algo_params_layout.addRow("c2 (PSO):", self._c2_spin)
        
        config_layout.addWidget(self._algo_params_group)
        
        # Initial parameters
        init_group = QGroupBox("Initial Parameters")
        init_layout = QVBoxLayout(init_group)
        
        self._init_params_table = QTableWidget(4, 3)
        self._init_params_table.setHorizontalHeaderLabels(["Parameter", "Initial Value", "Bounds"])
        self._init_params_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Default parameters
        default_params = ["Rs", "Ld", "Lq", "flux_pm"]
        for i, param in enumerate(default_params):
            self._init_params_table.setItem(i, 0, QTableWidgetItem(param))
            self._init_params_table.setItem(i, 1, QTableWidgetItem("0.0"))
            self._init_params_table.setItem(i, 2, QTableWidgetItem("[-100, 100]"))
        
        init_layout.addWidget(self._init_params_table)
        
        # Buttons for parameter management
        param_button_layout = QHBoxLayout()
        
        self._add_param_btn = QPushButton("Add Parameter")
        self._add_param_btn.clicked.connect(self._add_parameter)
        param_button_layout.addWidget(self._add_param_btn)
        
        self._remove_param_btn = QPushButton("Remove Selected")
        self._remove_param_btn.clicked.connect(self._remove_parameter)
        param_button_layout.addWidget(self._remove_param_btn)
        
        init_layout.addLayout(param_button_layout)
        config_layout.addWidget(init_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self._start_btn = QPushButton("Start Identification")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.clicked.connect(self._on_start)
        control_layout.addWidget(self._start_btn)
        
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("dangerButton")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        control_layout.addWidget(self._stop_btn)
        
        config_layout.addLayout(control_layout)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        progress_layout.addWidget(self._progress_bar)
        
        self._progress_label = QLabel("Ready")
        progress_layout.addWidget(self._progress_label)
        
        config_layout.addWidget(progress_group)
        
        config_layout.addStretch()
        
        splitter.addWidget(config_widget)
        
        # Right panel - Results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Results display
        results_group = QGroupBox("Results")
        results_layout_inner = QVBoxLayout(results_group)
        
        self._results_table = QTableWidget(4, 4)
        self._results_table.setHorizontalHeaderLabels([
            "Parameter", "Identified", "Initial", "Error %"
        ])
        self._results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout_inner.addWidget(self._results_table)
        
        # Summary
        summary_layout = QFormLayout()
        
        self._cost_label = QLabel("N/A")
        summary_layout.addRow("Final Cost:", self._cost_label)
        
        self._iterations_label = QLabel("N/A")
        summary_layout.addRow("Iterations:", self._iterations_label)
        
        self._converged_label = QLabel("N/A")
        summary_layout.addRow("Converged:", self._converged_label)
        
        self._algorithm_label = QLabel("N/A")
        summary_layout.addRow("Algorithm:", self._algorithm_label)
        
        results_layout_inner.addLayout(summary_layout)
        
        results_layout.addWidget(results_group)
        
        # Log output
        log_group = QGroupBox("Optimization Log")
        log_layout = QVBoxLayout(log_group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(200)
        log_layout.addWidget(self._log_text)
        
        results_layout.addWidget(log_group)
        
        # Export button
        export_layout = QHBoxLayout()
        
        self._export_btn = QPushButton("Export Results")
        self._export_btn.clicked.connect(self._export_results)
        export_layout.addWidget(self._export_btn)
        
        self._export_btn.setEnabled(False)
        
        results_layout.addLayout(export_layout)
        
        splitter.addWidget(results_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Update algorithm parameters visibility
        self._on_algorithm_changed(0)
    
    def _on_algorithm_changed(self, index: int):
        """Handle algorithm selection change."""
        is_lm = index == 0
        
        # Show/hide LM-specific parameters (including labels)
        for widget in (self._lambda_spin,):
            label = self._algo_params_layout.labelForField(widget)
            if label:
                label.setVisible(is_lm)
            widget.setVisible(is_lm)
            widget.setEnabled(is_lm)
        
        # Show/hide PSO-specific parameters (including labels)
        for widget in (self._n_particles_spin, self._w_spin, self._c1_spin, self._c2_spin):
            label = self._algo_params_layout.labelForField(widget)
            if label:
                label.setVisible(not is_lm)
            widget.setVisible(not is_lm)
            widget.setEnabled(not is_lm)
    
    def _add_parameter(self):
        """Add a new parameter row."""
        row = self._init_params_table.rowCount()
        self._init_params_table.insertRow(row)
        self._init_params_table.setItem(row, 0, QTableWidgetItem(f"param_{row}"))
        self._init_params_table.setItem(row, 1, QTableWidgetItem("0.0"))
        self._init_params_table.setItem(row, 2, QTableWidgetItem("[-100, 100]"))
    
    def _remove_parameter(self):
        """Remove selected parameter row."""
        current_row = self._init_params_table.currentRow()
        if current_row >= 0:
            self._init_params_table.removeRow(current_row)
    
    def _on_start(self):
        """Handle start button click."""
        # Get initial parameters
        initial_guess = []
        for row in range(self._init_params_table.rowCount()):
            item = self._init_params_table.item(row, 1)
            if item:
                try:
                    value = float(item.text())
                    initial_guess.append(value)
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Invalid value in row {row}")
                    return
        
        if not initial_guess:
            QMessageBox.warning(self, "Error", "No parameters defined")
            return
        
        initial_guess = np.array(initial_guess)
        
        # Get algorithm parameters
        algo_index = self._algo_combo.currentIndex()
        algorithm = "LM" if algo_index == 0 else "PSO"
        
        params = {
            "max_iter": self._max_iter_spin.value(),
            "tol": self._tol_spin.value(),
        }
        
        if algorithm == "LM":
            params["lambda_init"] = self._lambda_spin.value()
        else:
            params["n_particles"] = self._n_particles_spin.value()
            params["w"] = self._w_spin.value()
            params["c1"] = self._c1_spin.value()
            params["c2"] = self._c2_spin.value()
        
        # Get bounds
        bounds = []
        for row in range(self._init_params_table.rowCount()):
            item = self._init_params_table.item(row, 2)
            if item:
                try:
                    # Parse bounds string like "[-100, 100]"
                    bounds_str = item.text().strip("[]")
                    parts = bounds_str.split(",")
                    if len(parts) != 2:
                        raise ValueError("Expected two values")
                    low, high = map(float, parts)
                    if low > high:
                        raise ValueError("Lower bound > upper bound")
                    bounds.append((low, high))
                except (ValueError, AttributeError):
                    bounds.append((-100, 100))
            else:
                bounds.append((-100, 100))
        
        if algorithm == "PSO":
            params["bounds"] = bounds
        
        # Check if objective function is set
        if self._objective_fn is None:
            QMessageBox.warning(self, "Error", "No objective function set")
            return
        
        # Start optimization
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._log_text.clear()
        self._log_text.append(f"Starting {algorithm} optimization...")
        
        self.identification_started.emit(algorithm, params)
        
        # Stop old worker if still running
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            if not self._worker.wait(3000):
                self._worker.terminate()
                self._worker.wait()
            self._worker.deleteLater()
            self._worker = None
        
        self._worker = OptimizationWorker(
            algorithm, params, self._objective_fn, initial_guess
        )
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.optimization_finished.connect(self._on_finished)
        self._worker.optimization_error.connect(self._on_error)
        self._worker.start()
    
    def _on_stop(self):
        """Handle stop button click."""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._log_text.append("Optimization stopped by user")
    
    def _on_progress(self, iteration: int, cost: float):
        """Handle progress update."""
        self._progress_label.setText(f"Iteration {iteration}, Cost: {cost:.6f}")
        self._log_text.append(f"Iteration {iteration}: cost = {cost:.6f}")

        # Update progress bar
        max_iter = self._max_iter_spin.value()
        if max_iter > 0:
            pct = min(int(iteration / max_iter * 100), 100)
            self._progress_bar.setValue(pct)

        # Limit log to last 1000 lines
        doc = self._log_text.document()
        if doc.blockCount() > 1000:
            cursor = self._log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, doc.blockCount() - 1000)
            cursor.removeSelectedText()

        # Auto-scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_finished(self, results: Dict):
        """Handle optimization finished."""
        self._results = results
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._export_btn.setEnabled(True)
        
        # Clean up worker
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        
        # Update summary
        self._cost_label.setText(f"{results['cost']:.6f}")
        self._iterations_label.setText(str(results['iterations']))
        self._converged_label.setText("Yes" if results['converged'] else "No")
        self._algorithm_label.setText(results['algorithm'])
        
        # Update results table
        identified_params = results['params']
        for row in range(min(len(identified_params), self._results_table.rowCount())):
            # Parameter name
            param_item = self._init_params_table.item(row, 0)
            if param_item:
                self._results_table.setItem(row, 0, QTableWidgetItem(param_item.text()))
            
            # Identified value
            self._results_table.setItem(row, 1, QTableWidgetItem(f"{identified_params[row]:.6f}"))
            
            # Initial value
            init_item = self._init_params_table.item(row, 1)
            if init_item:
                self._results_table.setItem(row, 2, QTableWidgetItem(init_item.text()))
                
                # Error percentage
                try:
                    initial = float(init_item.text())
                    if initial != 0:
                        error_pct = abs(identified_params[row] - initial) / abs(initial) * 100
                        self._results_table.setItem(row, 3, QTableWidgetItem(f"{error_pct:.2f}%"))
                except (ValueError, ZeroDivisionError, TypeError):
                    pass
        
        self._log_text.append(f"\nOptimization finished!")
        self._log_text.append(f"Final cost: {results['cost']:.6f}")
        self._log_text.append(f"Iterations: {results['iterations']}")
        self._log_text.append(f"Converged: {results['converged']}")
        
        self.identification_finished.emit(results)
    
    def _on_error(self, error_msg: str):
        """Handle optimization error."""
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        
        # Clean up worker
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        
        self._log_text.append(f"\nError: {error_msg}")
        QMessageBox.critical(self, "Optimization Error", error_msg)
    
    def _export_results(self):
        """Export optimization results to CSV."""
        if self._results is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            import csv
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Parameter", "Identified", "Initial", "Error %"])
                params = self._results.get("params", [])
                for i, val in enumerate(params):
                    param_name = self._init_params_table.item(i, 0).text() if i < self._init_params_table.rowCount() else f"param_{i}"
                    init_item = self._init_params_table.item(i, 1)
                    initial = float(init_item.text()) if init_item else 0.0
                    error_pct = abs(val - initial) / abs(initial) * 100 if initial != 0 else 0.0
                    writer.writerow([param_name, f"{val:.6f}", f"{initial:.6f}", f"{error_pct:.2f}"])
                writer.writerow([])
                writer.writerow(["Final Cost", self._results.get("cost", "N/A")])
                writer.writerow(["Iterations", self._results.get("iterations", "N/A")])
                writer.writerow(["Converged", self._results.get("converged", "N/A")])
            QMessageBox.information(self, "Export", f"Results exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{e}")
    
    def set_objective_function(self, fn: Callable):
        """Set the objective function for optimization."""
        self._objective_fn = fn
    
    def get_results(self) -> Optional[Dict]:
        """Get optimization results."""
        return self._results
