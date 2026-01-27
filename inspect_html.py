from selenium import webdriver
from selenium.webdriver.common.by import By
import time

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)
driver.get(form_url)
time.sleep(5)

# Get first question element
elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Found {len(elements)} questions\n')

if len(elements) > 0:
    elem = elements[0]
    # Print HTML of first element
    print("=== First Question HTML ===")
    html = elem.get_attribute('outerHTML')
    # Print first 2000 chars
    print(html[:2000])

driver.quit()
