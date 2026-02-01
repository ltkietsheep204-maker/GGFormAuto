#!/usr/bin/env python3
"""
FINAL VERIFICATION: Extract 4 questions with options
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
    time.sleep(10)
    
    import unicodedata
    
    logger.info("\n" + "="*100)
    logger.info("FINAL EXTRACTION TEST - WHAT TOOL WILL EXTRACT")
    logger.info("="*100)
    
    # Get all .editable divs
    all_editable = driver.find_elements(By.CLASS_NAME, "editable")
    
    # Store data immediately to avoid stale element references
    editable_data = []
    for elem in all_editable:
        aria = elem.get_attribute('aria-label') or ""
        text = elem.text.strip() if elem.text else ""
        # Normalize Unicode!
        aria_normalized = unicodedata.normalize('NFC', aria)
        editable_data.append({
            'aria': aria_normalized,
            'text': text,
            'elem': elem
        })
    
    logger.info(f"\nProcessed {len(editable_data)} .editable divs\n")
    
    questions = []
    sections = []
    
    for item in editable_data:
        aria = item['aria']
        text = item['text']
        elem = item['elem']
        
        if aria == "Câu hỏi" and text:
            questions.append((text, elem))
        elif aria in ("Tiêu đề phần (không bắt buộc)", "Tiêu đề phần") and text:
            sections.append((text, elem))
    
    # RESULTS
    logger.info(f"\n✓ Found {len(questions)} QUESTIONS:")
    for idx, (text, _) in enumerate(questions):
        logger.info(f"  Q{idx+1}: {text}")
    
    logger.info(f"\n✓ Found {len(sections)} SECTION HEADERS:")
    for idx, (text, _) in enumerate(sections):
        logger.info(f"  S{idx+1}: {text}")
    
    # Extract options
    logger.info(f"\n" + "="*100)
    logger.info("QUESTIONS WITH OPTIONS")
    logger.info("="*100)
    
    for idx, (text, elem) in enumerate(questions):
        # Find parent container
        parent = driver.execute_script("""
            let el = arguments[0];
            while (el && el.parentElement) {
                if (el.getAttribute('data-item-id')) return el;
                el = el.parentElement;
            }
            return null;
        """, elem)
        
        if parent:
            opts = parent.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and @aria-label='giá trị tùy chọn']")
            
            logger.info(f"\nQ{idx+1}: {text}")
            logger.info(f"  Raw options: {len(opts)}")
            
            # Get unique options
            seen = set()
            unique_opts = []
            for opt in opts:
                val = opt.get_attribute('value')
                if val and val not in seen:
                    unique_opts.append(val)
                    seen.add(val)
            
            logger.info(f"  Unique options: {len(unique_opts)}")
            for opt_val in unique_opts:
                logger.info(f"    - {opt_val}")
        else:
            logger.info(f"\nQ{idx+1}: {text}")
            logger.info(f"  ERROR: No parent container found!")
    
    logger.info(f"\n" + "="*100)
    logger.info(f"SUMMARY")
    logger.info(f"  Questions: {len(questions)}")
    logger.info(f"  Sections: {len(sections)}")
    logger.info(f"  Total items: {len(questions) + len(sections)}")
    logger.info("="*100 + "\n")
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
