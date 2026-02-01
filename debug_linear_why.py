"""
Debug tại sao linear scale không click được
Sử dụng URL form trực tiếp
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# URL form
VIEWFORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdKEDlD-z9Z9l7QVgQ-bnTn7sJ8sYK9F7v5Y9s8Q5h8ZZbX8A/viewform"

def debug():
    print("🌐 Khởi động Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    print("\n📝 Nhập viewform URL:")
    url = input("URL: ").strip()
    
    if not url:
        print("❌ Cần URL!")
        driver.quit()
        return
    
    print(f"\n📂 Mở form: {url}")
    driver.get(url)
    time.sleep(3)
    
    print("\n" + "="*80)
    print("🔍 PHÂN TÍCH CÂU HỎI LINEAR SCALE")
    print("="*80)
    
    # Tìm tất cả question containers
    containers = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
    print(f"\n📊 Tìm thấy {len(containers)} câu hỏi")
    
    linear_count = 0
    
    for idx, container in enumerate(containers):
        try:
            # Lấy title
            try:
                title = container.find_element(By.CSS_SELECTOR, "div.M7eMe, span.M7eMe").text[:60]
            except:
                title = container.text[:50] if container.text else "(no text)"
            
            # Check for linear scale indicators
            has_data_value = len(container.find_elements(By.CSS_SELECTOR, "div[data-value]")) > 0
            radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            
            # Check if numeric radios
            is_numeric = False
            radio_labels = []
            if radios:
                for r in radios:
                    aria = r.get_attribute('aria-label')
                    if aria:
                        radio_labels.append(aria)
                        if aria.strip().isdigit():
                            is_numeric = True
            
            # Determine if linear scale
            is_linear = has_data_value or (len(radios) >= 3 and is_numeric)
            
            if is_linear:
                linear_count += 1
                print(f"\n{'='*80}")
                print(f"[Q{idx}] ✅ LINEAR SCALE DETECTED")
                print(f"{'='*80}")
                print(f"Title: {title}")
                print(f"Has data-value: {has_data_value}")
                print(f"Radio labels: {radio_labels}")
                
                # Phân tích chi tiết các options
                print(f"\n🎯 OPTIONS ANALYSIS:")
                
                # Method 1: div[data-value]
                dv_elements = container.find_elements(By.CSS_SELECTOR, "div[data-value]")
                print(f"\n   Method 1 - div[data-value]: {len(dv_elements)} elements")
                for i, dv in enumerate(dv_elements):
                    val = dv.get_attribute('data-value')
                    aria = dv.get_attribute('aria-label')
                    checked = dv.get_attribute('aria-checked')
                    classes = dv.get_attribute('class')
                    print(f"      [{i}] data-value='{val}' aria-label='{aria}' checked={checked}")
                    print(f"          class: {classes[:50]}..." if classes else "          class: (none)")
                
                # Method 2: div[role='radio']
                print(f"\n   Method 2 - div[role='radio']: {len(radios)} elements")
                for i, radio in enumerate(radios):
                    val = radio.get_attribute('data-value')
                    aria = radio.get_attribute('aria-label')
                    checked = radio.get_attribute('aria-checked')
                    classes = radio.get_attribute('class')
                    print(f"      [{i}] data-value='{val}' aria-label='{aria}' checked={checked}")
                    print(f"          class: {classes[:50]}..." if classes else "          class: (none)")
                
                # Test click option 3
                print(f"\n🖱️  TESTING CLICK (option '3'):")
                
                # Try different selectors
                selectors = [
                    ("div[data-value='3']", "data-value='3'"),
                    ("div.Od2TWd[data-value='3']", "Od2TWd + data-value='3'"),
                    ("div[role='radio'][data-value='3']", "role='radio' + data-value='3'"),
                    ("div[role='radio'][aria-label='3']", "role='radio' + aria-label='3'"),
                ]
                
                clicked = False
                for selector, desc in selectors:
                    try:
                        elems = container.find_elements(By.CSS_SELECTOR, selector)
                        if elems:
                            print(f"\n   ✓ Found {len(elems)} with '{desc}'")
                            
                            # Try click
                            elem = elems[0]
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.2)
                            
                            before = elem.get_attribute('aria-checked')
                            
                            # Try standard click
                            try:
                                elem.click()
                                time.sleep(0.3)
                                after = elem.get_attribute('aria-checked')
                                
                                if after == 'true':
                                    print(f"   ✅ CLICK THÀNH CÔNG! (before={before}, after={after})")
                                    clicked = True
                                    break
                                else:
                                    print(f"   ⚠️  Click executed but state unchanged (before={before}, after={after})")
                            except Exception as e:
                                print(f"   ❌ Standard click failed: {e}")
                                
                                # Try JS click
                                try:
                                    driver.execute_script("arguments[0].click();", elem)
                                    time.sleep(0.3)
                                    after = elem.get_attribute('aria-checked')
                                    if after == 'true':
                                        print(f"   ✅ JS CLICK THÀNH CÔNG!")
                                        clicked = True
                                        break
                                except:
                                    pass
                        else:
                            print(f"   ✗ No elements with '{desc}'")
                    except Exception as e:
                        print(f"   ✗ Error with '{desc}': {e}")
                
                if not clicked:
                    print(f"\n   ❌ KHÔNG THỂ CLICK! Cần kiểm tra thêm...")
                    
                    # Debug HTML structure
                    print(f"\n   📄 HTML STRUCTURE (first 500 chars):")
                    html = container.get_attribute('outerHTML')[:500]
                    print(f"   {html}")
        
        except Exception as e:
            print(f"\n[Q{idx}] ❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY: Tìm thấy {linear_count} câu hỏi linear scale")
    print(f"{'='*80}")
    
    print("\n⏸️  Chrome giữ mở để kiểm tra. Nhấn Enter để đóng...")
    input()
    driver.quit()

if __name__ == "__main__":
    debug()
