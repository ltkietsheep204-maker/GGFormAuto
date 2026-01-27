#!/usr/bin/env python3
"""Test complete extraction"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

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
    print(f"\nFound {len(elements)} questions\n")
    
    for idx, elem in enumerate(elements):
        # Get title
        spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
        title = spans[0].get_attribute('innerText') if spans else ""
        
        # Check if section header
        if "Mục không có tiêu đề" in title:
            print(f"{idx}. [SECTION HEADER] {title}")
            continue
        
        # Get options
        radios = elem.find_elements(By.XPATH, ".//div[@role='radio']")
        checkboxes = elem.find_elements(By.XPATH, ".//div[@role='checkbox']")
        
        options_list = []
        for radio in radios:
            text = radio.get_attribute('aria-label') or radio.get_attribute('data-value')
            if text:
                options_list.append(text.strip())
        
        for checkbox in checkboxes:
            text = checkbox.get_attribute('aria-label') or checkbox.get_attribute('data-value')
            if text:
                options_list.append(text.strip())
        
        print(f"{idx}. {title}")
        if options_list:
            for opt in options_list:
                print(f"     - {opt}")
        else:
            print(f"     (no options)")
        print()
    
    input("Press Enter to close...")

finally:
    driver.quit()
