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
    
    # Just wait a bit for page to load
    time.sleep(3)
    
    # Find questions
    elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
    print(f"Found {len(elements)} question elements")
    
    if len(elements) > 0:
        # Get HTML of first element (save to file)
        html = elements[0].get_attribute('outerHTML')
        with open('/tmp/question1.html', 'w') as f:
            f.write(html)
        print("Saved first question HTML to /tmp/question1.html")
        
        # Also extract text programmatically
        for idx, elem in enumerate(elements):
            print(f"\nQ{idx+1}:")
            
            # Try heading role
            try:
                heading = elem.find_element(By.XPATH, ".//div[@role='heading']")
                # Get text from first span that's not empty
                spans = heading.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    text = span.text.strip()
                    if text and text != "*":
                        print(f"  Title: {text}")
                        break
            except:
                print(f"  Title: NOT FOUND")
            
            # Check inputs - using role="radio" and role="checkbox" instead of input types
            radios = len(elem.find_elements(By.XPATH, ".//div[@role='radio']"))
            checks = len(elem.find_elements(By.XPATH, ".//div[@role='checkbox']"))
            texts = len(elem.find_elements(By.CSS_SELECTOR, "input[type='text']"))
            textareas = len(elem.find_elements(By.TAG_NAME, "textarea"))
            
            print(f"  Inputs: {radios} radios (role), {checks} checks (role), {texts} texts, {textareas} textareas")

finally:
    driver.quit()
    print("\nDone!")
