import sys
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Constants for serial communication and UI
SERIAL_PORT = 'COM9'  # Replace with actual serial port
BAUD_RATE = 115200  # Replace with actual baud rate
SLIDER_RANGE = (0, 100)
INITIAL_SLIDER_VALUE = 50
PID_SLIDER_RANGE = (0, 100)
PID_INITIAL_VALUE = 10

class SerialThread(QThread):
    """Handles serial communication in a separate thread."""
    feedback_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.running = True
        self.ser = None
        self.initialize_serial()

    def initialize_serial(self):
        """Initialize the serial port."""
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
        except serial.SerialException as e:
            print(f"Serial port initialization error: {e}")

    def run(self):
        """Continuously read data from the serial port and emit feedback_signal."""
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.readline()
                    if data:
                        feedback = float(data.decode('utf-8').strip())
                        self.feedback_signal.emit(feedback)
            except serial.SerialException as e:
                print(f"Serial communication error: {e}")
                self.initialize_serial()  # Try to reinitialize serial port
            except ValueError:
                print("Invalid data received")
                continue

    def stop(self):
        """Stop the thread and close the serial port."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_setpoint(self, setpoint,kp,ki,kd):
        """Send the target setpoint value via serial communication."""
        if self.ser and self.ser.is_open:
            try:
                message = f'{setpoint:.2f}\t{kp:.2f}\t{ki:.2f}\t{kd:.2f}\t'
                self.ser.write(message.encode('utf-8'))
            except serial.SerialException as e:
                print(f"Failed to send setpoint: {e}")

class PIDControllerApp(QWidget):
    """Main application window for PID controller tuning."""
    def __init__(self):
        super().__init__()
        self.initUI()

        # Start the serial thread for communication
        self.serial_thread = SerialThread()
        self.serial_thread.feedback_signal.connect(self.update_feedback)
        self.serial_thread.start()

        # Initialize data storage
        self.feedback_data = []
        self.time_data = []
        self.last_time = 0
        self.target = 0
        self.kp = 0
        self.ki = 0
        self.kd = 0

    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle('PID Controller Tuning')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Target Value Slider
        self.target_label = QLabel('Target Value:')
        layout.addWidget(self.target_label)
        self.target_slider = QSlider(Qt.Horizontal)
        self.target_slider.setRange(*SLIDER_RANGE)
        self.target_slider.setValue(INITIAL_SLIDER_VALUE)
        self.target_slider.valueChanged.connect(self.update_target)
        layout.addWidget(self.target_slider)

        # PID Parameters Sliders and Inputs
        self.create_pid_controls('Kp', self.update_kp, layout)
        self.create_pid_controls('Ki', self.update_ki, layout)
        self.create_pid_controls('Kd', self.update_kd, layout)

        self.feedback_label = QLabel('Feedback Data:')
        layout.addWidget(self.feedback_label)

        # Create matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Feedback Data Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Feedback')

        self.setLayout(layout)

    def create_pid_controls(self, name1, update_function, layout):
        """Helper method to create and add PID sliders and input boxes."""
        pid_layout = QHBoxLayout()

        # Slider
        slider_label = QLabel(f'{name1}:')
        pid_layout.addWidget(slider_label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(*PID_SLIDER_RANGE)
        slider.setValue(PID_INITIAL_VALUE)
        slider.valueChanged.connect(lambda value, name=name1: self.slider_changed(value, name, update_function))
        pid_layout.addWidget(slider)

        # Input Box
        input_box = QLineEdit()
        input_box.setText(f'{PID_INITIAL_VALUE / 10.0:.2f}')
        input_box.setMaxLength(5)
        input_box.textChanged.connect(lambda text, name=name1: self.input_changed(text, name, slider, update_function))
        pid_layout.addWidget(input_box)

        layout.addLayout(pid_layout)

        # Store references to sliders and input boxes for updates
        setattr(self, f'{name1.lower()}_slider', slider)
        setattr(self, f'{name1.lower()}_input', input_box)

    def slider_changed(self, value, name, update_function):
        """Update input box and send value when slider changes."""
        value = value / 10.0
        input_box = getattr(self, f'{name.lower()}_input')
        input_box.setText(f'{value:.2f}')
        update_function(value)

    def input_changed(self, text, name, slider, update_function):
        """Update slider and send value when input box changes."""
        try:
            value = float(text)
            slider.setValue(int(value * 10))
            update_function(value)
        except ValueError:
            pass  # Ignore invalid inputs

    def update_target(self, value):
        """Update target value based on slider input and send it via serial."""
        self.target = value
        self.serial_thread.send_setpoint(self.target,self.kp,self.ki,self.kd)

    def update_kp(self, value):
        """Update Kp parameter based on slider input and print the new value."""
        self.kp = value
        print(f'Updated Kp: {self.kp:.2f}')
        self.serial_thread.send_setpoint(self.target,self.kp,self.ki,self.kd)

    def update_ki(self, value):
        """Update Ki parameter based on slider input and print the new value."""
        self.ki = value
        print(f'Updated Ki: {self.ki:.2f}')
        self.serial_thread.send_setpoint(self.target,self.kp,self.ki,self.kd)

    def update_kd(self, value):
        """Update Kd parameter based on slider input and print the new value."""
        self.kd = value
        print(f'Updated Kd: {self.kd:.2f}')
        self.serial_thread.send_setpoint(self.target,self.kp,self.ki,self.kd)

    def update_feedback(self, feedback):
        """Update the feedback data and plot it."""
        current_time = len(self.feedback_data)

        # Append feedback data
        self.feedback_data.append(feedback)
        self.time_data.append(current_time)

        # Clear and update the plot
        self.ax.clear()
        self.ax.plot(self.time_data, self.feedback_data, label='Feedback')
        self.ax.set_title('Feedback Data Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Feedback')
        self.ax.legend()

        # Auto scale y-axis
        self.ax.relim()
        self.ax.autoscale_view()

        # Refresh the canvas
        self.canvas.draw()

    def closeEvent(self, event):
        """Handle window close event to stop the serial thread."""
        self.serial_thread.stop()
        self.serial_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PIDControllerApp()
    ex.show()
    sys.exit(app.exec_())
