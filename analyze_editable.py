#!/usr/bin/env python3
"""
Analyze all .editable divs
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
    
    # Get all .editable divs
    editable_divs = driver.find_elements(By.CLASS_NAME, "editable")
    logger.info(f"\nAll .editable divs: {len(editable_divs)}\n")
    logger.info("="*100)
    
    for idx, div in enumerate(editable_divs):
        aria = div.get_attribute('aria-label') or "(no aria-label)"
        text = div.text.strip() if div.text else "(no text)"
        role = div.get_attribute('role') or "(no role)"
        
        logger.info(f"\nDiv {idx+1}:")
        logger.info(f"  aria-label: {aria}")
        logger.info(f"  role: {role}")
        logger.info(f"  text: {text[:60]}{'...' if len(text) > 60 else ''}")
    
    logger.info("\n" + "="*100 + "\n")
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
