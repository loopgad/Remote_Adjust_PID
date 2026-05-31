#!/usr/bin/env python3
"""
Git Hooks 安装脚本 (跨平台)
将 pre-commit hook 安装到 .git/hooks 目录

用法:
    python install-hooks.py [选项]

选项:
    --uninstall, -u  卸载 hook
    --force, -f      强制覆盖现有 hook
    --check, -c      仅检查安装状态
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def get_repo_root() -> str:
    """获取 Git 仓库根目录"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("错误: 无法获取 Git 仓库根目录")
        sys.exit(1)


def check_python():
    """检查 Python 是否可用"""
    print(f"Python 版本: {sys.version}")

    try:
        import yaml
        print(f"PyYAML: 已安装")
    except ImportError:
        print("PyYAML: 未安装 (将使用内置解析器)")


# Unix hook 内容
HOOK_CONTENT_UNIX = '''#!/bin/sh
# Git Pre-commit Hook - 关联文件检测

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git-hooks"
[ ! -d "$HOOKS_DIR" ] && exit 0

PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "警告: 未找到 Python，跳过关联文件检测"
    exit 0
fi

CONFIG_FILE="$REPO_ROOT/.git-hooks-config.yml"
[ ! -f "$CONFIG_FILE" ] && exit 0

$PYTHON "$HOOKS_DIR/pre_commit.py" --config "$CONFIG_FILE" "$@"
exit $?
'''

# Windows hook 内容
HOOK_CONTENT_WIN = '''@echo off
REM Git Pre-commit Hook - 关联文件检测

for /f "tokens=*" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"
set "HOOKS_DIR=%REPO_ROOT%\\.git-hooks"
if not exist "%HOOKS_DIR%" exit /b 0

set "PYTHON="
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYTHON=python3" & goto :run)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (set "PYTHON=python" & goto :run)
echo 警告: 未找到 Python，跳过关联文件检测
exit /b 0

:run
set "CONFIG_FILE=%REPO_ROOT%\\.git-hooks-config.yml"
if not exist "%CONFIG_FILE%" exit /b 0
%PYTHON% "%HOOKS_DIR%\\pre_commit.py" --config "%CONFIG_FILE%" %*
exit /b %ERRORLEVEL%
'''


def install_hook(repo_root: str, force: bool = False) -> bool:
    """安装 pre-commit hook"""
    hooks_dir = Path(repo_root) / '.git' / 'hooks'

    # 创建 hooks 目录
    hooks_dir.mkdir(parents=True, exist_ok=True)

    if sys.platform == 'win32':
        target_file = hooks_dir / 'pre-commit.bat'
        hook_content = HOOK_CONTENT_WIN
    else:
        target_file = hooks_dir / 'pre-commit'
        hook_content = HOOK_CONTENT_UNIX

    # 检查是否已存在
    if target_file.exists() and not force:
        print(f"警告: pre-commit hook 已存在: {target_file}")
        response = input("是否覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print("已取消安装")
            return False

    # 写入文件
    with open(target_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(hook_content)

    # 设置可执行权限 (Unix)
    if sys.platform != 'win32':
        import stat
        st = os.stat(target_file)
        os.chmod(target_file, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"[OK] pre-commit hook 已安装: {target_file}")
    return True


def uninstall_hook(repo_root: str) -> bool:
    """卸载 pre-commit hook"""
    hooks_dir = Path(repo_root) / '.git' / 'hooks'

    removed = False
    for hook_name in ['pre-commit', 'pre-commit.bat', 'pre-commit.sh']:
        hook_file = hooks_dir / hook_name
        if hook_file.exists():
            hook_file.unlink()
            print(f"[OK] 已删除: {hook_file}")
            removed = True

    if not removed:
        print("未找到已安装的 pre-commit hook")

    return removed


def check_status(repo_root: str):
    """检查安装状态"""
    hooks_dir = Path(repo_root) / '.git' / 'hooks'

    print("\n安装状态检查:")
    print("=" * 50)

    # 检查配置文件
    config_file = Path(repo_root) / '.git-hooks-config.yml'
    if config_file.exists():
        print(f"[OK] 配置文件: {config_file}")
    else:
        print(f"[FAIL] 配置文件不存在: {config_file}")

    # 检查 hook 脚本
    script_dir = Path(__file__).parent
    source_file = script_dir / 'pre_commit.py'
    if source_file.exists():
        print(f"[OK] Hook 脚本: {source_file}")
    else:
        print(f"[FAIL] Hook 脚本不存在: {source_file}")

    # 检查已安装的 hook
    found = False
    for hook_name in ['pre-commit', 'pre-commit.bat']:
        hook_file = hooks_dir / hook_name
        if hook_file.exists():
            found = True
            print(f"[OK] 已安装 Hook: {hook_file}")

            with open(hook_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'pre_commit.py' in content:
                print("  └─ 指向正确的脚本")
            else:
                print("  └─ 警告: 可能指向错误的脚本")

    if not found:
        print("[FAIL] 未找到已安装的 hook")

    print("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Git Hooks 安装脚本')
    parser.add_argument('--uninstall', '-u', action='store_true',
                        help='卸载 hook')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制覆盖现有 hook')
    parser.add_argument('--check', '-c', action='store_true',
                        help='仅检查安装状态')

    args = parser.parse_args()

    # 获取仓库根目录
    repo_root = get_repo_root()

    print("Git Hooks 安装脚本")
    print("=" * 50)
    print(f"仓库根目录: {repo_root}")
    print()

    # 检查 Python
    check_python()
    print()

    # 仅检查状态
    if args.check:
        check_status(repo_root)
        return

    # 卸载
    if args.uninstall:
        if uninstall_hook(repo_root):
            print("\n卸载完成!")
        else:
            print("\n没有需要卸载的 hook")
        return

    # 安装
    if install_hook(repo_root, args.force):
        print("\n安装完成!")
        print("\n使用方法:")
        print("  - hook 会在每次 commit 时自动运行")
        print("  - 设置环境变量 GIT_HOOKS_ENABLED=false 可临时禁用")
        print("  - 运行 .git-hooks/pre_commit.py --help 查看更多选项")
    else:
        print("\n安装失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()
