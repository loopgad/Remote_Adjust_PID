import sys
import time
import logging
import threading
import queue
from collections import deque

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

try:
    import pyqtgraph as pg
    pg.setConfigOption("useOpenGL", True)
except Exception:
    import pyqtgraph as pg

logger = logging.getLogger(__name__)

BAUD_RATES = [9600, 115200, 230400, 460800]
SLIDER_RANGE = (0, 100)
INITIAL_SLIDER_VALUE = 50
PID_SLIDER_RANGE = (0, 10000)
PID_INITIAL_VALUE = 100
MAX_DATA_POINTS = 10000


class SerialThread(QThread):
    feedback_signal = Signal(float, float)
    error_signal = Signal(str)

    def __init__(self, port, baud_rate):
        super().__init__()
        self._port = port
        self._baud_rate = baud_rate
        self._stop_event = threading.Event()
        self._send_queue: queue.Queue = queue.Queue()
        self.ser = None
        self.buffer = b""
        self.last_send_time = 0
        self.send_interval = 0.05

    def initialize_serial(self, port, baud_rate):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=5)
        except serial.SerialException as e:
            logger.error("Serial port initialization error: %s", e)
            self.error_signal.emit(f"Cannot open {port}: {e}")

    def run(self):
        self.initialize_serial(self._port, self._baud_rate)
        if not self.ser:
            return
        try:
            while not self._stop_event.is_set():
                try:
                    # Process pending send commands
                    try:
                        setpoint, kp, ki, kd = self._send_queue.get_nowait()
                        message = f"\\{setpoint:.2f}\t{kp:.2f}\t{ki:.2f}\t{kd:.2f}\n"
                        self.ser.write(message.encode("utf-8"))
                        self.ser.reset_output_buffer()
                    except queue.Empty:
                        pass

                    if self.ser.in_waiting > 0:
                        data = self.ser.read(self.ser.in_waiting)
                        self.buffer += data

                        while b"\r\n" in self.buffer:
                            end_pos = self.buffer.find(b"\r\n")
                            frame = self.buffer[:end_pos]
                            self.buffer = self.buffer[end_pos + 2:]
                            self.process_frame(frame)
                    else:
                        time.sleep(0.01)

                except serial.SerialException as e:
                    logger.error("Serial communication error: %s", e)
                    self.error_signal.emit(str(e))
                    self.initialize_serial(self._port, self._baud_rate)
                    if self.ser:
                        self.ser.reset_input_buffer()
                except ValueError:
                    if self.ser:
                        self.ser.reset_input_buffer()
                    time.sleep(0.1)
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

    def stop(self):
        self._stop_event.set()

    def process_frame(self, frame):
        try:
            data_parts = frame.decode("utf-8").split(",")
            if len(data_parts) == 2:
                target_rpm = float(data_parts[0])
                rpm = float(data_parts[1])
                self.feedback_signal.emit(target_rpm, rpm)
        except Exception as e:
            logger.debug("Error processing frame: %s", e)

    def send_setpoint(self, setpoint, kp, ki, kd):
        self._send_queue.put((setpoint, kp, ki, kd))


class PIDControllerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.feedback_data = deque(maxlen=MAX_DATA_POINTS)
        self.target_data = deque(maxlen=MAX_DATA_POINTS)
        self.time_data = deque(maxlen=MAX_DATA_POINTS)
        self.target = 0
        self.kp = 0
        self.ki = 0
        self.kd = 0
        self._target_curve = None
        self._rpm_curve = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("PID Controller Tuning")
        self.resize(1000, 700)

        layout = QVBoxLayout()

        # Port selection with refresh
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Serial Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Refresh available serial ports")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        # Baud rate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(map(str, BAUD_RATES))
        self.baud_combo.setCurrentText("115200")
        baud_layout.addWidget(self.baud_combo)
        baud_layout.addStretch()
        layout.addLayout(baud_layout)

        # Connect button
        self.open_button = QPushButton("Connect")
        self.open_button.setToolTip("Open/close serial port connection")
        self.open_button.clicked.connect(self.toggle_serial)
        layout.addWidget(self.open_button)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ff3b30;")
        layout.addWidget(self._error_label)

        # Target slider
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target:"))
        self.target_slider = QSlider(Qt.Orientation.Horizontal)
        self.target_slider.setRange(*SLIDER_RANGE)
        self.target_slider.setValue(INITIAL_SLIDER_VALUE)
        self.target_slider.valueChanged.connect(self.update_target)
        target_layout.addWidget(self.target_slider)
        self._target_value_label = QLabel(f"{INITIAL_SLIDER_VALUE}")
        self._target_value_label.setMinimumWidth(40)
        target_layout.addWidget(self._target_value_label)
        layout.addLayout(target_layout)

        # PID controls
        self._create_pid_controls("Kp", self.update_kp, layout)
        self._create_pid_controls("Ki", self.update_ki, layout)
        self._create_pid_controls("Kd", self.update_kd, layout)

        # Feedback label
        self.feedback_label = QLabel("Feedback: —")
        layout.addWidget(self.feedback_label)

        # Plot
        self.plot_widget = pg.PlotWidget(title="Real-time Feedback")
        self.plot_widget.setLabel("left", "RPM")
        self.plot_widget.setLabel("bottom", "Sample")
        self.plot_widget.setBackground("w")
        self.plot_widget.addLegend()
        self._target_curve = self.plot_widget.plot(
            [], [], pen=pg.mkPen("b", width=2), name="Target"
        )
        self._rpm_curve = self.plot_widget.plot(
            [], [], pen=pg.mkPen("r", width=2), name="Actual"
        )
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.port_combo.addItems(ports)
            self._error_label.setText("")
        else:
            self.port_combo.addItem("(no ports found)")
            self._error_label.setText("No serial ports detected")

    def _create_pid_controls(self, name, update_function, layout):
        pid_layout = QHBoxLayout()
        pid_layout.addWidget(QLabel(f"{name}:"))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(*PID_SLIDER_RANGE)
        slider.setValue(PID_INITIAL_VALUE)
        slider.valueChanged.connect(
            lambda value, func=update_function, n=name: self._slider_changed(value, func, n)
        )
        pid_layout.addWidget(slider)

        input_box = QLineEdit()
        input_box.setText(f"{PID_INITIAL_VALUE / 100.0:.2f}")
        input_box.setMaximumWidth(60)
        input_box.textChanged.connect(
            lambda text, func=update_function, s=slider: self._input_changed(text, func, s)
        )
        pid_layout.addWidget(input_box)
        layout.addLayout(pid_layout)
        setattr(self, f"{name.lower()}_slider", slider)
        setattr(self, f"{name.lower()}_input", input_box)

    def _slider_changed(self, value, update_function, name):
        value /= 100.0
        input_box = getattr(self, f"{name.lower()}_input")
        input_box.setText(f"{value:.2f}")
        update_function(value)

    def _input_changed(self, text, update_function, slider):
        try:
            value = float(text)
            slider.setValue(int(value * 100))
            update_function(value)
        except ValueError:
            pass

    def toggle_serial(self):
        if self.serial_thread is None or not self.serial_thread.isRunning():
            port = self.port_combo.currentText()
            if not port or port.startswith("("):
                QMessageBox.warning(self, "Warning", "No serial port selected")
                return
            baud_rate = int(self.baud_combo.currentText())
            self.serial_thread = SerialThread(port, baud_rate)
            self.serial_thread.feedback_signal.connect(self.update_feedback)
            self.serial_thread.error_signal.connect(self._on_serial_error)
            self.serial_thread.start()
            self.open_button.setText("Disconnect")
            self._error_label.setText("")
        else:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
            self.open_button.setText("Connect")

    def _on_serial_error(self, msg):
        self._error_label.setText(msg)

    def update_target(self, value):
        self.target = value
        self._target_value_label.setText(str(value))
        self._send_if_active()

    def update_kp(self, value):
        self.kp = value
        self._send_if_active()

    def update_ki(self, value):
        self.ki = value
        self._send_if_active()

    def update_kd(self, value):
        self.kd = value
        self._send_if_active()

    def _send_if_active(self):
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.send_setpoint(self.target, self.kp, self.ki, self.kd)

    def update_feedback(self, target_rpm, rpm):
        current_time = len(self.feedback_data)
        self.feedback_data.append(rpm)
        self.target_data.append(target_rpm)
        self.time_data.append(current_time)

        self._target_curve.setData(list(self.time_data), list(self.target_data))
        self._rpm_curve.setData(list(self.time_data), list(self.feedback_data))
        self.feedback_label.setText(f"Feedback: Target={target_rpm:.1f} RPM, Actual={rpm:.1f} RPM")

    def closeEvent(self, event):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
        event.accept()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    from param_id_gui.gui.theme import apply_theme
    apply_theme(app)
    ex = PIDControllerApp()
    ex.show()
    sys.exit(app.exec())
