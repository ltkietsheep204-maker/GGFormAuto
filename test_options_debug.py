#!/usr/bin/env python3
"""Debug options extraction from Google Form - with visual output"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def extract_options(driver, question_element):
    """Extract options using new method"""
    options = []
    
    try:
        # Count radio buttons
        radios = question_element.find_elements(By.XPATH, ".//div[@role='radio']")
        print(f"  📻 Radio buttons: {len(radios)}")
        
        if len(radios) == 0:
            checkboxes = question_element.find_elements(By.XPATH, ".//div[@role='checkbox']")
            print(f"  ☑️  Checkboxes: {len(checkboxes)}")
            radios = checkboxes
        
        if not radios:
            print(f"  ❌ No radio/checkbox found")
            return []
        
        # Get all OIC90c spans
        all_spans = question_element.find_elements(By.CLASS_NAME, "OIC90c")
        print(f"  📝 OIC90c spans found: {len(all_spans)}")
        
        # Extract text from each span
        option_texts = []
        for idx, span in enumerate(all_spans):
            try:
                # Try innerText first, then textContent
                text = driver.execute_script(
                    "return arguments[0].innerText || arguments[0].textContent", 
                    span
                )
                text = text.strip() if text else ""
                
                # Show raw text
                print(f"    [{idx}] Raw: '{text[:60]}'")
                
                # Filter out non-option texts
                if (text and 
                    not any(x in text.lower() for x in ['mô tả', 'chú thích', 'mục khác', 'bắt buộc', 'required']) and
                    len(text) > 0):
                    option_texts.append(text)
                    print(f"    ✅ OPTION: '{text}'")
                else:
                    print(f"    ⏭️  SKIPPED (filtered)")
            except Exception as e:
                print(f"    ⚠️  Error: {e}")
        
        # Take only as many as radio buttons
        selected = option_texts[:len(radios)]
        print(f"  ✓ Selected: {len(selected)}/{len(radios)} options\n")
        return [{"index": i, "text": t} for i, t in enumerate(selected)]
        
    except Exception as e:
        print(f"  ❌ Exception: {e}\n")
        return []

# Setup Chrome with standard options
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("\n🚀 Opening Google Form...")
    driver.get("https://docs.google.com/forms/d/e/1FAIpQLSfVvKZ_tZvOxVpTrH6fEqnVf1h2YpWNk7o5F-oXCfxHpE7Qpw/viewform")
    
    # Wait for page load
    print("⏳ Waiting for page load...")
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//*[@data-item-id]"))
    )
    
    # Get questions
    questions = driver.find_elements(By.XPATH, "//*[@data-item-id and @data-item-id != '-1']")
    print(f"\n✅ Found {len(questions)} questions\n")
    print("=" * 60)
    
    # Process each question
    for q_idx, q in enumerate(questions):
        try:
            # Get title
            title_span = q.find_element(By.CLASS_NAME, "M7eMe")
            title = title_span.text.strip()
            print(f"\n❓ Question {q_idx + 1}: {title}")
            
            # Extract options
            opts = extract_options(driver, q)
            print(f"   Total options: {len(opts)}")
            for opt in opts:
                print(f"     • {opt['text']}")
            
        except Exception as e:
            print(f"\n❌ Error processing Q{q_idx + 1}: {e}")
    
    print("\n" + "=" * 60)
    print("\n✨ Done!")

except Exception as e:
    print(f"\n❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()

finally:
    input("\nPress Enter to close browser...")
    driver.quit()
