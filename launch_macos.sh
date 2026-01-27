#!/bin/bash
# 🚀 Google Form Auto Filler Launcher for macOS
# This script runs the Python application with minimal overhead

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python from https://python.org"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
python3 -c "import PyQt5; import selenium; import webdriver_manager" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Installing missing dependencies..."
    pip3 install -r requirements.txt
fi

# Run the app
echo "🚀 Starting Google Form Auto Filler..."
python3 gui_app_v3.py
