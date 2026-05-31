"""Application entry point for param_id_gui."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for the application."""
    try:
        from PySide6.QtWidgets import QApplication
        from param_id_gui.gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install PySide6: pip install PySide6")
        sys.exit(1)


if __name__ == "__main__":
    main()
