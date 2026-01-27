#!/usr/bin/env python3
"""
Build macOS app bundle for Google Form Auto Filler
This creates a proper .app bundle that can be moved to Applications folder
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist"
    app_dir = dist_dir / "Google Form Auto Filler.app"
    
    # Clean old builds
    if dist_dir.exists():
        print("🧹 Cleaning old build...")
        shutil.rmtree(dist_dir)
    
    # Build with PyInstaller
    print("🍎 Building Google Form Auto Filler for macOS...")
    print("This may take several minutes...\n")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--name", "Google Form Auto Filler",
            "--windowed",
            "--hidden-import=selenium",
            "--hidden-import=webdriver_manager",
            "--hidden-import=PyQt5",
            "--collect-all=webdriver_manager",
            "--collect-all=selenium",
            "--collect-all=PyQt5",
            "--distpath", str(dist_dir),
            "--specpath", str(project_dir),
            "gui_app_v3.py"
        ], cwd=str(project_dir), check=True)
        
        print("\n✅ Build completed successfully!")
        print(f"\n📦 App location:")
        print(f"   {app_dir}")
        print(f"\n📤 To use the app:")
        print(f"   1. Open Finder and go to: {dist_dir}")
        print(f"   2. Drag 'Google Form Auto Filler.app' to Applications folder")
        print(f"   3. Or run: mv '{app_dir}' /Applications/")
        print(f"\n💡 The app is ready to distribute!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
