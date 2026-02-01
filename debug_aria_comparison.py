#!/usr/bin/env python3
"""
Debug aria-label comparison
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
    
    # Get all .editable divs with aria-label containing "Câu"
    all_editable = driver.find_elements(By.CLASS_NAME, "editable")
    
    logger.info("\nAnalyzing aria-label values:\n")
    
    for elem in all_editable:
        aria = elem.get_attribute('aria-label')
        
        if aria and 'Câu' in aria:
            logger.info(f"Raw aria value: {repr(aria)}")
            logger.info(f"  repr: {repr(aria)}")
            logger.info(f"  len: {len(aria)}")
            logger.info(f"  bytes: {aria.encode('utf-8')}")
            logger.info(f"  == 'Câu hỏi': {aria == 'Câu hỏi'}")
            logger.info(f"  contains 'Câu hỏi': {'Câu hỏi' in aria}")
            logger.info(f"  strip() == 'Câu hỏi': {aria.strip() == 'Câu hỏi'}")
            logger.info()
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
