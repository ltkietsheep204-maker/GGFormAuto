#!/usr/bin/env python3
"""Test different text extraction methods"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

def test_text_extraction():
    """Test different ways to extract text"""
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
        
        # Get all 4 Qr7Oae elements
        elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        print(f"\nFound {len(elements)} Qr7Oae elements\n")
        
        for idx, elem in enumerate(elements):
            print(f"{'='*60}")
            print(f"ELEMENT {idx}")
            print(f"{'='*60}")
            
            # Find M7eMe span
            try:
                spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
                if spans:
                    span = spans[0]
                    
                    # Try different methods
                    print(f"  .text: '{span.text}'")
                    print(f"  .getAttribute('innerText'): '{span.get_attribute('innerText')}'")
                    print(f"  .getAttribute('textContent'): '{span.get_attribute('textContent')}'")
                    print(f"  .getAttribute('innerHTML'): '{span.get_attribute('innerHTML')}'")
                    
                    # Try executing JavaScript to get text
                    js_text = driver.execute_script("return arguments[0].textContent", span)
                    print(f"  JS textContent: '{js_text}'")
                    
                    js_inner = driver.execute_script("return arguments[0].innerText", span)
                    print(f"  JS innerText: '{js_inner}'")
                    
                    js_html = driver.execute_script("return arguments[0].innerHTML", span)
                    print(f"  JS innerHTML: '{js_html}'")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Also check heading div
            try:
                heading = elem.find_element(By.XPATH, ".//div[@role='heading']")
                print(f"\n  Heading div:")
                print(f"    .text: '{heading.text}'")
                print(f"    JS textContent: '{driver.execute_script('return arguments[0].textContent', heading)}'")
            except Exception as e:
                print(f"  No heading div: {e}")
        
        input("\nPress Enter to close...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_text_extraction()
