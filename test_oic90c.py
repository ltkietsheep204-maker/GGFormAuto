#!/usr/bin/env python3
"""Debug - Check span.OIC90c attributes"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

form_url = "https://docs.google.com/forms/d/1aysm61PsdT-m0hLwYHaO0rD4SR0dnLV-xCca5B_FeTo/edit?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(form_url)
time.sleep(5)

elements = driver.find_elements(By.XPATH, "//*[@data-item-id and @data-item-id != '-1']")
first_q = elements[0]

print("\n" + "="*70)
print("SPAN.OIC90c ATTRIBUTES")
print("="*70 + "\n")

oic_spans = first_q.find_elements(By.CLASS_NAME, "OIC90c")
print(f"Found {len(oic_spans)} spans\n")

for i, span in enumerate(oic_spans):
    print(f"Span {i}:")
    print(f"  text: '{span.text}'")
    print(f"  aria-label: '{span.get_attribute('aria-label')}'")
    print(f"  innerHTML: {span.get_attribute('innerHTML')[:100]}")
    
    # Try getting text via JS
    inner_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", span)
    print(f"  JS innerText: '{inner_text}'")
    print()

driver.quit()
