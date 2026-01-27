"""
Build script để tạo standalone executable cho macOS
Chạy: python build_app.py
Sẽ tạo file: dist/GoogleFormFiller.app
"""

import sys
import os
from PyInstaller.__main__ import run

if __name__ == "__main__":
    # Tham số cho PyInstaller
    args = [
        'gui_app.py',
        '--onefile',
        '--windowed',
        '--name=GoogleFormFiller',
        '--icon=icon.icns',  # Tùy chọn: nếu có icon
        '--add-data=.:.',
        '--hidden-import=selenium',
        '--hidden-import=PyQt5',
    ]
    
    print("🔨 Đang build ứng dụng...")
    print("Điều này có thể mất vài phút...")
    
    run(args)
    
    print("\n✅ Build hoàn tất!")
    print("📦 File ứng dụng: dist/GoogleFormFiller.app")
    print("💾 Bạn có thể copy file này sang máy khác để sử dụng")
