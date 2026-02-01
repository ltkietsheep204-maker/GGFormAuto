#!/usr/bin/env python3
"""
Simple test - find 4 questions
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
    
    # Wait longer for form to load completely
    time.sleep(8)
    
    logger.info("\n" + "="*100)
    logger.info("SEARCHING FOR 4 QUESTIONS")
    logger.info("="*100)
    
    # Method 1: Direct search for aria-label
    all_divs = driver.find_elements(By.XPATH, "//*[@aria-label='Câu hỏi']")
    logger.info(f"\nMethod 1 - XPath //*[@aria-label='Câu hỏi']: Found {len(all_divs)}")
    for idx, div in enumerate(all_divs):
        text = div.text.strip() if div.text else "(empty)"
        role = div.get_attribute('role')
        logger.info(f"  {idx+1}. text='{text}', role='{role}'")
    
    # Method 2: Search with role='textbox'
    divs_textbox = driver.find_elements(By.XPATH, "//*[@role='textbox' and @aria-label='Câu hỏi']")
    logger.info(f"\nMethod 2 - XPath //*[@role='textbox' and @aria-label='Câu hỏi']: Found {len(divs_textbox)}")
    for idx, div in enumerate(divs_textbox):
        text = div.text.strip() if div.text else "(empty)"
        logger.info(f"  {idx+1}. {text}")
    
    # Method 3: Search with jsname attribute
    divs_jsname = driver.find_elements(By.XPATH, "//*[@jsname='yrriRe' and @aria-label='Câu hỏi']")
    logger.info(f"\nMethod 3 - XPath //*[@jsname='yrriRe' and @aria-label='Câu hỏi']: Found {len(divs_jsname)}")
    for idx, div in enumerate(divs_jsname):
        text = div.text.strip() if div.text else "(empty)"
        logger.info(f"  {idx+1}. {text}")
    
    logger.info("\n" + "="*100 + "\n")
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
