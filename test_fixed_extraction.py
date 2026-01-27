#!/usr/bin/env python3
"""Quick test of fixed extraction"""
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
    """Lấy text câu hỏi"""
    try:
        # Strategy 1: Try M7eMe span (works for editor links)
        try:
            spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
            if spans:
                for span in spans:
                    # Use get_attribute('innerText') for editor links
                    text = span.get_attribute('innerText') or span.get_attribute('textContent')
                    if text:
                        text = text.strip().replace('\xa0', ' ').strip()
                        # Skip section headers
                        if "Mục không có tiêu đề" not in text and text:
                            logger.info(f"  ✓ Got title: {text}")
                            return text
        except Exception as e:
            logger.info(f"  Strategy 1 failed: {e}")
        
        logger.info(f"  ✗ Failed to extract text")
        return "Untitled Question"
    except Exception as e:
        logger.error(f"  Exception: {e}")
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
                    logger.info(f"  ✓ Section header: {text}")
                    return True
    except:
        pass
    return False

def test_extraction():
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
                continue
            
            title = get_question_text(driver, elem)
            if title != "Untitled Question":
                question_count += 1
            else:
                logger.info(f"  ✗ No title")
        
        logger.info(f"\n✓ Total questions: {question_count} (expected: 3)")
        input("\nPress Enter to close...")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_extraction()
