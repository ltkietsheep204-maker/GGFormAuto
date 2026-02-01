#!/usr/bin/env python3
"""
Test script to verify option extraction works correctly
"""

import sys
import json
sys.path.insert(0, '/Users/2apple_mgn_63_ram16/Desktop/Dự Án Code/GGform')

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulated extraction logic
FORM_URL = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
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
    
    logger.info(f"\nFound {len(question_elements)} question containers\n")
    logger.info("="*80)
    
    for idx, q_elem in enumerate(question_elements):
        try:
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
            
            # Find text element
            try:
                text_elem = q_elem.find_element(By.XPATH, ".//div[contains(@class, 'editable') and @role='textbox' and contains(@aria-label, 'Câu')]")
            except:
                text_elem = q_elem
            
            # Get options - jsname filter or fallback
            options_inputs = q_elem.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf') and @jsname='YPqjbf']")
            
            if not options_inputs:
                all_opts = q_elem.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf')]")
                options_inputs = all_opts[:20] if all_opts else []
            
            options_list = []
            for inp in options_inputs:
                value = inp.get_attribute('value')
                if value is not None:
                    text_value = value.strip() if value else ""
                    if not any(x in text_value for x in ['jsname', 'data-', 'aria-']):
                        options_list.append(text_value)
            
            # Filter out empty if there are non-empty
            non_empty = [o for o in options_list if o]
            if non_empty:
                options_list = non_empty
            
            logger.info(f"Q{idx+1}: {title[:40]}")
            logger.info(f"  Options: {len(options_list)}")
            if options_list:
                for opt in options_list[:5]:  # Show first 5
                    logger.info(f"    - {opt}")
                if len(options_list) > 5:
                    logger.info(f"    ... and {len(options_list)-5} more")
            logger.info("")
        except Exception as e:
            logger.error(f"Error on Q{idx+1}: {e}")
    
    logger.info("="*80)
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
