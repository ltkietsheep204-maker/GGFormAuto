import re

# Simulate HTML từ editor form
html_content = """
<div class="Qr7Oae">
  <div class="hj99tb KRoqRc editable" role="textbox" aria-label="Câu hỏi">ok m&nbsp;</div>
  <div class="something"><div role="radio">opt1</div><div role="radio">opt2</div></div>
</div>

<div class="Qr7Oae">
  <div class="hj99tb KRoqRc editable" role="textbox" aria-label="Câu hỏi">bạn tên là gì&nbsp;</div>
  <div><div role="radio">option a</div><div role="radio">option b</div></div>
</div>

<div class="Qr7Oae">
  <div class="Kk G9vf"><div class="aG9Vid M7eMe">Mục không có tiêu đề</div></div>
</div>
"""

# Test regex to extract questions
textbox_pattern = r'<div[^>]*role="textbox"[^>]*aria-label="Câu hỏi"[^>]*>([^<]*)</div>'
matches = re.findall(textbox_pattern, html_content)

print("Found questions using textbox pattern:")
for idx, match in enumerate(matches, 1):
    text = match.replace('&nbsp;', ' ').strip()
    print(f"  Q{idx}: '{text}'")

print("\nMatches found:", len(matches))
print("Expected: 2 (excluding section header)")

# Check for section header
section_pattern = r'<div[^>]*class="[^"]*M7eMe[^"]*"[^>]*>Mục không có'
if re.search(section_pattern, html_content):
    print("\nSection header detected correctly")
