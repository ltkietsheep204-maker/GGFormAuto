"""Debug script để xem cấu trúc HTML của multiple choice options"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json

# URL của form bạn đang test
FORM_URL = input("Nhập URL form (viewform): ").strip()

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1200,900")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    driver.get(FORM_URL)
    print("Loading form...")
    time.sleep(5)  # Wait for form to load
    
    # Tìm tất cả question containers
    question_containers = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
    print(f"\n=== Found {len(question_containers)} question containers ===\n")
    
    for i, container in enumerate(question_containers):
        print(f"\n{'='*60}")
        print(f"QUESTION {i+1}")
        print(f"{'='*60}")
        
        # Get question title
        try:
            title = container.find_element(By.CLASS_NAME, "M7eMe").text
            print(f"Title: {title}")
        except:
            print("Title: (not found)")
        
        # Check for YKDB3e options (multiple choice style)
        ykdb3e_options = container.find_elements(By.CLASS_NAME, "YKDB3e")
        print(f"\n  YKDB3e options: {len(ykdb3e_options)}")
        for j, opt in enumerate(ykdb3e_options):
            try:
                # Get text
                try:
                    label = opt.find_element(By.CLASS_NAME, "urLvsc")
                    text = label.text
                except:
                    text = opt.text[:50] if opt.text else "(no text)"
                
                # Get classes
                classes = opt.get_attribute("class")
                
                # Get role
                role = opt.get_attribute("role") or "(no role)"
                
                # Check clickable
                is_displayed = opt.is_displayed()
                
                print(f"    [{j}] text='{text}' | role={role} | displayed={is_displayed}")
                print(f"        classes: {classes[:80]}...")
                
                # Check for child div with role='radio'
                try:
                    radio_child = opt.find_element(By.CSS_SELECTOR, "div[role='radio']")
                    aria_checked = radio_child.get_attribute("aria-checked")
                    data_value = radio_child.get_attribute("data-value")
                    print(f"        → Has div[role='radio']: aria-checked={aria_checked}, data-value={data_value}")
                except:
                    pass
                    
            except Exception as e:
                print(f"    [{j}] Error: {e}")
        
        # Check for div[role='radiogroup']
        radiogroups = container.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")
        print(f"\n  div[role='radiogroup']: {len(radiogroups)}")
        for rg in radiogroups:
            radios = rg.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            print(f"    → Contains {len(radios)} div[role='radio'] elements")
            for k, radio in enumerate(radios[:5]):  # Limit to 5
                aria_label = radio.get_attribute("aria-label") or ""
                data_value = radio.get_attribute("data-value") or ""
                aria_checked = radio.get_attribute("aria-checked") or ""
                
                # Try to get the text label
                try:
                    parent = radio.find_element(By.XPATH, "..")
                    label_text = parent.text.split('\n')[0] if parent.text else ""
                except:
                    label_text = ""
                
                print(f"      [{k}] aria-label='{aria_label}' | data-value='{data_value}' | checked={aria_checked}")
                if label_text:
                    print(f"          parent_text: '{label_text[:40]}...'")
        
        # Check for docssharedWizToggleLabeledContainer
        toggles = container.find_elements(By.CLASS_NAME, "docssharedWizToggleLabeledContainer")
        print(f"\n  docssharedWizToggleLabeledContainer: {len(toggles)}")
        for k, tog in enumerate(toggles[:5]):
            try:
                text = tog.text.split('\n')[0] if tog.text else "(no text)"
                print(f"    [{k}] text='{text}'")
            except:
                pass
        
        print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    input("\nPress Enter to close browser...")
    driver.quit()
