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
    print(f"Found {len(elements)} question elements\n")
    
    if len(elements) > 0:
        # Get HTML of all elements
        for idx, elem in enumerate(elements):
            html = elem.get_attribute('outerHTML')
            filepath = f'/tmp/question{idx+1}.html'
            with open(filepath, 'w') as f:
                f.write(html)
            
            # Also extract info
            print(f"Q{idx+1}:")
            
            # Title
            try:
                heading = elem.find_element(By.XPATH, ".//div[@role='heading']")
                spans = heading.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    text = span.text.strip()
                    if text and text != "*":
                        print(f"  Title: '{text}'")
                        break
            except Exception as e:
                print(f"  Title: ERROR - {str(e)[:50]}")
            
            # Types
            radios = len(elem.find_elements(By.XPATH, ".//div[@role='radio']"))
            checks = len(elem.find_elements(By.XPATH, ".//div[@role='checkbox']"))
            texts = len(elem.find_elements(By.CSS_SELECTOR, "input[type='text']"))
            textareas = len(elem.find_elements(By.TAG_NAME, "textarea"))
            
            type_str = ""
            if radios > 0:
                type_str = f"multiple_choice ({radios})"
            elif checks > 0:
                type_str = f"checkbox ({checks})"
            elif texts > 0:
                type_str = f"short_answer ({texts})"
            elif textareas > 0:
                type_str = f"long_answer ({textareas})"
            else:
                type_str = "unknown"
            
            print(f"  Type: {type_str}")
            print()

finally:
    driver.quit()
    print("Done!")
