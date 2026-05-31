@echo off
REM Git Pre-commit Hook - 关联文件检测
REM 此脚本调用 pre_commit.py 进行检查

REM 获取仓库根目录
for /f "tokens=*" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"

REM 获取 .git-hooks 目录
set "HOOKS_DIR=%REPO_ROOT%\.git-hooks"
if not exist "%HOOKS_DIR%" exit /b 0

REM 检查 Python 是否可用
set "PYTHON="
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python3"
    goto :found_python
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python"
    goto :found_python
)

echo 警告: 未找到 Python，跳过关联文件检测
exit /b 0

:found_python

REM 检查配置文件是否存在
set "CONFIG_FILE=%REPO_ROOT%\.git-hooks-config.yml"
if not exist "%CONFIG_FILE%" (
    echo 警告: 配置文件不存在: %CONFIG_FILE%
    exit /b 0
)

REM 运行检查脚本
%PYTHON% "%HOOKS_DIR%\pre_commit.py" --config "%CONFIG_FILE%" %*
exit /b %ERRORLEVEL%
