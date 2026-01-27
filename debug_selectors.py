#!/usr/bin/env python3
"""Debug script để test selectors"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import sys

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

print("Initializing Chrome...")
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')

try:
    driver = webdriver.Chrome(options=options)
    
    print("Loading form...")
    driver.get(form_url)
    
    print("Waiting for page to load...")
    time.sleep(6)
    
    print("\n=== SELECTOR TESTS ===\n")
    
    # Test 1: Find all Qr7Oae
    elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
    print(f"1. Found {len(elements)} Qr7Oae elements")
    
    if len(elements) == 0:
        print("ERROR: No Qr7Oae elements found!")
        sys.exit(1)
    
    # Test 2: Look for textbox with aria-label="Câu hỏi" in first element
    elem = elements[0]
    print(f"\n2. Testing selectors on first element:")
    
    # Test 2a: XPath with AND
    try:
        result = elem.find_elements(By.XPATH, ".//div[@role='textbox' and @aria-label='Câu hỏi']")
        print(f"   XPath with AND: {len(result)} found")
        if result:
            print(f"      Text: '{result[0].text}'")
    except Exception as e:
        print(f"   XPath with AND: ERROR - {str(e)[:50]}")
    
    # Test 2b: XPath with separate conditions
    try:
        result = elem.find_elements(By.XPATH, ".//div[@role='textbox'][@aria-label='Câu hỏi']")
        print(f"   XPath chained: {len(result)} found")
        if result:
            print(f"      Text: '{result[0].text}'")
    except Exception as e:
        print(f"   XPath chained: ERROR - {str(e)[:50]}")
    
    # Test 2c: Find all textbox then filter
    print(f"\n3. All textboxes in first element:")
    textboxes = elem.find_elements(By.XPATH, ".//div[@role='textbox']")
    print(f"   Total textboxes: {len(textboxes)}")
    for idx, tb in enumerate(textboxes):
        aria_label = tb.get_attribute('aria-label')
        text = tb.text[:30] if tb.text else "(empty)"
        classes = tb.get_attribute('class')
        print(f"   [{idx}] aria-label='{aria_label}' | text='{text}' | class='{classes}'")
    
    # Test 3: Find questions using class selector
    print(f"\n4. Testing class-based selectors:")
    try:
        result = elem.find_elements(By.XPATH, ".//div[@class='hj99tb KRoqRc editable'][@aria-label='Câu hỏi']")
        print(f"   Full class selector: {len(result)} found")
        if result:
            print(f"      Text: '{result[0].text}'")
    except Exception as e:
        print(f"   Full class selector: ERROR - {str(e)[:50]}")
    
    # Test 4: Look for textbox with specific classes
    try:
        result = elem.find_elements(By.XPATH, ".//div[contains(@class, 'hj99tb')][@aria-label='Câu hỏi']")
        print(f"   Contains 'hj99tb': {len(result)} found")
        if result:
            print(f"      Text: '{result[0].text}'")
    except Exception as e:
        print(f"   Contains 'hj99tb': ERROR - {str(e)[:50]}")
    
    print("\n=== EXTRACTING ALL QUESTIONS ===\n")
    
    actual_count = 0
    for elem_idx, elem in enumerate(elements):
        # Find question textbox
        textboxes = elem.find_elements(By.XPATH, ".//div[@role='textbox']")
        
        question_title = None
        for tb in textboxes:
            aria_label = tb.get_attribute('aria-label')
            if aria_label == "Câu hỏi":
                question_title = tb.text.strip().replace('\xa0', ' ')
                break
        
        if not question_title:
            # Check if section header
            for tb in textboxes:
                aria_label = tb.get_attribute('aria-label')
                if aria_label == "Tiêu đề phần (không bắt buộc)":
                    section_text = tb.text.strip()
                    print(f"Element {elem_idx+1}: SECTION HEADER - '{section_text}'")
                    break
            else:
                print(f"Element {elem_idx+1}: NO TITLE FOUND")
            continue
        
        actual_count += 1
        
        # Check type
        radios = len(elem.find_elements(By.XPATH, ".//div[@role='radio']"))
        checks = len(elem.find_elements(By.XPATH, ".//div[@role='checkbox']"))
        
        q_type = "unknown"
        if radios > 0:
            q_type = f"multiple_choice ({radios})"
        elif checks > 0:
            q_type = f"checkbox ({checks})"
        
        print(f"Q{actual_count}: '{question_title}' - {q_type}")
    
    print(f"\n✅ Total actual questions found: {actual_count}")
    
finally:
    driver.quit()
    print("\nDone!")
