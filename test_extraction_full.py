#!/usr/bin/env python3
"""Test question and option extraction"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

def get_question_text(driver, question_element) -> str:
    """Get question title"""
    try:
        spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
        if spans:
            for span in spans:
                text = span.get_attribute('innerText') or span.get_attribute('textContent')
                if text:
                    text = text.strip().replace('\xa0', ' ').strip()
                    if "Mục không có tiêu đề" not in text and text:
                        return text
    except:
        pass
    
    return "Untitled Question"

def is_section_header(question_element) -> bool:
    """Check if section header"""
    try:
        spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
        for span in spans:
            text = span.get_attribute('innerText') or span.get_attribute('textContent')
            if text:
                text = text.strip().replace('\xa0', ' ').strip()
                if "Mục không có tiêu đề" in text:
                    return True
    except:
        pass
    return False

def get_options(question_element) -> list:
    """Get question options"""
    options = []
    
    # Strategy 1: For EDITOR link - find div[@role='radio']
    try:
        radio_divs = question_element.find_elements(By.XPATH, ".//div[@role='radio']")
        logger.info(f"    Found {len(radio_divs)} radio options")
        
        if radio_divs:
            for idx, radio in enumerate(radio_divs):
                try:
                    text = radio.get_attribute('aria-label') or radio.get_attribute('data-value')
                    if text and text.strip():
                        options.append(text.strip())
                except:
                    pass
    except Exception as e:
        logger.debug(f"    Radio strategy failed: {e}")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        driver.get(FORM_URL)
        time.sleep(8)
        
        elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        logger.info(f"\nFound {len(elements)} elements\n")
        
        question_count = 0
        for idx, elem in enumerate(elements):
            logger.info(f"Element {idx}:")
            
            if is_section_header(elem):
                logger.info(f"  [SKIP] Section header")
                continue
            
            title = get_question_text(driver, elem)
            options = get_options(elem)
            
            if title != "Untitled Question":
                question_count += 1
                logger.info(f"  Title: {title}")
                logger.info(f"  Options: {options}")
            else:
                logger.info(f"  [NO TITLE]")
        
        logger.info(f"\n✓ Total questions: {question_count} (expected: 3)")
        input("\nPress Enter to close...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test()
