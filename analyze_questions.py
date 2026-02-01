#!/usr/bin/env python3
"""
Debug chi tiết - Phân tích từng data-item-id element
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def analyze_questions(form_url):
    """Phân tích chi tiết cấu trúc câu hỏi"""
    
    logger.info("\n" + "="*70)
    logger.info(f"🔍 DETAILED QUESTION ANALYSIS")
    logger.info("="*70 + "\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        logger.info("⏳ Loading form...")
        driver.get(form_url)
        time.sleep(5)
        
        # Find all data-item-id elements
        elements = driver.find_elements(By.XPATH, "//*[@data-item-id]")
        logger.info(f"✓ Found {len(elements)} elements with data-item-id\n")
        
        for idx, elem in enumerate(elements):
            logger.info(f"\n{'='*70}")
            logger.info(f"ELEMENT {idx}")
            logger.info(f"{'='*70}")
            
            # Get data-item-id
            item_id = elem.get_attribute('data-item-id')
            logger.info(f"data-item-id: {item_id}")
            
            # Check for M7eMe (title)
            spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
            logger.info(f"M7eMe spans: {len(spans)}")
            if spans:
                for i, span in enumerate(spans):
                    text = span.get_attribute('innerText') or span.get_attribute('textContent') or ""
                    text = text.strip()
                    logger.info(f"  [{i}] '{text}'")
            
            # Check for radio buttons
            radios = elem.find_elements(By.XPATH, ".//div[@role='radio']")
            logger.info(f"Radio buttons: {len(radios)}")
            if radios:
                for i, radio in enumerate(radios[:3]):  # Show first 3
                    aria = radio.get_attribute('aria-label') or ""
                    logger.info(f"  [{i}] {aria}")
            
            # Check for checkboxes
            checkboxes = elem.find_elements(By.XPATH, ".//div[@role='checkbox']")
            logger.info(f"Checkboxes: {len(checkboxes)}")
            
            # Check for text input
            text_inputs = elem.find_elements(By.CSS_SELECTOR, "input[type='text']")
            logger.info(f"Text inputs: {len(text_inputs)}")
            
            # Check for textarea
            textareas = elem.find_elements(By.TAG_NAME, "textarea")
            logger.info(f"Textareas: {len(textareas)}")
            
            # Summary: is this a question?
            has_title = len(spans) > 0
            has_options = len(radios) > 0 or len(checkboxes) > 0
            has_input = len(text_inputs) > 0 or len(textareas) > 0
            
            is_question = (has_title and (has_options or has_input))
            
            logger.info(f"\n→ Has title: {has_title}")
            logger.info(f"→ Has options (radio/checkbox): {has_options}")
            logger.info(f"→ Has input (text/textarea): {has_input}")
            logger.info(f"→ IS QUESTION: {'✅ YES' if is_question else '❌ NO'}")
        
        logger.info("\n" + "="*70)
        logger.info("📊 SUMMARY")
        logger.info("="*70)
        
        # Count actual questions
        actual_questions = 0
        for elem in elements:
            spans = elem.find_elements(By.CLASS_NAME, "M7eMe")
            radios = elem.find_elements(By.XPATH, ".//div[@role='radio']")
            checkboxes = elem.find_elements(By.XPATH, ".//div[@role='checkbox']")
            text_inputs = elem.find_elements(By.CSS_SELECTOR, "input[type='text']")
            textareas = elem.find_elements(By.TAG_NAME, "textarea")
            
            has_title = len(spans) > 0
            has_options = len(radios) > 0 or len(checkboxes) > 0
            has_input = len(text_inputs) > 0 or len(textareas) > 0
            
            if has_title and (has_options or has_input):
                actual_questions += 1
        
        logger.info(f"✓ Actual questions: {actual_questions}")
        logger.info(f"Expected: 4 questions")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    form_url = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"
    analyze_questions(form_url)
