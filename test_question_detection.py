#!/usr/bin/env python3
"""
Test extraction with improved section header detection
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

def check_aria_label(element, label):
    """Check if element has specific aria-label"""
    try:
        divs = element.find_elements(By.XPATH, f".//div[@aria-label='{label}']")
        return len(divs) > 0
    except:
        return False

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
    
    logger.info(f"\nTotal {len(question_elements)} elements with data-item-id != -1\n")
    logger.info("="*100)
    
    questions_count = 0
    for idx, q_elem in enumerate(question_elements):
        # Check if it's a section header
        is_section = check_aria_label(q_elem, "Tiêu đề phần (không bắt buộc)")
        is_form_title = check_aria_label(q_elem, "Tiêu đề biểu mẫu")
        is_question = check_aria_label(q_elem, "Câu hỏi")
        
        logger.info(f"\nElement {idx+1}:")
        logger.info(f"  Is Form Title: {is_form_title}")
        logger.info(f"  Is Section Header: {is_section}")
        logger.info(f"  Is Question: {is_question}")
        
        if is_question:
            questions_count += 1
            question_div = q_elem.find_element(By.XPATH, ".//div[@aria-label='Câu hỏi']")
            text = question_div.text
            logger.info(f"  Question #{questions_count}: {text}")
        
        if is_section:
            section_div = q_elem.find_element(By.XPATH, ".//div[@aria-label='Tiêu đề phần (không bắt buộc)']")
            text = section_div.text
            logger.info(f"  Section Header: {text}")
        
        if is_form_title:
            logger.info(f"  [SKIP] Form Title")
    
    logger.info("\n" + "="*100)
    logger.info(f"\nFinal count: {questions_count} questions\n")
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
