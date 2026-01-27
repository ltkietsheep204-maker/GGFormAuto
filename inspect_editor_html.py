#!/usr/bin/env python3
"""Inspect actual HTML structure in editor link"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

def inspect_html():
    """Inspect raw HTML of first element"""
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
        
        # Get first Qr7Oae element
        qr_elem = driver.find_element(By.CLASS_NAME, "Qr7Oae")
        
        # Get its full HTML
        html = qr_elem.get_attribute('outerHTML')
        print("\n" + "="*80)
        print("FIRST Qr7Oae ELEMENT HTML:")
        print("="*80)
        print(html[:2000])  # First 2000 chars
        print("\n... (truncated if longer)")
        
        # Try to get all child elements and their classes
        print("\n" + "="*80)
        print("CHILD ELEMENTS:")
        print("="*80)
        children = qr_elem.find_elements(By.XPATH, ".//*")
        for idx, child in enumerate(children[:20]):  # First 20 children
            tag = child.tag_name
            classes = child.get_attribute('class') or ""
            text = child.text[:50] if child.text else ""
            print(f"{idx}: <{tag}> class='{classes}' text='{text}'")
        
        # Look for any input or contenteditable elements
        print("\n" + "="*80)
        print("LOOKING FOR INPUT ELEMENTS:")
        print("="*80)
        inputs = qr_elem.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input elements")
        
        print("\n" + "="*80)
        print("LOOKING FOR TEXTAREA ELEMENTS:")
        print("="*80)
        textareas = qr_elem.find_elements(By.TAG_NAME, "textarea")
        print(f"Found {len(textareas)} textarea elements")
        
        print("\n" + "="*80)
        print("LOOKING FOR CONTENTEDITABLE ELEMENTS:")
        print("="*80)
        contenteditable = qr_elem.find_elements(By.XPATH, ".//*[@contenteditable]")
        print(f"Found {len(contenteditable)} contenteditable elements")
        for idx, ce in enumerate(contenteditable[:5]):
            text = ce.text[:50] if ce.text else "(empty)"
            print(f"  {idx}: {ce.tag_name} - text: '{text}'")
        
        print("\n✓ Inspect complete. Keep window open to verify form structure.")
        print("Look at Chrome DevTools (F12) for actual DOM structure.")
        input("Press Enter to close...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_html()
