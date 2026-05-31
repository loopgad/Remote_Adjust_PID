"""Model Configuration GUI Panel.

Provides interface for editing model parameters, managing presets,
and validating parameter values.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QGroupBox, QScrollArea, QMessageBox,
    QTabWidget, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from param_id_gui.core.types import (
    PMSMParams, BuckConverterParams, BoostConverterParams, FOCParams
)
from param_id_gui.utils.validation import InputValidator


class ParameterWidget(QWidget):
    """Widget for a single parameter with label, input, and validation."""
    
    value_changed = Signal(str, float)  # param_name, value
    
    def __init__(self, name: str, label: str, value: float = 0.0,
                 min_val: float = -1e6, max_val: float = 1e6,
                 decimals: int = 6, unit: str = "",
                 parent: Optional[QWidget] = None):
        """Initialize parameter widget.
        
        Args:
            name: Parameter name (internal)
            label: Display label
            value: Initial value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            decimals: Number of decimal places
            unit: Unit string
            parent: Parent widget
        """
        super().__init__(parent)
        self._name = name
        self._unit = unit
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Label
        self._label = QLabel(f"{label}:")
        self._label.setMinimumWidth(150)
        layout.addWidget(self._label)
        
        # Spin box
        self._spin_box = QDoubleSpinBox()
        self._spin_box.setRange(min_val, max_val)
        self._spin_box.setDecimals(decimals)
        self._spin_box.setValue(value)
        self._spin_box.setSingleStep(0.1)
        self._spin_box.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self._spin_box)
        
        # Unit label
        if unit:
            self._unit_label = QLabel(unit)
            self._unit_label.setMinimumWidth(30)
            layout.addWidget(self._unit_label)
    
    def _on_value_changed(self, value: float):
        """Handle value change."""
        self.value_changed.emit(self._name, value)
    
    def get_value(self) -> float:
        """Get current value."""
        return self._spin_box.value()
    
    def set_value(self, value: float):
        """Set value."""
        self._spin_box.setValue(value)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable the widget."""
        self._spin_box.setEnabled(enabled)


class ModelConfigPanel(QWidget):
    """Model configuration panel.
    
    Provides interface for editing model parameters with validation,
    presets, and error handling.
    """
    
    # Signals
    params_changed = Signal(str, dict)  # model_name, params_dict
    
    # Default presets
    PRESETS = {
        "PMSM": {
            "Default": PMSMParams(),
            "High Performance": PMSMParams(
                Rs=0.5, Ld=0.005, Lq=0.008,
                psi_f=0.15, J=0.005, B=0.005, p=4
            ),
            "Low Inertia": PMSMParams(
                Rs=1.0, Ld=0.002, Lq=0.003,
                psi_f=0.1, J=0.0005, B=0.001, p=2
            ),
        },
        "Buck Converter": {
            "Default": BuckConverterParams(),
            "High Voltage": BuckConverterParams(Vin=48.0, L=0.002, C=0.0002),
            "Low Voltage": BuckConverterParams(Vin=5.0, L=0.0005, C=0.00005),
        },
        "Boost Converter": {
            "Default": BoostConverterParams(),
            "High Boost": BoostConverterParams(Vin=3.3, L=0.002, C=0.0002),
            "Low Boost": BoostConverterParams(Vin=12.0, L=0.001, C=0.0001),
        },
        "FOC Controller": {
            "Default": FOCParams(),
            "Fast Response": FOCParams(
                current_kp=5.0, current_ki=500.0,
                speed_kp=2.0, speed_ki=50.0
            ),
            "Conservative": FOCParams(
                current_kp=0.5, current_ki=50.0,
                speed_kp=0.5, speed_ki=10.0
            ),
        },
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize model configuration panel."""
        super().__init__(parent)
        
        self._param_widgets: Dict[str, Dict[str, ParameterWidget]] = {}
        self._current_model = "PMSM"
        
        self._setup_ui()
        self._load_model_params("PMSM")
    
    def _setup_ui(self):
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        
        self._model_combo = QComboBox()
        self._model_combo.addItems(["PMSM", "Buck Converter", "Boost Converter", "FOC Controller"])
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self._model_combo)
        
        # Preset selection
        model_layout.addWidget(QLabel("Preset:"))
        
        self._preset_combo = QComboBox()
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        model_layout.addWidget(self._preset_combo)
        
        model_layout.addStretch()
        main_layout.addLayout(model_layout)
        
        # Parameter tabs
        self._param_tabs = QTabWidget()
        main_layout.addWidget(self._param_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.clicked.connect(self._apply_params)
        button_layout.addWidget(self._apply_btn)
        
        self._reset_btn = QPushButton("Reset")
        self._reset_btn.clicked.connect(self._reset_params)
        button_layout.addWidget(self._reset_btn)
        
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.clicked.connect(self._validate_params)
        button_layout.addWidget(self._validate_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self._status_label)
    
    def _on_model_changed(self, model_name: str):
        """Handle model selection change."""
        self._current_model = model_name
        self._update_preset_combo()
        self._load_model_params(model_name)
    
    def _update_preset_combo(self):
        """Update preset combo box for current model."""
        self._preset_combo.clear()
        if self._current_model in self.PRESETS:
            self._preset_combo.addItems(self.PRESETS[self._current_model].keys())
    
    def _on_preset_changed(self, preset_name: str):
        """Handle preset selection change."""
        if not preset_name:
            return
        
        if self._current_model in self.PRESETS:
            presets = self.PRESETS[self._current_model]
            if preset_name in presets:
                self._load_params_from_model(presets[preset_name])
    
    def _load_model_params(self, model_name: str):
        """Load parameters for specified model."""
        # Clear existing tabs
        self._param_tabs.clear()
        self._param_widgets.clear()
        
        # Create parameter widgets based on model
        if model_name == "PMSM":
            self._create_pmsm_params()
        elif model_name == "Buck Converter":
            self._create_buck_params()
        elif model_name == "Boost Converter":
            self._create_boost_params()
        elif model_name == "FOC Controller":
            self._create_foc_params()
        
        # Update preset combo
        self._update_preset_combo()
    
    def _create_pmsm_params(self):
        """Create PMSM parameter widgets."""
        # Electrical parameters
        electrical_widget = QWidget()
        electrical_layout = QFormLayout(electrical_widget)
        
        params = {
            "Rs": ("Stator Resistance", 0.8, 0.001, 100.0, "Ω"),
            "Ld": ("d-axis Inductance", 0.008, 0.0001, 1.0, "H"),
            "Lq": ("q-axis Inductance", 0.012, 0.0001, 1.0, "H"),
            "psi_f": ("Flux Linkage", 0.12, 0.001, 10.0, "Wb"),
        }
        
        self._param_widgets["PMSM"] = {}
        for name, (label, value, min_val, max_val, unit) in params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val, unit=unit)
            electrical_layout.addRow(widget)
            self._param_widgets["PMSM"][name] = widget
        
        self._param_tabs.addTab(electrical_widget, "Electrical")
        
        # Mechanical parameters
        mechanical_widget = QWidget()
        mechanical_layout = QFormLayout(mechanical_widget)
        
        mech_params = {
            "J": ("Rotor Inertia", 0.001, 0.0001, 1.0, "kg·m²"),
            "B": ("Friction Coefficient", 0.001, 0.0, 1.0, "N·m·s"),
            "p": ("Pole Pairs", 4, 1, 20, ""),
        }
        
        for name, (label, value, min_val, max_val, unit) in mech_params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val,
                                     decimals=4, unit=unit)
            mechanical_layout.addRow(widget)
            self._param_widgets["PMSM"][name] = widget
        
        self._param_tabs.addTab(mechanical_widget, "Mechanical")
    
    def _create_buck_params(self):
        """Create Buck converter parameter widgets."""
        params_widget = QWidget()
        params_layout = QFormLayout(params_widget)
        
        params = {
            "Vin": ("Input Voltage", 12.0, 1.0, 100.0, "V"),
            "L": ("Inductance", 0.001, 0.0001, 0.1, "H"),
            "C": ("Capacitance", 0.0001, 0.00001, 0.01, "F"),
            "R": ("ESR", 0.01, 0.001, 10.0, "Ω"),
            "Rl": ("Inductor Resistance", 0.05, 0.001, 10.0, "Ω"),
            "f_sw": ("Switching Freq", 100000, 1000, 1000000, "Hz"),
        }
        
        self._param_widgets["Buck Converter"] = {}
        for name, (label, value, min_val, max_val, unit) in params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val,
                                     decimals=6, unit=unit)
            params_layout.addRow(widget)
            self._param_widgets["Buck Converter"][name] = widget
        
        self._param_tabs.addTab(params_widget, "Parameters")
    
    def _create_boost_params(self):
        """Create Boost converter parameter widgets."""
        params_widget = QWidget()
        params_layout = QFormLayout(params_widget)
        
        params = {
            "Vin": ("Input Voltage", 5.0, 1.0, 100.0, "V"),
            "L": ("Inductance", 0.001, 0.0001, 0.1, "H"),
            "C": ("Capacitance", 0.0001, 0.00001, 0.01, "F"),
            "R": ("ESR", 0.01, 0.001, 10.0, "Ω"),
            "Rl": ("Inductor Resistance", 0.05, 0.001, 10.0, "Ω"),
            "f_sw": ("Switching Freq", 100000, 1000, 1000000, "Hz"),
        }
        
        self._param_widgets["Boost Converter"] = {}
        for name, (label, value, min_val, max_val, unit) in params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val,
                                     decimals=6, unit=unit)
            params_layout.addRow(widget)
            self._param_widgets["Boost Converter"][name] = widget
        
        self._param_tabs.addTab(params_widget, "Parameters")
    
    def _create_foc_params(self):
        """Create FOC controller parameter widgets."""
        # Current controller
        current_widget = QWidget()
        current_layout = QFormLayout(current_widget)
        
        current_params = {
            "current_kp": ("Current Kp", 1.0, 0.01, 100.0, ""),
            "current_ki": ("Current Ki", 100.0, 0.1, 10000.0, ""),
        }
        
        self._param_widgets["FOC Controller"] = {}
        for name, (label, value, min_val, max_val, unit) in current_params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val,
                                     decimals=4, unit=unit)
            current_layout.addRow(widget)
            self._param_widgets["FOC Controller"][name] = widget
        
        self._param_tabs.addTab(current_widget, "Current Controller")
        
        # Speed controller
        speed_widget = QWidget()
        speed_layout = QFormLayout(speed_widget)
        
        speed_params = {
            "speed_kp": ("Speed Kp", 0.5, 0.01, 100.0, ""),
            "speed_ki": ("Speed Ki", 10.0, 0.1, 10000.0, ""),
        }
        
        for name, (label, value, min_val, max_val, unit) in speed_params.items():
            widget = ParameterWidget(name, label, value, min_val, max_val,
                                     decimals=4, unit=unit)
            speed_layout.addRow(widget)
            self._param_widgets["FOC Controller"][name] = widget
        
        self._param_tabs.addTab(speed_widget, "Speed Controller")
    
    def _load_params_from_model(self, model):
        """Load parameters from a Pydantic model."""
        model_name = self._current_model
        if model_name not in self._param_widgets:
            return
        
        params_dict = model.model_dump()
        for name, widget in self._param_widgets[model_name].items():
            if name in params_dict:
                widget.set_value(params_dict[name])
    
    def _apply_params(self):
        """Apply current parameters."""
        model_name = self._current_model
        if model_name not in self._param_widgets:
            return
        
        params = {}
        for name, widget in self._param_widgets[model_name].items():
            params[name] = widget.get_value()
        
        # Validate parameters
        try:
            self._validate_current_params()
            self.params_changed.emit(model_name, params)
            self._status_label.setText("Parameters applied successfully")
            self._status_label.setStyleSheet("color: green;")
        except ValueError as e:
            self._status_label.setText(f"Validation error: {e}")
            self._status_label.setStyleSheet("color: red;")
    
    def _reset_params(self):
        """Reset parameters to default."""
        model_name = self._current_model
        if model_name in self.PRESETS:
            presets = self.PRESETS[model_name]
            if "Default" in presets:
                self._load_params_from_model(presets["Default"])
                self._status_label.setText("Parameters reset to default")
                self._status_label.setStyleSheet("color: gray;")
    
    def _validate_params(self):
        """Validate current parameters."""
        try:
            self._validate_current_params()
            self._status_label.setText("All parameters valid")
            self._status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "Validation", "All parameters are valid!")
        except ValueError as e:
            self._status_label.setText(f"Validation error: {e}")
            self._status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Validation Error", str(e))
    
    def _validate_current_params(self):
        """Validate current parameter values."""
        model_name = self._current_model
        if model_name not in self._param_widgets:
            return
        
        for name, widget in self._param_widgets[model_name].items():
            value = widget.get_value()
            
            # Basic validation
            if value != value:  # NaN check
                raise ValueError(f"Parameter '{name}' is NaN")
            
            # Model-specific validation
            if model_name == "PMSM":
                if name in ("Rs", "Ld", "Lq", "J", "B") and value <= 0:
                    raise ValueError(f"Parameter '{name}' must be positive")
                if name == "p" and value < 1:
                    raise ValueError(f"Parameter '{name}' must be >= 1")
            elif model_name in ("Buck Converter", "Boost Converter"):
                if name in ("L", "C") and value <= 0:
                    raise ValueError(f"Parameter '{name}' must be positive")
                if name == "Vin" and value <= 0:
                    raise ValueError(f"Parameter '{name}' must be positive")
    
    def get_current_params(self) -> Dict[str, float]:
        """Get current parameter values."""
        model_name = self._current_model
        if model_name not in self._param_widgets:
            return {}
        
        params = {}
        for name, widget in self._param_widgets[model_name].items():
            params[name] = widget.get_value()
        
        return params
