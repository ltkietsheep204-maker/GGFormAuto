@echo off
REM Google Form Auto Filler - Windows Launcher
REM Run this to start the app

python3 "%~dp0gui_app_v3.py"

if %errorlevel% neq 0 (
    echo Error: Python 3 not found or app failed
    echo Please install Python 3 from: https://www.python.org/downloads/
    pause
)
