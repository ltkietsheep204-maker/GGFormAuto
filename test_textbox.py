from selenium import webdriver
from selenium.webdriver.common.by import By
import time

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

driver = webdriver.Chrome(options=options)

try:
    print("Loading form...")
    driver.get(form_url)
    time.sleep(3)
    
    # Find questions
    elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
    print(f"Found {len(elements)} elements\n")
    
    if len(elements) > 0:
        for idx, elem in enumerate(elements):
            print(f"=== Element {idx+1} ===")
            
            # Test textbox selector
            try:
                textbox = elem.find_element(By.XPATH, ".//div[@role='textbox' and @aria-label='Câu hỏi']")
                title = textbox.text.strip().replace('\xa0', ' ')
                print(f"Title (textbox): '{title}'")
            except:
                print(f"Title (textbox): NOT FOUND")
            
            # Check type
            radios = len(elem.find_elements(By.XPATH, ".//div[@role='radio']"))
            checks = len(elem.find_elements(By.XPATH, ".//div[@role='checkbox']"))
            
            if radios > 0:
                print(f"Type: multiple_choice ({radios} radios)")
            elif checks > 0:
                print(f"Type: checkbox ({checks} checks)")
            else:
                print(f"Type: unknown")
            
            print()

finally:
    driver.quit()
    print("Done!")
