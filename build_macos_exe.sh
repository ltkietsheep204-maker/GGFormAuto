#!/bin/bash

# Build macOS .app bundle for Google Form Auto Filler

echo "🔨 Building macOS .app bundle..."
echo "This may take 2-5 minutes..."

# Check if PyInstaller is installed
python3 -m pip show pyinstaller > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 Installing PyInstaller..."
    python3 -m pip install pyinstaller -q
fi

# Create output directories
mkdir -p dist/macos
mkdir -p build/macos
mkdir -p spec/macos

# Build the .app bundle
echo "🏗️ Creating .app bundle..."
python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name "Google Form Auto Filler" \
    --osx-bundle-identifier "com.ggform.autofiller" \
    --hidden-import=PyQt5 \
    --hidden-import=selenium \
    --hidden-import=webdriver_manager \
    --distpath=dist/macos \
    --buildpath=build/macos \
    --specpath=spec/macos \
    --target-architecture=universal2 \
    gui_app_v3.py

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"
echo "Application location: dist/macos/Google Form Auto Filler.app"
echo ""
echo "To run the app:"
echo "  open dist/macos/Google\ Form\ Auto\ Filler.app"
echo ""
