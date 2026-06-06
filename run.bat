@echo off
REM Start param_id_gui application
REM Usage: Double-click this file or run: run.bat

cd /d "%~dp0"
".venv\Scripts\python.exe" -m param_id_gui %*
