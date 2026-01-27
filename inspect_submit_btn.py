#!/usr/bin/env python3
"""Inspect the submit button structure"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

url = "https://forms.gle/KSkfKGw1jTvM2UA96"

chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--headless=new')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait for form to load
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Qr7Oae")))
    except:
        pass
    
    time.sleep(3)
    
    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    print("\n=== ALL BUTTONS ===")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Found {len(buttons)} buttons\n")
    
    for i, btn in enumerate(buttons):
        print(f"Button {i}:")
        print(f"  Text: '{btn.text}'")
        print(f"  Class: '{btn.get_attribute('class')}'")
        print(f"  ID: '{btn.get_attribute('id')}'")
        print(f"  Aria-label: '{btn.get_attribute('aria-label')}'")
        print(f"  Type: '{btn.get_attribute('type')}'")
        print(f"  Data-params: '{btn.get_attribute('data-params')}'")
        print(f"  Displayed: {btn.is_displayed()}")
        print(f"  HTML: {btn.get_attribute('outerHTML')[:200]}")
        print()
    
    print("\n=== ALL ELEMENTS WITH ROLE='BUTTON' ===")
    role_buttons = driver.find_elements(By.XPATH, "//*[@role='button']")
    print(f"Found {len(role_buttons)} elements with role='button'\n")
    
    for i, elem in enumerate(role_buttons):
        print(f"Role=button {i}:")
        print(f"  Text: '{elem.text}'")
        print(f"  Class: '{elem.get_attribute('class')}'")
        print(f"  Tag: {elem.tag_name}")
        print(f"  Displayed: {elem.is_displayed()}")
        print()
    
    print("\n=== PAGE SOURCE (last 2000 chars) ===")
    source = driver.page_source
    print(source[-2000:])

finally:
    driver.quit()
