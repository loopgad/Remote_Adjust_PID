@echo off
REM Git Hooks 安装脚本 (Windows)
REM 将 pre-commit hook 安装到 .git/hooks 目录

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 获取仓库根目录
for /f "tokens=*" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"

REM 检查是否在 Git 仓库中
if "%REPO_ROOT%"=="" (
    echo 错误: 无法获取 Git 仓库根目录，请确保在 Git 仓库中运行
    exit /b 1
)

REM Git hooks 目录
set "GIT_HOOKS_DIR=%REPO_ROOT%\.git\hooks"

echo Git Hooks 安装脚本
echo ================================

REM 检查 .git 目录是否存在
if not exist "%REPO_ROOT%\.git" (
    echo 错误: 当前目录不是 Git 仓库
    exit /b 1
)

REM 创建 hooks 目录（如果不存在）
if not exist "%GIT_HOOKS_DIR%" mkdir "%GIT_HOOKS_DIR%"

REM 检查是否已存在 pre-commit hook
if exist "%GIT_HOOKS_DIR%\pre-commit.bat" (
    echo 警告: pre-commit hook 已存在
    set /p "OVERWRITE=是否覆盖? (y/N): "
    if /i not "!OVERWRITE!"=="y" (
        echo 已取消安装
        exit /b 0
    )
)

REM 生成 pre-commit hook
echo 安装 pre-commit hook...
(
echo @echo off
echo REM Git Pre-commit Hook - 关联文件检测
echo.
echo REM 获取仓库根目录
echo for /f "tokens=*" %%%%i in ^('git rev-parse --show-toplevel 2^^^>nul'^) do set "REPO_ROOT=%%%%i"
echo.
echo REM 获取 .git-hooks 目录
echo set "HOOKS_DIR=%%REPO_ROOT%%\.git-hooks"
echo if not exist "%%HOOKS_DIR%%" exit /b 0
echo.
echo REM 检查 Python 是否可用
echo set "PYTHON="
echo where python3 ^>nul 2^>^&1
echo if %%ERRORLEVEL%% EQU 0 ^(
echo     set "PYTHON=python3"
echo     goto :found_python
echo ^)
echo where python ^>nul 2^>^&1
echo if %%ERRORLEVEL%% EQU 0 ^(
echo     set "PYTHON=python"
echo     goto :found_python
echo ^)
echo echo 警告: 未找到 Python，跳过关联文件检测
echo exit /b 0
echo.
echo :found_python
echo.
echo REM 检查配置文件是否存在
echo set "CONFIG_FILE=%%REPO_ROOT%%\.git-hooks-config.yml"
echo if not exist "%%CONFIG_FILE%%" ^(
echo     echo 警告: 配置文件不存在: %%CONFIG_FILE%%
echo     exit /b 0
echo ^)
echo.
echo REM 运行检查脚本
echo %%PYTHON%% "%%HOOKS_DIR%%\pre_commit.py" --config "%%CONFIG_FILE%%" %%*
echo exit /b %%ERRORLEVEL%%
) > "%GIT_HOOKS_DIR%\pre-commit.bat"

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

echo 警告: 未找到 Python，hook 可能无法运行
goto :check_config

:found_python

REM 检查 PyYAML 是否安装
%PYTHON% -c "import yaml" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 提示: 未安装 PyYAML，将使用内置的简单解析器
    echo       建议安装 PyYAML 以获得更好的兼容性: pip install pyyaml
)

:check_config

REM 验证安装
if exist "%GIT_HOOKS_DIR%\pre-commit.bat" (
    echo ✓ pre-commit hook 安装成功
) else (
    echo ✗ pre-commit hook 安装失败
    exit /b 1
)

REM 检查配置文件
if exist "%REPO_ROOT%\.git-hooks-config.yml" (
    echo ✓ 配置文件已存在
) else (
    echo 警告: 配置文件不存在: %REPO_ROOT%\.git-hooks-config.yml
    echo       请确保配置文件存在，否则 hook 将跳过检查
)

echo.
echo 安装完成!
echo.
echo 使用方法:
echo   - hook 会在每次 commit 时自动运行
echo   - 设置环境变量 GIT_HOOKS_ENABLED=false 可临时禁用
echo   - 运行 .git-hooks\pre_commit.py --help 查看更多选项
echo.
echo 卸载方法:
echo   del "%GIT_HOOKS_DIR%\pre-commit.bat"

endlocal
