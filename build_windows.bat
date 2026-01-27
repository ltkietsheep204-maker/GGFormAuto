@echo off
REM Windows Build Script for Google Form Auto Filler

setlocal enabledelayedexpansion

echo.
echo 🪟 Building Google Form Auto Filler for Windows...
echo ====================================================
echo.

REM 1. Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo ✓ Python found

REM 2. Check PyInstaller
echo.
echo Checking PyInstaller...
pip list | find "pyinstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install PyInstaller
)
echo ✓ PyInstaller ready

REM 3. Create directories
echo.
echo Creating build directories...
if not exist "build" mkdir build
if not exist "dist" mkdir dist
echo ✓ Directories created

REM 4. Build executable
echo.
echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.

pyinstaller ^
  --name "Google Form Auto Filler" ^
  --onefile ^
  --windowed ^
  --icon="icon.ico" ^
  --add-data "icon.ico;." ^
  --hidden-import=selenium ^
  --hidden-import=webdriver_manager ^
  --hidden-import=PyQt5 ^
  --collect-all=webdriver_manager ^
  --collect-all=selenium ^
  --collect-all=PyQt5 ^
  --distpath=dist ^
  --buildpath=build ^
  --specpath=. ^
  gui_app_v3.py

if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo ✅ Build Complete!
echo.
echo 📦 Output: dist\Google Form Auto Filler.exe
echo.
echo 📤 Next steps:
echo    1. Test the executable:
echo       dist\Google Form Auto Filler.exe
echo    2. Create ZIP for distribution:
echo       PowerShell -Command "Compress-Archive -Path 'dist\Google Form Auto Filler.exe' -DestinationPath 'GoogleFormAutoFiller-Windows.zip'"
echo.
echo 💾 You can now upload GoogleFormAutoFiller-Windows.zip to Google Drive
echo.
pause
