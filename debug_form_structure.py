#!/usr/bin/env python3
"""
Debug script - Kiểm tra cấu trúc HTML của form
"""
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def debug_form(form_url):
    """Kiểm tra chi tiết cấu trúc form"""
    
    logger.info("\n" + "="*70)
    logger.info(f"🔍 DEBUG: {form_url}")
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
        
        # Check page loaded
        page_title = driver.title
        logger.info(f"✓ Page title: {page_title}")
        
        page_source = driver.page_source
        logger.info(f"✓ Page size: {len(page_source)} characters")
        
        # Check for form indicators
        logger.info("\n📋 FORM INDICATORS:")
        checks = {
            "Has 'formContent'": '"formContent"' in page_source,
            "Has 'freebird' (Google Forms)": 'freebird' in page_source,
            "Has 'g_scs'": 'g_scs' in page_source,
            "Has 'initialData'": '"initialData"' in page_source,
        }
        for check, result in checks.items():
            status = "✓" if result else "✗"
            logger.info(f"  {status} {check}")
        
        # Try finding questions with DIFFERENT selectors
        logger.info("\n🔎 SEARCHING FOR QUESTIONS:\n")
        
        selectors = [
            ("Qr7Oae (current)", By.CLASS_NAME, "Qr7Oae"),
            ("M7eMe (titles)", By.CLASS_NAME, "M7eMe"),
            ("role='listitem'", By.XPATH, "//div[@role='listitem']"),
            ("role='heading'", By.XPATH, "//div[@role='heading']"),
            ("YKDB3e (options)", By.CLASS_NAME, "YKDB3e"),
            ("[data-item-id]", By.XPATH, "//*[@data-item-id]"),
            ("jrmQee (form item)", By.CLASS_NAME, "jrmQee"),
            ("class containing 'item'", By.XPATH, "//*[contains(@class, 'item')][@role='listitem']"),
        ]
        
        for name, by, selector in selectors:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    logger.info(f"✓ {name}: Found {len(elements)} elements")
                    
                    # Show first element details
                    if len(elements) > 0:
                        first = elements[0]
                        
                        # Try to extract text
                        text = first.text[:80] if first.text else "(no text)"
                        logger.info(f"    [0] Text: {text}")
                        
                        # Show classes
                        classes = first.get_attribute('class')
                        if classes:
                            logger.info(f"    [0] Classes: {classes[:80]}")
                        
                        # Show data attributes
                        outer = first.get_attribute('outerHTML')[:200]
                        logger.info(f"    [0] HTML: {outer}...")
                else:
                    logger.info(f"✗ {name}: Found 0 elements")
            except Exception as e:
                logger.info(f"✗ {name}: Error - {str(e)[:50]}")
        
        # Try to find radio/checkbox/input directly
        logger.info("\n🎯 INPUT ELEMENTS:")
        
        input_selectors = [
            ("input[type='radio']", By.CSS_SELECTOR, "input[type='radio']"),
            ("input[type='checkbox']", By.CSS_SELECTOR, "input[type='checkbox']"),
            ("input[type='text']", By.CSS_SELECTOR, "input[type='text']"),
            ("textarea", By.TAG_NAME, "textarea"),
            ("div[@role='radio']", By.XPATH, "//div[@role='radio']"),
            ("div[@role='checkbox']", By.XPATH, "//div[@role='checkbox']"),
            ("select", By.TAG_NAME, "select"),
        ]
        
        for name, by, selector in input_selectors:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    logger.info(f"  ✓ {name}: {len(elements)}")
                else:
                    logger.info(f"  ✗ {name}: 0")
            except:
                logger.info(f"  ✗ {name}: Error")
        
        # Save HTML for inspection
        html_file = "/tmp/form_debug.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info(f"\n💾 Saved HTML to: {html_file}")
        
        # Try to extract question text with various methods
        logger.info("\n📝 QUESTION TEXT EXTRACTION:")
        
        try:
            # Method 1: Find all divs with role
            all_divs = driver.find_elements(By.XPATH, "//div[@role='listitem' or @role='heading']")
            logger.info(f"  Found {len(all_divs)} divs with role")
            
            for i, div in enumerate(all_divs[:3]):
                text = div.text[:60] if div.text else "(empty)"
                logger.info(f"    [{i}] {text}")
        except Exception as e:
            logger.info(f"  Error: {e}")
        
        logger.info("\n" + "="*70)
        logger.info("✅ Debug complete!")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    form_url = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"
    
    if len(sys.argv) > 1:
        form_url = sys.argv[1]
    
    debug_form(form_url)
