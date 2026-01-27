#!/usr/bin/env python3
"""Check what's in the form"""
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
    print(f"Loading: {FORM_URL}")
    time.sleep(8)
    
    print(f"\nCurrent URL: {driver.current_url}")
    
    # Try multiple class names
    for class_name in ["Qr7Oae", "OxAavc", "pYfr3c", "question"]:
        count = len(driver.find_elements(By.CLASS_NAME, class_name))
        print(f"  {class_name}: {count}")
    
    # Check M7eMe spans
    spans = driver.find_elements(By.CLASS_NAME, "M7eMe")
    print(f"\nM7eMe spans: {len(spans)}")
    if spans:
        for idx, span in enumerate(spans[:3]):
            text = span.get_attribute('innerText') or ""
            print(f"  {idx}: {text}")
    
    input("\nPress Enter to close...")

finally:
    driver.quit()
