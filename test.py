import sys
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class PID:
    def __init__(self, kp=1.0, ki=0.1, kd=0.01):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = 0
        self.last_error = 0
        self.integral = 0

    def compute(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.last_error = error
        return output

class PIDControllerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.pid = PID()
        self.time_data = []
        self.measurements = []
        self.initial_measurement = 0

        # Initialize Serial
        self.serial_port = serial.Serial('COM9', 115200, timeout=1)

        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate)
        self.timer.start(100)
        self.current_time = 0

    def initUI(self):
        self.setWindowTitle('PID Controller Tuning')
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()

        # PID Parameters Sliders
        self.kp_slider = QSlider(Qt.Horizontal, self)
        self.kp_slider.setRange(0, 100)
        self.kp_slider.setValue(int(self.pid.kp * 10))
        self.kp_slider.valueChanged.connect(self.update_kp)
        layout.addWidget(QLabel('Kp:'))
        layout.addWidget(self.kp_slider)

        self.ki_slider = QSlider(Qt.Horizontal, self)
        self.ki_slider.setRange(0, 100)
        self.ki_slider.setValue(int(self.pid.ki * 10))
        self.ki_slider.valueChanged.connect(self.update_ki)
        layout.addWidget(QLabel('Ki:'))
        layout.addWidget(self.ki_slider)

        self.kd_slider = QSlider(Qt.Horizontal, self)
        self.kd_slider.setRange(0, 100)
        self.kd_slider.setValue(int(self.pid.kd * 10))
        self.kd_slider.valueChanged.connect(self.update_kd)
        layout.addWidget(QLabel('Kd:'))
        layout.addWidget(self.kd_slider)

        self.setpoint_input = QLineEdit(self)
        self.setpoint_input.setText(str(self.pid.setpoint))
        self.setpoint_input.textChanged.connect(self.update_setpoint)
        layout.addWidget(QLabel('Setpoint:'))
        layout.addWidget(self.setpoint_input)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Setpoint and Feedback Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Value')
        self.setLayout(layout)

    @pyqtSlot(int)
    def update_kp(self, value):
        self.pid.kp = value / 10.0
        self.send_parameters()

    @pyqtSlot(int)
    def update_ki(self, value):
        self.pid.ki = value / 10.0
        self.send_parameters()

    @pyqtSlot(int)
    def update_kd(self, value):
        self.pid.kd = value / 10.0
        self.send_parameters()

    @pyqtSlot(str)
    def update_setpoint(self, text):
        try:
            setpoint = float(text)
            self.pid.setpoint = setpoint
            self.send_parameters()
        except ValueError:
            pass

    def send_parameters(self):
        parameters = f"{self.pid.setpoint},{self.pid.kp},{self.pid.ki},{self.pid.kd}\n"
        self.serial_port.write(parameters.encode())

    def simulate(self):
        dt = 0.1
        measurement = self.initial_measurement

        output = self.pid.compute(measurement, dt)
        new_measurement = measurement + output * dt
        self.current_time += dt

        self.time_data.append(self.current_time)
        self.measurements.append(new_measurement)

        if len(self.time_data) > 500:
            self.time_data = self.time_data[-500:]
            self.measurements = self.measurements[-500:]

        self.update_plot()
        self.receive_feedback()

    def update_plot(self):
        self.ax.clear()
        self.ax.plot(self.time_data, self.measurements, label='Feedback', color='blue')
        self.ax.axhline(y=self.pid.setpoint, color='red', linestyle='--', label='Setpoint')
        self.ax.set_title('Setpoint and Feedback Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Value')
        self.ax.legend()
        self.canvas.draw()

    def receive_feedback(self):
        if self.serial_port.in_waiting:
            feedback = self.serial_port.readline().decode().strip()
            try:
                self.initial_measurement = float(feedback)
            except ValueError:
                pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PIDControllerApp()
    ex.show()
    sys.exit(app.exec_())
