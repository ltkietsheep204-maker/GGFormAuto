#!/bin/bash
# 🍎 Build macOS App Bundle (Simple version without code signing)

set -e

echo "🍎 Building Google Form Auto Filler for macOS..."
echo "================================================"

# 1. Kiểm tra Python
echo "✓ Checking Python..."
python3 --version

# 2. Kiểm tra PyInstaller
echo "✓ Checking PyInstaller..."
pip3 list | grep -i pyinstaller || (echo "Installing PyInstaller..." && pip3 install PyInstaller)

# 3. Tạo thư mục build
echo "✓ Creating build directories..."
mkdir -p build dist

# 4. Build executable (no code signing)
echo "✓ Building executable with PyInstaller..."
pyinstaller \
  --name "Google Form Auto Filler" \
  --onedir \
  --windowed \
  --hidden-import=selenium \
  --hidden-import=webdriver_manager \
  --hidden-import=PyQt5 \
  --collect-all=webdriver_manager \
  --collect-all=selenium \
  --collect-all=PyQt5 \
  --distpath=dist \
  --workpath=build \
  --specpath=. \
  -y \
  gui_app_v3.py

echo ""
echo "✅ Build Complete!"
echo ""
echo "📦 macOS App Bundle Created:"
echo "   dist/Google Form Auto Filler.app"
echo ""
echo "📦 Next Steps:"
echo "   1. Zip the app: cd dist && zip -r ../GoogleFormAutoFiller-macOS.zip 'Google Form Auto Filler.app'"
echo "   2. Users can extract and drag to Applications folder"
echo "   3. App is fully portable - no additional dependencies needed!"
