#!/bin/sh
# Git Hooks 安装脚本 (POSIX sh 兼容)
# 将 pre-commit hook 安装到 .git/hooks 目录

set -e

# 颜色定义 (POSIX 兼容: 使用 printf 和 tput 回退)
RED=''
GREEN=''
YELLOW=''
NC=''
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    RED=$(tput setaf 1 2>/dev/null || true)
    GREEN=$(tput setaf 2 2>/dev/null || true)
    YELLOW=$(tput setaf 3 2>/dev/null || true)
    NC=$(tput sgr0 2>/dev/null || true)
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 获取仓库根目录
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Git hooks 目录
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "${GREEN}Git Hooks 安装脚本${NC}"
echo "================================"

# 检查是否在 Git 仓库中
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "${RED}错误: 当前目录不是 Git 仓库${NC}"
    exit 1
fi

# 创建 hooks 目录（如果不存在）
mkdir -p "$GIT_HOOKS_DIR"

# 检查是否已存在 pre-commit hook
if [ -f "$GIT_HOOKS_DIR/pre-commit" ]; then
    echo "${YELLOW}警告: pre-commit hook 已存在${NC}"
    printf "是否覆盖? (y/N): "
    read REPLY
    case "$REPLY" in
        [Yy]|[Yy][Ee][Ss]) ;;
        *)
            echo "${YELLOW}已取消安装${NC}"
            exit 0
            ;;
    esac
fi

# 安装 pre-commit hook (使用内联生成，避免依赖源文件)
cat > "$GIT_HOOKS_DIR/pre-commit" << 'HOOK_EOF'
#!/bin/sh
# Git Pre-commit Hook - 关联文件检测
# 此脚本调用 pre_commit.py 进行检查

# 获取仓库根目录
REPO_ROOT="$(git rev-parse --show-toplevel)"

# 获取 .git-hooks 目录 (优先使用仓库根目录下的)
HOOKS_DIR="$REPO_ROOT/.git-hooks"
if [ ! -d "$HOOKS_DIR" ]; then
    exit 0
fi

# 检查 Python 是否可用
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "警告: 未找到 Python，跳过关联文件检测"
    exit 0
fi

# 检查配置文件是否存在
CONFIG_FILE="$REPO_ROOT/.git-hooks-config.yml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "警告: 配置文件不存在: $CONFIG_FILE"
    exit 0
fi

# 运行检查脚本
$PYTHON "$HOOKS_DIR/pre_commit.py" --config "$CONFIG_FILE" "$@"
exit $?
HOOK_EOF
chmod +x "$GIT_HOOKS_DIR/pre-commit"

# 检查 Python 是否可用
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "${YELLOW}警告: 未找到 Python，hook 可能无法运行${NC}"
fi

# 检查 PyYAML 是否安装
if [ -n "$PYTHON" ]; then
    if ! $PYTHON -c "import yaml" 2>/dev/null; then
        echo "${YELLOW}提示: 未安装 PyYAML，将使用内置的简单解析器${NC}"
        echo "      建议安装 PyYAML 以获得更好的兼容性: pip install pyyaml"
    fi
fi

# 验证安装
if [ -f "$GIT_HOOKS_DIR/pre-commit" ] && [ -x "$GIT_HOOKS_DIR/pre-commit" ]; then
    echo "${GREEN}✓ pre-commit hook 安装成功${NC}"
else
    echo "${RED}✗ pre-commit hook 安装失败${NC}"
    exit 1
fi

# 检查配置文件
if [ -f "$REPO_ROOT/.git-hooks-config.yml" ]; then
    echo "${GREEN}✓ 配置文件已存在${NC}"
else
    echo "${YELLOW}警告: 配置文件不存在: $REPO_ROOT/.git-hooks-config.yml${NC}"
    echo "      请确保配置文件存在，否则 hook 将跳过检查"
fi

echo ""
echo "${GREEN}安装完成!${NC}"
echo ""
echo "使用方法:"
echo "  - hook 会在每次 commit 时自动运行"
echo "  - 设置环境变量 GIT_HOOKS_ENABLED=false 可临时禁用"
echo "  - 运行 .git-hooks/pre_commit.py --help 查看更多选项"
echo ""
echo "卸载方法:"
echo "  rm $GIT_HOOKS_DIR/pre-commit"
