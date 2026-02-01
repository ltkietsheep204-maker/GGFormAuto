#!/usr/bin/env python3
"""
Debug script using correct selectors from user feedback
"""

import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Form URL - try edit version first
FORM_URL = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

try:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    logger.info("Opening form...")
    driver.get(FORM_URL)
    time.sleep(5)
    
    # Scroll to load all content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    logger.info("\n" + "="*80)
    logger.info("FINDING QUESTIONS")
    logger.info("="*80 + "\n")
    
    # Check for iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    logger.info(f"Found {len(iframes)} iframes on page\n")
    
    # Try each iframe
    questions = []
    for iframe_idx, iframe in enumerate(iframes):
        logger.info(f"Trying iframe {iframe_idx}...")
        try:
            driver.switch_to.default_content()  # Reset first
            driver.switch_to.frame(iframe)
            
            # Try to find questions
            test_questions = driver.find_elements(By.XPATH, "//div[@jsname='yrriRe' and @aria-label='Câu hỏi']")
            if test_questions:
                logger.info(f"✓ Found {len(test_questions)} questions in iframe {iframe_idx}\n")
                questions = test_questions
                break
            else:
                logger.info(f"✗ No questions in iframe {iframe_idx}")
        except Exception as e:
            logger.info(f"✗ Error switching to iframe {iframe_idx}: {str(e)[:50]}")
    
    if not questions:
        # Try without switching (maybe they're in main document)
        logger.info("\nTrying main document...")
        driver.switch_to.default_content()
    
    # Find all questions using CORRECT selectors from user
    logger.info("Trying different selectors for questions...\n")
    
    # Selector 1: Using jsname and class
    questions = driver.find_elements(By.XPATH, "//div[@jsname='yrriRe' and @aria-label='Câu hỏi']")
    logger.info(f"Selector 1 (jsname): Found {len(questions)} questions")
    
    # Selector 2: Using class and role
    if not questions:
        questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'hj99tb') and @role='textbox' and @aria-label='Câu hỏi']")
        logger.info(f"Selector 2 (class+role): Found {len(questions)} questions")
    
    # Selector 3: More flexible
    if not questions:
        questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'editable') and @role='textbox' and contains(@aria-label, 'Câu')]")
        logger.info(f"Selector 3 (editable): Found {len(questions)} questions")
    
    # Find all questions using CORRECT selectors from user
    logger.info("Trying different selectors for questions...\n")
    
    # Selector 1: Using jsname and class
    questions = driver.find_elements(By.XPATH, "//div[@jsname='yrriRe' and @aria-label='Câu hỏi']")
    logger.info(f"Selector 1 (jsname): Found {len(questions)} questions")
    
    # Selector 2: Using class and role
    if not questions:
        questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'hj99tb') and @role='textbox' and @aria-label='Câu hỏi']")
        logger.info(f"Selector 2 (class+role): Found {len(questions)} questions")
    
    # Selector 3: More flexible
    if not questions:
        questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'editable') and @role='textbox' and contains(@aria-label, 'Câu')]")
        logger.info(f"Selector 3 (editable): Found {len(questions)} questions")
    
    all_questions_data = []
    
    for idx, question in enumerate(questions):
        logger.info(f"\n{'='*80}")
        logger.info(f"QUESTION {idx + 1}")
        logger.info(f"{'='*80}")
        
        # Get question text
        question_text = question.text.strip()
        logger.info(f"Text: {question_text}\n")
        
        # Find options for this question
        # Strategy: Get ALL option inputs on page, then group by proximity to questions
        try:
            # Get parent container (usually a large div containing question + options)
            parent = question.find_element(By.XPATH, "ancestor::div[contains(@class, 'Xrj4Rb') or contains(@class, 'pxj')][1]")
        except:
            try:
                # Fallback: get a few levels up
                parent = question.find_element(By.XPATH, "ancestor::div[4]")
            except:
                parent = question
        
        # Find all option inputs within parent
        options_inputs = parent.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf')]")
        
        # If still empty, try searching entire doc and pick the closest ones
        if not options_inputs:
            all_options = driver.find_elements(By.XPATH, "//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf')]")
            # Simple heuristic: take up to 4 options starting at idx*4
            if len(all_options) > idx * 4:
                options_inputs = all_options[idx*4:idx*4 + 4]
        
        logger.info(f"Found {len(options_inputs)} options:")
        
        options_list = []
        for opt_idx, opt_input in enumerate(options_inputs):
            option_value = opt_input.get_attribute('value')
            logger.info(f"  Option {opt_idx + 1}: {option_value}")
            options_list.append({
                "index": opt_idx + 1,
                "text": option_value
            })
        
        question_data = {
            "index": idx + 1,
            "text": question_text,
            "options_count": len(options_inputs),
            "options": options_list
        }
        all_questions_data.append(question_data)
    
    # Save to JSON
    output_file = '/Users/2apple_mgn_63_ram16/Desktop/Dự Án Code/GGform/form_structure_debug.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"✓ Saved {len(all_questions_data)} questions to {output_file}")
    logger.info(f"{'='*80}\n")
    
    # Print summary
    logger.info("\nSUMMARY:")
    for q in all_questions_data:
        logger.info(f"  Q{q['index']}: {q['text'][:50]}... ({q['options_count']} options)")
    
    driver.quit()
    logger.info("\n✓ Debug complete")

except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    if 'driver' in locals():
        driver.quit()
