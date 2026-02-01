#!/usr/bin/env python3
"""
Debug script to inspect form HTML structure
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO, 
    format='%(message)s',
    handlers=[
        logging.FileHandler('/Users/2apple_mgn_63_ram16/Desktop/Dự Án Code/GGform/debug_output_form.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Form URL
FORM_URL = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/viewform?hl=vi"

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
    
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    logger.info("Opening form...")
    driver.get(FORM_URL)
    
    # Wait for page to fully load
    logger.info("Waiting for page to load...")
    time.sleep(5)
    
    # Scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Get page source and save it
    page_html = driver.page_source
    
    # Try different selectors
    logger.info("\nTrying different selectors to find questions...\n")
    
    selectors = [
        ("//div[@data-item-id]", "data-item-id"),
        ("//div[@data-item-id-key]", "data-item-id-key"),
        ("//div[contains(@class, 'HJarJ')]", "HJarJ class"),
        ("//div[@class='gg-form-question']", "gg-form-question"),
        ("//div[contains(@class, 'Xrj4Rb')]", "Xrj4Rb class"),
        ("//div[@role='listitem']", "listitem role"),
        ("//div[contains(@jsname, 'Wic08d')]", "jsname Wic08d"),
        ("//div[@data-question-id]", "data-question-id"),
    ]
    
    for xpath, desc in selectors:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                logger.info(f"✓ {desc}: Found {len(elements)} elements")
            else:
                logger.info(f"✗ {desc}: Found 0 elements")
        except Exception as e:
            logger.info(f"✗ {desc}: Error - {str(e)[:50]}")
    
    # Let's inspect the actual structure
    logger.info("\n" + "="*80)
    logger.info("INSPECTING PAGE STRUCTURE")
    logger.info("="*80 + "\n")
    
    # Get body HTML
    body = driver.find_element(By.TAG_NAME, "body")
    
    # Find main content area
    main_divs = driver.find_elements(By.XPATH, "//div[@role='main']")
    logger.info(f"Found {len(main_divs)} main divs\n")
    
    if main_divs:
        main_html = main_divs[0].get_attribute("innerHTML")[:3000]
        logger.info("First 3000 chars of main div:")
        logger.info(main_html[:1500])
        logger.info("\n...")
    
    # Try to find any text that looks like a question
    logger.info("\n" + "="*80)
    logger.info("LOOKING FOR QUESTION TEXT")
    logger.info("="*80 + "\n")
    
    spans = driver.find_elements(By.TAG_NAME, "span")
    question_count = 0
    for span in spans:
        text = span.text.strip()
        if text and len(text) > 10 and ("Câu" in text or "tôi" in text or "không" in text):
            logger.info(f"Found text: {text[:80]}")
            question_count += 1
            if question_count >= 3:
                break
    
    driver.quit()
    logger.info("\n✓ Debug complete")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    if 'driver' in locals():
        driver.quit()
