#!/usr/bin/env python3
"""
Check exactly how many input fields in each question
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
        
        # Count ALL input fields in this container
        all_inputs = q_elem.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb')]")
        
        # Count ONLY option inputs (jsname=YPqjbf)
        option_inputs = q_elem.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and @jsname='YPqjbf']")
        
        logger.info(f"Q{idx+1}: {title}")
        logger.info(f"  Total Hvn9fb inputs: {len(all_inputs)}")
        logger.info(f"  Option inputs (jsname=YPqjbf): {len(option_inputs)}")
        
        # Show values
        if option_inputs:
            values = []
            for inp in option_inputs[:12]:  # Show up to 12
                val = inp.get_attribute('value')
                values.append(val if val else "(empty)")
            logger.info(f"  Values: {values}")
        
        logger.info("")
    
    logger.info("="*80)
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
