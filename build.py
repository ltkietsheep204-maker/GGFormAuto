#!/usr/bin/env python3
"""
🚀 Build Script for Google Form Auto Filler
Supports: Windows, macOS, Linux
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg, level="info"):
    """Colored logging"""
    if level == "success":
        print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")
    elif level == "error":
        print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")
    elif level == "warning":
        print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")
    elif level == "header":
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{msg}{Colors.ENDC}\n")
    else:
        print(f"{Colors.OKBLUE}ℹ️  {msg}{Colors.ENDC}")

def run_command(cmd, description=""):
    """Run shell command"""
    try:
        log(description or f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {cmd}", "error")
        return False

def check_dependency(package, cmd=None):
    """Check if package is installed"""
    check_cmd = cmd or f"pip list | grep {package}"
    try:
        subprocess.run(check_cmd, shell=True, check=True, capture_output=True)
        return True
    except:
        return False

def install_dependencies():
    """Install required packages"""
    log("header", "📦 Installing Dependencies")
    
    packages = [
        "PyInstaller",
        "selenium",
        "PyQt5",
        "webdriver-manager"
    ]
    
    for package in packages:
        if check_dependency(package):
            log(f"{package} already installed")
        else:
            log(f"Installing {package}...")
            if not run_command(f"pip install {package}", f"Installing {package}"):
                log(f"Failed to install {package}", "error")
                return False
    
    return True

def clean_build_dirs():
    """Clean previous builds"""
    log("header", "🧹 Cleaning Old Builds")
    
    dirs_to_clean = ["build", "dist", ".egg-info"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            log(f"Removed {dir_name}")

def build_executable(system):
    """Build executable using PyInstaller"""
    log("header", f"🔨 Building Executable for {system}")
    
    icon_file = "icon.icns" if system == "macOS" else "icon.ico"
    
    # Check if icon exists
    if not os.path.exists(icon_file):
        log(f"Icon file {icon_file} not found, building without icon", "warning")
        icon_arg = ""
    else:
        icon_arg = f'--icon="{icon_file}"'
    
    cmd = (
        f"pyinstaller "
        f'--name "Google Form Auto Filler" '
        f"--onefile "
        f"--windowed "
        f"{icon_arg} "
        f"--hidden-import=selenium "
        f"--hidden-import=webdriver_manager "
        f"--hidden-import=PyQt5 "
        f"--collect-all=webdriver_manager "
        f"--collect-all=selenium "
        f"--collect-all=PyQt5 "
        f"--distpath=dist "
        f"--buildpath=build "
        f"--specpath=. "
        f"gui_app_v3.py"
    )
    
    if not run_command(cmd, "Building with PyInstaller..."):
        log("Build failed", "error")
        return False
    
    return True

def create_distribution(system):
    """Create distributable package"""
    log("header", "📦 Creating Distribution Package")
    
    if system == "Windows":
        exe_file = "dist/Google Form Auto Filler.exe"
        zip_file = "GoogleFormAutoFiller-Windows.zip"
        
        if os.path.exists(exe_file):
            cmd = f'powershell -Command "Compress-Archive -Path \\"{exe_file}\\" -DestinationPath \\"{zip_file}\\""'
            if run_command(cmd, f"Creating {zip_file}..."):
                log(f"Created {zip_file}", "success")
                return zip_file
    
    elif system == "macOS":
        app_dir = "dist/Google Form Auto Filler.app"
        zip_file = "GoogleFormAutoFiller-macOS.zip"
        
        if os.path.exists(app_dir):
            cmd = f'cd dist && zip -r "../{zip_file}" "Google Form Auto Filler.app"'
            if run_command(cmd, f"Creating {zip_file}..."):
                log(f"Created {zip_file}", "success")
                return zip_file
    
    elif system == "Linux":
        exe_file = "dist/Google Form Auto Filler"
        zip_file = "GoogleFormAutoFiller-Linux.tar.gz"
        
        if os.path.exists(exe_file):
            cmd = f'cd dist && tar -czf "../{zip_file}" "Google Form Auto Filler"'
            if run_command(cmd, f"Creating {zip_file}..."):
                log(f"Created {zip_file}", "success")
                return zip_file
    
    return None

def get_system_name():
    """Get OS name for build"""
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    elif system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    else:
        return system

def main():
    """Main build function"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 60)
    print("🤖 Google Form Auto Filler - Build System")
    print("=" * 60)
    print(f"{Colors.ENDC}\n")
    
    # Get system
    system = get_system_name()
    log(f"Detected OS: {system}")
    
    # Check if main file exists
    if not os.path.exists("gui_app_v3.py"):
        log("gui_app_v3.py not found!", "error")
        return False
    log("Found gui_app_v3.py")
    
    # Install dependencies
    if not install_dependencies():
        log("Failed to install dependencies", "error")
        return False
    
    # Clean old builds
    clean_build_dirs()
    
    # Build executable
    if not build_executable(system):
        return False
    
    log(f"Executable built successfully!", "success")
    
    # Create distribution
    zip_file = create_distribution(system)
    
    # Final summary
    log("header", "✨ Build Summary")
    log(f"Platform: {system}", "success")
    log(f"Output directory: dist/", "success")
    
    if zip_file:
        log(f"Distribution package: {zip_file}", "success")
        log(f"File size: {os.path.getsize(zip_file) / (1024*1024):.1f} MB", "success")
        log(f"\n📤 Ready to upload to Google Drive!", "success")
    
    print(f"\n{Colors.BOLD}📝 Next Steps:{Colors.ENDC}")
    print(f"1. Test the application")
    if system == "macOS":
        print(f'   open "dist/Google Form Auto Filler.app"')
    elif system == "Windows":
        print(f'   dist\\Google Form Auto Filler.exe')
    else:
        print(f'   ./dist/Google Form Auto Filler')
    
    if zip_file:
        print(f"\n2. Upload to Google Drive:")
        print(f"   {zip_file} ({os.path.getsize(zip_file) / (1024*1024):.1f} MB)")
    
    print(f"\n{Colors.OKGREEN}✅ Build complete!{Colors.ENDC}\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
