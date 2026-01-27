@echo off
REM Build Windows standalone exe using PyInstaller

echo Building Google Form Auto Filler for Windows...
echo ==================================================

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install PyInstaller
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build using PyInstaller
echo Packaging executable...
python -m PyInstaller --onedir ^
    --windowed ^
    --name "Google Form Auto Filler" ^
    --icon icon.ico ^
    --collect-all PyQt5 ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --hidden-import=PyQt5 ^
    gui_app_v3.py

echo.
echo Build complete!
echo.
echo App location: .\dist\Google Form Auto Filler
echo.
echo To use:
echo 1. Run: .\dist\Google Form Auto Filler\Google Form Auto Filler.exe
echo 2. Or create a zip and share the entire folder
pause
