#!/usr/bin/env python3
"""Debug viewform structure"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

print('=== DEBUG VIEWFORM STRUCTURE ===')

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Viewform URL
url = 'https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform'
print(f'Loading: {url}')
driver.get(url)
time.sleep(5)

# Find questions using different methods
print('\n=== METHOD 1: Qr7Oae ===')
q1 = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Found {len(q1)} elements')
for i, q in enumerate(q1[:10]):
    try:
        # Try to get title
        title_elem = q.find_elements(By.CLASS_NAME, 'M7eMe')
        title = title_elem[0].text if title_elem else 'NO TITLE'
        print(f'  [{i}] {title[:80]}')
    except Exception as e:
        print(f'  [{i}] Error: {e}')

print('\n=== METHOD 2: M7eMe (question titles) ===')
q2 = driver.find_elements(By.CLASS_NAME, 'M7eMe')
print(f'Found {len(q2)} title elements')
for i, q in enumerate(q2[:10]):
    print(f'  [{i}] {q.text[:80]}')

print('\n=== METHOD 3: data-item-id ===')
q3 = driver.find_elements(By.XPATH, '//*[@data-item-id]')
print(f'Found {len(q3)} elements with data-item-id')
for i, q in enumerate(q3[:10]):
    try:
        title_elem = q.find_elements(By.CLASS_NAME, 'M7eMe')
        title = title_elem[0].text if title_elem else 'NO TITLE'
        print(f'  [{i}] {title[:80]}')
    except:
        print(f'  [{i}] No title')

driver.quit()
print('\nDone!')
