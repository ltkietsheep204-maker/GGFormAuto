#!/usr/bin/env python3
"""Convert image to macOS .icns icon"""

from PIL import Image
from pathlib import Path
import subprocess
import shutil
import os

# Đường dẫn ảnh
image_path = "dist/615407782_909688095568175_2899494793591063018_n.png"
output_icon = "app_icon.icns"

print(f"📸 Processing image: {image_path}")

# Mở ảnh
img = Image.open(image_path)
print(f"  Original size: {img.size}")

# Convert to RGBA
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Tạo temp directory
temp_dir = Path("temp_icon_build")
if temp_dir.exists():
    shutil.rmtree(temp_dir)
temp_dir.mkdir(exist_ok=True)

# Tạo iconset directory
iconset_dir = temp_dir / "app.iconset"
iconset_dir.mkdir(exist_ok=True)

# Danh sách kích thước icon
sizes = [16, 32, 64, 128, 256, 512, 1024]

print("\n📦 Creating icon files...")

# Tạo các file PNG cho mỗi kích thước
for size in sizes:
    # Regular size
    icon_img = img.resize((size, size), Image.Resampling.LANCZOS)
    icon_path = iconset_dir / f"icon_{size}x{size}.png"
    icon_img.save(icon_path)
    print(f"  ✓ Created {size}x{size}")
    
    # Retina size (2x)
    if size < 1024:
        icon_2x_img = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
        icon_2x_path = iconset_dir / f"icon_{size}x{size}@2x.png"
        icon_2x_img.save(icon_2x_path)

print(f"\n🎨 Converting to .icns format...")

try:
    result = subprocess.run(
        ["iconutil", "-c", "icns", "-o", output_icon, str(iconset_dir)],
        capture_output=True,
        text=True,
        check=True
    )
    print(f"✅ Icon created successfully: {output_icon}")
    
    # Check file size
    file_size = os.path.getsize(output_icon)
    print(f"   Size: {file_size / 1024:.1f} KB")
    
except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e.stderr}")
    exit(1)
    
finally:
    # Clean up
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("🧹 Temp files cleaned")

print("\n✅ Icon ready!")
