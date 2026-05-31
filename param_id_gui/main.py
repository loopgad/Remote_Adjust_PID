"""Application entry point for param_id_gui."""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for the application."""
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
        from PySide6.QtCore import Qt
        
        app = QApplication(sys.argv)
        
        # Create main window
        window = QMainWindow()
        window.setWindowTitle("High-Precision Parameter Identification")
        window.setMinimumSize(800, 600)
        
        # Add a simple label for now
        label = QLabel("Welcome to High-Precision Parameter Identification Software")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        window.setCentralWidget(label)
        
        window.show()
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install PySide6: pip install PySide6")
        sys.exit(1)


if __name__ == "__main__":
    main()
