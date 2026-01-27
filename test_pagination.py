#!/usr/bin/env python3
"""
Test script để xác minh logic chuyển trang (Tiếp)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json

form_url = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/viewform?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(form_url)
time.sleep(6)

pages_data = []

page_num = 1
while True:
    print(f"\n{'='*60}")
    print(f"PAGE {page_num}")
    print(f"{'='*60}\n")
    
    # Get questions on current page
    questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
    print(f"Questions on page {page_num}: {len(questions)}")
    
    page_items = []
    for idx, q in enumerate(questions):
        spans = q.find_elements(By.CLASS_NAME, "M7eMe")
        title = ""
        for s in spans:
            text = s.get_attribute('innerText') or s.get_attribute('textContent')
            if text:
                title = text.strip()
                break
        
        print(f"  {idx + 1}. {title}")
        page_items.append(title)
    
    pages_data.append({
        "page": page_num,
        "questions": page_items
    })
    
    # Check for submit button
    submit_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Gửi')]")
    if submit_buttons:
        print(f"\n✓ Found submit button - form complete!")
        break
    
    # Find and click "Tiếp" (Next) button
    print(f"\n🔍 Looking for 'Tiếp' button...")
    next_buttons = driver.find_elements(By.XPATH, "//button//span[contains(text(), 'Tiếp')]")
    
    if next_buttons:
        print(f"✓ Found {len(next_buttons)} 'Tiếp' button(s)")
        
        for idx, btn in enumerate(next_buttons):
            try:
                if btn.is_displayed():
                    print(f"  Button {idx + 1}: Visible - clicking...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.5)
                    
                    # Get current question count
                    current_count = len(driver.find_elements(By.CLASS_NAME, "Qr7Oae"))
                    
                    btn.click()
                    print(f"  ✓ Clicked!")
                    time.sleep(3)  # Wait for page transition
                    
                    # Get new question count
                    new_count = len(driver.find_elements(By.CLASS_NAME, "Qr7Oae"))
                    print(f"  Previous: {current_count} questions, New: {new_count} questions")
                    
                    page_num += 1
                    break
                else:
                    print(f"  Button {idx + 1}: Not visible - skipping")
            except Exception as e:
                print(f"  Button {idx + 1}: Error - {e}")
    else:
        print(f"❌ No 'Tiếp' button found - cannot proceed")
        break

# Print summary
print(f"\n{'='*60}")
print(f"FORM STRUCTURE SUMMARY")
print(f"{'='*60}\n")

for page in pages_data:
    print(f"📄 Page {page['page']}:")
    for item in page['questions']:
        icon = "📌" if ("Phần" in item or "Mục" in item) else "📋"
        print(f"  {icon} {item}")
    print()

# Save to JSON
with open("/Users/2apple_mgn_63_ram16/Desktop/GGform/test_pagination_result.json", "w", encoding="utf-8") as f:
    json.dump(pages_data, f, indent=2, ensure_ascii=False)
print("✓ Saved to test_pagination_result.json")

driver.quit()
print("\n✓ Done!")
