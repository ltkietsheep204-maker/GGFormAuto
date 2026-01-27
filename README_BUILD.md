# 📦 Build Instructions - Google Form Auto Filler

## Cross-Platform Build (Recommended)

### Prerequisites
- Python 3.8 or later
- pip (Python package manager)

### Quick Build

```bash
# On macOS or Linux
python3 build.py

# On Windows (PowerShell)
python build.py
```

The script will automatically:
1. ✅ Check dependencies
2. ✅ Install PyInstaller if needed
3. ✅ Build executable for your platform
4. ✅ Create a distributable ZIP file

## Platform-Specific Build

### macOS Build

```bash
# Option 1: Using Python script
python3 build.py

# Option 2: Using shell script
chmod +x build_macos.sh
./build_macos.sh
```

**Output:** `GoogleFormAutoFiller-macOS.zip` (contains .app bundle)

### Windows Build

```batch
REM Option 1: Using Python script
python build.py

REM Option 2: Using batch script
build_windows.bat
```

**Output:** `GoogleFormAutoFiller-Windows.zip` (contains .exe)

### Linux Build

```bash
# Using Python script
python3 build.py

# Or manually with PyInstaller
pyinstaller \
  --name "Google Form Auto Filler" \
  --onefile \
  --hidden-import=selenium \
  --collect-all=webdriver_manager \
  gui_app_v3.py
```

## Installation & Testing

### After Build

1. **Extract the distribution file**
   ```bash
   unzip GoogleFormAutoFiller-*.zip
   ```

2. **Test the executable**
   
   **macOS:**
   ```bash
   open "Google Form Auto Filler.app"
   ```
   
   **Windows:**
   ```bash
   "Google Form Auto Filler.exe"
   ```
   
   **Linux:**
   ```bash
   ./dist/"Google Form Auto Filler"
   ```

3. **Upload to Google Drive**
   - Create folder: "Google Form Auto Filler"
   - Upload the ZIP file
   - Share link with others

## File Structure

```
GGform/
├── gui_app_v3.py              # Main application
├── requirements.txt            # Python dependencies
├── build.py                    # Python build script
├── build_macos.sh              # macOS build script
├── build_windows.bat           # Windows build script
├── README_BUILD.md             # This file
│
├── dist/                       # Built executables (after build)
│   ├── Google Form Auto Filler.exe    (Windows)
│   └── Google Form Auto Filler.app    (macOS)
│
└── GoogleFormAutoFiller-*.zip  # Distributable files
    ├── GoogleFormAutoFiller-Windows.zip
    └── GoogleFormAutoFiller-macOS.zip
```

## Troubleshooting

### "PyInstaller not found"
```bash
pip install PyInstaller
```

### "Selenium not found"
```bash
pip install selenium webdriver-manager
```

### "PyQt5 not found"
```bash
pip install PyQt5
```

### Application won't start
1. Check all dependencies are installed: `pip install -r requirements.txt`
2. Try running from terminal to see error messages
3. On macOS, you may need to allow in Security & Privacy

### macOS "Cannot open application"
The app is not signed. To fix:
```bash
xattr -d com.apple.quarantine "Google Form Auto Filler.app"
```

Or allow in:
System Preferences → Security & Privacy → General → Allow anyway

### Windows SmartScreen warning
This is normal for unsigned executables. Click "More info" → "Run anyway"

## File Sizes

Typical file sizes after build:
- **Windows .exe**: 200-250 MB (includes Python + libraries)
- **macOS .app**: 250-300 MB (includes Python + libraries)
- **Linux binary**: 200-250 MB

**Zipped size**: ~60-80 MB (much smaller!)

## Distribution Tips

1. **Google Drive Upload**
   - File size limit: 5 TB (no problem!)
   - Recommended: Create shared folder
   - Share link with password

2. **Alternative: GitHub Releases**
   - Free hosting for binaries
   - Automatic download stats
   - Version control

3. **Anti-virus Scanning**
   - Unsigned executables may trigger warnings
   - You can use VirusTotal to check: https://www.virustotal.com/
   - Warnings are normal for unsigned apps

## Rebuilding

To rebuild after code changes:

```bash
# Clean old builds
rm -rf build dist *.spec

# Rebuild
python3 build.py
```

## Next Steps for Distribution

1. ✅ Build the executable
2. ✅ Test on your platform
3. ✅ Create ZIP file
4. ✅ Upload to Google Drive
5. ✅ Share link with users

## Support

If build fails:
1. Check Python version: `python --version` (should be 3.8+)
2. Update pip: `pip install --upgrade pip`
3. Reinstall dependencies: `pip install --upgrade -r requirements.txt`
4. Check PyInstaller compatibility: `pip install --upgrade PyInstaller`

---

**Built with PyInstaller v5.0+**  
**Last Updated: January 25, 2026**
