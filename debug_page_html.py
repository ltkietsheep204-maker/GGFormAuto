#!/usr/bin/env python3
"""
Debug: Print page HTML to see actual structure
"""

import time
from selenium import webdriver
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
    time.sleep(8)
    
    # Get all elements with aria-label="Câu hỏi"
    page_html = driver.page_source
    
    # Count occurrences
    count = page_html.count('aria-label="Câu hỏi"')
    logger.info(f"\nFound {count} occurrences of aria-label=\"Câu hỏi\" in page HTML")
    
    # Extract snippets
    import re
    pattern = r'<[^>]*aria-label="Câu hỏi"[^>]*>'
    matches = re.findall(pattern, page_html)
    
    logger.info(f"\nFound {len(matches)} matching elements:")
    for idx, match in enumerate(matches[:10]):  # Show first 10
        logger.info(f"\n{idx+1}. {match[:150]}...")
    
    driver.quit()

except Exception as e:
    logger.error(f"Error: {e}")
    if 'driver' in locals():
        driver.quit()
