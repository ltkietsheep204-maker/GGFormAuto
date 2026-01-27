from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re

form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeUWWmxtyzzz3CIa2uqhDjxCyZFixr28sZBISd28IHTPxVYHA/viewform"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
driver.get(form_url)
time.sleep(4)

page_source = driver.page_source

# Check for various indicators
checks = {
    "Form has 'No longer accepting responses'": "No longer accepting responses" in page_source or "không còn tiếp nhận" in page_source,
    "Form has 'closed'": "closed" in page_source.lower(),
    "Form has script data": '"formContent"' in page_source or '"initialData"' in page_source,
    "Page has hidden form data": 'data-initial-data' in page_source or 'g_scs' in page_source,
    "Page has 'freebird' (Google Forms)": 'freebird' in page_source,
}

for check, result in checks.items():
    status = "✓" if result else "✗"
    print(f"{status} {check}: {result}")

# Try to find form ID and data
form_id_match = re.search(r'/forms/d/e/([^/]+)', form_url)
if form_id_match:
    print(f"\n✓ Form ID: {form_id_match.group(1)}")

# Check page length
print(f"\n✓ Page source length: {len(page_source)} characters")

# Look for any text that might indicate questions
if "câu hỏi" in page_source.lower() or "question" in page_source.lower():
    print("✓ Found 'question' or 'câu hỏi' text in page")

driver.quit()
