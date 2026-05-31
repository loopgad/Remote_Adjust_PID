# 高精度参数识别自动化调参软件重构计划

## TL;DR

> **快速摘要**: 将 sim_platform 重构为 PySide6 GUI + C++ 加速的高精度参数识别自动化调参软件
> 
> **交付物**:
> - PySide6 桌面 GUI 应用（模型配置、仿真运行、参数识别、结果可视化）
> - C++ 加速的 ODE 求解器（nanobind 绑定）
> - 参数识别算法库（LM + PSO，可扩展）
> - PMSM FOC 模型 + 简单电源模型
> - 完整测试套件（单元测试 + 集成测试 + 物理验证）
> 
> **预估工作量**: Large（4-6周）
> **并行执行**: YES - 4 waves
> **关键路径**: 项目初始化 → 核心框架 → C++加速 → GUI集成 → 验证

---

## Context

### 原始请求
使用 codegraph 和结合搬运 D:\Workbuddy\2026-05-31-01-59-37\sim_platform 的内容，使用 pyside 而不是用原生 cpp 的 qt，只是计算仿真部分使用 cpp 高速加速。进行完整的目标重构为结合建模与数学的高精度参数识别自动化调参的完整交互软件，并且高效高精度。

### 访谈摘要
**关键讨论**:
- C++加速范围: D) 全部计算密集型部分（第一版锁定ODE求解器）
- 参数识别算法: E) 全部都要（第一版锁定LM + PSO）
- GUI功能: F) 全部都要（第一版不含插件管理GUI）
- 目标模型库: A/B/C/E（电机类+电源类+控制类+自定义框架）
- 部署平台: 跨平台设计，C++验证本机Windows+LLVM，Python 3.12.10 (uv管理)

**研究发现**:
- PSO-LM混合算法精度提升95.7%（需验证来源）
- nanobind 替代 pybind11：编译更快、二进制更小、ABI稳定
- scikit-build-core + CMake: Python生态标准构建系统
- PySide6: Qt官方绑定，LGPL许可

### Metis 审查
**已识别的间隙** (已解决):
- sim_platform代码位置确认: D:\Workbuddy\2026-05-31-01-59-37\sim_platform
- 范围蔓延防护: 第一版锁定核心功能，标记可扩展点
- 验收标准定义: 参数识别精度、仿真速度、GUI响应性、C++构建、测试覆盖率
- 技术栈锁定: nanobind + scikit-build-core + PySide6 + pytest

---

## Work Objectives

### 核心目标
构建高精度参数识别自动化调参完整交互软件，融合 sim_platform 架构与 PySide6 GUI + C++ 加速

### 具体交付物
1. PySide6 桌面应用（模型配置、仿真监控、参数识别、结果分析）
2. C++ 加速的 ODE 求解器（nanobind 绑定，scikit-build-core 构建）
3. 参数识别算法库（Levenberg-Marquardt + Particle Swarm Optimization）
4. PMSM FOC 仿真模型 + 简单 DC-DC 变换器模型
5. 完整测试套件（单元测试、集成测试、物理验证测试、安全测试）

### 完成定义
- [ ] `uv pip install -e .` 在 Windows + LLVM MinGW 下成功构建 C++ 扩展
- [ ] PySide6 GUI 启动并显示主界面
- [ ] PMSM FOC 仿真运行成功，结果可可视化
- [ ] LM 参数识别精度 < 5% 相对误差
- [ ] PSO 参数识别精度 < 10% 相对误差
- [ ] C++ ODE 求解器比纯 Python 快 > 5x
- [ ] 所有测试通过（pytest）
- [ ] 核心模块测试覆盖率 > 80%

### 必须有
- PySide6 GUI（模型配置、仿真运行、结果查看）
- C++ 加速的 ODE 求解器
- Levenberg-Marquardt 参数识别
- Particle Swarm Optimization 参数识别
- PMSM FOC 模型
- 输入验证 + NaN/Inf 守卫
- HDF5 数据存储
- 单元测试 + 集成测试

### 必须没有（防护栏）
- ❌ gRPC 内部 API（单机应用不需要）
- ❌ GPU 加速（当前环境 Intel 核显，CUDA 不可用）
- ❌ 分布式计算（单机参数识别工具不需要）
- ❌ pluggy 插件系统（第一版用简单类继承 + 注册表）
- ❌ COBALT 形式化验证（学术研究级，非工程需求）
- ❌ Sandlock 沙箱（Linux 特有，Windows 不支持）
- ❌ QML 界面（另一套技术栈，增加复杂度）
- ❌ NetCDF/Zarr 数据格式（锁定 HDF5）
- ❌ C++20/23 特性（锁定 C++17 兼容性）
- ❌ gmpy2 高精度库（过度工程化，用 mpmath 替代）

---

## Verification Strategy

> **零人工干预** - 所有验证由 agent 执行，无例外

### 测试决策
- **基础设施存在**: NO（需创建）
- **自动化测试**: YES (TDD)
- **框架**: pytest
- **TDD 流程**: RED (失败测试) → GREEN (最小实现) → REFACTOR

### QA 策略
每个任务必须包含 agent 执行的 QA 场景。
证据保存到 `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`。

- **GUI**: 使用 Playwright（playwright skill）- 导航、交互、断言 DOM、截图
- **CLI/TUI**: 使用 interactive_bash (tmux) - 运行命令、发送按键、验证输出
- **API/后端**: 使用 Bash (curl) - 发送请求、断言状态 + 响应字段
- **库/模块**: 使用 Bash (bun/node REPL) - 导入、调用函数、比较输出

---

## Execution Strategy

### 并行执行波次

> 最大化吞吐量，将独立任务分组为并行波次。
> 每个波次完成后才开始下一个。
> 目标：每波 5-8 个任务。少于 3 个（除最终波次）= 拆分不足。

```
Wave 1 (立即开始 - 基础设施 + 项目初始化):
├── Task 1: 项目初始化 (pyproject.toml + uv + 目录结构) [quick]
├── Task 2: sim_platform 代码分析与核心模块提取 [deep]
├── Task 3: C++ 构建系统配置 (scikit-build-core + CMake) [unspecified-high]
├── Task 4: PySide6 项目骨架 + 主窗口框架 [visual-engineering]
├── Task 5: 测试基础设施搭建 (pytest + fixtures) [quick]
└── Task 6: 类型系统 + 核心数据结构定义 [quick]

Wave 2 (Wave 1 完成后 - 核心模块实现):
├── Task 7: ODE 求解器 C++ 实现 + nanobind 绑定 [deep]
├── Task 8: PMSM FOC 模型实现 (Python层) [deep]
├── Task 9: DataBus 数据总线实现 [unspecified-high]
├── Task 10: ModelRegistry 模型注册中心 [unspecified-high]
├── Task 11: Levenberg-Marquardt 算法实现 [deep]
├── Task 12: Particle Swarm Optimization 算法实现 [deep]
└── Task 13: 仿真编排器 (Orchestrator) 实现 [deep]

Wave 3 (Wave 2 完成后 - GUI 集成 + 模型扩展):
├── Task 14: 模型配置 GUI 面板 [visual-engineering]
├── Task 15: 仿真运行 GUI 面板 + 实时波形 [visual-engineering]
├── Task 16: 参数识别 GUI 面板 [visual-engineering]
├── Task 17: 结果可视化 + 对比分析 GUI [visual-engineering]
├── Task 18: DC-DC 变换器模型实现 [unspecified-high]
├── Task 19: 输入验证 + 数值安全守卫 [unspecified-high]
└── Task 20: HDF5 数据记录与回放 [unspecified-high]

Wave 4 (Wave 3 完成后 - 验证 + 集成):
├── Task 21: 端到端集成测试 [deep]
├── Task 22: 物理验证测试 (PMSM FOC 精度) [deep]
├── Task 23: 性能基准测试 (C++ vs Python) [unspecified-high]
├── Task 24: 安全攻击测试 (输入验证) [unspecified-high]
└── Task 25: 动态调用测试 (插件接口) [unspecified-high]

Wave FINAL (所有任务完成后 - 4 个并行审查):
├── Task F1: 计划合规审计 (oracle)
├── Task F2: 代码质量审查 (unspecified-high)
├── Task F3: 真实手动 QA (unspecified-high)
└── Task F4: 范围保真度检查 (deep)
-> 呈现结果 -> 获取用户明确确认

关键路径: Task 1 → Task 3 → Task 7 → Task 8 → Task 13 → Task 15 → F1-F4 → 用户确认
并行加速: ~65% 快于顺序执行
最大并发: 7 (Wave 1 & 2)
```

### 依赖矩阵

| 任务 | 依赖 | 阻塞 | 波次 |
|------|------|------|------|
| 1 | - | 2-6, 1 | 1 |
| 2 | 1 | 7-13, 2 | 1 |
| 3 | 1 | 7, 3 | 1 |
| 4 | 1 | 14-17, 4 | 1 |
| 5 | 1 | 21-25, 5 | 1 |
| 6 | 1 | 7-13, 6 | 1 |
| 7 | 2, 3, 6 | 13, 15, 7 | 2 |
| 8 | 2, 6 | 13, 15, 8 | 2 |
| 9 | 2, 6 | 13, 9 | 2 |
| 10 | 2, 6 | 13, 10 | 2 |
| 11 | 2, 6 | 16, 11 | 2 |
| 12 | 2, 6 | 16, 12 | 2 |
| 13 | 7, 8, 9, 10 | 15, 13 | 2 |
| 14 | 4, 10 | 21, 14 | 3 |
| 15 | 4, 7, 8, 13 | 21, 15 | 3 |
| 16 | 4, 11, 12 | 21, 16 | 3 |
| 17 | 4, 13 | 21, 17 | 3 |
| 18 | 2, 6 | 21, 18 | 3 |
| 19 | 2, 6 | 21, 19 | 3 |
| 20 | 2, 9 | 21, 20 | 3 |
| 21 | 14-20 | F1-F4, 21 | 4 |
| 22 | 8, 13, 15 | F1-F4, 22 | 4 |
| 23 | 7, 8 | F1-F4, 23 | 4 |
| 24 | 19 | F1-F4, 24 | 4 |
| 25 | 10, 18 | F1-F4, 25 | 4 |

### Agent 调度摘要

- **Wave 1**: **6** - T1 → `quick`, T2 → `deep`, T3 → `unspecified-high`, T4 → `visual-engineering`, T5 → `quick`, T6 → `quick`
- **Wave 2**: **7** - T7 → `deep`, T8 → `deep`, T9 → `unspecified-high`, T10 → `unspecified-high`, T11 → `deep`, T12 → `deep`, T13 → `deep`
- **Wave 3**: **7** - T14 → `visual-engineering`, T15 → `visual-engineering`, T16 → `visual-engineering`, T17 → `visual-engineering`, T18 → `unspecified-high`, T19 → `unspecified-high`, T20 → `unspecified-high`
- **Wave 4**: **5** - T21 → `deep`, T22 → `deep`, T23 → `unspecified-high`, T24 → `unspecified-high`, T25 → `unspecified-high`
- **FINAL**: **4** - F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. 项目初始化 (pyproject.toml + uv + 目录结构)

  **What to do**:
  - 创建 `pyproject.toml` 配置（项目元数据、依赖、构建系统）
  - 配置 scikit-build-core 作为构建后端
  - 创建标准 Python 项目目录结构：
    ```
    param_id_gui/
    ├── __init__.py
    ├── main.py              # 应用入口
    ├── core/                # 核心框架
    │   ├── __init__.py
    │   ├── orchestrator.py  # 仿真编排器
    │   ├── data_bus.py      # 数据总线
    │   └── model_registry.py # 模型注册中心
    ├── models/              # 仿真模型
    │   ├── __init__.py
    │   ├── motor/           # 电机模型
    │   ├── power/           # 电源模型
    │   └── controller/      # 控制器模型
    ├── algorithms/          # 参数识别算法
    │   ├── __init__.py
    │   ├── lm.py            # Levenberg-Marquardt
    │   └── pso.py           # Particle Swarm Optimization
    ├── gui/                 # PySide6 GUI
    │   ├── __init__.py
    │   ├── main_window.py   # 主窗口
    │   ├── panels/          # 功能面板
    │   └── widgets/         # 自定义控件
    ├── cpp/                 # C++ 加速模块
    │   ├── CMakeLists.txt
    │   ├── ode_solver/      # ODE 求解器
    │   └── bindings/        # nanobind 绑定
    ├── data/                # 数据存储
    │   ├── __init__.py
    │   └── hdf5_handler.py  # HDF5 处理
    └── utils/               # 工具函数
        ├── __init__.py
        ├── validation.py    # 输入验证
        └── safety.py        # 数值安全
    tests/
    ├── __init__.py
    ├── conftest.py          # pytest fixtures
    ├── unit/                # 单元测试
    ├── integration/         # 集成测试
    ├── physics/             # 物理验证测试
    └── security/            # 安全测试
    ```
  - 配置 `uv` 虚拟环境（Python 3.12.10）
  - 创建 `.gitignore` 和基础配置文件
  - 验证 `uv pip install -e .` 成功（无 C++ 扩展时）

  **Must NOT do**:
  - 不要添加 gRPC、GPU 加速、分布式计算依赖
  - 不要添加 pluggy、COBALT、Sandlock 依赖
  - 不要使用 C++20/23 特性
  - 不要创建 QML 文件

  **Recommended Agent Profile**:
  > 项目初始化任务，需要快速完成基础搭建
  - **Category**: `quick`
    - Reason: 简单的文件创建和配置任务，无需复杂逻辑
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (首先执行)
  - **Blocks**: Tasks 2-6 (所有 Wave 1 任务依赖此任务)
  - **Blocked By**: None (立即开始)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有 sim_platform 项目结构参考

  **API/Type References** (接口契约):
  - Python packaging guide: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
  - scikit-build-core docs: https://scikit-build-core.readthedocs.io/en/latest/

  **External References** (库和框架):
  - scikit-build-core: Python C++ 扩展构建标准
  - nanobind: Python-C++ 绑定库

  **WHY Each Reference Matters**:
  - sim_platform 结构: 了解现有架构，确保新项目结构兼容
  - packaging guide: 确保 pyproject.toml 格式正确
  - scikit-build-core: 配置 C++ 构建系统

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 项目初始化成功
    Tool: Bash
    Preconditions: 当前目录为 D:\Destop\test_ui\Remote_Adjust
    Steps:
      1. 运行 `uv venv --python 3.12.10` 创建虚拟环境
      2. 运行 `uv pip install -e .` 安装项目（无 C++ 扩展）
      3. 运行 `python -c "import param_id_gui; print('OK')"` 验证导入
    Expected Result: 输出 "OK"，无错误
    Failure Indicators: ImportError、ModuleNotFoundError、构建失败
    Evidence: .sisyphus/evidence/task-1-project-init.txt

  Scenario: 目录结构正确
    Tool: Bash
    Preconditions: 项目初始化完成
    Steps:
      1. 运行 `ls -la param_id_gui/` 检查主包目录
      2. 运行 `ls -la param_id_gui/core/` 检查核心模块
      3. 运行 `ls -la param_id_gui/gui/` 检查 GUI 模块
      4. 运行 `ls -la tests/` 检查测试目录
    Expected Result: 所有目录存在且包含 __init__.py
    Failure Indicators: 目录不存在、缺少 __init__.py
    Evidence: .sisyphus/evidence/task-1-directory-structure.txt
  ```

  **Evidence to Capture:**
  - [ ] task-1-project-init.txt
  - [ ] task-1-directory-structure.txt

  **Commit**: YES
  - Message: `feat(init): project scaffolding with pyproject.toml and directory structure`
  - Files: `pyproject.toml, param_id_gui/, tests/`
  - Pre-commit: `uv pip install -e .`

- [ ] 2. sim_platform 代码分析与核心模块提取

  **What to do**:
  - 分析 `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` 代码结构
  - 识别核心模块和可复用组件：
    - Orchestrator (仿真编排器)
    - DataBus (数据总线)
    - ModelRegistry (模型注册中心)
    - PMSM FOC 模型
    - FOC 控制器
  - 提取核心逻辑到新项目 `param_id_gui/core/`
  - 保留现有架构模式，适配新项目结构
  - 记录需要修改的部分（GUI 集成、C++ 加速接口）

  **Must NOT do**:
  - 不要直接复制整个 sim_platform（只提取核心）
  - 不要保留 Textual TUI 代码（用 PySide6 替代）
  - 不要保留旧的测试框架（用 pytest 重写）

  **Recommended Agent Profile**:
  > 代码分析和重构任务，需要深入理解现有架构
  - **Category**: `deep`
    - Reason: 需要深入分析现有代码架构，理解模块关系
  - **Skills**: [`understand`]
    - `understand`: 分析 sim_platform 代码架构和模块关系
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (与 Tasks 3-6 并行)
  - **Blocks**: Tasks 7-13 (Wave 2 核心模块实现)
  - **Blocked By**: Task 1 (需要项目结构)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\core\orchestrator.py` - 仿真编排器实现
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\core\data_bus.py` - 数据总线实现
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\motor\pmsm_dq.py` - PMSM 模型实现

  **API/Type References** (接口契约):
  - sim_platform 模块接口文档（如果有）

  **External References** (库和框架):
  - numpy: 数学计算基础
  - scipy: 科学计算工具

  **WHY Each Reference Matters**:
  - orchestrator.py: 理解仿真编排逻辑，提取核心算法
  - data_bus.py: 理解数据交换模式，设计新数据总线
  - pmsm_dq.py: 理解 PMSM 模型数学，确保物理正确性

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 核心模块提取成功
    Tool: Bash
    Preconditions: sim_platform 代码可访问
    Steps:
      1. 运行 `python -c "from param_id_gui.core.orchestrator import Orchestrator; print('OK')"` 验证编排器导入
      2. 运行 `python -c "from param_id_gui.core.data_bus import DataBus; print('OK')"` 验证数据总线导入
      3. 运行 `python -c "from param_id_gui.core.model_registry import ModelRegistry; print('OK')"` 验证模型注册中心导入
    Expected Result: 所有导入成功，无错误
    Failure Indicators: ImportError、模块缺失
    Evidence: .sisyphus/evidence/task-2-core-modules.txt

  Scenario: PMSM 模型数学正确性
    Tool: Bash
    Preconditions: PMSM 模型已提取
    Steps:
      1. 运行 `python -c "from param_id_gui.models.motor.pmsm_dq import PMSMModel; m = PMSMModel(); print(m.params)"` 验证模型参数
      2. 运行简单仿真测试，验证电流、转速计算
    Expected Result: 模型参数合理，仿真结果物理正确
    Failure Indicators: 参数不合理、仿真结果异常
    Evidence: .sisyphus/evidence/task-2-pmsm-model.txt
  ```

  **Evidence to Capture:**
  - [ ] task-2-core-modules.txt
  - [ ] task-2-pmsm-model.txt

  **Commit**: YES
  - Message: `refactor(core): extract core modules from sim_platform`
  - Files: `param_id_gui/core/, param_id_gui/models/`
  - Pre-commit: `python -c "from param_id_gui.core import *"`

- [ ] 3. C++ 构建系统配置 (scikit-build-core + CMake)

  **What to do**:
  - 配置 scikit-build-core 作为构建后端
  - 创建 CMakeLists.txt 配置（C++17 标准）
  - 配置 nanobind 绑定系统
  - 创建示例 C++ 模块（简单函数）验证构建
  - 配置 LLVM MinGW 工具链（Windows）
  - 验证 `uv pip install -e .` 成功构建 C++ 扩展

  **Must NOT do**:
  - 不要使用 C++20/23 特性
  - 不要使用 pybind11（锁定 nanobind）
  - 不要使用 Meson/Makefile（锁定 CMake）
  - 不要添加 GPU 加速（CUDA/OpenCL）

  **Recommended Agent Profile**:
  > C++ 构建系统配置，需要处理跨平台编译问题
  - **Category**: `unspecified-high`
    - Reason: C++ 构建系统配置复杂，需要处理平台差异
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (与 Tasks 2, 4-6 并行)
  - **Blocks**: Task 7 (ODE 求解器 C++ 实现)
  - **Blocked By**: Task 1 (需要项目结构)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\filter\` - 现有 C++ 滤波器实现参考
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有 Python 项目结构

  **API/Type References** (接口契约):
  - scikit-build-core docs: https://scikit-build-core.readthedocs.io/en/latest/
  - nanobind docs: https://nanobind.readthedocs.io/en/latest/

  **External References** (库和框架):
  - scikit-build-core: Python C++ 扩展构建标准
  - nanobind: Python-C++ 绑定库
  - CMake: 跨平台构建系统

  **WHY Each Reference Matters**:
  - filter/: 了解现有 C++ 代码结构和构建模式
  - scikit-build-core: 配置正确的构建后端
  - nanobind: 配置 Python-C++ 绑定

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: C++ 构建成功
    Tool: Bash
    Preconditions: LLVM MinGW 已安装
    Steps:
      1. 运行 `uv pip install -e .` 构建项目
      2. 运行 `python -c "from param_id_gui._core import hello; print(hello())"` 验证 C++ 扩展
    Expected Result: 输出 "Hello from C++!"，无错误
    Failure Indicators: 编译错误、链接错误、导入错误
    Evidence: .sisyphus/evidence/task-3-cpp-build.txt

  Scenario: 跨平台构建配置
    Tool: Bash
    Preconditions: 项目配置完成
    Steps:
      1. 检查 CMakeLists.txt 配置（C++17、平台检测）
      2. 检查 pyproject.toml 构建配置
      3. 验证 nanobind 绑定配置
    Expected Result: 配置正确，支持 Windows/Linux/macOS
    Failure Indicators: 配置错误、平台不兼容
    Evidence: .sisyphus/evidence/task-3-build-config.txt
  ```

  **Evidence to Capture:**
  - [ ] task-3-cpp-build.txt
  - [ ] task-3-build-config.txt

  **Commit**: YES
  - Message: `build(cpp): configure scikit-build-core with nanobind`
  - Files: `CMakeLists.txt, pyproject.toml, param_id_gui/_core/`
  - Pre-commit: `uv pip install -e .`

- [ ] 4. PySide6 项目骨架 + 主窗口框架

  **What to do**:
  - 创建 PySide6 主窗口框架
  - 配置应用入口（`param_id_gui/main.py`）
  - 创建基本菜单栏、工具栏、状态栏
  - 创建面板容器（模型配置、仿真运行、参数识别、结果查看）
  - 配置信号槽系统
  - 验证 GUI 启动成功

  **Must NOT do**:
  - 不要使用 QML（锁定 PySide6 Widgets）
  - 不要实现具体功能（只创建骨架）
  - 不要添加插件管理 GUI

  **Recommended Agent Profile**:
  > GUI 框架搭建，需要视觉设计和交互设计
  - **Category**: `visual-engineering`
    - Reason: GUI 界面设计和布局
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: GUI 设计和用户体验
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (与 Tasks 2, 3, 5, 6 并行)
  - **Blocks**: Tasks 14-17 (GUI 面板实现)
  - **Blocked By**: Task 1 (需要项目结构)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\pid_adjust.py` - 现有 PyQt5 GUI 参考
  - `D:\Destop\test_ui\Remote_Adjust\Serial_Draw\` - 现有 Qt6 C++ GUI 参考

  **API/Type References** (接口契约):
  - PySide6 docs: https://doc.qt.io/qtforpython-6/
  - Qt Widgets reference: https://doc.qt.io/qt-6/qwidget.html

  **External References** (库和框架):
  - PySide6: Qt 官方 Python 绑定
  - Qt Widgets: GUI 控件库

  **WHY Each Reference Matters**:
  - pid_adjust.py: 了解现有 GUI 模式，确保一致性
  - Serial_Draw/: 了解 Qt6 C++ 模式，参考设计
  - PySide6 docs: 确保使用正确的 API

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: GUI 启动成功
    Tool: Bash
    Preconditions: PySide6 已安装
    Steps:
      1. 运行 `python -m param_id_gui.main` 启动应用
      2. 等待 3 秒，检查进程是否存活
      3. 运行 `tasklist | findstr python` 检查进程
    Expected Result: 应用启动，进程存活
    Failure Indicators: 启动崩溃、导入错误、进程退出
    Evidence: .sisyphus/evidence/task-4-gui-launch.txt

  Scenario: 主窗口布局正确
    Tool: Playwright (如果支持) 或 Bash
    Preconditions: GUI 已启动
    Steps:
      1. 检查主窗口标题
      2. 检查菜单栏存在
      3. 检查面板容器存在
    Expected Result: 窗口标题正确，菜单栏和面板存在
    Failure Indicators: 窗口为空、缺少控件
    Evidence: .sisyphus/evidence/task-4-gui-layout.txt
  ```

  **Evidence to Capture:**
  - [ ] task-4-gui-launch.txt
  - [ ] task-4-gui-layout.txt

  **Commit**: YES
  - Message: `feat(gui): PySide6 main window skeleton`
  - Files: `param_id_gui/main.py, param_id_gui/gui/`
  - Pre-commit: `python -m param_id_gui.main`

- [ ] 5. 测试基础设施搭建 (pytest + fixtures)

  **What to do**:
  - 配置 pytest 测试框架
  - 创建 `tests/conftest.py` 共享 fixtures
  - 配置测试目录结构（unit、integration、physics、security）
  - 创建示例测试验证框架工作
  - 配置 pytest-cov 覆盖率报告
  - 验证 `pytest tests/` 成功运行

  **Must NOT do**:
  - 不要使用 unittest（锁定 pytest）
  - 不要创建过于复杂的 fixtures（保持简单）
  - 不要添加 mock 库（除非必要）

  **Recommended Agent Profile**:
  > 测试基础设施搭建，需要快速完成配置
  - **Category**: `quick`
    - Reason: 简单的配置和文件创建任务
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (与 Tasks 2-4, 6 并行)
  - **Blocks**: Tasks 21-25 (测试任务)
  - **Blocked By**: Task 1 (需要项目结构)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\verification\` - 现有测试结构参考

  **API/Type References** (接口契约):
  - pytest docs: https://docs.pytest.org/en/stable/
  - pytest-cov docs: https://pytest-cov.readthedocs.io/en/latest/

  **External References** (库和框架):
  - pytest: Python 测试框架
  - pytest-cov: 覆盖率报告

  **WHY Each Reference Matters**:
  - sim_platform verification: 了解现有测试模式，确保一致性
  - pytest docs: 确保使用正确的配置

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 测试框架工作正常
    Tool: Bash
    Preconditions: pytest 已安装
    Steps:
      1. 运行 `pytest tests/ -v` 执行所有测试
      2. 检查测试输出格式
      3. 检查覆盖率报告生成
    Expected Result: 所有测试通过，覆盖率报告生成
    Failure Indicators: 测试失败、配置错误
    Evidence: .sisyphus/evidence/task-5-pytest-setup.txt

  Scenario: 测试目录结构正确
    Tool: Bash
    Preconditions: 测试目录已创建
    Steps:
      1. 检查 `tests/unit/` 目录存在
      2. 检查 `tests/integration/` 目录存在
      3. 检查 `tests/physics/` 目录存在
      4. 检查 `tests/security/` 目录存在
    Expected Result: 所有测试目录存在
    Failure Indicators: 目录缺失
    Evidence: .sisyphus/evidence/task-5-test-structure.txt
  ```

  **Evidence to Capture:**
  - [ ] task-5-pytest-setup.txt
  - [ ] task-5-test-structure.txt

  **Commit**: YES
  - Message: `test(init): setup pytest framework with fixtures`
  - Files: `tests/, pyproject.toml`
  - Pre-commit: `pytest tests/`

- [ ] 6. 类型系统 + 核心数据结构定义

  **What to do**:
  - 定义核心数据结构（使用 Pydantic 或 dataclasses）
  - 创建类型别名和协议
  - 定义模型参数类型
  - 定义仿真状态类型
  - 定义算法配置类型
  - 验证类型系统工作正常

  **Must NOT do**:
  - 不要使用过于复杂的类型（保持简单）
  - 不要添加 holoviz/param 依赖（用 Pydantic 替代）
  - 不要创建过于抽象的类型层次

  **Recommended Agent Profile**:
  > 类型系统定义，需要清晰的设计
  - **Category**: `quick`
    - Reason: 简单的类型定义任务
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (与 Tasks 2-5 并行)
  - **Blocks**: Tasks 7-13 (核心模块实现)
  - **Blocked By**: Task 1 (需要项目结构)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\` - 现有模型类型参考

  **API/Type References** (接口契约):
  - Pydantic docs: https://docs.pydantic.dev/
  - Python typing: https://docs.python.org/3/library/typing.html

  **External References** (库和框架):
  - Pydantic: 数据验证和类型定义
  - Python typing: 类型注解

  **WHY Each Reference Matters**:
  - sim_platform models: 了解现有数据结构，确保兼容性
  - Pydantic docs: 确保使用正确的类型定义

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 类型系统工作正常
    Tool: Bash
    Preconditions: Pydantic 已安装
    Steps:
      1. 运行 `python -c "from param_id_gui.core.types import ModelParams; print('OK')"` 验证类型导入
      2. 运行 `python -c "from param_id_gui.core.types import SimulationState; print('OK')"` 验证状态类型
    Expected Result: 所有类型导入成功
    Failure Indicators: ImportError、类型错误
    Evidence: .sisyphus/evidence/task-6-types.txt

  Scenario: 类型验证工作正常
    Tool: Bash
    Preconditions: 类型定义完成
    Steps:
      1. 创建 ModelParams 实例，验证参数验证
      2. 创建 SimulationState 实例，验证状态验证
    Expected Result: 类型验证正确，错误参数被拒绝
    Failure Indicators: 验证失败、类型不匹配
    Evidence: .sisyphus/evidence/task-6-type-validation.txt
  ```

  **Evidence to Capture:**
  - [ ] task-6-types.txt
  - [ ] task-6-type-validation.txt

  **Commit**: YES
  - Message: `feat(types): define core data structures and type system`
  - Files: `param_id_gui/core/types.py`
  - Pre-commit: `python -c "from param_id_gui.core.types import *"`

- [ ] 7. ODE 求解器 C++ 实现 + nanobind 绑定

  **What to do**:
  - 实现 C++ ODE 求解器（Runge-Kutta 4th order）
  - 创建 nanobind 绑定
  - 实现 Python 接口
  - 验证求解器精度和性能
  - 与纯 Python 实现对比速度
  - 验证 C++ 比 Python 快 > 5x

  **Must NOT do**:
  - 不要使用 C++20/23 特性
  - 不要添加 GPU 加速
  - 不要实现过于复杂的求解器（RK4 足够）

  **Recommended Agent Profile**:
  > C++ 数值计算实现，需要数学和编程能力
  - **Category**: `deep`
    - Reason: 复杂的数值计算和 C++ 绑定
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 8-13 并行)
  - **Blocks**: Task 13 (仿真编排器)
  - **Blocked By**: Tasks 2, 3, 6 (需要核心模块和构建系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\filter\` - 现有 C++ 实现参考
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\motor\pmsm_dq.py` - PMSM 模型 ODE

  **API/Type References** (接口契约):
  - nanobind docs: https://nanobind.readthedocs.io/en/latest/
  - Runge-Kutta 算法参考

  **External References** (库和框架):
  - nanobind: Python-C++ 绑定
  - Eigen: 线性代数库（可选）

  **WHY Each Reference Matters**:
  - filter/: 了解现有 C++ 代码模式
  - pmsm_dq.py: 理解 ODE 方程，确保求解器正确性
  - nanobind docs: 确保绑定正确

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ODE 求解器精度验证
    Tool: Bash
    Preconditions: C++ 求解器已构建
    Steps:
      1. 运行 `python -c "from param_id_gui._core import ode_solve; print(ode_solve([0,0,0], 0.001, 10))"` 验证求解器
      2. 与 scipy.integrate.solve_ivp 结果对比
    Expected Result: 结果与 scipy 一致（误差 < 1e-6）
    Failure Indicators: 结果不一致、精度不足
    Evidence: .sisyphus/evidence/task-7-ode-accuracy.txt

  Scenario: ODE 求解器性能基准
    Tool: Bash
    Preconditions: Python 和 C++ 求解器都可用
    Steps:
      1. 运行纯 Python ODE 求解器，记录时间
      2. 运行 C++ ODE 求解器，记录时间
      3. 计算加速比
    Expected Result: C++ 比 Python 快 > 5x
    Failure Indicators: 加速比不足、性能未达标
    Evidence: .sisyphus/evidence/task-7-ode-performance.txt
  ```

  **Evidence to Capture:**
  - [ ] task-7-ode-accuracy.txt
  - [ ] task-7-ode-performance.txt

  **Commit**: YES
  - Message: `feat(ode): implement C++ ODE solver with nanobind binding`
  - Files: `param_id_gui/cpp/ode_solver/, param_id_gui/_core/`
  - Pre-commit: `pytest tests/unit/test_ode_solver.py`

- [ ] 8. PMSM FOC 模型实现 (Python层)

  **What to do**:
  - 实现 PMSM dq 轴模型
  - 实现 FOC 控制器（Clarke/Park/PI/SVPWM）
  - 实现电流传感器和编码器模型
  - 验证模型数学正确性
  - 创建模型参数配置
  - 验证仿真结果物理正确

  **Must NOT do**:
  - 不要实现过于复杂的模型（L2 保真度足够）
  - 不要添加故障注入（第一版不含）
  - 不要实现硬件在环接口

  **Recommended Agent Profile**:
  > 电机模型实现，需要数学和物理知识
  - **Category**: `deep`
    - Reason: 复杂的数学模型和物理验证
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 7, 9-13 并行)
  - **Blocks**: Task 13 (仿真编排器)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\motor\pmsm_dq.py` - 现有 PMSM 模型
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\controller\foc.py` - 现有 FOC 控制器

  **API/Type References** (接口契约):
  - PMSM 数学模型参考
  - FOC 控制算法参考

  **External References** (库和框架):
  - numpy: 数学计算
  - scipy: 科学计算

  **WHY Each Reference Matters**:
  - pmsm_dq.py: 理解 PMSM 数学模型，确保正确性
  - foc.py: 理解 FOC 控制算法，确保实现正确

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: PMSM 模型数学正确性
    Tool: Bash
    Preconditions: PMSM 模型已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.models.motor import PMSMModel; m = PMSMModel(); print(m.params)"` 验证模型参数
      2. 运行开环仿真，验证电流、转速计算
    Expected Result: 模型参数合理，仿真结果物理正确
    Failure Indicators: 参数不合理、仿真结果异常
    Evidence: .sisyphus/evidence/task-8-pmsm-model.txt

  Scenario: FOC 控制器验证
    Tool: Bash
    Preconditions: FOC 控制器已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.models.controller import FOCController; c = FOCController(); print(c.params)"` 验证控制器参数
      2. 运行闭环仿真，验证控制效果
    Expected Result: 控制器参数合理，闭环仿真稳定
    Failure Indicators: 控制器不稳定、参数不合理
    Evidence: .sisyphus/evidence/task-8-foc-controller.txt
  ```

  **Evidence to Capture:**
  - [ ] task-8-pmsm-model.txt
  - [ ] task-8-foc-controller.txt

  **Commit**: YES
  - Message: `feat(model): implement PMSM FOC model with controller`
  - Files: `param_id_gui/models/motor/, param_id_gui/models/controller/`
  - Pre-commit: `pytest tests/unit/test_pmsm_model.py`

- [ ] 9. DataBus 数据总线实现

  **What to do**:
  - 实现主题式数据总线
  - 支持实时/批量/事件三种数据模式
  - 实现数据订阅和发布机制
  - 实现数据缓存和历史记录
  - 验证数据总线性能
  - 集成到仿真编排器接口

  **Must NOT do**:
  - 不要实现 ACL 安全控制（第一版不含）
  - 不要实现分布式数据同步
  - 不要添加 gRPC 通信

  **Recommended Agent Profile**:
  > 数据总线实现，需要设计清晰的接口
  - **Category**: `unspecified-high`
    - Reason: 数据总线是核心组件，需要稳定可靠
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 7, 8, 10-13 并行)
  - **Blocks**: Task 13 (仿真编排器)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\core\data_bus.py` - 现有数据总线实现

  **API/Type References** (接口契约):
  - 发布-订阅模式参考
  - 数据缓存策略参考

  **External References** (库和框架):
  - Python threading: 并发数据处理
  - collections.deque: 高效缓存

  **WHY Each Reference Matters**:
  - data_bus.py: 理解现有数据总线设计，确保兼容性

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 数据总线发布订阅
    Tool: Bash
    Preconditions: DataBus 已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.core.data_bus import DataBus; db = DataBus(); db.publish('test', 123); print(db.subscribe('test'))"` 验证发布订阅
      2. 验证数据缓存和历史记录
    Expected Result: 数据发布订阅成功，缓存工作正常
    Failure Indicators: 数据丢失、订阅失败
    Evidence: .sisyphus/evidence/task-9-databus.txt

  Scenario: 数据总线性能测试
    Tool: Bash
    Preconditions: DataBus 已实现
    Steps:
      1. 发布 10000 条数据，记录时间
      2. 订阅 10000 条数据，记录时间
    Expected Result: 发布订阅延迟 < 1ms
    Failure Indicators: 性能不足、延迟过高
    Evidence: .sisyphus/evidence/task-9-databus-performance.txt
  ```

  **Evidence to Capture:**
  - [ ] task-9-databus.txt
  - [ ] task-9-databus-performance.txt

  **Commit**: YES
  - Message: `feat(databus): implement topic-based data bus`
  - Files: `param_id_gui/core/data_bus.py`
  - Pre-commit: `pytest tests/unit/test_data_bus.py`

- [ ] 10. ModelRegistry 模型注册中心

  **What to do**:
  - 实现模型注册中心
  - 支持模型元数据管理
  - 实现模型发现和加载机制
  - 实现模型版本管理
  - 验证模型注册和查询
  - 集成到仿真编排器接口

  **Must NOT do**:
  - 不要实现 pluggy 插件系统
  - 不要实现动态模型加载（第一版静态注册）
  - 不要添加模型验证（第一版不含）

  **Recommended Agent Profile**:
  > 模型注册中心实现，需要清晰的架构设计
  - **Category**: `unspecified-high`
    - Reason: 模型注册中心是核心组件，需要稳定可靠
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 7-9, 11-13 并行)
  - **Blocks**: Task 13 (仿真编排器)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\core\model_registry.py` - 现有模型注册中心

  **API/Type References** (接口契约):
  - 注册表模式参考
  - 元数据管理参考

  **External References** (库和框架):
  - Python typing: 类型注解
  - Pydantic: 数据验证

  **WHY Each Reference Matters**:
  - model_registry.py: 理解现有模型注册中心设计，确保兼容性

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 模型注册和查询
    Tool: Bash
    Preconditions: ModelRegistry 已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.core.model_registry import ModelRegistry; mr = ModelRegistry(); mr.register('pmsm', PMSMModel); print(mr.get('pmsm'))"` 验证模型注册
      2. 验证模型元数据查询
    Expected Result: 模型注册成功，查询返回正确模型
    Failure Indicators: 注册失败、查询错误
    Evidence: .sisyphus/evidence/task-10-model-registry.txt

  Scenario: 模型版本管理
    Tool: Bash
    Preconditions: ModelRegistry 已实现
    Steps:
      1. 注册模型版本 1.0
      2. 注册模型版本 2.0
      3. 查询最新版本
    Expected Result: 版本管理正确，返回最新版本
    Failure Indicators: 版本冲突、查询错误
    Evidence: .sisyphus/evidence/task-10-model-version.txt
  ```

  **Evidence to Capture:**
  - [ ] task-10-model-registry.txt
  - [ ] task-10-model-version.txt

  **Commit**: YES
  - Message: `feat(registry): implement model registry with metadata`
  - Files: `param_id_gui/core/model_registry.py`
  - Pre-commit: `pytest tests/unit/test_model_registry.py`

- [ ] 11. Levenberg-Marquardt 算法实现

  **What to do**:
  - 实现 Levenberg-Marquardt 优化算法
  - 支持参数边界约束
  - 实现收敛判断和迭代控制
  - 验证算法精度（相对误差 < 5%）
  - 集成到参数识别接口
  - 创建算法配置参数

  **Must NOT do**:
  - 不要实现过于复杂的变体（标准 LM 足够）
  - 不要添加 GPU 加速
  - 不要实现分布式优化

  **Recommended Agent Profile**:
  > 优化算法实现，需要数学和编程能力
  - **Category**: `deep`
    - Reason: 复杂的数学算法实现
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 7-10, 12, 13 并行)
  - **Blocks**: Task 16 (参数识别 GUI)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有优化算法参考（如果有）

  **API/Type References** (接口契约):
  - Levenberg-Marquardt 算法参考
  - scipy.optimize.least_squares 参考

  **External References** (库和框架):
  - scipy.optimize: 优化算法参考
  - numpy: 数学计算

  **WHY Each Reference Matters**:
  - scipy.optimize: 了解 LM 算法标准实现

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: LM 算法精度验证
    Tool: Bash
    Preconditions: LM 算法已实现
    Steps:
      1. 创建测试函数（已知参数）
      2. 运行 LM 算法识别参数
      3. 计算相对误差
    Expected Result: 相对误差 < 5%
    Failure Indicators: 误差过大、算法不收敛
    Evidence: .sisyphus/evidence/task-11-lm-accuracy.txt

  Scenario: LM 算法收敛性测试
    Tool: Bash
    Preconditions: LM 算法已实现
    Steps:
      1. 测试不同初始参数
      2. 验证算法收敛性
      3. 记录迭代次数和收敛时间
    Expected Result: 算法收敛，迭代次数合理
    Failure Indicators: 不收敛、迭代次数过多
    Evidence: .sisyphus/evidence/task-11-lm-convergence.txt
  ```

  **Evidence to Capture:**
  - [ ] task-11-lm-accuracy.txt
  - [ ] task-11-lm-convergence.txt

  **Commit**: YES
  - Message: `feat(algorithm): implement Levenberg-Marquardt optimizer`
  - Files: `param_id_gui/algorithms/lm.py`
  - Pre-commit: `pytest tests/unit/test_lm.py`

- [ ] 12. Particle Swarm Optimization 算法实现

  **What to do**:
  - 实现粒子群优化算法
  - 支持参数边界约束
  - 实现惯性权重和学习因子调整
  - 验证算法精度（相对误差 < 10%）
  - 集成到参数识别接口
  - 创建算法配置参数

  **Must NOT do**:
  - 不要实现过于复杂的变体（标准 PSO 足够）
  - 不要添加 GPU 加速
  - 不要实现分布式优化

  **Recommended Agent Profile**:
  > 优化算法实现，需要数学和编程能力
  - **Category**: `deep`
    - Reason: 复杂的数学算法实现
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (与 Tasks 7-11, 13 并行)
  - **Blocks**: Task 16 (参数识别 GUI)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有优化算法参考（如果有）

  **API/Type References** (接口契约):
  - Particle Swarm Optimization 算法参考
  - 惯性权重调整策略参考

  **External References** (库和框架):
  - numpy: 数学计算
  - scipy: 科学计算

  **WHY Each Reference Matters**:
  - PSO 算法参考: 了解标准 PSO 实现

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: PSO 算法精度验证
    Tool: Bash
    Preconditions: PSO 算法已实现
    Steps:
      1. 创建测试函数（已知参数）
      2. 运行 PSO 算法识别参数
      3. 计算相对误差
    Expected Result: 相对误差 < 10%
    Failure Indicators: 误差过大、算法不收敛
    Evidence: .sisyphus/evidence/task-12-pso-accuracy.txt

  Scenario: PSO 算法收敛性测试
    Tool: Bash
    Preconditions: PSO 算法已实现
    Steps:
      1. 测试不同粒子数量
      2. 验证算法收敛性
      3. 记录迭代次数和收敛时间
    Expected Result: 算法收敛，迭代次数合理
    Failure Indicators: 不收敛、迭代次数过多
    Evidence: .sisyphus/evidence/task-12-pso-convergence.txt
  ```

  **Evidence to Capture:**
  - [ ] task-12-pso-accuracy.txt
  - [ ] task-12-pso-convergence.txt

  **Commit**: YES
  - Message: `feat(algorithm): implement Particle Swarm Optimization`
  - Files: `param_id_gui/algorithms/pso.py`
  - Pre-commit: `pytest tests/unit/test_pso.py`

- [ ] 13. 仿真编排器 (Orchestrator) 实现

  **What to do**:
  - 实现仿真编排器（GlobalClock + 多速率调度）
  - 集成 ODE 求解器、PMSM 模型、DataBus
  - 实现仿真流程控制（启动、暂停、停止、重置）
  - 实现仿真状态管理
  - 验证仿真编排器功能
  - 创建仿真配置参数

  **Must NOT do**:
  - 不要实现分布式仿真
  - 不要实现硬件在环接口
  - 不要添加故障注入

  **Recommended Agent Profile**:
  > 仿真编排器实现，需要系统集成能力
  - **Category**: `deep`
    - Reason: 复杂的系统集成和流程控制
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (最后执行，依赖 Tasks 7-12)
  - **Blocks**: Task 15 (仿真运行 GUI)
  - **Blocked By**: Tasks 7, 8, 9, 10 (需要所有核心模块)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\core\orchestrator.py` - 现有仿真编排器

  **API/Type References** (接口契约):
  - 仿真编排模式参考
  - 多速率调度参考

  **External References** (库和框架):
  - Python threading: 并发仿真
  - Python time: 时间控制

  **WHY Each Reference Matters**:
  - orchestrator.py: 理解现有仿真编排器设计，确保兼容性

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 仿真编排器功能验证
    Tool: Bash
    Preconditions: Orchestrator 已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.core.orchestrator import Orchestrator; o = Orchestrator(); o.start(); o.stop()"` 验证启停
      2. 验证仿真状态管理
    Expected Result: 仿真启停正常，状态管理正确
    Failure Indicators: 启停失败、状态异常
    Evidence: .sisyphus/evidence/task-13-orchestrator.txt

  Scenario: 仿真编排器集成测试
    Tool: Bash
    Preconditions: 所有核心模块已集成
    Steps:
      1. 运行完整仿真流程（配置 → 运行 → 结果）
      2. 验证数据总线数据交换
      3. 验证 ODE 求解器调用
    Expected Result: 仿真流程完整，数据交换正确
    Failure Indicators: 流程中断、数据丢失
    Evidence: .sisyphus/evidence/task-13-orchestrator-integration.txt
  ```

  **Evidence to Capture:**
  - [ ] task-13-orchestrator.txt
  - [ ] task-13-orchestrator-integration.txt

  **Commit**: YES
  - Message: `feat(orchestrator): implement simulation orchestrator`
  - Files: `param_id_gui/core/orchestrator.py`
  - Pre-commit: `pytest tests/unit/test_orchestrator.py`

- [ ] 14. 模型配置 GUI 面板

  **What to do**:
  - 实现模型配置 GUI 面板
  - 支持模型参数编辑
  - 支持参数预设管理
  - 实现参数验证和错误提示
  - 集成到主窗口
  - 验证配置保存和加载

  **Must NOT do**:
  - 不要实现插件管理 GUI
  - 不要实现过于复杂的参数编辑器
  - 不要添加参数导入导出（第一版不含）

  **Recommended Agent Profile**:
  > GUI 面板实现，需要视觉设计和交互设计
  - **Category**: `visual-engineering`
    - Reason: GUI 界面设计和交互
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: GUI 设计和用户体验
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 15-20 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 4, 10 (需要主窗口和模型注册中心)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\pid_adjust.py` - 现有参数编辑 GUI 参考

  **API/Type References** (接口契约):
  - PySide6 docs: https://doc.qt.io/qtforpython-6/
  - Qt Widgets reference: https://doc.qt.io/qt-6/qwidget.html

  **External References** (库和框架):
  - PySide6: Qt 官方 Python 绑定
  - Qt Widgets: GUI 控件库

  **WHY Each Reference Matters**:
  - pid_adjust.py: 了解现有参数编辑 GUI 模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 模型配置面板功能
    Tool: Bash
    Preconditions: GUI 已启动
    Steps:
      1. 打开模型配置面板
      2. 编辑模型参数
      3. 保存配置
    Expected Result: 参数编辑成功，配置保存正确
    Failure Indicators: 编辑失败、保存错误
    Evidence: .sisyphus/evidence/task-14-model-config.txt

  Scenario: 参数验证测试
    Tool: Bash
    Preconditions: 模型配置面板已打开
    Steps:
      1. 输入无效参数（负数、超出范围）
      2. 验证错误提示
    Expected Result: 无效参数被拒绝，错误提示正确
    Failure Indicators: 无效参数被接受、错误提示缺失
    Evidence: .sisyphus/evidence/task-14-param-validation.txt
  ```

  **Evidence to Capture:**
  - [ ] task-14-model-config.txt
  - [ ] task-14-param-validation.txt

  **Commit**: YES
  - Message: `feat(gui): implement model configuration panel`
  - Files: `param_id_gui/gui/panels/model_config.py`
  - Pre-commit: `python -c "from param_id_gui.gui.panels.model_config import ModelConfigPanel"`

- [ ] 15. 仿真运行 GUI 面板 + 实时波形

  **What to do**:
  - 实现仿真运行 GUI 面板
  - 支持仿真启停控制
  - 实现实时波形显示（电流、转速等）
  - 实现仿真状态显示
  - 集成到主窗口
  - 验证实时波形更新

  **Must NOT do**:
  - 不要实现过于复杂的波形编辑器
  - 不要添加波形导出（第一版不含）
  - 不要实现实时硬件通信

  **Recommended Agent Profile**:
  > GUI 面板实现，需要视觉设计和交互设计
  - **Category**: `visual-engineering`
    - Reason: GUI 界面设计和实时数据可视化
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: GUI 设计和用户体验
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14, 16-20 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 4, 7, 8, 13 (需要主窗口、ODE 求解器、PMSM 模型、编排器)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\Serial_Draw\` - 现有实时波形显示参考

  **API/Type References** (接口契约):
  - PySide6 docs: https://doc.qt.io/qtforpython-6/
  - matplotlib integration: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html

  **External References** (库和框架):
  - PySide6: Qt 官方 Python 绑定
  - matplotlib: 波形绘制

  **WHY Each Reference Matters**:
  - Serial_Draw/: 了解现有实时波形显示模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 仿真运行面板功能
    Tool: Bash
    Preconditions: GUI 已启动
    Steps:
      1. 打开仿真运行面板
      2. 启动仿真
      3. 观察实时波形
    Expected Result: 仿真启动成功，波形实时更新
    Failure Indicators: 启动失败、波形不更新
    Evidence: .sisyphus/evidence/task-15-simulation-panel.txt

  Scenario: 实时波形性能测试
    Tool: Bash
    Preconditions: 仿真正在运行
    Steps:
      1. 运行仿真 10 秒
      2. 记录波形更新延迟
    Expected Result: 波形更新延迟 < 100ms
    Failure Indicators: 延迟过高、波形卡顿
    Evidence: .sisyphus/evidence/task-15-waveform-performance.txt
  ```

  **Evidence to Capture:**
  - [ ] task-15-simulation-panel.txt
  - [ ] task-15-waveform-performance.txt

  **Commit**: YES
  - Message: `feat(gui): implement simulation panel with real-time waveform`
  - Files: `param_id_gui/gui/panels/simulation.py`
  - Pre-commit: `python -c "from param_id_gui.gui.panels.simulation import SimulationPanel"`

- [ ] 16. 参数识别 GUI 面板

  **What to do**:
  - 实现参数识别 GUI 面板
  - 支持目标函数定义
  - 支持算法选择（LM、PSO）
  - 实现识别结果展示
  - 集成到主窗口
  - 验证参数识别流程

  **Must NOT do**:
  - 不要实现过于复杂的目标函数编辑器
  - 不要添加算法参数自动调整
  - 不要实现识别历史管理

  **Recommended Agent Profile**:
  > GUI 面板实现，需要视觉设计和交互设计
  - **Category**: `visual-engineering`
    - Reason: GUI 界面设计和交互
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: GUI 设计和用户体验
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14, 15, 17-20 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 4, 11, 12 (需要主窗口、LM 算法、PSO 算法)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\pid_adjust.py` - 现有参数调整 GUI 参考

  **API/Type References** (接口契约):
  - PySide6 docs: https://doc.qt.io/qtforpython-6/
  - Qt Widgets reference: https://doc.qt.io/qt-6/qwidget.html

  **External References** (库和框架):
  - PySide6: Qt 官方 Python 绑定
  - Qt Widgets: GUI 控件库

  **WHY Each Reference Matters**:
  - pid_adjust.py: 了解现有参数调整 GUI 模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 参数识别面板功能
    Tool: Bash
    Preconditions: GUI 已启动
    Steps:
      1. 打开参数识别面板
      2. 定义目标函数
      3. 选择算法（LM 或 PSO）
      4. 运行识别
    Expected Result: 识别流程完整，结果展示正确
    Failure Indicators: 流程中断、结果错误
    Evidence: .sisyphus/evidence/task-16-param-id-panel.txt

  Scenario: 参数识别精度验证
    Tool: Bash
    Preconditions: 参数识别已完成
    Steps:
      1. 使用已知参数的测试数据
      2. 运行参数识别
      3. 计算识别精度
    Expected Result: LM 误差 < 5%，PSO 误差 < 10%
    Failure Indicators: 精度未达标
    Evidence: .sisyphus/evidence/task-16-param-id-accuracy.txt
  ```

  **Evidence to Capture:**
  - [ ] task-16-param-id-panel.txt
  - [ ] task-16-param-id-accuracy.txt

  **Commit**: YES
  - Message: `feat(gui): implement parameter identification panel`
  - Files: `param_id_gui/gui/panels/param_id.py`
  - Pre-commit: `python -c "from param_id_gui.gui.panels.param_id import ParamIDPanel"`

- [ ] 17. 结果可视化 + 对比分析 GUI

  **What to do**:
  - 实现结果可视化 GUI 面板
  - 支持仿真结果对比分析
  - 实现数据导出（CSV、HDF5）
  - 实现图表生成和保存
  - 集成到主窗口
  - 验证结果可视化功能

  **Must NOT do**:
  - 不要实现过于复杂的图表编辑器
  - 不要添加报告生成（第一版不含）
  - 不要实现实时数据流可视化

  **Recommended Agent Profile**:
  > GUI 面板实现，需要视觉设计和交互设计
  - **Category**: `visual-engineering`
    - Reason: GUI 界面设计和数据可视化
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: GUI 设计和用户体验
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14-16, 18-20 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 4, 13 (需要主窗口和编排器)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Destop\test_ui\Remote_Adjust\Serial_Draw\` - 现有数据可视化参考

  **API/Type References** (接口契约):
  - PySide6 docs: https://doc.qt.io/qtforpython-6/
  - matplotlib integration: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html

  **External References** (库和框架):
  - PySide6: Qt 官方 Python 绑定
  - matplotlib: 数据可视化

  **WHY Each Reference Matters**:
  - Serial_Draw/: 了解现有数据可视化模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 结果可视化面板功能
    Tool: Bash
    Preconditions: GUI 已启动
    Steps:
      1. 打开结果可视化面板
      2. 加载仿真结果
      3. 生成对比图表
    Expected Result: 图表生成成功，对比分析正确
    Failure Indicators: 图表生成失败、对比错误
    Evidence: .sisyphus/evidence/task-17-results-visualization.txt

  Scenario: 数据导出测试
    Tool: Bash
    Preconditions: 结果可视化面板已打开
    Steps:
      1. 导出数据为 CSV
      2. 导出数据为 HDF5
      3. 验证导出文件
    Expected Result: 导出成功，文件格式正确
    Failure Indicators: 导出失败、文件损坏
    Evidence: .sisyphus/evidence/task-17-data-export.txt
  ```

  **Evidence to Capture:**
  - [ ] task-17-results-visualization.txt
  - [ ] task-17-data-export.txt

  **Commit**: YES
  - Message: `feat(gui): implement results visualization and comparison`
  - Files: `param_id_gui/gui/panels/results.py`
  - Pre-commit: `python -c "from param_id_gui.gui.panels.results import ResultsPanel"`

- [ ] 18. DC-DC 变换器模型实现

  **What to do**:
  - 实现 DC-DC 变换器模型（Buck、Boost）
  - 实现 PWM 控制器
  - 实现电感、电容、开关模型
  - 验证模型数学正确性
  - 创建模型参数配置
  - 集成到模型注册中心

  **Must NOT do**:
  - 不要实现过于复杂的拓扑（Buck、Boost 足够）
  - 不要添加热模型
  - 不要实现故障注入

  **Recommended Agent Profile**:
  > 电源模型实现，需要电力电子知识
  - **Category**: `unspecified-high`
    - Reason: 电源模型需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14-17, 19, 20 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\models\power\` - 现有电源模型参考

  **API/Type References** (接口契约):
  - DC-DC 变换器数学模型参考
  - PWM 控制算法参考

  **External References** (库和框架):
  - numpy: 数学计算
  - scipy: 科学计算

  **WHY Each Reference Matters**:
  - sim_platform power models: 了解现有电源模型设计

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: DC-DC 变换器模型验证
    Tool: Bash
    Preconditions: DC-DC 模型已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.models.power import BuckConverter; m = BuckConverter(); print(m.params)"` 验证模型参数
      2. 运行开环仿真，验证电压、电流计算
    Expected Result: 模型参数合理，仿真结果物理正确
    Failure Indicators: 参数不合理、仿真结果异常
    Evidence: .sisyphus/evidence/task-18-dcdc-model.txt

  Scenario: PWM 控制器验证
    Tool: Bash
    Preconditions: PWM 控制器已实现
    Steps:
      1. 运行 `python -c "from param_id_gui.models.power import PWMController; c = PWMController(); print(c.params)"` 验证控制器参数
      2. 运行闭环仿真，验证控制效果
    Expected Result: 控制器参数合理，闭环仿真稳定
    Failure Indicators: 控制器不稳定、参数不合理
    Evidence: .sisyphus/evidence/task-18-pwm-controller.txt
  ```

  **Evidence to Capture:**
  - [ ] task-18-dcdc-model.txt
  - [ ] task-18-pwm-controller.txt

  **Commit**: YES
  - Message: `feat(model): implement DC-DC converter models`
  - Files: `param_id_gui/models/power/`
  - Pre-commit: `pytest tests/unit/test_dcdc_model.py`

- [ ] 19. 输入验证 + 数值安全守卫

  **What to do**:
  - 实现输入验证框架
  - 实现 NaN/Inf 守卫
  - 实现参数范围检查
  - 实现数值稳定性检查
  - 集成到所有模块
  - 验证安全守卫功能

  **Must NOT do**:
  - 不要实现 COBALT 形式化验证
  - 不要实现 Sandlock 沙箱
  - 不要实现过于复杂的验证规则

  **Recommended Agent Profile**:
  > 安全守卫实现，需要安全编程知识
  - **Category**: `unspecified-high`
    - Reason: 安全守卫需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14-18, 20 并行)
  - **Blocks**: Task 24 (安全攻击测试)
  - **Blocked By**: Tasks 2, 6 (需要核心模块和类型系统)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有安全守卫参考

  **API/Type References** (接口契约):
  - 输入验证最佳实践参考
  - 数值安全编程参考

  **External References** (库和框架):
  - Python typing: 类型注解
  - Pydantic: 数据验证

  **WHY Each Reference Matters**:
  - sim_platform: 了解现有安全守卫设计

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 输入验证测试
    Tool: Bash
    Preconditions: 输入验证已实现
    Steps:
      1. 输入无效参数（负数、超出范围、非数字）
      2. 验证错误提示
    Expected Result: 无效参数被拒绝，错误提示正确
    Failure Indicators: 无效参数被接受、错误提示缺失
    Evidence: .sisyphus/evidence/task-19-input-validation.txt

  Scenario: NaN/Inf 守卫测试
    Tool: Bash
    Preconditions: 数值安全守卫已实现
    Steps:
      1. 输入 NaN 值
      2. 输入 Inf 值
      3. 验证守卫拦截
    Expected Result: NaN/Inf 被拦截，错误提示正确
    Failure Indicators: NaN/Inf 未被拦截
    Evidence: .sisyphus/evidence/task-19-nan-guard.txt
  ```

  **Evidence to Capture:**
  - [ ] task-19-input-validation.txt
  - [ ] task-19-nan-guard.txt

  **Commit**: YES
  - Message: `feat(safety): implement input validation and NaN/Inf guards`
  - Files: `param_id_gui/utils/validation.py, param_id_gui/utils/safety.py`
  - Pre-commit: `pytest tests/security/test_validation.py`

- [ ] 20. HDF5 数据记录与回放

  **What to do**:
  - 实现 HDF5 数据记录器
  - 支持仿真数据实时记录
  - 实现数据回放功能
  - 实现数据查询和过滤
  - 集成到仿真编排器
  - 验证数据记录和回放

  **Must NOT do**:
  - 不要实现 NetCDF/Zarr 支持（锁定 HDF5）
  - 不要实现分布式数据存储
  - 不要实现数据压缩（第一版不含）

  **Recommended Agent Profile**:
  > 数据存储实现，需要数据管理知识
  - **Category**: `unspecified-high`
    - Reason: 数据存储需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无 GUI 交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (与 Tasks 14-19 并行)
  - **Blocks**: Task 21 (端到端集成测试)
  - **Blocked By**: Tasks 2, 9 (需要核心模块和数据总线)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\tools\replay\hdf5_logger.py` - 现有 HDF5 记录器

  **API/Type References** (接口契约):
  - h5py docs: https://docs.h5py.org/en/stable/
  - HDF5 数据格式参考

  **External References** (库和框架):
  - h5py: HDF5 Python 绑定
  - HDF5: 数据存储格式

  **WHY Each Reference Matters**:
  - hdf5_logger.py: 了解现有 HDF5 记录器设计

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: HDF5 数据记录测试
    Tool: Bash
    Preconditions: HDF5 记录器已实现
    Steps:
      1. 运行仿真并记录数据
      2. 验证 HDF5 文件生成
      3. 验证数据完整性
    Expected Result: HDF5 文件生成成功，数据完整
    Failure Indicators: 文件未生成、数据损坏
    Evidence: .sisyphus/evidence/task-20-hdf5-record.txt

  Scenario: HDF5 数据回放测试
    Tool: Bash
    Preconditions: HDF5 数据文件存在
    Steps:
      1. 加载 HDF5 数据文件
      2. 回放仿真数据
      3. 验证数据一致性
    Expected Result: 数据回放成功，数据一致
    Failure Indicators: 回放失败、数据不一致
    Evidence: .sisyphus/evidence/task-20-hdf5-playback.txt
  ```

  **Evidence to Capture:**
  - [ ] task-20-hdf5-record.txt
  - [ ] task-20-hdf5-playback.txt

  **Commit**: YES
  - Message: `feat(data): implement HDF5 data recording and playback`
  - Files: `param_id_gui/data/hdf5_handler.py`
  - Pre-commit: `pytest tests/unit/test_hdf5.py`

- [ ] 21. 端到端集成测试

  **What to do**:
  - 实现端到端集成测试
  - 测试完整工作流（配置 → 仿真 → 识别 → 结果）
  - 验证模块间集成
  - 测试错误处理和恢复
  - 验证数据一致性
  - 创建测试数据集

  **Must NOT do**:
  - 不要实现过于复杂的测试场景
  - 不要添加性能测试（单独任务）
  - 不要实现自动化回归测试

  **Recommended Agent Profile**:
  > 集成测试实现，需要系统测试知识
  - **Category**: `deep`
    - Reason: 复杂的系统集成测试
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (与 Tasks 22-25 并行)
  - **Blocks**: F1-F4 (最终验证)
  - **Blocked By**: Tasks 14-20 (需要所有 GUI 面板和功能模块)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\verification\` - 现有测试参考

  **API/Type References** (接口契约):
  - pytest docs: https://docs.pytest.org/en/stable/
  - 集成测试最佳实践参考

  **External References** (库和框架):
  - pytest: Python 测试框架
  - pytest-cov: 覆盖率报告

  **WHY Each Reference Matters**:
  - sim_platform verification: 了解现有测试模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 端到端工作流测试
    Tool: Bash
    Preconditions: 所有模块已实现
    Steps:
      1. 运行 `pytest tests/integration/test_workflow.py -v` 执行工作流测试
      2. 验证配置 → 仿真 → 识别 → 结果流程
    Expected Result: 所有测试通过，工作流完整
    Failure Indicators: 测试失败、流程中断
    Evidence: .sisyphus/evidence/task-21-e2e-workflow.txt

  Scenario: 错误处理测试
    Tool: Bash
    Preconditions: 集成测试已配置
    Steps:
      1. 测试无效配置处理
      2. 测试仿真异常处理
      3. 测试识别失败处理
    Expected Result: 错误处理正确，应用不崩溃
    Failure Indicators: 应用崩溃、错误未处理
    Evidence: .sisyphus/evidence/task-21-error-handling.txt
  ```

  **Evidence to Capture:**
  - [ ] task-21-e2e-workflow.txt
  - [ ] task-21-error-handling.txt

  **Commit**: YES
  - Message: `test(integration): implement end-to-end workflow tests`
  - Files: `tests/integration/`
  - Pre-commit: `pytest tests/integration/ -v`

- [ ] 22. 物理验证测试 (PMSM FOC 精度)

  **What to do**:
  - 实现物理验证测试
  - 验证 PMSM 模型物理正确性
  - 验证 FOC 控制器性能
  - 验证仿真结果与理论一致
  - 创建物理测试数据集
  - 验证数值稳定性

  **Must NOT do**:
  - 不要实现过于复杂的物理场景
  - 不要添加实验数据对比（第一版不含）
  - 不要实现形式化验证

  **Recommended Agent Profile**:
  > 物理验证测试，需要物理和数学知识
  - **Category**: `deep`
    - Reason: 复杂的物理验证和数学验证
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (与 Tasks 21, 23-25 并行)
  - **Blocks**: F1-F4 (最终验证)
  - **Blocked By**: Tasks 8, 13, 15 (需要 PMSM 模型、编排器、仿真面板)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\verification\` - 现有物理验证参考

  **API/Type References** (接口契约):
  - PMSM 物理模型参考
  - FOC 控制理论参考

  **External References** (库和框架):
  - numpy: 数学计算
  - scipy: 科学计算

  **WHY Each Reference Matters**:
  - sim_platform verification: 了解现有物理验证模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: PMSM 模型物理验证
    Tool: Bash
    Preconditions: PMSM 模型已实现
    Steps:
      1. 运行开环仿真，验证电流、转速计算
      2. 与理论公式对比
      3. 验证数值稳定性
    Expected Result: 仿真结果与理论一致，数值稳定
    Failure Indicators: 结果不一致、数值不稳定
    Evidence: .sisyphus/evidence/task-22-pmsm-physics.txt

  Scenario: FOC 控制器性能验证
    Tool: Bash
    Preconditions: FOC 控制器已实现
    Steps:
      1. 运行闭环仿真，验证控制效果
      2. 验证响应时间、超调量
      3. 验证稳态误差
    Expected Result: 控制性能达标，响应快、超调小、误差小
    Failure Indicators: 控制性能不达标
    Evidence: .sisyphus/evidence/task-22-foc-performance.txt
  ```

  **Evidence to Capture:**
  - [ ] task-22-pmsm-physics.txt
  - [ ] task-22-foc-performance.txt

  **Commit**: YES
  - Message: `test(physics): implement PMSM FOC physics verification`
  - Files: `tests/physics/`
  - Pre-commit: `pytest tests/physics/ -v`

- [ ] 23. 性能基准测试 (C++ vs Python)

  **What to do**:
  - 实现性能基准测试
  - 测试 C++ ODE 求解器性能
  - 测试 Python ODE 求解器性能
  - 计算加速比
  - 验证 C++ 比 Python 快 > 5x
  - 创建性能报告

  **Must NOT do**:
  - 不要实现过于复杂的性能测试场景
  - 不要添加 GPU 性能测试
  - 不要实现分布式性能测试

  **Recommended Agent Profile**:
  > 性能测试实现，需要性能分析知识
  - **Category**: `unspecified-high`
    - Reason: 性能测试需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (与 Tasks 21, 22, 24, 25 并行)
  - **Blocks**: F1-F4 (最终验证)
  - **Blocked By**: Tasks 7, 8 (需要 ODE 求解器和 PMSM 模型)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有性能测试参考

  **API/Type References** (接口契约):
  - Python timeit: 性能测量
  - 性能基准测试最佳实践参考

  **External References** (库和框架):
  - Python timeit: 性能测量
  - Python cProfile: 性能分析

  **WHY Each Reference Matters**:
  - sim_platform: 了解现有性能测试模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: C++ ODE 求解器性能测试
    Tool: Bash
    Preconditions: C++ ODE 求解器已实现
    Steps:
      1. 运行 C++ ODE 求解器，记录时间
      2. 运行 Python ODE 求解器，记录时间
      3. 计算加速比
    Expected Result: C++ 比 Python 快 > 5x
    Failure Indicators: 加速比不足
    Evidence: .sisyphus/evidence/task-23-cpp-performance.txt

  Scenario: 性能报告生成
    Tool: Bash
    Preconditions: 性能测试已完成
    Steps:
      1. 生成性能报告
      2. 验证报告格式和内容
    Expected Result: 报告生成成功，内容完整
    Failure Indicators: 报告生成失败、内容缺失
    Evidence: .sisyphus/evidence/task-23-performance-report.txt
  ```

  **Evidence to Capture:**
  - [ ] task-23-cpp-performance.txt
  - [ ] task-23-performance-report.txt

  **Commit**: YES
  - Message: `test(benchmark): implement C++ vs Python performance tests`
  - Files: `tests/benchmark/`
  - Pre-commit: `pytest tests/benchmark/ -v`

- [ ] 24. 安全攻击测试 (输入验证)

  **What to do**:
  - 实现安全攻击测试
  - 测试输入验证绕过
  - 测试数值攻击（NaN、Inf、溢出）
  - 测试边界条件攻击
  - 验证安全守卫有效性
  - 创建安全测试报告

  **Must NOT do**:
  - 不要实现过于复杂的攻击场景
  - 不要添加网络攻击测试
  - 不要实现形式化验证

  **Recommended Agent Profile**:
  > 安全测试实现，需要安全测试知识
  - **Category**: `unspecified-high`
    - Reason: 安全测试需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (与 Tasks 21-23, 25 并行)
  - **Blocks**: F1-F4 (最终验证)
  - **Blocked By**: Task 19 (需要输入验证和安全守卫)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有安全测试参考

  **API/Type References** (接口契约):
  - 安全测试最佳实践参考
  - 输入验证攻击模式参考

  **External References** (库和框架):
  - pytest: Python 测试框架
  - 安全测试工具参考

  **WHY Each Reference Matters**:
  - sim_platform: 了解现有安全测试模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 输入验证绕过测试
    Tool: Bash
    Preconditions: 输入验证已实现
    Steps:
      1. 测试各种无效输入（负数、超出范围、非数字）
      2. 验证验证拦截
    Expected Result: 所有无效输入被拦截
    Failure Indicators: 无效输入未被拦截
    Evidence: .sisyphus/evidence/task-24-input-bypass.txt

  Scenario: 数值攻击测试
    Tool: Bash
    Preconditions: 数值安全守卫已实现
    Steps:
      1. 测试 NaN 攻击
      2. 测试 Inf 攻击
      3. 测试溢出攻击
    Expected Result: 所有数值攻击被拦截
    Failure Indicators: 数值攻击未被拦截
    Evidence: .sisyphus/evidence/task-24-numerical-attack.txt
  ```

  **Evidence to Capture:**
  - [ ] task-24-input-bypass.txt
  - [ ] task-24-numerical-attack.txt

  **Commit**: YES
  - Message: `test(security): implement input validation attack tests`
  - Files: `tests/security/`
  - Pre-commit: `pytest tests/security/ -v`

- [ ] 25. 动态调用测试 (插件接口)

  **What to do**:
  - 实现动态调用测试
  - 测试模型动态加载
  - 测试算法动态调用
  - 测试接口兼容性
  - 验证插件接口稳定性
  - 创建动态调用测试报告

  **Must NOT do**:
  - 不要实现 pluggy 插件系统
  - 不要实现动态代码加载
  - 不要实现过于复杂的插件接口

  **Recommended Agent Profile**:
  > 动态调用测试，需要接口测试知识
  - **Category**: `unspecified-high`
    - Reason: 动态调用测试需要专业知识
  - **Skills**: []
    - 无特殊技能需求
  - **Skills Evaluated but Omitted**:
    - `playwright`: 无浏览器交互
    - `git-master`: 无复杂 git 操作

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (与 Tasks 21-24 并行)
  - **Blocks**: F1-F4 (最终验证)
  - **Blocked By**: Tasks 10, 18 (需要模型注册中心和 DC-DC 模型)

  **References**:

  **Pattern References** (现有代码参考):
  - `D:\Workbuddy\2026-05-31-01-59-37\sim_platform\` - 现有动态调用参考

  **API/Type References** (接口契约):
  - Python importlib: 动态导入
  - 接口测试最佳实践参考

  **External References** (库和框架):
  - Python importlib: 动态导入
  - Python typing: 类型注解

  **WHY Each Reference Matters**:
  - sim_platform: 了解现有动态调用模式

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: 模型动态加载测试
    Tool: Bash
    Preconditions: 模型注册中心已实现
    Steps:
      1. 动态加载 PMSM 模型
      2. 动态加载 DC-DC 模型
      3. 验证模型功能
    Expected Result: 模型动态加载成功，功能正常
    Failure Indicators: 加载失败、功能异常
    Evidence: .sisyphus/evidence/task-25-dynamic-model.txt

  Scenario: 算法动态调用测试
    Tool: Bash
    Preconditions: 算法接口已定义
    Steps:
      1. 动态调用 LM 算法
      2. 动态调用 PSO 算法
      3. 验证算法结果
    Expected Result: 算法动态调用成功，结果正确
    Failure Indicators: 调用失败、结果错误
    Evidence: .sisyphus/evidence/task-25-dynamic-algorithm.txt
  ```

  **Evidence to Capture:**
  - [ ] task-25-dynamic-model.txt
  - [ ] task-25-dynamic-algorithm.txt

  **Commit**: YES
  - Message: `test(dynamic): implement dynamic invocation tests`
  - Files: `tests/integration/test_dynamic.py`
  - Pre-commit: `pytest tests/integration/test_dynamic.py -v`

---

## Final Verification Wave (所有实现任务完成后 — 4 个并行审查)

> 4 个审查 agent 并行运行。全部必须通过。向用户呈现合并结果并获取明确"确认"后才能完成。
>
> **验证完成后不要自动继续。等待用户明确确认后再标记工作完成。**
> **获取用户确认前不要勾选 F1-F4。** 拒绝或用户反馈 → 修复 → 重新运行 → 再次呈现 → 等待确认。

- [ ] F1. **计划合规审计** — `oracle`
  阅读整个计划。对每个"必须有"：验证实现存在（读取文件、curl 端点、运行命令）。对每个"必须没有"：在代码库中搜索禁止模式 — 如果发现则拒绝并给出 file:line。检查 .sisyphus/evidence/ 中的证据文件是否存在。将交付物与计划进行比较。
  输出: `必须有 [N/N] | 必须没有 [N/N] | 任务 [N/N] | 结论: 通过/拒绝`

- [ ] F2. **代码质量审查** — `unspecified-high`
  运行 `tsc --noEmit` + linter + `bun test`。审查所有更改的文件：`as any`/`@ts-ignore`、空 catch、生产代码中的 console.log、注释掉的代码、未使用的导入。检查 AI slop：过度注释、过度抽象、通用名称（data/result/item/temp）。
  输出: `构建 [通过/失败] | Lint [通过/失败] | 测试 [N 通过/N 失败] | 文件 [N 清洁/N 问题] | 结论`

- [ ] F3. **真实手动 QA** — `unspecified-high` (+ `playwright` skill 如果有 UI)
  从干净状态开始。执行每个任务的每个 QA 场景 — 按照确切步骤操作，捕获证据。测试跨任务集成（功能协同工作，而不是隔离测试）。测试边缘情况：空状态、无效输入、快速操作。保存到 `.sisyphus/evidence/final-qa/`。
  输出: `场景 [N/N 通过] | 集成 [N/N] | 边缘情况 [N 已测试] | 结论`

- [ ] F4. **范围保真度检查** — `deep`
  对每个任务：阅读"做什么"，阅读实际差异（git log/diff）。验证 1:1 — 规范中的所有内容都已构建（无遗漏），规范之外的内容未构建（无蔓延）。检查"必须没有"合规性。检测跨任务污染：任务 N 触及任务 M 的文件。标记未 accounted 的更改。
  输出: `任务 [N/N 合规] | 污染 [清洁/N 问题] | 未 accounted [清洁/N 文件] | 结论`

---

## Commit Strategy

- **Wave 1**: `feat(init): project scaffolding with pyproject.toml and directory structure`
- **Wave 2**: `feat(core): implement ODE solver, PMSM model, and parameter identification algorithms`
- **Wave 3**: `feat(gui): PySide6 GUI panels for model config, simulation, and parameter ID`
- **Wave 4**: `test(verification): end-to-end, physics, performance, and security tests`
- **Final**: `chore(review): final verification and cleanup`

---

## Success Criteria

### 验证命令
```bash
# 构建验证
uv pip install -e .  # Expected: 成功构建 C++ 扩展

# 测试验证
pytest tests/ -v  # Expected: 所有测试通过

# GUI 启动验证
python -m param_id_gui.main  # Expected: PySide6 窗口显示

# 性能验证
pytest tests/benchmark/ -v  # Expected: C++ 比 Python 快 > 5x
```

### 最终清单
- [ ] 所有"必须有" present
- [ ] 所有"必须没有" absent
- [ ] 所有测试通过
- [ ] C++ 构建成功
- [ ] GUI 启动成功
- [ ] 参数识别精度达标
- [ ] 性能基准达标
