#!/usr/bin/env python3
"""Quick test to inspect Google Form HTML"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

print("Starting browser...")
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://forms.gle/KSkfKGw1jTvM2UA96"
print(f"Loading: {url}")
driver.get(url)

print("Waiting for page to load...")
time.sleep(5)

print("\nLooking for questions...")
questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
print(f"Found {len(questions)} questions\n")

for q_idx, q in enumerate(questions):
    print(f"Question {q_idx + 1}:")
    
    # Print the HTML of the question to see structure
    try:
        html = q.get_attribute('innerHTML')
        print(f"  HTML length: {len(html)} chars")
        print(f"  First 500 chars:")
        print(f"    {html[:500]}")
    except:
        pass
    
    # Title
    try:
        title = q.find_element(By.CLASS_NAME, "Uc2Deb").text
        print(f"  Title: {title}")
    except:
        print("  Title: Not found")
        # Try alternative selectors
        try:
            titles = q.find_elements(By.TAG_NAME, "div")
            print(f"    Found {len(titles)} divs, checking for text...")
            for t_idx, t in enumerate(titles[:5]):
                text = t.text.strip()
                if text and len(text) > 0 and len(text) < 200:
                    print(f"    Div {t_idx}: {text}")
        except:
            pass
    
    # Options via YKDB3e
    options_found = q.find_elements(By.CLASS_NAME, "YKDB3e")
    print(f"  Options (YKDB3e method): {len(options_found)}")
    
    # Check for other potential option containers
    all_divs = q.find_elements(By.TAG_NAME, "div")
    print(f"  Total divs: {len(all_divs)}")
    
    # Check for radio buttons
    radios = q.find_elements(By.CSS_SELECTOR, "input[type='radio']")
    print(f"  Radio buttons: {len(radios)}")
    
    # Check for spans
    spans = q.find_elements(By.TAG_NAME, "span")
    print(f"  Spans: {len(spans)}")
    print(f"    First 10 spans:")
    for s_idx, s in enumerate(spans[:10]):
        text = s.text.strip()
        if text:
            print(f"      [{s_idx}] {text}")
    
    print()

driver.quit()
print("Done")
