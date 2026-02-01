#!/usr/bin/env python3
"""
Analyze option input types in Q3
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
    
    # Get Q3
    q3 = question_elements[2]
    logger.info("Q3: Analyzing input structure...\n")
    
    # Get all option inputs
    option_inputs = q3.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and @jsname='YPqjbf']")
    
    logger.info(f"Total option inputs: {len(option_inputs)}\n")
    logger.info("="*100)
    
    for i, inp in enumerate(option_inputs):
        value = inp.get_attribute('value')
        placeholder = inp.get_attribute('placeholder')
        
        # Check if it's in a "value" field (often has class containing "value" or similar)
        classes = inp.get_attribute('class')
        aria_label = inp.get_attribute('aria-label')
        
        logger.info(f"\nInput {i+1}:")
        logger.info(f"  Value: '{value}'")
        logger.info(f"  Placeholder: '{placeholder}'")
        logger.info(f"  Aria-label: '{aria_label}'")
        logger.info(f"  Classes: {classes}")
        
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
