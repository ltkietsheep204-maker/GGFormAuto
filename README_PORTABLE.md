# 📦 Portable Distribution Package
# Google Form Auto Filler - Ready to Use

## Quick Start (No Installation Needed!)

### For macOS Users

```bash
# 1. Extract the ZIP file
unzip GoogleFormAutoFiller-Portable-macOS.zip
cd GoogleFormAutoFiller

# 2. Install dependencies (one time only)
pip3 install -r requirements.txt

# 3. Run the app
./launch_macos.sh
```

**Or double-click**: `launch_macos.sh`

### For Windows Users

```batch
REM 1. Extract the ZIP file
REM    Right-click → Extract All

REM 2. Double-click: launch_windows.bat
REM    (Will install dependencies automatically)
```

### For Linux Users

```bash
# 1. Extract the archive
tar -xzf GoogleFormAutoFiller-Portable-Linux.tar.gz
cd GoogleFormAutoFiller

# 2. Install dependencies (one time only)
pip3 install -r requirements.txt

# 3. Run the app
./launch_linux.sh
```

## What's Included

```
GoogleFormAutoFiller/
├── gui_app_v3.py              ← Main application
├── requirements.txt            ← Dependencies (auto-install)
├── launch_macos.sh             ← macOS launcher
├── launch_windows.bat          ← Windows launcher
├── launch_linux.sh             ← Linux launcher
├── README_PORTABLE.md          ← This file
├── SETUP_GUIDE.md              ← Complete guide
├── README_BUILD.md             ← Build instructions
└── CHANGELOG.md                ← Version history
```

## Requirements

### One-Time Setup

- **Python 3.8+**: [Download here](https://python.org)
- **Google Chrome**: [Download here](https://google.com/chrome)

That's it! Dependencies are installed automatically.

## No Installation Hassles

✅ **No Admin Rights Needed**  
✅ **No Registry Changes** (Windows)  
✅ **No System Modifications**  
✅ **Fully Portable**  
✅ **Can Run from USB Drive**  

## Features

- 🔍 Auto-extract form questions & options
- ☑️ Visual answer selection (like real form)
- 🎲 Random mode with percentage distribution
- ⚡ Parallel processing (1-5 Chrome tabs)
- 🔒 Headless Chrome (invisible)
- 📊 Real-time progress tracking
- 🌐 Supports Vietnamese interface

## Troubleshooting

### "Python not found"
- Install Python from https://python.org
- Make sure to check "Add Python to PATH"

### "Chrome not found"
- Install Google Chrome from https://google.com/chrome
- Or install Chromium

### "Permission denied" (macOS/Linux)
```bash
chmod +x launch_macos.sh  # or launch_linux.sh
./launch_macos.sh
```

### "Module not found"
```bash
pip3 install -r requirements.txt
```

## First Run

The first run will:
1. ✓ Install any missing dependencies
2. ✓ Download Chrome WebDriver
3. ✓ Start the application

This takes 1-2 minutes on first run, then launches instantly after.

## System Requirements

| OS | Version | RAM | Disk | Browser |
|----|---------|-----|------|---------|
| Windows | 7+ | 4GB | 500MB | Chrome |
| macOS | 10.14+ | 4GB | 500MB | Chrome |
| Linux | Ubuntu 18.04+ | 4GB | 500MB | Chrome |

## Version Information

- **Version**: 3.1
- **Release**: January 25, 2026
- **Features**:
  - ✅ Headless Chrome (no visible windows)
  - ✅ Parallel processing (5 tabs max)
  - ✅ Random mode with percentages
  - ✅ Real-time progress tracking
  - ✅ 100% local processing

## Privacy & Security

✅ No data leaves your computer  
✅ No tracking or telemetry  
✅ Open-source code  
✅ Direct connection to Google Forms only  
✅ Your answers are never stored  

## Advanced Usage

### Custom Chrome Location

If Chrome is installed in a non-standard location:

```bash
# macOS
export CHROMEDRIVER_PATH="/path/to/chrome"
./launch_macos.sh

# Windows (set in environment variables first)
set CHROMEDRIVER_PATH=C:\path\to\chrome
launch_windows.bat
```

### Python Virtual Environment (Optional)

For isolated Python environment:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python3 gui_app_v3.py
```

## Getting Updates

1. Check CHANGELOG.md for version history
2. Download latest from Google Drive
3. Replace files in your folder

## Support

- 📖 Read SETUP_GUIDE.md for detailed instructions
- 🔧 Read README_BUILD.md for technical details
- 💬 Check CHANGELOG.md for known issues

## Distribution

Feel free to share this package with others:
- ✅ Share via Google Drive
- ✅ Share via email
- ✅ Host on your own server
- ✅ Include in documentation

## License & Credits

This tool is provided as-is for educational purposes.  
Uses: Selenium, PyQt5, Chrome WebDriver

---

**Ready to use. No installation. Just run!**

Questions? Check the documentation files included in this package.
