#!/usr/bin/env python3
"""
Test with longer wait and scrolling
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    logger.info("Waiting 10 seconds for page to fully load...")
    time.sleep(10)
    
    # Try to find and click inside form area to trigger focus
    try:
        form_body = driver.find_element(By.CLASS_NAME, "Dy5Kwe")
        driver.execute_script("arguments[0].click();", form_body)
        time.sleep(2)
    except:
        pass
    
    # Scroll down to load all elements
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    # Now search for questions
    logger.info("\n" + "="*100)
    logger.info("SEARCHING FOR QUESTIONS")
    logger.info("="*100)
    
    # Search all divs with aria-label containing "Câu"
    all_q = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Câu')]")
    logger.info(f"\nAll elements with aria-label containing 'Câu': {len(all_q)}")
    
    # Search specific
    q_divs = driver.find_elements(By.XPATH, "//div[@aria-label='Câu hỏi']")
    logger.info(f"\nDivs with aria-label='Câu hỏi': {len(q_divs)}")
    for idx, div in enumerate(q_divs):
        text = div.text.strip() if div.text else "(no text)"
        logger.info(f"  {idx+1}. {text}")
    
    # Try to get all text content divs
    editable_divs = driver.find_elements(By.CLASS_NAME, "editable")
    logger.info(f"\nAll .editable divs: {len(editable_divs)}")
    
    question_count = 0
    for idx, div in enumerate(editable_divs):
        aria = div.get_attribute('aria-label') or ""
        text = div.text.strip() if div.text else ""
        
        if aria == "Câu hỏi":
            question_count += 1
            logger.info(f"\n  Q{question_count}: {text}")
    
    logger.info(f"\n" + "="*100)
    logger.info(f"Total questions found: {question_count}")
    logger.info("="*100 + "\n")
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    if 'driver' in locals():
        driver.quit()
