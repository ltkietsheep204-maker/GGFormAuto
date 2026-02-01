"""
🔍 QUICK DEBUG - Kiểm tra tại sao linear scale không click được
Chỉ cần paste viewform URL
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import sys

# Hardcode URL nếu cần test nhanh
TEST_URL = "https://docs.google.com/forms/d/1V3LZd-3gIrzRczrSwkWwqE7OB_w1pzNWoJnIYaqaG6M/viewform"

def quick_debug(url=None):
    if not url:
        url = TEST_URL
    
    print("🌐 Khởi động Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    print(f"📂 Mở: {url}")
    driver.get(url)
    time.sleep(4)
    
    page = 1
    
    while True:
        print(f"\n{'='*80}")
        print(f"📄 TRANG {page}")
        print(f"{'='*80}")
        
        # Tìm containers
        containers = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        
        if not containers:
            containers = driver.find_elements(By.CSS_SELECTOR, "div.freebirdFormviewerComponentsQuestionBaseRoot")
        
        print(f"Found {len(containers)} containers")
        
        for idx, container in enumerate(containers):
            try:
                # Title
                try:
                    title = container.find_element(By.CSS_SELECTOR, "span.M7eMe").text[:50]
                except:
                    try:
                        title = container.find_element(By.CSS_SELECTOR, "div.M7eMe").text[:50]
                    except:
                        title = "(no title)"
                
                # Check radios
                radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                
                # Check if linear scale (numeric labels)
                is_linear = False
                if radios:
                    labels = [r.get_attribute('aria-label') for r in radios]
                    numeric = [l for l in labels if l and l.strip().isdigit()]
                    if len(numeric) >= 3:
                        is_linear = True
                
                if is_linear:
                    print(f"\n🔴 [Q{idx}] LINEAR SCALE: {title}")
                    print(f"    Radios: {len(radios)}")
                    
                    # List all options
                    for i, r in enumerate(radios):
                        aria = r.get_attribute('aria-label')
                        dv = r.get_attribute('data-value')
                        checked = r.get_attribute('aria-checked')
                        print(f"      [{i}] aria='{aria}' data-value='{dv}' checked={checked}")
                    
                    # TRY CLICK option "3"
                    print(f"\n    🖱️  Trying to click '3'...")
                    
                    clicked = False
                    for r in radios:
                        aria = r.get_attribute('aria-label')
                        if aria and aria.strip() == '3':
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", r)
                                time.sleep(0.3)
                                
                                before = r.get_attribute('aria-checked')
                                r.click()
                                time.sleep(0.5)
                                after = r.get_attribute('aria-checked')
                                
                                if after == 'true':
                                    print(f"    ✅ CLICK SUCCESS! (before={before} → after={after})")
                                    clicked = True
                                else:
                                    print(f"    ⚠️  Clicked but not selected (before={before} → after={after})")
                                break
                            except Exception as e:
                                print(f"    ❌ Click error: {e}")
                    
                    if not clicked:
                        # Try data-value selector
                        dvs = container.find_elements(By.CSS_SELECTOR, "div[data-value='3']")
                        if dvs:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dvs[0])
                                time.sleep(0.3)
                                dvs[0].click()
                                time.sleep(0.5)
                                after = dvs[0].get_attribute('aria-checked')
                                if after == 'true':
                                    print(f"    ✅ data-value CLICK SUCCESS!")
                                    clicked = True
                            except Exception as e:
                                print(f"    ❌ data-value click error: {e}")
                    
                    if not clicked:
                        print(f"    ❌ FAILED TO CLICK LINEAR SCALE")
                
                else:
                    # Not linear scale
                    q_type = "multiple_choice" if radios else "other"
                    print(f"\n🟢 [Q{idx}] {q_type}: {title} ({len(radios)} options)")
            
            except Exception as e:
                print(f"[Q{idx}] Error: {e}")
        
        # Find next button
        next_btn = None
        for xpath in [
            "//span[contains(text(),'Tiếp')]/ancestor::div[@role='button']",
            "//span[contains(text(),'Next')]/ancestor::div[@role='button']",
        ]:
            btns = driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                if btn.is_displayed():
                    next_btn = btn
                    break
            if next_btn:
                break
        
        if next_btn:
            print(f"\n⏭️  Click 'Tiếp' → trang {page + 1}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(0.5)
            next_btn.click()
            time.sleep(2)
            page += 1
        else:
            print(f"\n✓ Đây là trang cuối")
            break
    
    print(f"\n{'='*80}")
    print("⏸️  Chrome giữ mở. Nhấn Enter để đóng...")
    input()
    driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        quick_debug(sys.argv[1])
    else:
        quick_debug()
