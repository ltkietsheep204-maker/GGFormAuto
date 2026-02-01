"""
Test thực tế: Extract từ Editor → Lưu đáp án → Click trên Viewform
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# URL để test
EDITOR_URL = input("Nhập URL Editor (hoặc để trống để skip): ").strip()
VIEWFORM_URL = input("Nhập URL Viewform: ").strip()

if not VIEWFORM_URL:
    VIEWFORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf9ToOHatXUi3Cq1SHOmOSGhK1WjWIGYgYn_ZH9cTALqGHyKQ/viewform"

print("\n" + "="*60)
print("TEST REAL FLOW: Simulate GUI behavior")
print("="*60)

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1400,900")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    # =====================================
    # STEP 1: Simulate saved answer (from UI)
    # =====================================
    # Giả sử user đã chọn option "4" cho câu linear scale
    saved_answer = input("\nNhập giá trị muốn chọn cho linear scale (1-5): ").strip() or "4"
    print(f"\n📝 Simulated saved answer: '{saved_answer}'")
    
    # =====================================
    # STEP 2: Open Viewform
    # =====================================
    print(f"\n📄 Đang mở Viewform: {VIEWFORM_URL}")
    driver.get(VIEWFORM_URL)
    time.sleep(5)
    
    # =====================================
    # STEP 3: Find question element (simulate _fill_form)
    # =====================================
    print("\n🔍 Tìm question elements...")
    
    question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
    print(f"  Tìm thấy {len(question_elements)} question containers (Qr7Oae)")
    
    if len(question_elements) == 0:
        question_elements = driver.find_elements(By.XPATH, "//*[@data-item-id]")
        print(f"  Fallback: Tìm thấy {len(question_elements)} elements với data-item-id")
    
    if len(question_elements) == 0:
        print("  ❌ Không tìm thấy question elements!")
    else:
        # Lấy question element đầu tiên (giả sử là linear scale)
        q_element = question_elements[0]
        
        # Debug: In ra thông tin về question element
        try:
            title_elem = q_element.find_element(By.CLASS_NAME, "M7eMe")
            title = title_elem.text[:50] if title_elem.text else "(no title)"
            print(f"  Question 1 title: '{title}'")
        except:
            print("  (Không lấy được title)")
        
        # =====================================
        # STEP 4: Simulate _select_option
        # =====================================
        print(f"\n🖱️ Simulating _select_option(q_element, '{saved_answer}')")
        
        option_text = saved_answer
        clicked = False
        
        # Method 0a: Tìm trong question_element
        if option_text.strip().isdigit():
            print("  → Detected numeric option, trying LINEAR SCALE methods...")
            
            for selector in [
                f"div.Od2TWd[data-value='{option_text}']",
                f"div[role='radio'][data-value='{option_text}']",
                f"div[data-value='{option_text}']"
            ]:
                try:
                    radios = q_element.find_elements(By.CSS_SELECTOR, selector)
                    if radios:
                        radio = radios[0]
                        is_checked = radio.get_attribute("aria-checked") == "true"
                        print(f"  ✓ Found via {selector} in question_element (checked={is_checked})")
                        
                        if not is_checked:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", radio)
                            time.sleep(0.5)
                            
                            # Verify
                            is_now_checked = radio.get_attribute("aria-checked") == "true"
                            print(f"  ✅ CLICKED! aria-checked after click: {is_now_checked}")
                            clicked = True
                            break
                        else:
                            print(f"  (Already checked, skip)")
                except Exception as e:
                    print(f"  ✗ {selector} failed: {e}")
        
        if not clicked:
            # Method 6: GLOBAL search (fallback)
            print("\n  → Method 6: Trying GLOBAL search...")
            try:
                for selector in [
                    f"div[data-value='{option_text}']",
                    f"div[role='radio'][data-value='{option_text}']"
                ]:
                    radios = driver.find_elements(By.CSS_SELECTOR, selector)
                    if radios:
                        for radio in radios:
                            is_checked = radio.get_attribute("aria-checked") == "true"
                            if not is_checked:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                time.sleep(0.3)
                                driver.execute_script("arguments[0].click();", radio)
                                time.sleep(0.5)
                                print(f"  ✅ GLOBAL: Clicked via {selector}")
                                clicked = True
                                break
                        if clicked:
                            break
            except Exception as e:
                print(f"  ✗ Global search failed: {e}")
        
        if not clicked:
            print("  ❌ Could not click option!")
        else:
            print("\n✅ SUCCESS! Option was clicked correctly.")
    
    # Wait for user to see result
    input("\n\nNhấn Enter để đóng Chrome...")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nNhấn Enter để đóng Chrome...")

finally:
    driver.quit()
    print("✓ Đã đóng Chrome")
