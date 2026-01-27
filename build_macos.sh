#!/bin/bash
# 🍎 Build macOS App Bundle for Google Form Auto Filler

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

# 4. Build executable
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
  --arch=arm64 \
  gui_app_v3.py

echo ""
echo "✅ Build Complete!"
echo ""
echo "📦 Output location:"
echo "   dist/Google Form Auto Filler.app"
echo ""
echo "📤 To prepare for distribution:"
echo "   1. Notarize: xcrun altool --notarize-app -f 'dist/Google Form Auto Filler.app' -t osx ..."
echo "   2. Codesign: codesign -s - 'dist/Google Form Auto Filler.app'"
echo "   3. Create DMG: hdiutil create -volname 'Google Form Auto Filler' -srcfolder dist -ov -format UDZO dist/Google-Form-Auto-Filler.dmg"
echo ""
echo "📌 For now, you can ZIP the .app:"
echo "   cd dist && zip -r ../GoogleFormAutoFiller-macOS.zip 'Google Form Auto Filler.app'"
