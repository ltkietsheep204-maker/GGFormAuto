#!/usr/bin/env python3
"""Test selector debugging"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Form URL
FORM_URL = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi"

def test_selectors():
    """Test different selector strategies"""
    # Chrome options - NO HEADLESS
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        # Open form
        logger.info(f"Opening form: {FORM_URL}")
        driver.get(FORM_URL)
        
        # Wait for page to load
        time.sleep(8)
        
        # Find all Qr7Oae elements
        question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        logger.info(f"Found {len(question_elements)} Qr7Oae elements")
        
        # Test each element
        for idx, qe in enumerate(question_elements):
            logger.info(f"\n{'='*60}")
            logger.info(f"ELEMENT {idx}")
            logger.info(f"{'='*60}")
            
            try:
                # Test Strategy 1: contenteditable textboxes
                logger.info("Strategy 1: contenteditable textboxes")
                textboxes = qe.find_elements(By.XPATH, ".//div[@role='textbox'][@contenteditable='true']")
                logger.info(f"  Found {len(textboxes)} contenteditable textboxes")
                for tb_idx, tb in enumerate(textboxes):
                    aria_label = tb.get_attribute('aria-label')
                    text = tb.text.strip().replace('\xa0', ' ')
                    logger.info(f"    TB {tb_idx}: aria-label='{aria_label}', text='{text}'")
            except Exception as e:
                logger.error(f"  Strategy 1 failed: {e}")
            
            try:
                # Test Strategy 2: any role='textbox'
                logger.info("Strategy 2: any role='textbox'")
                textboxes = qe.find_elements(By.XPATH, ".//div[@role='textbox']")
                logger.info(f"  Found {len(textboxes)} textboxes")
                for tb_idx, tb in enumerate(textboxes):
                    aria_label = tb.get_attribute('aria-label')
                    text = tb.text.strip().replace('\xa0', ' ')
                    logger.info(f"    TB {tb_idx}: aria-label='{aria_label}', text='{text}'")
            except Exception as e:
                logger.error(f"  Strategy 2 failed: {e}")
            
            try:
                # Test Strategy 3: hj99tb class
                logger.info("Strategy 3: hj99tb class")
                textboxes = qe.find_elements(By.XPATH, ".//div[contains(@class, 'hj99tb')]")
                logger.info(f"  Found {len(textboxes)} hj99tb divs")
                for tb_idx, tb in enumerate(textboxes):
                    text = tb.text.strip().replace('\xa0', ' ')
                    logger.info(f"    TB {tb_idx}: text='{text}'")
            except Exception as e:
                logger.error(f"  Strategy 3 failed: {e}")
            
            try:
                # Test Strategy 4: M7eMe spans
                logger.info("Strategy 4: M7eMe spans")
                spans = qe.find_elements(By.CLASS_NAME, "M7eMe")
                logger.info(f"  Found {len(spans)} M7eMe spans")
                for sp_idx, sp in enumerate(spans):
                    text = sp.text.strip().replace('\xa0', ' ')
                    logger.info(f"    SP {sp_idx}: text='{text}'")
            except Exception as e:
                logger.error(f"  Strategy 4 failed: {e}")
            
            try:
                # Test Strategy 5: Any textbox role element
                logger.info("Strategy 5: Get all text from element")
                all_text = qe.text.strip().replace('\xa0', ' ')
                logger.info(f"  Full element text: '{all_text}'")
            except Exception as e:
                logger.error(f"  Strategy 5 failed: {e}")
    
    finally:
        # Keep window open for inspection
        logger.info("\n✓ Test complete - Chrome window still open")
        input("Press Enter to close...")
        driver.quit()

if __name__ == "__main__":
    test_selectors()
