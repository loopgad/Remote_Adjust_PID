import numpy as np
import matplotlib.pyplot as plt

class First_Order_BPF:
    def __init__(self, fc, bw, fs):
        self.fc_ = fc
        self.bw_ = bw
        self.fs_ = fs
        self.calculate_coefficients()
        self.last_output = 0
        self.last_input = 0

    def calculate_coefficients(self):
        # 计算归一化截止频率
        Wn = 2 * np.pi * (self.fc_ - self.bw_ / 2) / self.fs_
        Wd = 2 * np.pi * (self.fc_ + self.bw_ / 2) / self.fs_

        # 计算一阶通频带滤波器的系数 a0_为低阶，a1_为高阶
        self.a0_ = Wn/(Wn+1)
        self.a1_ = 1/(1+Wd)

    def filter(self, input):
        # 计算当前输出值
        output1 = self.a0_ * input + (1 - self.a0_)  * self.last_output

        output2 = self.a1_*(input - self.last_input) + self.a1_ * self.last_output

        # 计算反馈项
        feedback = output1 + output2
        self.last_input = input
        self.last_output = feedback
        return feedback  # 返回滤波后的输出值

# 生成测试信号
t = np.linspace(0, 1, 1000, endpoint=False)  # 1 second
signal = np.sin(2 * np.pi * 24544540 * t) + 0.5 * np.sin(np.pi * 2 * t )  # 10 Hz and 20 Hz

# 应用滤波器
bpf = First_Order_BPF(16000, 2, 1000)  # 中心频率15Hz，带宽5Hz，采样频率1000Hz
filtered_signal = np.array([bpf.filter(val) for val in signal])

# 可视化结果
plt.figure(figsize=(10, 6))

plt.subplot(2, 1, 1)
plt.plot(t, signal, label='Original Signal')
plt.legend()
plt.title('Original Signal')

plt.subplot(2, 1, 2)
plt.plot(t, filtered_signal, label='Band-Pass Filtered Signal', color='red')
plt.legend()
plt.title('Band-Pass Filtered Signal')

plt.tight_layout()
plt.show()