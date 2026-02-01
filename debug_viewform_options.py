#!/usr/bin/env python3
"""
Debug script to see how options appear in VIEWFORM (when filling form)
"""

import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Viewform URL (for filling, not editing)
FORM_URL = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/viewform?hl=vi"

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    logger.info("Opening VIEWFORM...")
    driver.get(FORM_URL)
    time.sleep(5)
    
    logger.info("\n" + "="*80)
    logger.info("ANALYZING OPTIONS IN VIEWFORM")
    logger.info("="*80 + "\n")
    
    # Find first question
    questions = driver.find_elements(By.XPATH, "//div[@data-item-id]")
    logger.info(f"Found {len(questions)} question containers\n")
    
    if questions:
        first_q = questions[0]
        q_text = first_q.text[:100] if first_q.text else "?"
        logger.info(f"First question: {q_text}\n")
        
        logger.info("Looking for option elements...\n")
        
        # Check different option types
        selectors = [
            ("Radio buttons", ".//div[@role='radio']"),
            ("Checkboxes", ".//div[@role='checkbox']"),
            ("Radio + label", ".//input[@type='radio']"),
            ("Checkbox + label", ".//input[@type='checkbox']"),
            ("OIC90c spans", ".//span[@class='OIC90c']"),
            ("All spans", ".//span"),
            ("Text inputs", ".//input[@type='text']"),
            ("Divs with role button", ".//div[@role='button']"),
        ]
        
        for desc, xpath in selectors:
            try:
                elements = first_q.find_elements(By.XPATH, xpath)
                if elements:
                    logger.info(f"✓ {desc}: Found {len(elements)}")
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = elem.text or elem.get_attribute('value') or elem.get_attribute('aria-label') or "?"
                            logger.info(f"    [{i}] {text[:50]}")
                        except:
                            pass
                    logger.info("")
            except Exception as e:
                logger.info(f"✗ {desc}: Error - {str(e)[:30]}\n")
        
        # Print raw HTML of first question
        logger.info("\n" + "="*80)
        logger.info("RAW HTML OF FIRST QUESTION (first 2000 chars)")
        logger.info("="*80 + "\n")
        
        try:
            html = first_q.get_attribute("innerHTML")
            logger.info(html[:2000])
        except:
            pass
    
    driver.quit()
    logger.info("\n✓ Debug complete")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    if 'driver' in locals():
        driver.quit()
