"""
Debug Linear Scale - Interactive Mode
Mở Chrome để user có thể click và xem cấu trúc HTML của linear scale
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# URL form có linear scale - thay bằng URL của bạn
FORM_URL = input("Nhập URL viewform: ").strip()

if not FORM_URL:
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfExample/viewform"
    print(f"Sử dụng URL mặc định: {FORM_URL}")

print("\n" + "="*60)
print("DEBUG LINEAR SCALE - INTERACTIVE MODE")
print("="*60)

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1400,900")
# KHÔNG headless để user có thể tương tác

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    print(f"\n📄 Đang mở: {FORM_URL}")
    driver.get(FORM_URL)
    time.sleep(5)
    
    print("\n" + "="*60)
    print("🎯 HƯỚNG DẪN:")
    print("="*60)
    print("1. Tìm câu hỏi LINEAR SCALE (ví dụ: 'phê ko' với scale 1-5)")
    print("2. Khi bạn click vào một đáp án, script sẽ ghi nhận")
    print("3. Nhập lệnh trong terminal để debug:")
    print("   - 'scan' = Quét tất cả linear scale options")
    print("   - 'html' = In HTML của câu hỏi linear scale")
    print("   - 'click X' = Thử click vào option X (ví dụ: 'click 5')")
    print("   - 'quit' = Thoát")
    print("="*60)
    
    while True:
        cmd = input("\n>>> Nhập lệnh: ").strip().lower()
        
        if cmd == 'quit' or cmd == 'q':
            print("Thoát...")
            break
        
        elif cmd == 'scan':
            print("\n🔍 Đang quét LINEAR SCALE options...")
            
            # Tìm tất cả radiogroup
            radiogroups = driver.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")
            print(f"\nTìm thấy {len(radiogroups)} radiogroups")
            
            for rg_idx, rg in enumerate(radiogroups):
                print(f"\n--- Radiogroup {rg_idx + 1} ---")
                
                # Lấy radios trong group này
                radios = rg.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                print(f"  Có {len(radios)} radio buttons")
                
                for r_idx, radio in enumerate(radios):
                    aria_label = radio.get_attribute("aria-label") or "(no aria-label)"
                    data_value = radio.get_attribute("data-value") or "(no data-value)"
                    aria_checked = radio.get_attribute("aria-checked") or "false"
                    classes = radio.get_attribute("class") or ""
                    
                    print(f"  [{r_idx}] aria-label='{aria_label}' | data-value='{data_value}' | checked={aria_checked}")
                    print(f"       classes: {classes[:80]}...")
            
            # Tìm thêm các element khác có thể là linear scale
            print("\n🔍 Tìm kiếm thêm với data-value...")
            data_value_divs = driver.find_elements(By.CSS_SELECTOR, "div[data-value]")
            print(f"Tìm thấy {len(data_value_divs)} elements với data-value")
            
            for idx, div in enumerate(data_value_divs[:20]):  # Giới hạn 20
                dv = div.get_attribute("data-value")
                role = div.get_attribute("role") or "(no role)"
                text = div.text[:30] if div.text else "(no text)"
                print(f"  [{idx}] data-value='{dv}' | role='{role}' | text='{text}'")
        
        elif cmd == 'html':
            print("\n📜 Lấy HTML của LINEAR SCALE question...")
            
            # Tìm câu hỏi có linear scale (tìm parent của radiogroup)
            radiogroups = driver.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")
            
            for rg_idx, rg in enumerate(radiogroups):
                # Kiểm tra xem có phải linear scale không (có data-value là số)
                radios = rg.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                if radios:
                    first_value = radios[0].get_attribute("data-value") or radios[0].get_attribute("aria-label") or ""
                    if first_value.isdigit():
                        print(f"\n--- LINEAR SCALE Radiogroup {rg_idx + 1} ---")
                        # In HTML của radiogroup
                        outer_html = rg.get_attribute("outerHTML")
                        # Truncate if too long
                        if len(outer_html) > 3000:
                            print(outer_html[:3000] + "\n... (truncated)")
                        else:
                            print(outer_html)
                        break
        
        elif cmd.startswith('click '):
            value = cmd.split(' ')[1]
            print(f"\n🖱️ Thử click vào option '{value}'...")
            
            clicked = False
            
            # Method 1: data-value
            try:
                selectors = [
                    f"div[data-value='{value}']",
                    f"div[role='radio'][data-value='{value}']",
                    f"div.Od2TWd[data-value='{value}']"
                ]
                
                for sel in selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        elem = elements[0]
                        print(f"  ✓ Tìm thấy với selector: {sel}")
                        print(f"    - Tag: {elem.tag_name}")
                        print(f"    - Class: {elem.get_attribute('class')}")
                        print(f"    - aria-checked before: {elem.get_attribute('aria-checked')}")
                        
                        # Click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(0.5)
                        
                        print(f"    - aria-checked after: {elem.get_attribute('aria-checked')}")
                        clicked = True
                        break
                
                if not clicked:
                    print(f"  ✗ Không tìm thấy với data-value selectors")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Method 2: aria-label
            if not clicked:
                try:
                    radios = driver.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                    for radio in radios:
                        aria = radio.get_attribute("aria-label") or ""
                        if aria == value:
                            print(f"  ✓ Tìm thấy với aria-label='{aria}'")
                            driver.execute_script("arguments[0].click();", radio)
                            time.sleep(0.5)
                            print(f"    - aria-checked after: {radio.get_attribute('aria-checked')}")
                            clicked = True
                            break
                except Exception as e:
                    print(f"  Error method 2: {e}")
            
            if not clicked:
                print(f"  ❌ Không thể click vào option '{value}'")
        
        elif cmd == 'structure':
            print("\n📊 Cấu trúc câu hỏi trên trang...")
            
            # Tìm tất cả question containers
            questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            print(f"Tìm thấy {len(questions)} câu hỏi (class Qr7Oae)")
            
            for q_idx, q in enumerate(questions):
                try:
                    # Lấy title
                    title_elem = q.find_element(By.CLASS_NAME, "M7eMe")
                    title = title_elem.text[:50] if title_elem.text else "(no title)"
                except:
                    title = "(title not found)"
                
                # Check type
                has_radiogroup = len(q.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")) > 0
                has_checkbox = len(q.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")) > 0
                has_text = len(q.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")) > 0
                
                # Check if linear scale
                radios = q.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                is_linear = False
                if radios:
                    first_val = radios[0].get_attribute("data-value") or ""
                    is_linear = first_val.isdigit()
                
                q_type = "unknown"
                if is_linear:
                    q_type = "LINEAR_SCALE"
                elif has_radiogroup:
                    q_type = "multiple_choice"
                elif has_checkbox:
                    q_type = "checkbox"
                elif has_text:
                    q_type = "text"
                
                print(f"  [{q_idx + 1}] {q_type}: {title}")
        
        else:
            print("Lệnh không hợp lệ. Thử: scan, html, click X, structure, quit")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    input("\n\nNhấn Enter để đóng Chrome...")
    driver.quit()
    print("✓ Đã đóng Chrome")
