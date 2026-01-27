from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

form_url = 'https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi'

# Mở Chrome UI để debug
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Dùng headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)

try:
    driver.get(form_url)
    print("✓ Form page accessed")
    
    # Wait for form to load
    print("Waiting for form to load...")
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CLASS_NAME, 'Qr7Oae')) > 0
    )
    print("✓ Form loaded successfully")

# Test các selectors
print("\n" + "="*60)
print("TEST SELECTORS")
print("="*60)

# Test 1: Qr7Oae
elements = driver.find_elements(By.CLASS_NAME, 'Qr7Oae')
print(f'\n1. class="Qr7Oae": Found {len(elements)} elements')

if len(elements) > 0:
    print("\n" + "="*60)
    print("QUESTION EXTRACTION TEST")
    print("="*60)
    
    for idx, elem in enumerate(elements):
        print(f'\n=== QUESTION {idx+1} ===')
        
        # Method 1: role="heading" + M7eMe
        try:
            heading = elem.find_element(By.XPATH, ".//div[@role='heading']")
            print(f'Found heading role: YES')
            
            # Cách 1a: Tìm span với class M7eMe
            try:
                span = heading.find_element(By.CLASS_NAME, "M7eMe")
                text = span.text.strip()
                print(f'  → span.M7eMe: "{text}"')
            except:
                print(f'  → span.M7eMe: NOT FOUND')
            
            # Cách 1b: Tất cả spans trong heading
            spans = heading.find_elements(By.TAG_NAME, "span")
            print(f'  → Total spans in heading: {len(spans)}')
            for sp_idx, sp in enumerate(spans):
                text = sp.text.strip()
                classes = sp.get_attribute('class')
                if text:
                    print(f'     Span {sp_idx}: "{text[:50]}" (class: {classes})')
        except Exception as e:
            print(f'role="heading": NOT FOUND - {e}')
        
        # Method 2: Uc2Deb class
        try:
            title = elem.find_element(By.CLASS_NAME, "Uc2Deb")
            print(f'Found Uc2Deb class: "{title.text.strip()}"')
        except:
            print(f'Uc2Deb class: NOT FOUND')
        
        # Method 3: Tất cả spans
        spans = elem.find_elements(By.TAG_NAME, "span")
        print(f'Total spans in question: {len(spans)}')
        
        longest = ''
        for sp in spans:
            text = sp.text.strip()
            if text and len(text) > len(longest) and len(text) < 200:
                if '*' not in text and 'Câu hỏi' not in text:
                    longest = text
        if longest:
            print(f'Longest span text: "{longest}"')
        
        # Check question type
        print(f'\nQuestion type:')
        radios = elem.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        if radios:
            print(f'  → Multiple choice: {len(radios)} radios')
        
        checkboxes = elem.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        if checkboxes:
            print(f'  → Checkbox: {len(checkboxes)} checkboxes')
        
        textareas = elem.find_elements(By.TAG_NAME, "textarea")
        if textareas:
            print(f'  → Long answer: {len(textareas)} textareas')
        
        text_inputs = elem.find_elements(By.CSS_SELECTOR, "input[type='text']")
        if text_inputs:
            print(f'  → Short answer: {len(text_inputs)} text inputs')

print("\n" + "="*60)
print("DONE! Closing browser...")
print("="*60)
time.sleep(2)
driver.quit()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    driver.quit()
