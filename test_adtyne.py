#!/usr/bin/env python3
"""Debug - Check if span.aDTYNe selector works"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

form_url = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(form_url)
time.sleep(5)

# Get first real question (data-item-id != -1)
elements = driver.find_elements(By.XPATH, "//*[@data-item-id and @data-item-id != '-1']")

print("\n" + "="*70)
print("TEST SPAN.aDTYNe SELECTOR")
print("="*70)

for q_idx, elem in enumerate(elements[:2]):
    print(f"\n\nQUESTION {q_idx}:")
    
    # Get title (M7eMe)
    titles = elem.find_elements(By.CLASS_NAME, "M7eMe")
    if titles:
        title_text = titles[0].text.strip()
        print(f"Title: {title_text}")
    
    # Try span.aDTYNe
    adtyne_spans = elem.find_elements(By.CLASS_NAME, "aDTYNe")
    print(f"\nFound {len(adtyne_spans)} spans with class 'aDTYNe'")
    
    for i, span in enumerate(adtyne_spans[:5]):
        text = span.text.strip()
        classes = span.get_attribute('class')
        print(f"  [{i}] text='{text}' | class='{classes}'")
    
    # Try span.OIC90c (might be simpler)
    oic_spans = elem.find_elements(By.CLASS_NAME, "OIC90c")
    print(f"\nFound {len(oic_spans)} spans with class 'OIC90c'")
    
    for i, span in enumerate(oic_spans[:5]):
        text = span.text.strip()
        print(f"  [{i}] '{text}'")

driver.quit()
print("\n" + "="*70)
