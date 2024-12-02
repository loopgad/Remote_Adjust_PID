# 滤波器实现文档

## 文件说明

该代码文件定义了三个滤波器类，分别实现了一阶带通滤波器、中值滤波器和均值滤波器。这些滤波器可用于信号处理，以实现频率选择或噪声抑制功能。

---

## 1. 一阶带通滤波器 (`First_Order_BPF`)

### 功能
一阶带通滤波器能够通过一段特定的频率范围内的信号，并抑制该范围外的频率成分。

### 构造函数

```cpp
First_Order_BPF(double fc, double bw, double fs);
```

- **参数说明**：
  - `fc`: 中心频率 (Hz)。
  - `bw`: 带宽 (Hz)。
  - `fs`: 采样频率 (Hz)。

- **功能**：
  构造函数初始化滤波器的参数并调用 `calculateCoefficients()` 方法计算滤波器系数。

---

### 核心方法

#### `calculateCoefficients`

```cpp
void First_Order_BPF::calculateCoefficients();
```

- **功能**：
  计算归一化截止频率和滤波器的系数 `a0_` 和 `a1_`。
  
- **计算公式**：
  - 归一化截止频率：  

$$
Wn = \frac{2\pi \left(f_c - \frac{bw}{2}\right)}{f_s}, \quad Wd = \frac{2\pi \left(f_c + \frac{bw}{2}\right)}{f_s}
$$

- 系数计算：  

$$
a0 = \frac{Wn}{Wn + 1}, \quad a1 = \frac{1}{1 + Wd}
$$

---

#### `filter`

```cpp
float First_Order_BPF::filter(const float& input);
```

- **参数**：
  - `input`: 当前输入的信号值。

- **功能**：
  通过静态变量存储上一次的输入和输出值，基于当前输入和滤波器系数，计算输出信号。

- **返回值**：
  滤波后的信号值。

---

## 2. 中值滤波器 (`MedianFilter`)

### 功能
中值滤波器通过排序滑动窗口中的数据，返回窗口中间值，能够有效去除突发噪声。

### 构造函数

```cpp
MedianFilter(int windowSize);
```

- **参数说明**：
  - `windowSize`: 滤波器窗口的大小。

---

### 核心方法

#### `filter`

```cpp
float MedianFilter::filter(float input[filter_max_size]);
```

- **参数**：
  - `input`: 输入的信号数组。

- **功能**：
  将输入数组的值复制到窗口数组，进行排序，并返回中值。

---

#### `sort`

```cpp
void MedianFilter::sort(float arr[], int n);
```

- **参数**：
  - `arr`: 待排序的数组。
  - `n`: 数组大小。

- **功能**：
  使用冒泡排序对数组进行升序排列。

---

#### `swap`

```cpp
void MedianFilter::swap(float* x, float* y);
```

- **参数**：
  - `x`, `y`: 待交换的两个数组元素。

- **功能**：
  交换两个浮点数值。

---

#### 数据输入与输出方法

##### `input`

```cpp
float MedianFilter::input(const float& input);
```

- **功能**：
  接收输入数据，填充滑动窗口，并更新状态标志位。

##### `output`

```cpp
float MedianFilter::output(const float& output);
```

- **功能**：
  检查窗口是否填满，如果满足条件则计算中值并返回，否则返回 0。

---

## 3. 均值滤波器 (`MeanFilter`)

### 功能
均值滤波器通过对指定窗口大小的数据取平均值，从而实现平滑滤波，常用于去除信号中的高频噪声。

### 构造函数

```cpp
MeanFilter(double windowSize);
```

- **参数说明**：
  - `windowSize`: 滤波器窗口的大小。

---

### 核心方法

#### `filter`

```cpp
float MeanFilter::filter(const float input[filter_max_size]);
```

- **参数**：
  - `input`: 输入的信号数组。

- **功能**：
  对窗口内的所有数据进行累加，并返回平均值。

- **返回值**：
  返回窗口内数据的平均值。

---

#### 数据输入与输出方法

##### `input`

```cpp
float MeanFilter::input(const float& input);
```

- **功能**：
  接收输入数据，填充滑动窗口，并更新状态标志位。

##### `output`

```cpp
float MeanFilter::output(const float& output);
```

- **功能**：
  检查窗口是否填满，如果满足条件则计算均值并返回，否则返回 0。

---

## 注意事项

1. **滤波器使用限制**：
   - 一阶带通滤波器的参数需要根据实际采样频率和信号频率仔细选择，避免数值稳定性问题。
   - 中值滤波器的窗口大小不可超过 `filter_max_size`。
   - 均值滤波器的窗口大小决定了平滑程度，窗口过大可能导致信号延迟。

2. **性能优化**：
   - 冒泡排序时间复杂度较高，建议替换为更高效的排序算法，如快速排序或堆排序。
   - 均值滤波器的计算复杂度较低，但窗口较大时可能会影响性能。

---

## 示例用法

### 一阶带通滤波器

```cpp
First_Order_BPF bpf(1000, 200, 8000); // 中心频率 1000Hz，带宽 200Hz，采样频率 8000Hz
float filtered_signal = bpf.filter(input_signal);
```

### 中值滤波器

```cpp
MedianFilter median(5); // 窗口大小为 5
float input_array[5] = {1.0, 3.0, 5.0, 2.0, 4.0};
float median_value = median.filter(input_array);
```

### 均值滤波器

```cpp
MeanFilter mean(5); // 窗口大小为 5
float input_array[5] = {1.0, 3.0, 5.0, 2.0, 4.0};
float mean_value = mean.filter(input_array);
```

---

## 总结

该代码实现了简单且实用的一阶带通滤波器、中值滤波器和均值滤波器，适用于嵌入式或实时系统的信号处理任务。
