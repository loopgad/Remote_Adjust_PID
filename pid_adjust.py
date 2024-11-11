import struct
import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QHBoxLayout, QPushButton, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg

# Enable OpenGL for hardware acceleration
pg.setConfigOption('useOpenGL', True)

# Constants for serial communication and UI
BAUD_RATES = [9600, 115200, 230400, 460800]  # Example baud rates
SLIDER_RANGE = (0, 100)
INITIAL_SLIDER_VALUE = 50
PID_SLIDER_RANGE = (0, 1000)
PID_INITIAL_VALUE = 10

class SerialThread(QThread):
    feedback_signal = pyqtSignal(float, float)  # 用于发送目标 RPM 和实际 RPM

    def __init__(self, port, baud_rate):
        super().__init__()
        self.running = True
        self.ser = None
        self.buffer = b''  # 缓存数据
        self.last_send_time = 0  # 初始化上次发送时间
        self.send_interval = 0.05  # 设置发送间隔为1秒
        self.initialize_serial(port, baud_rate)

    def initialize_serial(self, port, baud_rate):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=5)
        except serial.SerialException as e:
            print(f"Serial port initialization error: {e}")

    def run(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    # 读取所有可用的字节
                    data = self.ser.read(self.ser.in_waiting)
                    self.buffer += data  # 将新接收到的数据添加到缓存中
                    print(f"Buffered data: {self.buffer}")

                    # 每次检查缓存数据的最后部分是否包含 \r\n
                    while b'\r\n' in self.buffer:
                        # 查找帧尾的位置
                        end_pos = self.buffer.find(b'\r\n')
                        frame = self.buffer[:end_pos]  # 提取到帧尾之前的数据作为完整帧
                        self.buffer = self.buffer[end_pos + 2:]  # 清理缓存中已处理的部分
                        self.process_frame(frame)  # 处理数据帧

            except serial.SerialException as e:
                print(f"Serial communication error: {e}")
                self.initialize_serial(port, baud_rate)
                self.ser.flushInput()
            except ValueError:
                print("Invalid data received")
                self.ser.flushInput()
                time.sleep(0.1)
                continue

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def process_frame(self, frame):
        """解析数据帧并发出反馈信号"""
        try:
            # 假设数据帧是两个浮点数，格式类似 '32.4,43.5'
            data_parts = frame.decode('utf-8').split(',')
            if len(data_parts) == 2:
                target_rpm = float(data_parts[0])
                rpm = float(data_parts[1])
                print(f"Processed data: target_rpm={target_rpm}, rpm={rpm}")
                # 发出反馈信号，将数据传递给主界面
                self.feedback_signal.emit(target_rpm, rpm)
            else:
                print("Invalid frame data")
        except Exception as e:
            print(f"Error processing frame: {e}")

    def send_setpoint(self, setpoint, kp, ki, kd):
        self.current_time = time.time()
        if self.current_time - self.last_send_time >= self.send_interval:
            if self.ser and self.ser.is_open:
                try:
                    message = f'\\{setpoint:.2f}\t{kp:.2f}\t{ki:.2f}\t{kd:.2f}\n'
                    self.ser.write(message.encode('utf-8'))
                    self.last_send_time = self.current_time  # 更新上次发送时间
                    self.ser.flushOutput()
                except serial.SerialException as e:
                    print(f"Failed to send setpoint: {e}")


class PIDControllerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.serial_thread = None
        self.feedback_data = []
        self.target_data = []  # 添加此行初始化 target_data
        self.time_data = []
        self.target = 0
        self.kp = 0
        self.ki = 0
        self.kd = 0

    def initUI(self):
        self.setWindowTitle('PID Controller Tuning')
        self.setGeometry(200, 200, 1000, 700)

        layout = QVBoxLayout()

        # Serial Port Selection
        self.port_label = QLabel('Select Serial Port:')
        layout.addWidget(self.port_label)
        self.port_combo = QComboBox()
        self.refresh_ports()  # Initialize available ports
        layout.addWidget(self.port_combo)

        # Baud Rate Selection
        self.baud_label = QLabel('Select Baud Rate:')
        layout.addWidget(self.baud_label)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(map(str, BAUD_RATES))
        layout.addWidget(self.baud_combo)

        # Open/Close Serial Button
        self.open_button = QPushButton('Open Serial')
        self.open_button.setStyleSheet("background-color: green; color: white;")
        self.open_button.clicked.connect(self.toggle_serial)
        layout.addWidget(self.open_button)

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

        # Create pyqtgraph plot
        self.plot_widget = pg.PlotWidget(title='Feedback Data Over Time')
        self.plot_widget.setLabel('left', 'Feedback')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.setBackground('w')  # Set background to white
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

    def refresh_ports(self):
        """Refresh available serial ports."""
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(available_ports)

    def create_pid_controls(self, name, update_function, layout):
        pid_layout = QHBoxLayout()

        slider_label = QLabel(f'{name}:')
        pid_layout.addWidget(slider_label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(*PID_SLIDER_RANGE)
        slider.setValue(PID_INITIAL_VALUE)
        slider.valueChanged.connect(
            lambda value, func=update_function, name=name: self.slider_changed(value, func, name))
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

    def toggle_serial(self):
        if self.serial_thread is None or not self.serial_thread.isRunning():
            port = self.port_combo.currentText()
            baud_rate = int(self.baud_combo.currentText())
            self.serial_thread = SerialThread(port, baud_rate)
            self.serial_thread.feedback_signal.connect(self.update_feedback)
            self.serial_thread.start()
            self.open_button.setText('Close Serial')
            self.open_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
            self.open_button.setText('Open Serial')
            self.open_button.setStyleSheet("background-color: green; color: white;")

    def update_target(self, value):
        self.target = value
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.send_setpoint(self.target, self.kp, self.ki, self.kd)

    def update_kp(self, value):
        self.kp = value
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.send_setpoint(self.target, self.kp, self.ki, self.kd)

    def update_ki(self, value):
        self.ki = value
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.send_setpoint(self.target, self.kp, self.ki, self.kd)

    def update_kd(self, value):
        self.kd = value
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.send_setpoint(self.target, self.kp, self.ki, self.kd)

    def update_feedback(self, target_rpm, rpm):
        current_time = len(self.feedback_data)

        # Append data for both rpm and target_rpm
        self.feedback_data.append(rpm)
        self.target_data.append(target_rpm)
        self.time_data.append(current_time)

        # Update plot
        self.plot_widget.clear()
        # 绘制 target_rpm 数据，使用蓝色线条
        self.plot_widget.plot(self.time_data, self.target_data, pen='b', symbol='o', name="Target RPM")
        # 绘制 rpm 数据，使用红色线条
        self.plot_widget.plot(self.time_data, self.feedback_data, pen='r', symbol='x', name="RPM")

        # Clear buffer for next frame
        self.buffer = b''

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PIDControllerApp()
    ex.show()
    sys.exit(app.exec_())
