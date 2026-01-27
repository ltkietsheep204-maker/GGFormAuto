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

elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'Found {len(elements)} questions\n')

for idx, elem in enumerate(elements):
    print(f'=== Q{idx+1} ===')
    
    # Get title
    try:
        heading = elem.find_element(By.XPATH, ".//div[@role='heading']")
        spans = heading.find_elements(By.TAG_NAME, "span")
        title = ""
        for span in spans:
            text = span.text.strip()
            if text and text != "*":
                title = text
                break
        print(f'Title: {title}')
    except:
        print('Title: Could not find')
    
    # Check types
    radios = elem.find_elements(By.CSS_SELECTOR, "input[type='radio']")
    checkboxes = elem.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    textareas = elem.find_elements(By.TAG_NAME, "textarea")
    text_inputs = elem.find_elements(By.CSS_SELECTOR, "input[type='text']")
    
    if radios:
        print(f'Type: multiple_choice ({len(radios)} radios)')
    elif checkboxes:
        print(f'Type: checkbox ({len(checkboxes)} checkboxes)')
    elif textareas:
        print(f'Type: long_answer ({len(textareas)} textareas)')
    elif text_inputs:
        print(f'Type: short_answer ({len(text_inputs)} text inputs)')
    else:
        print('Type: unknown')
    
    print()

driver.quit()
