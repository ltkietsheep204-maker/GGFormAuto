"""
Debug script để xem HTML structure của Google Form
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Form URL từ user
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeUWWmxtyzzz3CIa2uqhDjxCyZFixr28sZBISd28IHTPxVYHA/formResponse"

# Auto-convert to viewform
if "/formResponse" in form_url:
    form_url = form_url.replace("/formResponse", "/viewform")
    print(f"✓ Converted to viewform URL: {form_url}")


# Chuẩn bị driver
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
driver.get(form_url)
time.sleep(3)

print("=" * 80)
print("PAGE TITLE:", driver.title)
print("=" * 80)

# Check if it's a form response page
page_source = driver.page_source

if "formResponse" in form_url or "Your response has been recorded" in page_source:
    print("⚠️  This looks like a RESPONSE submission page, not the form itself!")
    print("\nTrying to extract form URL from page...")
    
    # Try to find the actual form view link
    try:
        # Look for edit link or view link
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            text = link.text
            print(f"Found link: {text} -> {href}")
    except:
        pass

print("\n" + "=" * 80)
print("SEARCHING FOR FORM ELEMENTS...")
print("=" * 80)

# Search for various form elements
searches = {
    "divs with role='listitem'": ("//div[@role='listitem']", "xpath"),
    "class 'Qr7Oae'": ("Qr7Oae", "class"),
    "class 'MocG8c'": ("MocG8c", "class"),
    "divs with data-params": ("//div[@data-params]", "xpath"),
    "input[type='radio']": ("input[type='radio']", "css"),
    "input[type='checkbox']": ("input[type='checkbox']", "css"),
    "input[type='text']": ("input[type='text']", "css"),
    "textarea": ("textarea", "tag"),
}

for desc, (selector, method) in searches.items():
    try:
        if method == "class":
            elements = driver.find_elements(By.CLASS_NAME, selector)
        elif method == "xpath":
            elements = driver.find_elements(By.XPATH, selector)
        elif method == "css":
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        elif method == "tag":
            elements = driver.find_elements(By.TAG_NAME, selector)
        
        print(f"\n✓ {desc}: Found {len(elements)} elements")
        
        # Print first 3 elements
        for idx, elem in enumerate(elements[:3]):
            try:
                text = elem.text[:80] if elem.text else "(no text)"
                tag = elem.tag_name
                classes = elem.get_attribute("class")
                print(f"  [{idx}] <{tag} class='{classes}'> {text}")
            except:
                print(f"  [{idx}] (unable to read)")
    
    except Exception as e:
        print(f"\n✗ {desc}: Error - {e}")

print("\n" + "=" * 80)
print("HTML SNIPPET (first 2000 chars):")
print("=" * 80)
print(driver.page_source[:2000])

driver.quit()
print("\n✓ Debug complete")
