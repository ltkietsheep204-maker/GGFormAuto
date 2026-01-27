from selenium import webdriver
from selenium.webdriver.common.by import By
import time

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')

driver = webdriver.Chrome(options=options)
driver.get(form_url)
time.sleep(5)

# Try different selectors
print("Testing selectors...")
print()

# Test 1: Qr7Oae
elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Qr7Oae class: {len(elements)} elements')

# Test 2: role=listitem
elements = driver.find_elements(By.XPATH, "//div[@role='listitem']")
print(f'role=listitem: {len(elements)} elements')

# Test 3: OxAavc class
elements = driver.find_elements(By.CLASS_NAME, 'OxAavc')
print(f'OxAavc class: {len(elements)} elements')

# Test 4: cTDvob class  
elements = driver.find_elements(By.CLASS_NAME, 'cTDvob')
print(f'cTDvob class: {len(elements)} elements')

# Test 5: LygNqb
elements = driver.find_elements(By.CLASS_NAME, 'LygNqb')
print(f'LygNqb class: {len(elements)} elements')

# Test 6: pYfr3c
elements = driver.find_elements(By.CLASS_NAME, 'pYfr3c')
print(f'pYfr3c class: {len(elements)} elements')

driver.quit()
