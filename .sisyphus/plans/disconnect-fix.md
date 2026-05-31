# 断链修复计划 — 端到端工作流集成

> 修复 param_id_gui 项目的 10 个断链点，使 GUI → Orchestrator → Model → DataBus → GUI 显示的完整数据流可执行。

## TL;DR

> **快速总结**: 项目 25 个功能 Task 已完成、515 测试通过，但所有模块互相断开。本次修复创建 SimulationController 胶水类 + C++ 兼容层，连接 GUI ↔ Core ↔ C++ 的完整数据流。
> 
> **交付物**:
> - `param_id_gui/core/simulation_controller.py` — 胶水类，桥接 GUI ↔ Orchestrator ↔ DataBus
> - `param_id_gui/core/_core_compat.py` — C++/Python 兼容层，自动 fallback
> - 修改后的 `main_window.py` / `simulation.py` / `main.py` — 信号连接 + 数据绑定
> - 端到端集成测试
> 
> **预估工作量**: Medium
> **并行执行**: YES - 3 waves
> **关键路径**: T1 → T3 → T5 → T7 → T9

---

## Context

### 原始请求
用户深度审查发现模块间完全断开，要求修复所有断链点使端到端工作流可执行。

### 审查总结
**10 个断链点**（3 🔴 + 3 🟠 + 4 🟡）：
- 🔴 #1 C++ _core 未被 import
- 🔴 #2 _update_display() 空实现
- 🔴 #3 _on_start() 未触发仿真
- 🔴 #4 _setup_panels() 无 connect()
- 🟠 #5 params_changed 信号未连接
- 🟠 #6 无 Orchestrator↔DataBus 桥接
- 🟠 #7 模型结果未发布到 DataBus
- 🟡 #8 GUI 面板未订阅 DataBus
- 🟡 #9 ModelRegistry 未在 GUI 使用
- 🟡 #10 C++ 缺少部分模型（已确认不在范围）

**根因**: 缺少 SimulationController 胶水类。

### Metis 审查发现
- **线程安全**: 必须使用 `moveToThread()` 模式，GUI 通过 QTimer 轮询 DataBus
- **发布频率**: DataBus 全速发布，GUI 以 30-60 FPS 读取 `read_latest()`
- **参数同步**: 仿真开始时快照参数，非实时同步
- **C++ fallback**: `try/except ImportError` 包装，静默降级
- **范围控制**: ParamIDPanel 不在本次范围，断链点 #10 不在范围

---

## Work Objectives

### 核心目标
创建胶水代码连接已存在的独立组件，使端到端仿真工作流可执行。

### 具体交付物
- `simulation_controller.py`: QObject 子类，持有 Orchestrator + DataBus + ModelRegistry
- `_core_compat.py`: C++ _core 自动检测 + fallback
- 修改后的 GUI 面板：信号连接 + 数据显示
- 端到端集成测试

### 完成定义
- [ ] GUI 点击 Start → 仿真运行 → 波形实时更新 → Stop 停止
- [ ] C++ 加速自动生效，不可用时静默 fallback
- [ ] 所有现有 515 个测试通过（零回归）
- [ ] 端到端集成测试覆盖完整数据流

### Must Have
- SimulationController 桥接 GUI ↔ Orchestrator
- DataBus 发布仿真结果，GUI 订阅显示
- C++ _core 兼容层 + fallback
- QThread moveToThread() 线程模式
- GUI 定时器轮询 DataBus（30-60 FPS）

### Must NOT Have（护栏）
- 不修改 `orchestrator.py`、`data_bus.py`、`model_registry.py`
- 不修改 `param_id_gui/models/` 目录下的任何文件
- 不修改 ParamIDPanel 或 ResultsPanel
- 不添加新 C++ 绑定
- 不修改 pyproject.toml 或 CMake 配置
- 不添加任何新依赖
- 不使用 `as any`、`@ts-ignore` 等类型压制

---

## Verification Strategy

> **零人工干预** — 所有验证由 agent 执行。

- **自动化测试**: pytest + 端到端集成测试
- **GUI 验证**: QTest 模拟按钮点击 + QTimer 超时检查
- **证据**: `.sisyphus/evidence/disconnect-fix-*.txt`

---

## Execution Strategy

### 并行执行波次

```
Wave 1 (立即并行 — 基础层):
├── Task 1: C++ 兼容层 (_core_compat.py) [quick]
├── Task 2: SimulationController 骨架 [deep]
└── Task 3: GUI 信号映射表审查 [quick]

Wave 2 (Wave 1 完成后并行 — 连接层):
├── Task 4: SimulationController 仿真生命周期 [deep]
├── Task 5: SimulationController DataBus 桥接 [deep]
└── Task 6: GUI 面板连接 (simulation.py) [visual-engineering]

Wave 3 (Wave 2 完成后并行 — 集成层):
├── Task 7: MainWindow 全局连接 [visual-engineering]
├── Task 8: main.py 入口集成 [quick]
└── Task 9: 端到端集成测试 [deep]

Wave FINAL (所有任务完成后):
├── Task F1: 计划合规审计
├── Task F2: 代码质量审查
└── Task F3: 端到端 QA
```

### 依赖矩阵

| Task | 依赖 | 被依赖 | 阻断 |
|------|------|--------|------|
| 1 | 无 | 4,8 | 是 |
| 2 | 无 | 4,5 | 是 |
| 3 | 无 | 6,7 | 是 |
| 4 | 1,2 | 9 | 是 |
| 5 | 2 | 9 | 是 |
| 6 | 3 | 9 | 是 |
| 7 | 3 | 9 | 是 |
| 8 | 1 | 9 | 是 |
| 9 | 4-8 | F1-F3 | 是 |

---

## TODOs

- [ ] 1. C++ 兼容层 — `_core_compat.py`

  **What to do**:
  - 创建 `param_id_gui/core/_core_compat.py`
  - 实现 `get_core()` 函数：`try: import param_id_gui._core as core; return core` + `except ImportError: logging.warning("C++ core unavailable, using Python fallback"); return None`
  - 实现 `get_solver()` 函数：返回 C++ RK4Solver 或 Python fallback
  - 实现 `get_filters()` 函数：返回 C++ 滤波器或 Python fallback
  - 在模块顶部添加 `__all__ = ["get_core", "get_solver", "get_filters"]`

  **Must NOT do**:
  - 不修改 `param_id_gui/cpp/` 目录下的任何文件
  - 不修改 `param_id_gui/models/` 目录下的任何文件

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 单文件创建，逻辑简单（try/except + 返回值）
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Tasks 4, 8
  - **Blocked By**: None

  **References**:
  - `param_id_gui/cpp/src/bindings.cpp:1-356` — nanobind 绑定定义，了解 _core 模块暴露的接口
  - `param_id_gui/core/orchestrator.py:1-498` — Orchestrator 类，了解需要桥接的核心组件
  - `param_id_gui/core/data_bus.py:184-221` — DataBus publish 模式参考

  **Acceptance Criteria**:
  - [ ] `python -c "from param_id_gui.core._core_compat import get_core; c = get_core(); print('OK' if c else 'fallback')"` 不报错
  - [ ] 当 C++ 可用时输出 "OK"，不可用时输出 "fallback"

  **QA Scenarios**:

  ```
  Scenario: C++ 核心模块兼容性检测
    Tool: Bash
    Preconditions: 项目根目录, .venv 已激活
    Steps:
      1. 运行 `.venv\\Scripts\\python.exe -c "from param_id_gui.core._core_compat import get_core; c = get_core(); print(type(c).__name__ if c else 'None')"`
      2. 验证输出为 "module" 或 "None"
    Expected Result: 输出 "module"（C++ 可用）或 "None"（fallback 模式），无 ImportError
    Failure Indicators: ImportError, ModuleNotFoundError, 输出为空
    Evidence: `.sisyphus/evidence/disconnect-fix-core-compat.txt`

  Scenario: get_solver() 返回可用求解器
    Tool: Bash
    Preconditions: 同上
    Steps:
      1. 运行 `.venv\\Scripts\\python.exe -c "from param_id_gui.core._core_compat import get_solver; s = get_solver(1e-4); print(type(s).__name__)"`
      2. 验证输出为 "RK4Solver" 或 "None"
    Expected Result: 不报错，返回求解器实例或 None
    Failure Indicators: TypeError, AttributeError
    Evidence: `.sisyphus/evidence/disconnect-fix-core-compat.txt`
  ```

  **Commit**: YES
  - Message: `feat(core): add C++ compatibility layer with Python fallback`
  - Files: `param_id_gui/core/_core_compat.py`

---

- [ ] 2. SimulationController 骨架

  **What to do**:
  - 创建 `param_id_gui/core/simulation_controller.py`
  - 实现 `SimulationController(QObject)` 类：
    - 属性: `_orchestrator`, `_data_bus`, `_model_registry`, `_worker_thread`, `_current_params`, `_current_model_name`
    - 信号: `state_changed(str)`, `step_completed(dict)`, `error_occurred(str)`
    - 构造函数: 接收 Orchestrator + DataBus + ModelRegistry 实例（依赖注入）
    - 方法签名: `start_simulation(model_name, params, duration, step_size)`, `pause_simulation()`, `stop_simulation()`, `reset_simulation()`, `get_latest_data()`
  - 实现 `SimulationWorker(QObject)` 内部类：
    - `run()` 方法：注册模型到 Orchestrator → 注册 DataBus 发布 → 调用 `orchestrator.run()`
    - 每步完成后 emit `step_completed` 信号
    - 使用 `moveToThread()` 模式（不是继承 QThread）
  - 参考 `orchestrator.py:329-349` 的 `start_threaded()` 线程模式

  **Must NOT do**:
  - 不修改 `orchestrator.py`、`data_bus.py` 的任何代码
  - 不实现 GUI 更新逻辑（Task 6 负责）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 核心架构设计，需要理解 Orchestrator + DataBus + QThread 交互
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Tasks 4, 5
  - **Blocked By**: None

  **References**:
  - `param_id_gui/core/orchestrator.py:329-349` — `start_threaded()` 方法，QThread 使用模式
  - `param_id_gui/core/orchestrator.py:146-154` — `register_stepper()` 方法，了解如何注册仿真步
  - `param_id_gui/core/data_bus.py:184-221` — `publish()` 方法，了解如何发布数据
  - `param_id_gui/core/data_bus.py:223-259` — `subscribe()` 方法，了解如何订阅数据
  - `param_id_gui/core/model_registry.py:79-131` — `register()` / `get()` 方法
  - `param_id_gui/core/orchestrator.py:329-349` — `start_threaded()` 线程化运行模式
  - `param_id_gui/core/types.py:16-21` — `SimulationState` 枚举

  **Acceptance Criteria**:
  - [ ] `from param_id_gui.core.simulation_controller import SimulationController` 成功
  - [ ] `SimulationController` 继承 `QObject`
  - [ ] 构造函数接收 3 个参数（orchestrator, data_bus, model_registry）

  **QA Scenarios**:

  ```
  Scenario: SimulationController 导入与实例化
    Tool: Bash
    Preconditions: 项目根目录, .venv 已激活
    Steps:
      1. 运行 `.venv\\Scripts\\python.exe -c "from param_id_gui.core.simulation_controller import SimulationController; print('OK')"`
      2. 验证无 ImportError
    Expected Result: 输出 "OK"
    Failure Indicators: ImportError, SyntaxError
    Evidence: `.sisyphus/evidence/disconnect-fix-controller-skeleton.txt`

  Scenario: SimulationController 依赖注入
    Tool: Bash
    Preconditions: 同上
    Steps:
      1. 运行 Python 脚本：创建 Orchestrator + DataBus + ModelRegistry 实例
      2. 创建 SimulationController 实例
      3. 验证 controller._orchestrator 不为 None
    Expected Result: 所有依赖正确注入
    Failure Indicators: TypeError（参数不匹配）, AttributeError
    Evidence: `.sisyphus/evidence/disconnect-fix-controller-skeleton.txt`
  ```

  **Commit**: YES (groups with Task 4, 5)
  - Message: `feat(core): add SimulationController skeleton with QThread worker`
  - Files: `param_id_gui/core/simulation_controller.py`

---

- [ ] 3. GUI 信号映射表审查

  **What to do**:
  - 读取 `param_id_gui/gui/panels/simulation.py`，列出所有已定义的信号和按钮
  - 读取 `param_id_gui/gui/panels/model_config.py`，列出所有已定义的信号
  - 读取 `param_id_gui/gui/main_window.py`，列出所有 QAction 和菜单项
  - 创建信号映射表：`信号名 → 应该连接到 → SimulationController 的哪个方法`
  - 输出映射表到 `.sisyphus/evidence/disconnect-fix-signal-map.txt`

  **Must NOT do**:
  - 不修改任何代码文件
  - 只做审查和文档化

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 纯读取 + 文档化，无代码修改
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Tasks 6, 7
  - **Blocked By**: None

  **References**:
  - `param_id_gui/gui/panels/simulation.py:1-588` — SimulationPanel 完整源码
  - `param_id_gui/gui/panels/model_config.py:1-789` — ModelConfigPanel 完整源码
  - `param_id_gui/gui/main_window.py:1-289` — MainWindow 完整源码

  **Acceptance Criteria**:
  - [ ] 信号映射表文件存在且包含所有面板的信号列表
  - [ ] 每个信号都有明确的连接目标

  **QA Scenarios**:

  ```
  Scenario: 信号映射表完整性
    Tool: Bash
    Preconditions: Task 3 完成
    Steps:
      1. 检查 `.sisyphus/evidence/disconnect-fix-signal-map.txt` 存在
      2. 验证文件包含 "SimulationPanel"、"ModelConfigPanel"、"MainWindow" 三个段落
      3. 验证每个段落至少有 3 个信号定义
    Expected Result: 映射表完整，覆盖所有面板
    Failure Indicators: 文件不存在, 缺少面板段落, 信号数量不足
    Evidence: `.sisyphus/evidence/disconnect-fix-signal-map.txt`
  ```

  **Commit**: NO (纯审查，无文件变更)

---

- [ ] 4. SimulationController 仿真生命周期

  **What to do**:
  - 在 `simulation_controller.py` 中实现 `start_simulation()` 方法：
    1. 快照当前参数（从 params dict）
    2. 从 ModelRegistry 获取模型类
    3. 实例化模型，注入参数
    4. 创建 SimulationWorker，moveToThread
    5. 连接 worker.finished → _on_simulation_finished
    6. 启动 worker 线程
  - 实现 `pause_simulation()` / `stop_simulation()` / `reset_simulation()`
  - 实现 `_on_simulation_finished()`：清理线程，emit state_changed("stopped")
  - 实现状态机：IDLE → RUNNING → PAUSED → STOPPED

  **Must NOT do**:
  - 不修改 orchestrator.py
  - 不实现 DataBus 发布（Task 5 负责）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 核心生命周期管理，需要理解 QThread 状态机
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6)
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:
  - `param_id_gui/core/orchestrator.py:329-349` — `start_threaded()` 方法，QThread 创建模式
  - `param_id_gui/core/orchestrator.py:202-360` — `run()` 方法，仿真循环逻辑
  - `param_id_gui/core/orchestrator.py:363-396` — `pause()` / `stop()` 方法
  - `param_id_gui/core/types.py:57-65` — `SimulationState` 枚举值
  - `param_id_gui/gui/panels/simulation.py:295-348` — `_on_start()` / `_on_pause()` / `_on_stop()` 当前实现（只切换按钮状态）

  **Acceptance Criteria**:
  - [ ] `controller.start_simulation("PMSM", params, 0.1, 1e-4)` 不报错
  - [ ] `controller.stop_simulation()` 正确停止
  - [ ] state_changed 信号正确发射

  **QA Scenarios**:

  ```
  Scenario: 仿真启动与停止
    Tool: Bash
    Preconditions: SimulationController 已创建
    Steps:
      1. 创建 Orchestrator + DataBus + ModelRegistry
      2. 创建 SimulationController
      3. 调用 start_simulation("PMSM", pmsm_params, 0.01, 1e-4)
      4. 等待 100ms
      5. 调用 stop_simulation()
      6. 验证 orchestrator.get_state() == SimulationState.STOPPED
    Expected Result: 仿真启动后状态为 RUNNING，停止后状态为 STOPPED
    Failure Indicators: 死锁, 状态未变更, 异常
    Evidence: `.sisyphus/evidence/disconnect-fix-lifecycle.txt`

  Scenario: 仿真暂停与恢复
    Tool: Bash
    Preconditions: 同上
    Steps:
      1. 启动仿真
      2. 等待 50ms
      3. 调用 pause_simulation()
      4. 验证状态为 PAUSED
      5. 调用 resume_simulation()
      6. 验证状态为 RUNNING
    Expected Result: 暂停后状态正确，恢复后继续运行
    Failure Indicators: 状态未变更, 恢复后死锁
    Evidence: `.sisyphus/evidence/disconnect-fix-lifecycle.txt`
  ```

  **Commit**: YES (groups with Task 2, 5)
  - Message: `feat(core): implement SimulationController lifecycle management`
  - Files: `param_id_gui/core/simulation_controller.py`

---

- [ ] 5. SimulationController DataBus 桥接

  **What to do**:
  - 在 SimulationWorker.run() 中添加 DataBus 发布逻辑：
    1. 模型 step() 返回 dict 后，调用 `data_bus.publish_vector(model_name, dict, module_id="simulation")`
    2. 或遍历 dict 的 key-value，调用 `data_bus.publish_scalar(f"{model_name}/{key}", value, module_id="simulation")`
    3. 参考 `data_bus.py:231-270` 的 `publish_scalar()` / `publish_vector()` 方法
    4. 同时 emit `step_completed(dict)` 信号
  - 在 SimulationController 中添加 `get_latest_data()` 方法：
    1. 从 DataBus 读取所有已发布 topic 的最新值
    2. 返回 dict 格式 {topic: value}
  - 实现 `_on_step_completed()` slot：更新内部 `_latest_data` 缓冲

  **Must NOT do**:
  - 不修改 data_bus.py
  - 不实现 GUI 更新逻辑（Task 6 负责）

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: DataBus 发布/订阅逻辑，需要理解 topic 命名和回调机制
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 6)
  - **Blocks**: Task 9
  - **Blocked By**: Task 2

  **References**:
  - `param_id_gui/core/data_bus.py:231-270` — `publish_scalar()` / `publish_vector()` 方法
  - `param_id_gui/core/data_bus.py:275-282` — `subscribe()` 方法签名和实现
  - `param_id_gui/core/data_bus.py:284-295` — `read_latest()` 方法
  - `param_id_gui/core/orchestrator.py:250-291` — 仿真循环中数据发布模式

  **Acceptance Criteria**:
  - [ ] 仿真运行后 DataBus 包含已发布的 topic
  - [ ] `get_latest_data()` 返回正确的数据

  **QA Scenarios**:

  ```
  Scenario: DataBus 发布验证
    Tool: Bash
    Preconditions: SimulationController 已创建
    Steps:
      1. 创建组件并启动仿真
      2. 等待 200ms
      3. 停止仿真
      4. 调用 data_bus.read_latest("PMSM/id") 或类似 topic
      5. 验证返回值不为 None
    Expected Result: DataBus 中有仿真数据
    Failure Indicators: read_latest 返回 None, topic 不存在
    Evidence: `.sisyphus/evidence/disconnect-fix-databus.txt`

  Scenario: get_latest_data() 返回完整数据
    Tool: Bash
    Preconditions: 同上
    Steps:
      1. 仿真运行 200ms 后调用 controller.get_latest_data()
      2. 验证返回 dict 包含至少 3 个 key（如 id, iq, speed 等）
      3. 验证所有值为 finite 浮点数
    Expected Result: 返回非空 dict，所有值 finite
    Failure Indicators: 空 dict, NaN/Inf 值
    Evidence: `.sisyphus/evidence/disconnect-fix-databus.txt`
  ```

  **Commit**: YES (groups with Task 2, 4)
  - Message: `feat(core): implement SimulationController DataBus bridge`
  - Files: `param_id_gui/core/simulation_controller.py`

---

- [ ] 6. GUI 面板连接 (simulation.py)

  **What to do**:
  - 修改 `param_id_gui/gui/panels/simulation.py`：
    1. 添加 `_controller: SimulationController` 属性
    2. 添加 `set_controller(controller)` 方法
    3. 实现 `_on_start()`：调用 `controller.start_simulation(...)` 而非只切换按钮
    4. 实现 `_on_pause()` / `_on_stop()`：调用 controller 对应方法
    5. 实现 `_update_display()`：从 `controller.get_latest_data()` 读取并更新波形
    6. 添加 `QTimer` 定时器（33ms 间隔 ≈ 30 FPS），触发 `_update_display()`
    7. 连接 `controller.step_completed` → `_on_step_completed`（更新内部缓冲）
  - 波形更新逻辑：
    - 读取 `latest_data["id"]`, `latest_data["iq"]`, `latest_data["speed"]` 等
    - 调用 `self._current_waveform.add_data_point(key, value)`

  **Must NOT do**:
  - 不修改 SimulationController（Task 4, 5 已完成）
  - 不修改 DataBus 或 Orchestrator
  - 不实现 ModelConfigPanel 连接（Task 7 负责）

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: GUI 面板修改，涉及 PySide6 信号/槽、QTimer、波形更新
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 9
  - **Blocked By**: Task 3

  **References**:
  - `param_id_gui/gui/panels/simulation.py:392-426` — `_on_start()` / `_on_pause()` / `_on_stop()` 当前实现（空壳）
  - `param_id_gui/gui/panels/simulation.py:156-255` — `_setup_ui()` 中的按钮和控件定义
  - `param_id_gui/gui/panels/simulation.py:151-152` — `_update_timer` QTimer 初始化
  - `param_id_gui/gui/panels/simulation.py:30-131` — WaveformWidget 类定义（在 simulation.py 内部）
  - `param_id_gui/gui/panels/simulation.py:370-373` — `_update_display()` 当前空实现（pass）

  **Acceptance Criteria**:
  - [ ] `_on_start()` 调用 controller.start_simulation()
  - [ ] `_update_display()` 从 controller 读取数据并更新波形
  - [ ] QTimer 以 30 FPS 触发 `_update_display()`

  **QA Scenarios**:

  ```
  Scenario: SimulationPanel 启动按钮触发仿真
    Tool: Bash (pytest)
    Preconditions: SimulationController 已创建并注入到 panel
    Steps:
      1. 创建 SimulationPanel + SimulationController
      2. 调用 panel._on_start()
      3. 等待 100ms
      4. 验证 controller._orchestrator.get_state() == SimulationState.RUNNING
    Expected Result: 按钮点击触发真实仿真
    Failure Indicators: 状态仍为 IDLE, AttributeError
    Evidence: `.sisyphus/evidence/disconnect-fix-gui-sim.txt`

  Scenario: 波形实时更新
    Tool: Bash (pytest)
    Preconditions: 同上
    Steps:
      1. 启动仿真
      2. 等待 500ms
      3. 检查 panel._current_waveform._data 中是否有数据
    Expected Result: 波形数据非空
    Failure Indicators: _data 为空 dict, 无新数据点
    Evidence: `.sisyphus/evidence/disconnect-fix-gui-sim.txt`
  ```

  **Commit**: YES
  - Message: `feat(gui): connect SimulationPanel to SimulationController`
  - Files: `param_id_gui/gui/panels/simulation.py`

---

- [ ] 7. MainWindow 全局连接

  **What to do**:
  - 修改 `param_id_gui/gui/main_window.py`：
    1. 添加 `_controller: SimulationController` 属性
    2. 添加 `set_controller(controller)` 方法
    3. 在 `_setup_panels()` 中：
       - 为每个面板调用 `panel.set_controller(controller)`
       - 连接 `controller.state_changed` → `_update_status()`
    4. 实现 `_update_status(status_str)`：更新状态栏文本
    5. 连接菜单栏/工具栏的 QAction：
       - `action_start.triggered` → `controller.start_simulation()`
       - `action_pause.triggered` → `controller.pause_simulation()`
       - `action_stop.triggered` → `controller.stop_simulation()`
       - `action_new.triggered` → `controller.reset_simulation()`
  - 实现 ModelConfigPanel 信号连接：
    1. 连接 `model_config_panel.params_changed` → `_on_params_changed`
    2. `_on_params_changed(model_name, params)` 更新 `controller._current_model_name` 和 `controller._current_params`

  **Must NOT do**:
  - 不修改 SimulationController
  - 不修改 ParamIDPanel 或 ResultsPanel
  - 不修改 ModelConfigPanel 内部实现

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: GUI 主窗口修改，涉及菜单栏、工具栏、信号连接
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 8, 9)
  - **Blocks**: Task 9
  - **Blocked By**: Task 3

  **References**:
  - `param_id_gui/gui/main_window.py:143-159` — `_setup_panels()` 当前实现（只有 addTab）
  - `param_id_gui/gui/main_window.py:58-103` — `_setup_menu_bar()` 中的 QAction 定义（start/pause/stop 未连接）
  - `param_id_gui/gui/main_window.py:105-129` — `_setup_toolbar()` 中的 QAction 定义（未连接）
  - `param_id_gui/gui/panels/model_config.py:96` — `params_changed` 信号定义（Signal(str, dict)）
  - `param_id_gui/gui/panels/model_config.py:381` — `params_changed.emit()` 调用

  **Acceptance Criteria**:
  - [ ] `_setup_panels()` 中有 `connect()` 调用
  - [ ] `_update_status()` 更新状态栏文本
  - [ ] 菜单 Start/QAction 触发 controller.start_simulation()

  **QA Scenarios**:

  ```
  Scenario: MainWindow 菜单连接验证
    Tool: Bash (pytest)
    Preconditions: MainWindow 已创建并注入 controller
    Steps:
      1. 创建 MainWindow + SimulationController
      2. 调用 main_window._update_status("running")
      3. 验证 statusBar 当前文本包含 "running"
    Expected Result: 状态栏正确更新
    Failure Indicators: statusBar 文本未变更
    Evidence: `.sisyphus/evidence/disconnect-fix-mainwindow.txt`

  Scenario: ModelConfigPanel 参数同步
    Tool: Bash (pytest)
    Preconditions: 同上
    Steps:
      1. 模拟 model_config_panel.params_changed.emit("PMSM", {"Rs": 0.5})
      2. 验证 controller._current_params 包含 "Rs" key
      3. 验证 controller._current_model_name == "PMSM"
    Expected Result: 参数和模型名正确同步到 controller
    Failure Indicators: _current_params 未更新, _current_model_name 未更新
    Evidence: `.sisyphus/evidence/disconnect-fix-mainwindow.txt`
  ```

  **Commit**: YES
  - Message: `feat(gui): connect MainWindow to SimulationController`
  - Files: `param_id_gui/gui/main_window.py`

---

- [ ] 8. main.py 入口集成

  **What to do**:
  - 修改 `param_id_gui/main.py`：
    1. 导入 SimulationController, Orchestrator, DataBus, ModelRegistry
    2. 导入 `_core_compat.get_core`
    3. 在 `main()` 函数中：
       - 调用 `core = get_core()` 检测 C++ 可用性
       - 创建 Orchestrator, DataBus, ModelRegistry 实例
       - 创建 SimulationController 实例
       - 创建 MainWindow，传入 controller
    4. 注册默认模型到 ModelRegistry（PMSM, FOC, Buck, Boost）
    5. 打印 C++ 状态日志

  **Must NOT do**:
  - 不修改 pyproject.toml
  - 不修改 CMake 配置
  - 不添加新依赖

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 入口文件修改，逻辑简单（实例化 + 注入）
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 7, 9)
  - **Blocks**: Task 9
  - **Blocked By**: Task 1

  **References**:
  - `param_id_gui/main.py:1-39` — 当前 main.py 实现
  - `param_id_gui/core/orchestrator.py:1-25` — Orchestrator 导入路径
  - `param_id_gui/core/data_bus.py:1-15` — DataBus 导入路径
  - `param_id_gui/core/model_registry.py:1-15` — ModelRegistry 导入路径
  - `param_id_gui/core/_core_compat.py` — Task 1 创建的兼容层

  **Acceptance Criteria**:
  - [ ] `python -m param_id_gui.main` 启动成功
  - [ ] 控制台输出 C++ 状态日志
  - [ ] MainWindow 显示后标题包含 "参数识别"

  **QA Scenarios**:

  ```
  Scenario: 应用启动与组件初始化
    Tool: Bash
    Preconditions: 项目根目录, .venv 已激活
    Steps:
      1. 运行 `.venv\\Scripts\\python.exe -m param_id_gui.main` (后台，3秒后 kill)
      2. 检查 stderr 输出是否包含 "C++" 或 "core" 关键字
      3. 检查进程是否正常退出（无崩溃）
    Expected Result: 进程正常启动，输出 C++ 状态日志
    Failure Indicators: ImportError, 进程崩溃, 无输出
    Evidence: `.sisyphus/evidence/disconnect-fix-main-py.txt`

  Scenario: 模型注册验证
    Tool: Bash
    Preconditions: 同上
    Steps:
      1. 运行 Python 脚本：创建 ModelRegistry，注册 PMSM
      2. 验证 registry.get("PMSM") 不为 None
    Expected Result: 模型注册成功
    Failure Indicators: get() 返回 None, 注册失败
    Evidence: `.sisyphus/evidence/disconnect-fix-main-py.txt`
  ```

  **Commit**: YES
  - Message: `feat(app): integrate SimulationController into main entry point`
  - Files: `param_id_gui/main.py`

---

- [ ] 9. 端到端集成测试

  **What to do**:
  - 创建 `tests/integration/test_disconnect_fix.py`：
    1. 测试 C++ 兼容层：`test_core_compat_fallback()`
    2. 测试 SimulationController 生命周期：`test_controller_lifecycle()`
    3. 测试 DataBus 桥接：`test_databus_bridge()`
    4. 测试 GUI 信号连接：`test_gui_signals()`
    5. 测试端到端工作流：`test_e2e_simulation()`
    - 使用 pytest-qt 的 `qtbot` fixture
    - 使用 `QTest.qWait()` 等待异步操作
    - 所有测试必须在 10 秒内完成
  - 测试场景：
    - 正常流程：选择模型 → 设置参数 → Start → 运行 → Stop → 验证数据
    - 异常流程：无效参数 → 错误处理
    - 边界条件：duration=0, step_size=0

  **Must NOT do**:
  - 不修改现有测试文件
  - 不删除任何测试

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 端到端测试设计，需要理解完整数据流
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 7, 8)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: Tasks 4, 5, 6

  **References**:
  - `tests/integration/test_workflow.py:1-100` — 现有集成测试结构参考
  - `tests/conftest.py:1-50` — fixture 定义参考
  - `param_id_gui/core/simulation_controller.py` — Task 2/4/5 创建的 SimulationController
  - `param_id_gui/gui/panels/simulation.py` — Task 6 修改后的 SimulationPanel

  **Acceptance Criteria**:
  - [ ] 所有新测试通过
  - [ ] 端到端测试覆盖完整数据流
  - [ ] 现有 515 个测试通过（零回归）

  **QA Scenarios**:

  ```
  Scenario: 端到端仿真工作流
    Tool: Bash (pytest)
    Preconditions: 所有 Task 1-8 完成
    Steps:
      1. 运行 `.venv\\Scripts\\python.exe -m pytest tests/integration/test_disconnect_fix.py -v`
      2. 验证所有测试通过
      3. 运行 `.venv\\Scripts\\python.exe -m pytest tests/ -v` 完整测试套件
      4. 验证 515+ 测试通过，0 失败
    Expected Result: 新测试全部通过，现有测试零回归
    Failure Indicators: 任何测试失败, 回归
    Evidence: `.sisyphus/evidence/disconnect-fix-e2e.txt`

  Scenario: 无效参数处理
    Tool: Bash (pytest)
    Preconditions: SimulationController 已创建
    Steps:
      1. 调用 start_simulation("PMSM", {}, 0.1, 1e-4)  # 空参数
      2. 验证 error_occurred 信号被发射
    Expected Result: 优雅错误处理，不崩溃
    Failure Indicators: 未捕获异常, 崩溃
    Evidence: `.sisyphus/evidence/disconnect-fix-e2e.txt`
  ```

  **Commit**: YES
  - Message: `test(integration): add end-to-end disconnect fix tests`
  - Files: `tests/integration/test_disconnect_fix.py`

---

## Final Verification Wave

> 3 个审查代理并行运行 — 全部通过后才能交付。

- [ ] F1. **计划合规审计** — `oracle`
  随机抽取 3-5 个任务，验证文件存在、代码模式、QA 场景通过。
  输出：`[8/8] ✅` 或 `[6/8] ❌ → [原因]`

- [ ] F2. **代码质量审查** — `oracle`
  运行完整测试套件，检查零回归。
  输出：`✅ 525+ tests passed` 或 `❌ [失败列表]`

- [ ] F3. **端到端 QA** — `unspecified-high`
  执行所有 QA Scenarios 的真实 bash 命令。
  输出：`✅ 9/9 场景通过` 或 `❌ [失败场景]`

---

## Commit Strategy

| Task | Commit Message | Files |
|------|----------------|-------|
| 1 | `feat(core): add C++ compatibility layer with Python fallback` | `_core_compat.py` |
| 2+4+5 | `feat(core): add SimulationController with lifecycle and DataBus bridge` | `simulation_controller.py` |
| 6 | `feat(gui): connect SimulationPanel to SimulationController` | `simulation.py` |
| 7 | `feat(gui): connect MainWindow to SimulationController` | `main_window.py` |
| 8 | `feat(app): integrate SimulationController into main entry point` | `main.py` |
| 9 | `test(integration): add end-to-end disconnect fix tests` | `test_disconnect_fix.py` |

---

## Success Criteria

### 验证命令
```bash
# 1. C++ 兼容层
python -c "from param_id_gui.core._core_compat import get_core; print('OK' if get_core() else 'fallback')"

# 2. SimulationController 导入
python -c "from param_id_gui.core.simulation_controller import SimulationController; print('OK')"

# 3. 端到端测试
pytest tests/integration/test_disconnect_fix.py -v

# 4. 完整测试套件（零回归）
pytest tests/ -v

# 5. 应用启动
python -m param_id_gui.main  # 应正常启动 GUI 窗口
```

### 最终检查清单
- [ ] 所有 "Must Have" 存在
- [ ] 所有 "Must NOT Have" 不存在
- [ ] C++ 兼容层工作（fallback 模式）
- [ ] GUI 点击 Start → 仿真运行 → 波形更新 → Stop
- [ ] 515+ 测试通过（零回归）

