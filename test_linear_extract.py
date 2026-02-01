#!/usr/bin/env python3
"""Test LINEAR SCALE extraction logic"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def test_linear_scale():
    print("=== TEST LINEAR SCALE EXTRACTION ===\n")
    
    # Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        url = "https://docs.google.com/forms/d/1V3LZd-3gIrzRczrSwkWwqE7OB_w1pzNWoJnIYaqaG6M/edit"
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Find questions
        question_elements = driver.find_elements(By.XPATH, "//*[@data-item-id]")
        print(f"\nFound {len(question_elements)} question elements")
        
        linear_count = 0
        linear_with_options = 0
        
        for idx, q_elem in enumerate(question_elements[:15]):
            text = q_elem.text or ""
            lines = text.split('\n')[:5]  # First 5 lines
            
            print(f"\n{'='*60}")
            print(f"QUESTION {idx}")
            print(f"First 5 lines: {lines}")
            
            # Check for linear scale pattern "1\n2\n3\n4\n5"
            pattern_1_5 = "1\n2\n3\n4\n5"
            is_linear = pattern_1_5 in text
            
            if is_linear:
                linear_count += 1
                print(f"✅ LINEAR SCALE DETECTED (pattern '1\\n2\\n3\\n4\\n5' found)")
                
                # Try to extract options
                options = []
                for scale_range in [(1, 5), (0, 10), (1, 10), (1, 7), (0, 5)]:
                    min_v, max_v = scale_range
                    pattern_nums = '\n'.join(str(i) for i in range(min_v, max_v + 1))
                    if pattern_nums in text:
                        print(f"  ✓ Matched pattern {min_v}-{max_v}")
                        for val in range(min_v, max_v + 1):
                            options.append(str(val))
                        break
                
                if options:
                    linear_with_options += 1
                    print(f"  Generated options: {options}")
                else:
                    print(f"  ⚠️ No options generated")
                    
                # Also check for scale labels
                scale_inputs = q_elem.find_elements(By.XPATH, ".//input[contains(@aria-label, 'giới hạn tỷ lệ')]")
                if scale_inputs:
                    for inp in scale_inputs:
                        aria = inp.get_attribute('aria-label') or ""
                        value = inp.get_attribute('value') or ""
                        print(f"  Scale label input: value='{value}', aria='{aria}'")
            else:
                # Check if it's a section header
                if "Phần" in text and "/" in text:
                    print(f"📄 SECTION HEADER")
                else:
                    # Check for other types
                    radios = q_elem.find_elements(By.XPATH, ".//input[@type='text' and @aria-label='giá trị tùy chọn']")
                    if radios:
                        print(f"📝 MULTIPLE CHOICE ({len(radios)} options)")
                    else:
                        print(f"❓ OTHER TYPE")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Total questions: {len(question_elements)}")
        print(f"  Linear scale detected: {linear_count}")
        print(f"  Linear with options generated: {linear_with_options}")
        
    finally:
        driver.quit()
        print("\nDone!")

if __name__ == "__main__":
    test_linear_scale()
