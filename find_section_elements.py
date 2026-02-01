#!/usr/bin/env python3
"""
Detailed DOM analysis to find section headers
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
    
    # Search for ALL elements with jsname="yrriRe"
    all_editable = driver.find_elements(By.XPATH, "//*[@jsname='yrriRe']")
    logger.info(f"\nTotal elements with jsname='yrriRe': {len(all_editable)}\n")
    
    for idx, elem in enumerate(all_editable):
        aria_label = elem.get_attribute('aria-label')
        class_list = elem.get_attribute('class')
        text = elem.text
        
        logger.info(f"\nElement {idx+1}:")
        logger.info(f"  aria-label: {aria_label}")
        logger.info(f"  class: {class_list}")
        logger.info(f"  text: {text[:50]}..." if len(text) > 50 else f"  text: {text}")
        
        # Check if it's a section title (check for specific classes or attributes)
        is_section = "Tiêu đề" in aria_label if aria_label else False
        logger.info(f"  Is Section: {is_section}")
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
