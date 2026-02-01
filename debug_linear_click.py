#!/usr/bin/env python3
"""Debug script để test click linear scale trên viewform"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# URL viewform của bạn
VIEWFORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform"

def main():
    print("="*60)
    print("DEBUG LINEAR SCALE CLICK")
    print("="*60)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,900")
    # KHÔNG headless để xem
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        print(f"\n1. Loading: {VIEWFORM_URL}")
        driver.get(VIEWFORM_URL)
        time.sleep(3)
        
        print(f"\n2. Current page: {driver.title}")
        
        # Tìm tất cả question containers
        print("\n3. Finding question containers (Qr7Oae)...")
        questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        print(f"   Found {len(questions)} Qr7Oae elements")
        
        for i, q in enumerate(questions):
            try:
                q_text = q.text[:100].replace('\n', ' ')
                print(f"   [{i}] {q_text}...")
            except:
                pass
        
        # Chọn câu hỏi đầu tiên
        if questions:
            q = questions[0]
            print(f"\n4. Analyzing first question...")
            
            # Tìm Zki2Ve elements
            print("\n5. Finding Zki2Ve elements (linear scale options)...")
            zki2ve = q.find_elements(By.CLASS_NAME, "Zki2Ve")
            print(f"   Found {len(zki2ve)} Zki2Ve elements")
            for i, z in enumerate(zki2ve):
                print(f"   [{i}] text='{z.text}'")
            
            # Tìm tất cả div với data-value
            print("\n6. Finding elements with data-value...")
            data_values = q.find_elements(By.CSS_SELECTOR, "[data-value]")
            print(f"   Found {len(data_values)} elements with data-value")
            for i, dv in enumerate(data_values):
                val = dv.get_attribute('data-value')
                role = dv.get_attribute('role')
                print(f"   [{i}] data-value='{val}' role='{role}'")
            
            # Tìm tất cả role=radio
            print("\n7. Finding div[role='radio']...")
            radios = q.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            print(f"   Found {len(radios)} radio elements")
            for i, r in enumerate(radios):
                val = r.get_attribute('data-value')
                aria = r.get_attribute('aria-label')
                print(f"   [{i}] data-value='{val}' aria-label='{aria}'")
            
            # THỬ CLICK VÀO OPTION "2"
            print("\n8. TRYING TO CLICK OPTION '2'...")
            
            # Method 1: Click div[data-value='2']
            try:
                radio_2 = q.find_element(By.CSS_SELECTOR, "div[data-value='2']")
                print(f"   Found div[data-value='2']")
                driver.execute_script("arguments[0].scrollIntoView(true);", radio_2)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", radio_2)
                print(f"   ✓ CLICKED via data-value='2'")
                time.sleep(2)
            except Exception as e:
                print(f"   ✗ Method 1 failed: {e}")
                
                # Method 2: Tìm Zki2Ve với text='2' rồi click parent
                try:
                    for z in zki2ve:
                        if z.text.strip() == '2':
                            parent = z.find_element(By.XPATH, "./..")
                            print(f"   Found Zki2Ve with text='2', parent tag={parent.tag_name}")
                            # Lấy grandparent
                            grandparent = parent.find_element(By.XPATH, "./..")
                            print(f"   Grandparent tag={grandparent.tag_name} class={grandparent.get_attribute('class')}")
                            driver.execute_script("arguments[0].click();", grandparent)
                            print(f"   ✓ CLICKED via grandparent")
                            time.sleep(2)
                            break
                except Exception as e2:
                    print(f"   ✗ Method 2 failed: {e2}")
            
            # Kiểm tra xem đã chọn chưa
            print("\n9. Checking if option was selected...")
            selected = q.find_elements(By.CSS_SELECTOR, "div[role='radio'][aria-checked='true']")
            if selected:
                val = selected[0].get_attribute('data-value')
                print(f"   ✓ Selected: data-value='{val}'")
            else:
                print(f"   ✗ No option selected!")
        
        # Giữ browser mở để xem
        print("\n10. Browser will stay open for 30 seconds for inspection...")
        print("    Press Ctrl+C to exit earlier")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        driver.quit()
        print("Done!")

if __name__ == "__main__":
    main()
