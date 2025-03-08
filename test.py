import numpy as np
import matplotlib.pyplot as plt

# 两轮差速小车的运动学参数
wheel_radius = 0.1  # 轮子半径
wheel_base = 0.5  # 轮子间距
time_step = 0.1  # 时间步长
target_pos = np.array([5.0, 5.0])  # 目标位置
dead_zone = 0.1  # 死区半径

# 初始状态
state_pid = np.array([0.0, 0.0, 0.0])  # [x, y, theta]，theta为朝向角度
state_ndi = np.array([0.0, 0.0, 0.0])  # [x, y, theta]，theta为朝向角度

# PID控制器参数
kp = 1.5
ki = 0.01
kd = 0.05
pid_error_integral = np.array([0.0, 0.0])
pid_previous_error = np.array([0.0, 0.0])

# NDI控制器参数
ndi_kp = 1.5
ndi_kd = 0.3

# 初始化路径数据
pid_path_x = [state_pid[0]]
pid_path_y = [state_pid[1]]
ndi_path_x = [state_ndi[0]]
ndi_path_y = [state_ndi[1]]


# PWM到速度的映射函数
def pwm_to_velocity(pwm):
    # 假设PWM信号范围为0到255，速度范围为-1到1
    return (pwm - 127.5) / 127.5


# PID控制器
def pid_control(state, target_pos, pid_error_integral, pid_previous_error, kp, ki, kd):
    error = target_pos - state[:2]
    pid_error_integral += error * time_step
    error_derivative = (error - pid_previous_error) / time_step
    u_pid_pwm = kp * error + ki * pid_error_integral + kd * error_derivative
    pid_previous_error = error
    return u_pid_pwm, pid_error_integral, pid_previous_error


# NDI控制器
def ndi_control(state, target_pos, ndi_kp, ndi_kd):
    error = target_pos - state[:2]
    error_derivative = -ndi_kd * state[2]
    u_ndi_pwm = ndi_kp * error + error_derivative
    return u_ndi_pwm


# 两轮差速小车的运动学模型更新
def update_state(state, u, time_step):
    # 将PWM信号转换为速度
    v_left = pwm_to_velocity(u[0])
    v_right = pwm_to_velocity(u[1])

    # 计算线速度和角速度
    if v_right == v_left:
        wz = 0
        vx = v_right
    else:
        wz = (v_right - v_left) / wheel_base * wheel_radius
        R = wheel_base * (v_right + v_left) / 2 / (v_right - v_left)
        vx = wz * R

    # 更新状态
    state[0] += vx * np.cos(state[2]) * time_step
    state[1] += vx * np.sin(state[2]) * time_step
    state[2] += wz * time_step
    return state


# 动态更新
while True:
    # 更新PID状态
    u_pid_pwm, pid_error_integral, pid_previous_error = pid_control(state_pid, target_pos, pid_error_integral,
                                                                    pid_previous_error, kp, ki, kd)
    state_pid = update_state(state_pid, u_pid_pwm, time_step)
    pid_path_x.append(state_pid[0])
    pid_path_y.append(state_pid[1])

    # 更新NDI状态
    u_ndi_pwm = ndi_control(state_ndi, target_pos, ndi_kp, ndi_kd)
    state_ndi = update_state(state_ndi, u_ndi_pwm, time_step)
    ndi_path_x.append(state_ndi[0])
    ndi_path_y.append(state_ndi[1])

    # 检查是否到达目标位置
    if np.linalg.norm(state_pid[:2] - target_pos) < dead_zone or np.linalg.norm(state_ndi[:2] - target_pos) < dead_zone:
        print('Reached the target position.')
        break

# 可视化
plt.figure()
plt.plot(pid_path_x, pid_path_y, 'b', linewidth=2, label='PID Path')
plt.plot(ndi_path_x, ndi_path_y, 'g', linewidth=2, label='NDI Path')
plt.scatter(target_pos[0], target_pos[1], color='r', label='Target Position')
plt.legend()
plt.axis('equal')
plt.xlim([-10, 10])
plt.ylim([-10, 10])
plt.grid(True)
plt.show()