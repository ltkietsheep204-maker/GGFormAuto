#!/bin/bash
# Build macOS standalone app using PyInstaller

echo "🔨 Building Google Form Auto Filler for macOS..."
echo "=================================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip3 install PyInstaller
fi

# Clean previous builds
rm -rf build dist

# Build using PyInstaller
echo "📦 Building executable..."
pyinstaller --onedir \
    --windowed \
    --name "Google Form Auto Filler" \
    --icon icon.icns \
    --collect-all PyQt5 \
    --hidden-import=selenium \
    --hidden-import=webdriver_manager \
    --hidden-import=PyQt5 \
    --add-data "icon.icns:." \
    gui_app_v3.py

echo "✅ Build complete!"
echo ""
echo "📂 App location: ./dist/Google Form Auto Filler.app"
echo ""
echo "To use:"
echo "1. Double-click the .app file to run"
echo "2. Or create a zip and share: zip -r 'Google Form Auto Filler.zip' './dist/Google Form Auto Filler.app'"
