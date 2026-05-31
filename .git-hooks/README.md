# Git Hooks - 关联文件检测

本项目使用 Git pre-commit hook 来检测代码更改是否需要同步更新关联文件和文档。

## 功能概述

当你修改某个文件时，hook 会自动检查：
1. 该文件是否有需要同步更新的关联文件
2. 关联文件是否已被暂存或更新
3. 是否存在已知的代码问题（如重复定义）

## 安装

### 方法 1: Python 安装脚本（推荐，跨平台）

```bash
# 安装
python .git-hooks/install-hooks.py

# 强制覆盖现有 hook
python .git-hooks/install-hooks.py --force

# 仅检查安装状态
python .git-hooks/install-hooks.py --check

# 卸载
python .git-hooks/install-hooks.py --uninstall
```

### 方法 2: Shell 脚本 (Linux/macOS)

```bash
bash .git-hooks/install.sh
```

### 方法 3: 批处理脚本 (Windows)

```cmd
.git-hooks\install.bat
```

## 使用方法

安装后，hook 会在每次 `git commit` 时自动运行。

### 输出示例

```
============================================================
Git Pre-commit Hook - Related File Check
============================================================

[WARN] The following files may need synchronized updates:

> Type Definition Sync
  Source: param_id_gui/core/types.py
  Related files:
    - param_id_gui/models/motor/pmsm_dq.py [NOT STAGED]
    - param_id_gui/models/power/power_models.py [NOT STAGED]
    - param_id_gui/gui/panels/model_config.py [NOT STAGED]

============================================================
Result: 1 warnings found, commit allowed
============================================================
```

### 严重级别

- **[WARN] 警告**: 提示可能需要更新的关联文件，但允许提交
- **[BLOCK] 阻塞**: 必须修复才能提交（如导出不存在的类）

## 配置

### 配置文件

配置文件位于项目根目录: `.git-hooks-config.yml`

### 环境变量

- `GIT_HOOKS_ENABLED=false` - 临时禁用 hook

### 命令行选项

```bash
# 查看帮助
.git-hooks/pre_commit.py --help

# JSON 输出格式
.git-hooks/pre_commit.py --json

# 显示通过的检查
.git-hooks/pre_commit.py --show-passed

# 禁用颜色输出
.git-hooks/pre_commit.py --no-color
```

## 规则说明

### 模块关联规则

| 触发文件 | 关联文件 | 说明 |
|---------|---------|------|
| `core/types.py` | `models/*.py`, `gui/panels/*.py` | 类型定义同步 |
| `core/orchestrator.py` | `core/types.py`, `gui/panels/simulation.py` | 编排器状态同步 |
| `core/model_registry.py` | `core/types.py`, `gui/panels/model_config.py` | 注册中心同步 |
| `core/data_bus.py` | `core/orchestrator.py`, `gui/panels/simulation.py` | 数据总线同步 |
| `models/motor/pmsm_dq.py` | `models/__init__.py`, `gui/panels/*.py` | PMSM 模型同步 |
| `models/power/power_models.py` | `models/__init__.py`, `gui/panels/model_config.py` | 电源模型同步 |
| `models/controller/foc.py` | `models/__init__.py`, `gui/panels/model_config.py` | FOC 控制器同步 |
| `algorithms/lm.py` | `algorithms/__init__.py`, `gui/panels/param_id.py` | LM 算法同步 |
| `algorithms/pso.py` | `algorithms/__init__.py`, `gui/panels/param_id.py` | PSO 算法同步 |
| `gui/main_window.py` | `gui/panels/*.py` | 主窗口同步 |
| `gui/panels/*.py` | `gui/panels/__init__.py`, `gui/main_window.py` | 面板模块同步 |
| `data/hdf5_handler.py` | `data/__init__.py`, `gui/panels/results.py` | HDF5 处理器同步 |
| `cpp/bindings/*.cpp` | `cmake/CMakeLists.txt`, `cpp/include/*.h` | C++ 绑定同步 |
| `cpp/include/*.h` | `cpp/src/*.cpp`, `cpp/bindings/*.cpp` | C++ 头文件同步 |
| `cpp/src/*.cpp` | `cpp/include/*.h`, `cmake/CMakeLists.txt` | C++ 源文件同步 |
| `cmake/CMakeLists.txt` | `cpp/src/*.cpp`, `cpp/include/*.h` | CMake 配置同步 |
| `pyproject.toml` | `param_id_gui/__init__.py`, `README.md` | 项目配置同步 |

### 特殊规则

| 规则名称 | 严重级别 | 说明 |
|---------|---------|------|
| 导出存在性检查 | BLOCK | 检查 `__init__.py` 导出的类/函数是否在模块中存在 |
| 重复定义检查 | WARN | 检查同一类/函数是否在多个文件中定义 |
| 测试文件关联 | WARN | 修改源文件时，提醒更新对应测试 |
| 测试文件反向关联 | WARN | 修改测试文件时，提醒检查源文件 |

### 文档关联规则

| 触发文件 | 关联文档 | 说明 |
|---------|---------|------|
| `core/*.py`, `models/*.py`, `algorithms/*.py` | `README.md` | 核心模块文档 |
| `core/types.py`, `core/orchestrator.py` 等 | `README.md`, `docs/*.md` | API 文档 |
| `core/*.py`, `models/*.py` | `.sisyphus/plans/param-id-refactor.md` | 重构计划 |

### 已知问题检测

| 问题名称 | 严重级别 | 说明 |
|---------|---------|------|
| SimulationState 重复定义 | WARN | SimulationState 在 orchestrator.py 和 types.py 中重复定义 |
| FidelityLevel 重复定义 | WARN | FidelityLevel 在 model_registry.py 和 types.py 中重复定义 |
| Legacy wrapper 检查 | WARN | 修改新接口时，检查 legacy wrapper 是否需要同步 |

## 自定义规则

### 添加新规则

编辑 `.git-hooks-config.yml` 文件，在 `rules` 部分添加新规则：

```yaml
rules:
  - name: "规则名称"
    description: "规则描述"
    match: "触发文件模式"  # 支持 glob 通配符
    related:
      - "关联文件1"
      - "关联文件2"
    severity: warn  # warn 或 block
    message: "提示信息"
```

### 禁用单条规则

在规则中添加 `enabled: false`：

```yaml
rules:
  - name: "规则名称"
    enabled: false  # 禁用此规则
    match: "..."
```

### 变量说明

在 `related` 中可以使用以下变量：

- `$MODULE`: 匹配的模块路径 (如 `param_id_gui/core`)
- `$FILE`: 匹配的文件名 (如 `types.py`)
- `$BASENAME`: 不带扩展名的文件名 (如 `types`)

### 排除文件

在 `config.exclude_patterns` 中添加不需要检查的文件模式：

```yaml
config:
  exclude_patterns:
    - "*.md"
    - ".gitignore"
    - "build/*"
```

## 故障排除

### Hook 未运行

1. 检查 hook 是否已安装：
   ```bash
   python .git-hooks/install-hooks.py --check
   ```

2. 检查 hook 是否有执行权限 (Linux/macOS)：
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. 检查环境变量是否禁用了 hook：
   ```bash
   echo $GIT_HOOKS_ENABLED
   ```

### 配置文件解析错误

1. 检查 YAML 语法：
   ```bash
   python -c "import yaml; yaml.safe_load(open('.git-hooks-config.yml'))"
   ```

2. 如果没有安装 PyYAML，hook 会使用内置的简单解析器，但可能不支持所有 YAML 特性

### 性能问题

如果 hook 运行缓慢，可以：
1. 减少 `exclude_patterns` 中的模式
2. 简化规则中的通配符模式
3. 使用 `--json` 输出格式减少格式化开销

## 文件结构

```
.git-hooks/
├── pre_commit.py      # 主要检查脚本
├── pre-commit         # Shell 包装器 (Unix)
├── pre-commit.bat     # 批处理包装器 (Windows)
├── install-hooks.py   # Python 安装脚本
├── install.sh         # Shell 安装脚本 (Unix)
├── install.bat        # 批处理安装脚本 (Windows)
└── README.md          # 本文档

.git-hooks-config.yml  # 规则配置文件
```

## 许可证

本项目使用 MIT 许可证。
