"""PySide6 main window for the parameter identification application."""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QLabel, QToolBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from param_id_gui.gui.panels import (
    ModelConfigPanel,
    SimulationPanel,
    ParamIDPanel,
    ResultsPanel,
)


class MainWindow(QMainWindow):
    """Main window for the parameter identification application.
    
    This class provides the main application window with menu bar,
    toolbar, status bar, and tabbed interface for different panels.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("High-Precision Parameter Identification")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and layout
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        self._layout = QVBoxLayout(self._central_widget)
        
        # Create tab widget
        self._tab_widget = QTabWidget()
        self._layout.addWidget(self._tab_widget)
        
        # Setup UI components
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_panels()
        
        # Setup timer for status updates
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)  # Update every second
    
    def _setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("Simulation")
        
        start_action = QAction("Start", self)
        start_action.setShortcut("F5")
        sim_menu.addAction(start_action)
        
        pause_action = QAction("Pause", self)
        pause_action.setShortcut("F6")
        sim_menu.addAction(pause_action)
        
        stop_action = QAction("Stop", self)
        stop_action.setShortcut("F7")
        sim_menu.addAction(stop_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        new_action = QAction("New", self)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        start_action = QAction("Start", self)
        toolbar.addAction(start_action)
        
        pause_action = QAction("Pause", self)
        toolbar.addAction(pause_action)
        
        stop_action = QAction("Stop", self)
        toolbar.addAction(stop_action)
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        # Add permanent widgets
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)
        
        self._time_label = QLabel("Time: 0.000 s")
        self._status_bar.addPermanentWidget(self._time_label)
    
    def _setup_panels(self):
        """Setup the tabbed panels."""
        # Model Configuration Panel
        self._model_config_panel = ModelConfigPanel()
        self._tab_widget.addTab(self._model_config_panel, "Model Configuration")
        
        # Simulation Panel
        self._simulation_panel = SimulationPanel()
        self._tab_widget.addTab(self._simulation_panel, "Simulation")
        
        # Parameter Identification Panel
        self._param_id_panel = ParamIDPanel()
        self._tab_widget.addTab(self._param_id_panel, "Parameter Identification")
        
        # Results Panel
        self._results_panel = ResultsPanel()
        self._tab_widget.addTab(self._results_panel, "Results")
    
    def _update_status(self):
        """Update status bar information."""
        # This will be connected to the orchestrator later
        pass
    
    def add_panel(self, name: str, widget: QWidget):
        """Add a new panel to the tab widget.
        
        Args:
            name: Panel name
            widget: Panel widget
        """
        self._tab_widget.addTab(widget, name)
    
    def set_status(self, message: str):
        """Set status bar message.
        
        Args:
            message: Status message
        """
        self._status_label.setText(message)
    
    def set_time(self, time: float):
        """Set time display in status bar.
        
        Args:
            time: Current simulation time in seconds
        """
        self._time_label.setText(f"Time: {time:.3f} s")
