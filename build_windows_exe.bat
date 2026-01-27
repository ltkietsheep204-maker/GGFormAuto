@echo off
REM Build Windows executable for Google Form Auto Filler

echo Building Windows .exe... This may take 2-5 minutes

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller -q
)

REM Build the executable
echo Creating executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Google Form Auto Filler" ^
    --icon=icon.ico ^
    --hidden-import=PyQt5 ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --distpath=dist/windows ^
    --buildpath=build/windows ^
    --specpath=spec/windows ^
    gui_app_v3.py

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ======================================
echo Build Complete!
echo ======================================
echo Executable location: dist\windows\Google Form Auto Filler.exe
echo.
pause
