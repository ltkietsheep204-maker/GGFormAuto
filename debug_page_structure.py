"""
Debug script để phân tích cấu trúc trang form
Tìm tiêu đề trang, câu hỏi, options
"""
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

form_url = "https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/viewform?hl=vi"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(form_url)
time.sleep(6)

# ========== TÌM TIÊU ĐỀ TRANG ==========
print("\n" + "="*60)
print("TÌONG TIÊU ĐỀ TRANG (Phần 1 / 2)")
print("="*60)

# Tìm text "Phần"
page_title_xpaths = [
    "//div[contains(text(), 'Phần')]",
    "//*[contains(text(), 'Phần')]",
    "//h1[contains(text(), 'Phần')]",
    "//span[contains(text(), 'Phần')]",
    "//div[@aria-label[contains(., 'Phần')]]",
]

for xpath in page_title_xpaths:
    try:
        elements = driver.find_elements(By.XPATH, xpath)
        if elements:
            print(f"\n✓ Found with XPath: {xpath}")
            for elem in elements:
                text = elem.text or elem.get_attribute('innerText')
                print(f"  Text: {text}")
                # Lấy parent classes
                parent_classes = elem.get_attribute('class')
                print(f"  Element class: {parent_classes}")
                # Lấy parent HTML
                parent_html = driver.execute_script("return arguments[0].parentElement.outerHTML", elem)[:200]
                print(f"  Parent HTML: {parent_html}...")
    except Exception as e:
        pass

# ========== TÌM CÂU HỎI ==========
print("\n" + "="*60)
print("TÌM CÂU HỎI VÀ OPTIONS")
print("="*60)

questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
print(f"\nTìm thấy {len(questions)} question elements (class Qr7Oae)\n")

for idx, q in enumerate(questions):
    print(f"\n--- Question Element {idx} ---")
    
    # Tìm tiêu đề câu hỏi
    try:
        spans = q.find_elements(By.CLASS_NAME, "M7eMe")
        if spans:
            for s in spans:
                text = s.get_attribute('innerText') or s.get_attribute('textContent')
                if text:
                    text = text.strip()
                    print(f"📌 Tiêu đề: {text}")
    except:
        pass
    
    # Tìm loại câu hỏi
    radio = q.find_elements(By.XPATH, ".//div[@role='radio']")
    checkbox = q.find_elements(By.XPATH, ".//div[@role='checkbox']")
    textbox = q.find_elements(By.XPATH, ".//textarea | .//input[@type='text']")
    
    if radio:
        print(f"  Loại: Multiple Choice")
    elif checkbox:
        print(f"  Loại: Checkbox (Chọn nhiều)")
    elif textbox:
        print(f"  Loại: Text Input")
    
    # Tìm OPTIONS
    print(f"  Options:")
    
    # Với radio buttons
    for r in radio:
        text = driver.execute_script("return arguments[0].nextElementSibling?.textContent || arguments[0].textContent", r)
        print(f"    - {text}")
    
    # Với checkboxes
    for c in checkbox:
        text = driver.execute_script("return arguments[0].nextElementSibling?.textContent || arguments[0].textContent", c)
        print(f"    - {text}")

# ========== LƯU HTML ĐẦY ĐỦ ==========
print("\n" + "="*60)
print("SAVING FULL PAGE HTML")
print("="*60)

html = driver.page_source
with open("/Users/2apple_mgn_63_ram16/Desktop/GGform/form_page_structure.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✓ Saved to form_page_structure.html")

driver.quit()
print("\n✓ Done!")
