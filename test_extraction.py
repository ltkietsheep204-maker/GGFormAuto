#!/usr/bin/env python3
"""
Test script to extract form structure with detailed logging
This directly tests the options extraction without GUI
"""

import logging
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_form(url):
    """Test extracting form structure"""
    logger.info(f"Testing form: {url}")
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        logger.info("Form loaded, waiting for elements...")
        
        # Wait for form to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Qr7Oae")))
        
        time.sleep(2)  # Extra wait
        
        # Get all questions
        questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        logger.info(f"Found {len(questions)} questions")
        
        for q_idx, question in enumerate(questions):
            logger.info(f"\n{'='*60}")
            logger.info(f"Question {q_idx + 1}:")
            
            # Get question text
            try:
                title = question.find_element(By.CLASS_NAME, "Uc2Deb")
                logger.info(f"  Title: {title.text}")
            except:
                logger.info("  Title: Not found")
            
            # Get options using multiple methods
            logger.info("  Extracting options:")
            
            # Method 1: YKDB3e
            options_ykdb = question.find_elements(By.CLASS_NAME, "YKDB3e")
            logger.info(f"    Method 1 (YKDB3e): {len(options_ykdb)} containers found")
            
            for opt_idx, opt in enumerate(options_ykdb):
                try:
                    urLvsc = opt.find_element(By.CLASS_NAME, "urLvsc")
                    text = urLvsc.text.strip()
                    logger.info(f"      [{opt_idx}] {text}")
                except:
                    logger.debug(f"      [{opt_idx}] Failed to get text")
            
            # Method 2: Radio buttons
            radios = question.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            logger.info(f"    Method 2 (radio): {len(radios)} found")
            
            for radio_idx, radio in enumerate(radios):
                try:
                    parent = radio.find_element(By.XPATH, "..")
                    spans = parent.find_elements(By.TAG_NAME, "span")
                    if spans:
                        text = spans[0].text.strip() if spans[0].text else "No text"
                        logger.info(f"      [{radio_idx}] {text}")
                except Exception as e:
                    logger.debug(f"      [{radio_idx}] Error: {e}")
            
            # Method 3: All spans
            all_spans = question.find_elements(By.TAG_NAME, "span")
            logger.info(f"    Method 3 (all spans): {len(all_spans)} total spans")
            
            # Print first 20 non-empty spans
            spans_printed = 0
            for span_idx, span in enumerate(all_spans):
                if spans_printed >= 20:
                    break
                text = span.text.strip()
                if text and len(text) > 1 and "Required" not in text:
                    logger.info(f"      [{spans_printed}] {text}")
                    spans_printed += 1
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Google Form URL: ").strip()
    
    test_form(url)
