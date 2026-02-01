#!/usr/bin/env python3
"""Debug - Analyze radio button structure"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

form_url = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get(form_url)
    time.sleep(5)
    
    # Get first question with data-item-id != -1
    elements = driver.find_elements(By.XPATH, "//*[@data-item-id and @data-item-id != '-1']")
    
    if elements:
        first_q = elements[0]
        
        print("\n" + "="*70)
        print("FIRST QUESTION ANALYSIS")
        print("="*70)
        
        # Get title
        spans = first_q.find_elements(By.CLASS_NAME, "M7eMe")
        title = ""
        for span in spans:
            text = (span.get_attribute('innerText') or "").strip()
            if text and "Mục không có tiêu đề" not in text and "Phần" not in text and len(text) > 2:
                title = text
                break
        
        print(f"\n✓ Title: {title}")
        
        # Get all radios
        radios = first_q.find_elements(By.XPATH, ".//div[@role='radio']")
        print(f"\n✓ Found {len(radios)} radio buttons")
        
        print("\nRadio button details:")
        for i, radio in enumerate(radios):
            print(f"\n  Radio {i}:")
            
            # Check attributes
            aria_label = radio.get_attribute('aria-label')
            data_value = radio.get_attribute('data-value')
            print(f"    aria-label: {aria_label}")
            print(f"    data-value: {data_value}")
            
            # Check inner HTML
            inner_html = radio.get_attribute('innerHTML')[:100] if radio.get_attribute('innerHTML') else ""
            print(f"    innerHTML: {inner_html}...")
            
            # Check child spans
            child_spans = radio.find_elements(By.TAG_NAME, "span")
            print(f"    Child spans: {len(child_spans)}")
            for j, span in enumerate(child_spans[:2]):
                span_text = span.text.strip() if span.text else ""
                span_class = span.get_attribute('class')
                if span_text or span_class:
                    print(f"      [{j}] text='{span_text}' class='{span_class}'")
            
            # Try to get visible text
            try:
                visible_text = driver.execute_script("""
                    const elem = arguments[0];
                    return elem.innerText || elem.textContent;
                """, radio)
                print(f"    Visible text: {visible_text.strip()[:50]}")
            except:
                pass
        
        print("\n" + "="*70)
        
finally:
    driver.quit()
