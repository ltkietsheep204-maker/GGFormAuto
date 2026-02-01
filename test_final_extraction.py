#!/usr/bin/env python3
"""
Final test: Identify exactly which questions will be extracted
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORM_URL = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    logger.info("Opening form...")
    driver.get(FORM_URL)
    time.sleep(5)
    
    logger.info("\n" + "="*100)
    logger.info("EXTRACTION LOGIC TEST")
    logger.info("="*100)
    
    # Step 1: Find all "Câu hỏi" elements (actual questions)
    question_divs = driver.find_elements(By.XPATH, ".//div[@role='textbox' and @aria-label='Câu hỏi']")
    logger.info(f"\n✓ Found {len(question_divs)} QUESTIONS (aria-label='Câu hỏi'):")
    for idx, div in enumerate(question_divs):
        text = div.text.strip()
        logger.info(f"  Q{idx+1}: {text}")
    
    # Step 2: Find all section headers
    section_divs = driver.find_elements(By.XPATH, ".//div[@role='textbox' and @aria-label='Tiêu đề phần (không bắt buộc)']")
    logger.info(f"\n✓ Found {len(section_divs)} SECTION HEADERS (aria-label='Tiêu đề phần'):")
    for idx, div in enumerate(section_divs):
        text = div.text.strip()
        logger.info(f"  Section{idx+1}: {text}")
    
    # Step 3: Show what would be skipped
    logger.info(f"\n✗ SKIPPED items:")
    skip_divs = driver.find_elements(By.XPATH, ".//div[@role='textbox' and @aria-label='Tiêu đề biểu mẫu']")
    logger.info(f"  - Form Title (Tiêu đề biểu mẫu): {skip_divs[0].text if skip_divs else 'None'}")
    
    desc_divs = driver.find_elements(By.XPATH, ".//div[@role='textbox' and (@aria-label='Mô tả' or @aria-label='Mô tả biểu mẫu' or @aria-label='Mô tả (không bắt buộc)')]")
    logger.info(f"  - Descriptions (Mô tả*): {len(desc_divs)} items")
    
    # Step 4: For each question, get options
    logger.info(f"\n" + "="*100)
    logger.info("QUESTIONS WITH OPTIONS")
    logger.info("="*100)
    
    for idx, q_div in enumerate(question_divs):
        q_text = q_div.text.strip()
        
        # Find parent container for this question
        parent_container = driver.execute_script("""
            let el = arguments[0];
            while (el && el.parentElement) {
                if (el.getAttribute('data-item-id')) {
                    return el;
                }
                el = el.parentElement;
            }
            return null;
        """, q_div)
        
        if parent_container:
            # Get options from this container
            option_inputs = parent_container.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and @aria-label='giá trị tùy chọn']")
            
            logger.info(f"\nQ{idx+1}: {q_text}")
            logger.info(f"  Options: {len(option_inputs)}")
            
            # Show unique options
            seen = set()
            for opt in option_inputs:
                val = opt.get_attribute('value')
                if val and val not in seen:
                    logger.info(f"    - {val}")
                    seen.add(val)
    
    logger.info("\n" + "="*100)
    logger.info(f"SUMMARY: {len(question_divs)} questions + {len(section_divs)} section headers")
    logger.info("="*100 + "\n")
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
