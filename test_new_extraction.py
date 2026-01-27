#!/usr/bin/env python3
"""Test the new options extraction logic"""

import logging
import sys
from pathlib import Path

# Set up logging like the app does
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the worker class
sys.path.insert(0, str(Path(__file__).parent))
from gui_app_v3 import GoogleFormWorker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("Testing new options extraction...\n")

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://forms.gle/KSkfKGw1jTvM2UA96"
print(f"Loading form: {url}\n")
driver.get(url)

# Wait for form to load
try:
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Qr7Oae")))
except:
    pass

time.sleep(3)

# Get questions
questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
print(f"Found {len(questions)} questions\n")

# Create a mock worker to test the extraction methods
worker = GoogleFormWorker("https://forms.gle/KSkfKGw1jTvM2UA96")

for q_idx, question in enumerate(questions):
    print(f"Question {q_idx + 1}:")
    
    # Test _get_question_text
    text = worker._get_question_text(question)
    print(f"  Title: {text}")
    
    # Test _get_options_complete
    options = worker._get_options_complete(question)
    print(f"  Options: {len(options)} found")
    for opt in options:
        print(f"    - {opt['text']}")
    
    print()

driver.quit()
print("Done!")
