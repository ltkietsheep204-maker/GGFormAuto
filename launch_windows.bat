@echo off
REM 🚀 Google Form Auto Filler Launcher for Windows
REM This script runs the Python application

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo 🔍 Checking dependencies...
python -c "import PyQt5; import selenium; import webdriver_manager" 2>nul

if errorlevel 1 (
    echo ⚠️  Installing missing dependencies...
    pip install -r requirements.txt
)

echo 🚀 Starting Google Form Auto Filler...
python gui_app_v3.py

pause
