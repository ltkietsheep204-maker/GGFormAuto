#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # Open form
    print("Loading form...")
    driver.get("https://docs.google.com/forms/d/e/1FAIpQLSfVvKZ_tZvOxVpTrH6fEqnVf1h2YpWNk7o5F-oXCfxHpE7Qpw/viewform")
    print("Waiting for OIC90c spans...")
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "OIC90c")))
    print("Page loaded!")
    
    # Get question elements
    questions = driver.find_elements(By.XPATH, "//*[@data-item-id and @data-item-id != '-1']")
    print(f"\n✓ Found {len(questions)} questions\n")
    
    for q_idx, q in enumerate(questions[:2]):  # Test first 2 questions
        title_span = q.find_element(By.CLASS_NAME, "M7eMe")
        title = title_span.text.strip()
        print(f"Q{q_idx}: {title}")
        
        # Get options
        radios = q.find_elements(By.XPATH, ".//div[@role='radio']")
        print(f"  Radio buttons: {len(radios)}")
        
        oic_spans = q.find_elements(By.CLASS_NAME, "OIC90c")
        print(f"  OIC90c spans: {len(oic_spans)}")
        
        option_texts = []
        for i, span in enumerate(oic_spans):
            try:
                text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", span)
                text = text.strip() if text else ""
                
                if (text and 
                    not any(x in text.lower() for x in ['mô tả', 'chú thích', 'mục khác', 'bắt buộc', 'required']) and
                    len(text) > 0):
                    option_texts.append(text)
                    print(f"    [{i}] OPTION: '{text}'")
                else:
                    print(f"    [{i}] SKIP: '{text[:40] if text else '(empty)'}...'")
            except Exception as e:
                print(f"    [{i}] ERROR: {e}")
        
        print(f"  ✓ Extracted {len(option_texts[:len(radios)])} options\n")

finally:
    driver.quit()
