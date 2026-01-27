#!/usr/bin/env python3
"""Test script để kiểm tra question extraction"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    print("Loading form...")
    driver.get(form_url)
    time.sleep(4)
    
    # Find all Qr7Oae elements
    elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
    print(f"\nFound {len(elements)} Qr7Oae elements\n")
    
    actual_questions = 0
    
    for idx, elem in enumerate(elements):
        print(f"=== Element {idx+1} ===")
        
        # Check if section header
        is_section = False
        try:
            textboxes = elem.find_elements(By.XPATH, ".//div[@role='textbox']")
            for tb in textboxes:
                aria_label = tb.get_attribute('aria-label')
                if aria_label == "Tiêu đề phần (không bắt buộc)":
                    text = tb.text.strip()
                    if "Mục không có" in text:
                        is_section = True
                        print(f"Type: SECTION HEADER")
                        break
        except:
            pass
        
        if is_section:
            print()
            continue
        
        # Get question title
        title = "NOT FOUND"
        try:
            textboxes = elem.find_elements(By.XPATH, ".//div[@role='textbox']")
            for tb in textboxes:
                aria_label = tb.get_attribute('aria-label')
                if aria_label == "Câu hỏi":
                    title = tb.text.strip().replace('\xa0', ' ')
                    break
        except:
            pass
        
        if title == "NOT FOUND":
            print(f"Title: NOT FOUND")
            print()
            continue
        
        actual_questions += 1
        print(f"Title: '{title}'")
        
        # Check type
        radios = len(elem.find_elements(By.XPATH, ".//div[@role='radio']"))
        checks = len(elem.find_elements(By.XPATH, ".//div[@role='checkbox']"))
        
        if radios > 0:
            print(f"Type: multiple_choice ({radios} radios)")
        elif checks > 0:
            print(f"Type: checkbox ({checks} checks)")
        else:
            print(f"Type: unknown")
        
        print()
    
    print(f"RESULT: Found {actual_questions} actual questions (expected: 3)")

finally:
    driver.quit()
