#!/usr/bin/env python3
"""
Check section headers vs questions
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
    
    # Find ALL data-item-id elements
    all_items = driver.find_elements(By.XPATH, "//*[@data-item-id]")
    
    logger.info(f"\nTotal {len(all_items)} items with data-item-id\n")
    logger.info("="*100)
    
    for idx, item in enumerate(all_items):
        item_id = item.get_attribute('data-item-id')
        
        # Check if it's a section header (aria-label="Tiêu đề phần")
        section_title_elem = item.find_elements(By.XPATH, ".//div[@jsname='yrriRe' and @aria-label='Tiêu đề phần']")
        is_section = len(section_title_elem) > 0
        
        # Get section title text
        section_text = ""
        if is_section:
            section_elems = item.find_elements(By.XPATH, ".//div[@jsname='yrriRe' and @aria-label='Tiêu đề phần (không bắt buộc)']")
            if not section_elems:
                section_elems = item.find_elements(By.XPATH, ".//div[@jsname='yrriRe'][@aria-label*='Tiêu đề']")
            if section_elems:
                section_text = section_elems[0].text
        
        # Get question text
        question_text = ""
        question_elems = item.find_elements(By.XPATH, ".//div[@aria-label='Câu hỏi']")
        if not question_elems:
            question_elems = item.find_elements(By.XPATH, ".//div[contains(@aria-label, 'Câu')]")
        if question_elems:
            question_text = question_elems[0].text
        
        # Show info
        logger.info(f"\nItem {idx+1} (data-item-id={item_id}):")
        logger.info(f"  Is Section Header: {is_section}")
        if is_section:
            logger.info(f"  Section Title: {section_text}")
        else:
            logger.info(f"  Question: {question_text}")
            
            # Count options for this question
            options_count = len(item.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and @aria-label='giá trị tùy chọn']"))
            logger.info(f"  Options count: {options_count}")
    
    logger.info("\n" + "="*100)
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
