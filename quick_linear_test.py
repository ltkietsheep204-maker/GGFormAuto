#!/usr/bin/env python3
"""Quick test script for linear scale analysis"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')
options.add_argument('--disable-gpu')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Analyze viewform
url = 'https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform'
driver.get(url)
time.sleep(8)

print('='*60)
print('VIEWFORM ANALYSIS - LINEAR SCALE')
print('='*60)

# Find all questions
questions = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Found {len(questions)} questions')

for i, q in enumerate(questions):
    print(f'\n--- Question {i+1} ---')
    
    # Get title
    try:
        title = q.find_element(By.CLASS_NAME, 'M7eMe').text
        print(f'Title: {title[:60]}...')
    except:
        print('Title: (not found)')
    
    # Check for radiogroup
    radiogroups = q.find_elements(By.XPATH, './/div[@role="radiogroup"]')
    if radiogroups:
        radios = radiogroups[0].find_elements(By.XPATH, './/div[@role="radio"]')
        print(f'Radiogroup with {len(radios)} radios')
        
        if radios:
            for j, radio in enumerate(radios):
                aria = radio.get_attribute('aria-label') or ''
                dval = radio.get_attribute('data-value') or ''
                print(f'  Radio {j}: aria-label="{aria}", data-value="{dval}"')
        
        first_aria = radios[0].get_attribute('aria-label') or '' if radios else ''
        if first_aria.isdigit():
            print('  >>> THIS IS A LINEAR SCALE!')
            
            scale_labels = q.find_elements(By.CLASS_NAME, 'Xb9hP')
            print(f'  Scale labels (Xb9hP): {len(scale_labels)}')
            for lbl in scale_labels:
                print(f'    - "{lbl.text}"')

driver.quit()
print('\n✅ Done!')
