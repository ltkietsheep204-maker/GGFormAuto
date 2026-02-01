#!/usr/bin/env python3
"""Debug script để tìm đúng selectors cho viewform"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

VIEWFORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform"

def main():
    print("="*60)
    print("DEBUG VIEWFORM STRUCTURE")
    print("="*60)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,900")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        print(f"\n1. Loading: {VIEWFORM_URL}")
        driver.get(VIEWFORM_URL)
        time.sleep(5)  # Wait longer
        
        print(f"\n2. Page title: {driver.title}")
        
        # Try different selectors
        selectors = [
            ("Qr7Oae", By.CLASS_NAME),
            ("freebirdFormviewerComponentsQuestionBaseRoot", By.CLASS_NAME),
            ("freebirdFormviewerViewItemsItemItem", By.CLASS_NAME),
            ("m2", By.CLASS_NAME),
            ("div[role='listitem']", By.CSS_SELECTOR),
            ("div[data-params]", By.CSS_SELECTOR),
            ("[data-item-id]", By.CSS_SELECTOR),
            ("M7eMe", By.CLASS_NAME),  # Question title
            ("Zki2Ve", By.CLASS_NAME),  # Linear scale options
            ("div[role='radio']", By.CSS_SELECTOR),
            ("div[role='radiogroup']", By.CSS_SELECTOR),
        ]
        
        print("\n3. Testing selectors...")
        for name, by_type in selectors:
            try:
                elements = driver.find_elements(by_type, name)
                if elements:
                    print(f"   ✓ {name}: Found {len(elements)} elements")
                    if len(elements) <= 5:
                        for i, e in enumerate(elements):
                            try:
                                text = e.text[:60].replace('\n', ' ') if e.text else "(no text)"
                                print(f"      [{i}] {text}")
                            except:
                                pass
                else:
                    print(f"   ✗ {name}: 0 elements")
            except Exception as ex:
                print(f"   ✗ {name}: Error - {ex}")
        
        # Print page HTML snippet
        print("\n4. Body HTML structure (first 3000 chars):")
        try:
            html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")[:3000]
            print(html)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n5. Browser stays open 20s for manual inspection...")
        time.sleep(20)
        
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
