#!/usr/bin/env python3
"""Inspect options HTML in editor link"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

def inspect_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        driver.get(FORM_URL)
        time.sleep(8)
        
        elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        print(f"\nFound {len(elements)} Qr7Oae elements\n")
        
        for idx, elem in enumerate(elements[:2]):  # Check first 2 elements
            print(f"{'='*60}")
            print(f"ELEMENT {idx}")
            print(f"{'='*60}")
            
            # Get first span to identify element
            spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
            if spans:
                title = spans[0].get_attribute('innerText') or ""
                print(f"Title: {title}\n")
            
            # Look for different option selectors
            print("Looking for option elements:")
            
            # Option selector 1: YKDB3e (viewform)
            try:
                opts = elem.find_elements(By.CLASS_NAME, "YKDB3e")
                print(f"  YKDB3e class: Found {len(opts)} elements")
            except:
                pass
            
            # Option selector 2: role='radio'
            try:
                opts = elem.find_elements(By.XPATH, ".//div[@role='radio']")
                print(f"  role='radio': Found {len(opts)} elements")
                for opt_idx, opt in enumerate(opts[:2]):
                    # Try to get option text
                    text = opt.get_attribute('aria-label') or ""
                    inner = opt.get_attribute('innerText') or ""
                    print(f"    {opt_idx}: aria-label='{text}', innerText='{inner}'")
            except Exception as e:
                print(f"  role='radio': Error - {e}")
            
            # Option selector 3: OIC90c (might be label)
            try:
                opts = elem.find_elements(By.CLASS_NAME, "OIC90c")
                print(f"  OIC90c class: Found {len(opts)} elements")
                for opt_idx, opt in enumerate(opts[:2]):
                    text = opt.text or "(empty)"
                    print(f"    {opt_idx}: text='{text}'")
            except:
                pass
            
            # Option selector 4: snByac (might be label text)
            try:
                opts = elem.find_elements(By.CLASS_NAME, "snByac")
                print(f"  snByac class: Found {len(opts)} elements")
                for opt_idx, opt in enumerate(opts[:2]):
                    text = opt.text or "(empty)"
                    js_text = driver.execute_script("return arguments[0].textContent", opt)
                    print(f"    {opt_idx}: text='{text}', JS='{js_text}'")
            except Exception as e:
                print(f"  snByac: Error - {e}")
            
            # Get full HTML of first option to inspect
            print("\nFull HTML of first radio option:")
            try:
                opt = elem.find_element(By.XPATH, ".//div[@role='radio']")
                html = opt.get_attribute('outerHTML')
                print(html[:500])
            except Exception as e:
                print(f"Error: {e}")
        
        input("\nPress Enter to close...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_options()
