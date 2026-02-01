#!/usr/bin/env python3
"""
Test extraction with aria-label filter
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
    
    # Find questions
    all_items = driver.find_elements(By.XPATH, "//*[@data-item-id]")
    question_elements = []
    
    for item in all_items:
        item_id = item.get_attribute('data-item-id')
        if item_id != "-1":
            question_elements.append(item)
    
    logger.info(f"\nTotal {len(question_elements)} question containers\n")
    logger.info("="*80)
    
    for idx, q_elem in enumerate(question_elements):
        # Get title
        spans = q_elem.find_elements(By.CLASS_NAME, "M7eMe")
        title = ""
        for span in spans:
            text = span.text.strip() if span.text else ""
            if text and "Phần" not in text and "Mục không có tiêu đề" not in text:
                title = text
                break
        
        if not title:
            continue
        
        # NEW: Only get inputs with aria-label='giá trị tùy chọn'
        option_inputs = q_elem.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf') and @aria-label='giá trị tùy chọn']")
        
        logger.info(f"Q{idx+1}: {title}")
        logger.info(f"  Option inputs (aria-label=giá trị tùy chọn): {len(option_inputs)}")
        
        # Show values with deduplication
        if option_inputs:
            values = []
            seen = set()
            for inp in option_inputs:
                val = inp.get_attribute('value')
                val = val if val else "(empty)"
                if val not in seen:
                    values.append(val)
                    seen.add(val)
            logger.info(f"  Unique values: {values}")
        
        logger.info("")
    
    logger.info("="*80)
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
