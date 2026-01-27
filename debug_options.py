#!/usr/bin/env python3
"""Debug options search"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

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
    
    # Check first element
    elem = elements[0]
    
    # Get title
    spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
    if spans:
        title = spans[0].get_attribute('innerText') or ""
        print(f"Question: {title}\n")
    
    # Try different selectors for options
    print("Searching for option elements:\n")
    
    # 1. Input with class
    print("1. input[@class='Hvn9fb zHQkBf']:")
    inputs = elem.find_elements(By.XPATH, ".//input[@class='Hvn9fb zHQkBf']")
    print(f"   Found: {len(inputs)}")
    for inp in inputs[:2]:
        print(f"     value: {inp.get_attribute('value')}")
    
    # 2. Any input
    print("\n2. Any input elements:")
    all_inputs = elem.find_elements(By.TAG_NAME, "input")
    print(f"   Found: {len(all_inputs)}")
    for idx, inp in enumerate(all_inputs[:3]):
        cls = inp.get_attribute('class') or "(no class)"
        val = inp.get_attribute('value') or "(no value)"
        print(f"     {idx}: class='{cls}', value='{val}'")
    
    # 3. div with role='radio'
    print("\n3. div[@role='radio']:")
    radios = elem.find_elements(By.XPATH, ".//div[@role='radio']")
    print(f"   Found: {len(radios)}")
    for idx, radio in enumerate(radios[:2]):
        aria = radio.get_attribute('aria-label') or ""
        print(f"     {idx}: aria-label='{aria}'")
    
    # 4. Check full HTML of first radio
    if radios:
        print(f"\n4. Full HTML of first radio:")
        html = radios[0].get_attribute('outerHTML')
        print(html[:1000])
    
    input("\nPress Enter to close...")

finally:
    driver.quit()
