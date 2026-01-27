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
time.sleep(3)

# Test the selector
elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Found {len(elements)} elements with class Qr7Oae\n')

for idx, elem in enumerate(elements):
    print(f'=== Q{idx+1} ===')
    
    # Try different selectors
    try:
        title_uc = elem.find_element(By.CLASS_NAME, 'Uc2Deb').text
        print(f'Uc2Deb: {title_uc}')
    except Exception as e:
        print(f'Uc2Deb: Not found')
    
    try:
        divs = elem.find_elements(By.XPATH, './/div[@role="heading"]')
        for div in divs:
            if div.text:
                print(f'heading role: {div.text[:60]}')
    except:
        pass
    
    try:
        spans = elem.find_elements(By.TAG_NAME, 'span')
        longest = ''
        for span in spans:
            text = span.text.strip()
            if len(text) > len(longest) and len(text) < 200:
                longest = text
        if longest:
            print(f'longest span: {longest[:60]}')
    except:
        pass
    
    # Check type
    try:
        radios = elem.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        if radios:
            print(f'Type: multiple_choice (found {len(radios)} radios)')
    except:
        pass
    
    try:
        text_inputs = elem.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
        if text_inputs:
            print(f'Type: short_answer (found {len(text_inputs)} inputs)')
    except:
        pass
    
    print()

driver.quit()
