import sys
import numpy as np
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import time

# Enable OpenGL for hardware acceleration
pg.setConfigOption('useOpenGL', True)

# Constants for UI
SLIDER_RANGE = (0, 100)
INITIAL_SLIDER_VALUE = 50
PID_SLIDER_RANGE = (0, 1000)
PID_INITIAL_VALUE = 10
UPDATE_INTERVAL = 1  # Update every 1 ms
SMOOTHING_WINDOW = 5  # Size of the smoothing window


class PIDControllerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.feedback_data = []
        self.target_data = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pid)
        self.running = False

        # Initialize PID parameters
        self.kp = PID_INITIAL_VALUE / 10.0
        self.ki = PID_INITIAL_VALUE / 10.0
        self.kd = PID_INITIAL_VALUE / 10.0
        self.previous_error = 0
        self.integral = 0
        self.target = 0

        # For frame rate calculation
        self.frame_count = 0
        self.start_time = time.time()

    def initUI(self):
        self.setWindowTitle('PID Controller Tuning')
        self.setGeometry(200, 200, 1000, 700)

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

        # Frame Rate Label
        self.fps_label = QLabel('FPS: 0')
        layout.addWidget(self.fps_label)

        # Start/Stop Button
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.start_button)

        # Create pyqtgraph plot
        self.plot_widget = pg.PlotWidget(title='Feedback and Target Data Over Time')
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setBackground('w')  # Set background to white
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

    def create_pid_controls(self, name, update_function, layout):
        pid_layout = QHBoxLayout()

        slider_label = QLabel(f'{name}:')
        pid_layout.addWidget(slider_label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(*PID_SLIDER_RANGE)
        slider.setValue(PID_INITIAL_VALUE)
        slider.valueChanged.connect(lambda value, func=update_function: self.slider_changed(value, func, name))
        pid_layout.addWidget(slider)

        input_box = QLineEdit()
        input_box.setText(f'{PID_INITIAL_VALUE / 10.0:.2f}')
        input_box.setMaxLength(5)
        input_box.textChanged.connect(lambda text, func=update_function, s=slider: self.input_changed(text, func, s))
        pid_layout.addWidget(input_box)

        layout.addLayout(pid_layout)

        setattr(self, f'{name.lower()}_slider', slider)
        setattr(self, f'{name.lower()}_input', input_box)

    def slider_changed(self, value, update_function, name):
        value /= 10.0
        input_box = getattr(self, f'{name.lower()}_input')
        input_box.setText(f'{value:.2f}')
        update_function(value)

    def input_changed(self, text, update_function, slider):
        try:
            value = float(text)
            slider.setValue(int(value * 10))
            update_function(value)
        except ValueError:
            pass

    def toggle_timer(self):
        if not self.running:
            self.running = True
            self.timer.start(UPDATE_INTERVAL)  # Start the timer
            self.start_button.setText('Stop')
        else:
            self.running = False
            self.timer.stop()  # Stop the timer
            self.start_button.setText('Start')

    def update_pid(self):
        # Generate random target value between 1 and 6000
        random_target = random.randint(1, 6000)
        self.target_data.append(random_target)

        # Calculate PID feedback data
        if not self.feedback_data:  # First call, initialize feedback
            current_feedback = 0
        else:
            current_feedback = self.simulate_pid(random_target)
        self.feedback_data.append(current_feedback)

        # Update frame rate
        self.frame_count += 1
        if time.time() - self.start_time >= 1.0:  # Every second
            self.fps_label.setText(f'FPS: {self.frame_count}')
            self.frame_count = 0
            self.start_time = time.time()

        # Update plot
        self.update_plot()

    def simulate_pid(self, target):
        # Simple PID simulation
        if not self.feedback_data:  # First call
            return 0  # Assume initial feedback is 0

        error = target - self.feedback_data[-1]
        self.integral += error * (UPDATE_INTERVAL / 1000)  # Time in seconds
        derivative = error - self.previous_error

        # PID output
        output = self.feedback_data[-1] + (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)

        # Update for next iteration
        self.previous_error = error

        return output

    def smooth_data(self, data):
        if len(data) < SMOOTHING_WINDOW:
            return data  # 不足平滑窗口大小时直接返回原始数据
        return np.convolve(data, np.ones(SMOOTHING_WINDOW) / SMOOTHING_WINDOW, mode='valid')

    def update_plot(self):
        time_data = np.linspace(0, len(self.feedback_data) * (UPDATE_INTERVAL / 1000),
                                num=len(self.feedback_data))  # Update time scale

        # Smooth the feedback and target data
        smooth_feedback_data = self.smooth_data(np.array(self.feedback_data))
        smooth_target_data = self.smooth_data(np.array(self.target_data))

        # Clear the plot
        self.plot_widget.clear()

        # Plot feedback and target data
        self.plot_widget.plot(time_data[:len(smooth_feedback_data)], smooth_feedback_data, pen='r', symbol='o',
                              label='PID Output (Smooth)')
        self.plot_widget.plot(time_data[:len(smooth_target_data)], smooth_target_data, pen='b', symbol='x',
                              label='Target Value (Smooth)')

        self.plot_widget.addLegend()  # Show legend for clarity

    def update_target(self, value):
        self.target = value / 1.0  # 保持为浮点数，确保目标值更新

    def update_kp(self, value):
        self.kp = value / 10.0

    def update_ki(self, value):
        self.ki = value / 10.0

    def update_kd(self, value):
        self.kd = value / 10.0

    def closeEvent(self, event):
        self.running = False
        self.timer.stop()  # Stop the timer
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PIDControllerApp()
    ex.show()
    sys.exit(app.exec_())
