#!/usr/bin/env python3
"""
Debug script để test xem Chrome driver có hoạt động đúng với Google Forms không
Chạy với form URL thực tế để xem vấn đề
"""

import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Form URL - thay bằng URL form thực tế của bạn
FORM_URL = input("Nhập URL form Google: ").strip()
if not FORM_URL:
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf..." # placeholder

def test_form_interaction():
    """Test tương tác với Google Form"""
    print("=" * 60)
    print("TEST: Google Form interaction")
    print("=" * 60)
    
    driver_path = ChromeDriverManager().install()
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1200,900")
    
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    
    try:
        print(f"1. Driver created, session_id: {driver.session_id}")
        
        driver.get(FORM_URL)
        print(f"2. Navigated to: {driver.current_url}")
        
        # Wait for page load
        time.sleep(2)
        print(f"3. Page title: {driver.title}")
        
        # Find all radio elements
        print("\n--- Finding radio elements ---")
        radios = driver.find_elements(By.CSS_SELECTOR, "div[role='radio']")
        print(f"Found {len(radios)} div[role='radio'] elements")
        
        for i, radio in enumerate(radios[:10]):  # Chỉ hiển thị 10 đầu tiên
            try:
                data_value = radio.get_attribute("data-value") or ""
                aria_label = radio.get_attribute("aria-label") or ""
                text = radio.text.strip()[:30] if radio.text else ""
                aria_checked = radio.get_attribute("aria-checked")
                print(f"  [{i}] data-value='{data_value}', aria-label='{aria_label[:20]}', text='{text}', checked={aria_checked}")
            except Exception as e:
                print(f"  [{i}] Error: {e}")
        
        # Find all YKDB3e elements (common in Google Forms)
        print("\n--- Finding YKDB3e elements ---")
        ykdb3e = driver.find_elements(By.CLASS_NAME, "YKDB3e")
        print(f"Found {len(ykdb3e)} YKDB3e elements")
        
        for i, elem in enumerate(ykdb3e[:10]):
            try:
                text = elem.text.strip()[:50] if elem.text else ""
                print(f"  [{i}] text='{text}'")
            except Exception as e:
                print(f"  [{i}] Error: {e}")
        
        # Try to click first radio
        if radios:
            print("\n--- Testing click on first radio ---")
            target = radios[0]
            
            # Method 1: JS click
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", target)
                print("  JS click executed")
                time.sleep(0.5)
                
                # Check if clicked
                new_checked = target.get_attribute("aria-checked")
                print(f"  After click: aria-checked = {new_checked}")
                
                if new_checked == "true":
                    print("  ✓ Click SUCCESS!")
                else:
                    print("  ✗ Click may have FAILED")
                    
            except Exception as e:
                print(f"  ✗ Click error: {e}")
        
        # Find Next/Tiếp button
        print("\n--- Finding navigation buttons ---")
        buttons = driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
        print(f"Found {len(buttons)} div[role='button'] elements")
        
        for i, btn in enumerate(buttons):
            try:
                text = btn.text.strip()
                is_displayed = btn.is_displayed()
                print(f"  [{i}] text='{text}', visible={is_displayed}")
            except Exception as e:
                print(f"  [{i}] Error: {e}")
        
        print("\n" + "=" * 60)
        print("Waiting 10 seconds for you to observe Chrome...")
        print("=" * 60)
        time.sleep(10)
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("Driver closed")

if __name__ == "__main__":
    print("\n🔍 GOOGLE FORM DEBUG TEST\n")
    test_form_interaction()
