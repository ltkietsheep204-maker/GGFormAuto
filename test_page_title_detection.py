#!/usr/bin/env python3
"""
Test script để xác minh page title detection logic
"""
import sys
sys.path.insert(0, '/Users/2apple_mgn_63_ram16/Desktop/GGform')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json

form_url = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/viewform?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(form_url)
time.sleep(6)

# Get all question elements
questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
print(f"\n{'='*60}")
print(f"FOUND {len(questions)} QUESTION ELEMENTS")
print(f"{'='*60}\n")

extracted = []

for idx, q in enumerate(questions):
    print(f"\n--- Element {idx} ---")
    
    # Get title
    spans = q.find_elements(By.CLASS_NAME, "M7eMe")
    title = ""
    is_page_title = False
    
    for s in spans:
        text = s.get_attribute('innerText') or s.get_attribute('textContent')
        if text:
            text = text.strip().replace('\xa0', ' ').strip()
            print(f"Title text: {text}")
            title = text
            
            # Check if page title
            if "Phần" in text and "/" in text:
                print(f"✓ PAGE TITLE DETECTED: {text}")
                is_page_title = True
            elif "Mục không có tiêu đề" in text:
                print(f"✓ SECTION HEADER: {text}")
                is_page_title = True
    
    # Get options
    options_list = []
    radio = q.find_elements(By.XPATH, ".//div[@role='radio']")
    if radio:
        print(f"Type: multiple_choice ({len(radio)} options)")
        for r in radio:
            # Get option text
            try:
                # Try to find sibling span with text
                opt_text = driver.execute_script("""
                    let elem = arguments[0];
                    // Try parent's next element
                    if (elem.parentElement?.nextElementSibling?.textContent) {
                        return elem.parentElement.nextElementSibling.textContent.trim();
                    }
                    // Try to find direct text
                    let spans = elem.querySelectorAll('span');
                    for (let span of spans) {
                        if (span.textContent.trim()) return span.textContent.trim();
                    }
                    return elem.textContent.trim();
                """, r)
                if opt_text:
                    print(f"  Option: {opt_text}")
                    options_list.append(opt_text)
            except:
                pass
    
    # Save to list
    item = {
        "index": idx,
        "title": title,
        "is_page_title": is_page_title,
        "type": "section_header" if is_page_title else "multiple_choice",
        "options_count": len(options_list),
        "options": options_list[:3]  # First 3 options
    }
    extracted.append(item)

# Print summary
print(f"\n{'='*60}")
print(f"EXTRACTED DATA SUMMARY")
print(f"{'='*60}\n")

for item in extracted:
    icon = "📌" if item['is_page_title'] else "📋"
    print(f"{icon} {item['title']}")
    print(f"   Type: {item['type']}")
    if item['options_count'] > 0:
        print(f"   Options: {item['options_count']}")
    print()

# Save to JSON
with open("/Users/2apple_mgn_63_ram16/Desktop/GGform/extracted_form_test.json", "w", encoding="utf-8") as f:
    json.dump(extracted, f, indent=2, ensure_ascii=False)
print("\n✓ Saved to extracted_form_test.json")

driver.quit()
