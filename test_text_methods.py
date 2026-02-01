#!/usr/bin/env python3
"""
Test .text vs innerText
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
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
    all_editable = driver.find_elements(By.CLASS_NAME, "editable")
    
    logger.info(f"\nAnalyzing {len(all_editable)} .editable divs:\n")
    logger.info("="*100)
    
    for idx, elem in enumerate(all_editable):
        aria = elem.get_attribute('aria-label') or ""
        
        # Try different ways to get text
        text1 = elem.text.strip() if elem.text else "(empty via .text)"
        text2 = driver.execute_script("return arguments[0].innerText", elem) or "(empty via innerText)"
        text3 = driver.execute_script("return arguments[0].textContent", elem) or "(empty via textContent)"
        
        logger.info(f"\nDiv {idx+1} - aria-label: {aria}")
        logger.info(f"  .text:        '{text1}'")
        logger.info(f"  innerText:    '{text2}'")
        logger.info(f"  textContent:  '{text3}'")
    
    logger.info("\n" + "="*100 + "\n")
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
