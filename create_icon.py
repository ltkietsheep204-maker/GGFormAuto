#!/usr/bin/env python3
"""Create app icon for Google Form Auto Filler"""

from PIL import Image, ImageDraw

# Create icon 1024x1024
icon_size = 1024
icon = Image.new('RGBA', (icon_size, icon_size), color=(255, 255, 255, 0))
draw = ImageDraw.Draw(icon)

# Draw background circle with blue gradient
radius = icon_size // 2 - 20
center = icon_size // 2

for i in range(50):
    color_int = 100 + i * 3
    draw.ellipse(
        [center - radius + i, center - radius + i, 
         center + radius - i, center + radius - i],
        fill=(100 + i, 150 + i, 220 + i, 255)
    )

# Draw form rectangle
form_left = center - 150
form_top = center - 200
form_right = center + 150
form_bottom = center + 200

draw.rectangle([form_left, form_top, form_right, form_bottom], 
              outline='white', width=15, fill=(255, 255, 255, 200))

# Draw form field lines
line_y_start = form_top + 80
for i in range(4):
    y = line_y_start + i * 50
    draw.line([(form_left + 40, y), (form_right - 40, y)], 
             fill=(100, 150, 220, 255), width=8)

# Draw checkbox with checkmark
checkbox_x = form_left + 40
checkbox_y = form_bottom - 60
checkbox_size = 30
draw.rectangle([checkbox_x, checkbox_y, checkbox_x + checkbox_size, checkbox_y + checkbox_size],
              outline='white', width=6, fill=(100, 200, 100, 200))

# Draw checkmark
tick_x1, tick_y1 = checkbox_x + 8, checkbox_y + 15
tick_x2, tick_y2 = checkbox_x + 15, checkbox_y + 25
tick_x3, tick_y3 = checkbox_x + 30, checkbox_y + 5
draw.line([(tick_x1, tick_y1), (tick_x2, tick_y2)], fill='white', width=6)
draw.line([(tick_x2, tick_y2), (tick_x3, tick_y3)], fill='white', width=6)

# Save PNG
png_path = '/Users/2apple_mgn_63_ram16/Desktop/GGform/app_icon.png'
icon.save(png_path, 'PNG')
print(f"✅ Icon PNG created: {png_path}")
