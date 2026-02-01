"""
Debug script - Mở Chrome và kiểm tra tại sao linear scale không điền được
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_linear_scale():
    print("="*80)
    print("🔍 DEBUG LINEAR SCALE QUESTIONS")
    print("="*80)
    
    # Nhập URL
    print("\n📝 Nhập URL Google Form (editor hoặc viewform):")
    print("   Ví dụ: https://docs.google.com/forms/d/.../edit")
    print("   Hoặc: https://docs.google.com/forms/d/.../viewform")
    form_url = input("\nURL: ").strip()
    
    if not form_url:
        print("❌ Không có URL!")
        return
    
    # Khởi tạo Chrome
    print("\n🌐 Đang mở Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Mở form
        print(f"📂 Đang mở form: {form_url}")
        driver.get(form_url)
        time.sleep(3)
        
        # Xác định editor hay viewform
        is_editor = '/edit' in driver.current_url
        is_viewform = '/viewform' in driver.current_url
        
        print(f"\n📍 Detected: {'EDITOR' if is_editor else 'VIEWFORM' if is_viewform else 'UNKNOWN'}")
        print(f"   Current URL: {driver.current_url}")
        
        # Tìm tất cả question containers
        print("\n" + "="*80)
        print("🔎 TÌM KIẾM QUESTION CONTAINERS:")
        print("="*80)
        
        if is_editor:
            selectors = [
                "div[data-params*='FreebirdFormviewerComponentsQuestionBaseRoot']",
                "div.freebirdFormviewerComponentsQuestionBaseRoot",
                "div.Qr7Oae"
            ]
        else:
            selectors = [
                "div[data-params*='FreebirdFormviewerComponentsQuestionBaseRoot']",
                "div.freebirdFormviewerComponentsQuestionBaseRoot",
                "div[jsname]",
                "div[role='listitem']"
            ]
        
        all_questions = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✓ Tìm thấy {len(elements)} elements với selector: {selector}")
                    all_questions.extend(elements)
            except Exception as e:
                print(f"✗ Lỗi với selector '{selector}': {e}")
        
        print(f"\n📊 Tổng cộng: {len(all_questions)} question containers")
        
        # Phân tích từng question
        print("\n" + "="*80)
        print("📋 PHÂN TÍCH CÁC QUESTIONS:")
        print("="*80)
        
        linear_scale_questions = []
        
        for idx, q_elem in enumerate(all_questions[:20]):  # Chỉ check 20 đầu
            try:
                # Lấy text
                q_text = q_elem.text[:100] if q_elem.text else "(no text)"
                
                print(f"\n[{idx}] {q_text}...")
                
                # Kiểm tra xem có phải linear scale không
                is_linear = False
                detection_method = ""
                
                # Method 1: Check class names
                class_names = q_elem.get_attribute('class') or ""
                if 'Ht8Grd' in class_names or 'lLfZXe' in class_names:
                    is_linear = True
                    detection_method = f"class '{class_names[:50]}'"
                
                # Method 2: Check for numbered options
                if not is_linear:
                    try:
                        radios = q_elem.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                        if radios:
                            labels = [r.get_attribute('aria-label') for r in radios[:5]]
                            numeric_labels = [l for l in labels if l and l.strip().isdigit()]
                            
                            print(f"    Radio labels: {labels}")
                            
                            if len(numeric_labels) >= 3:
                                is_linear = True
                                detection_method = f"numeric radios: {numeric_labels}"
                    except Exception as e:
                        print(f"    Error checking radios: {e}")
                
                # Method 3: Check for data-value attributes
                if not is_linear:
                    try:
                        data_values = q_elem.find_elements(By.CSS_SELECTOR, "div[data-value]")
                        if len(data_values) >= 3:
                            values = [dv.get_attribute('data-value') for dv in data_values[:10]]
                            numeric_values = [v for v in values if v and v.isdigit()]
                            
                            if len(numeric_values) >= 3:
                                is_linear = True
                                detection_method = f"data-value: {numeric_values}"
                    except:
                        pass
                
                if is_linear:
                    print(f"    ✅ LINEAR SCALE DETECTED! ({detection_method})")
                    linear_scale_questions.append({
                        'index': idx,
                        'element': q_elem,
                        'text': q_text,
                        'method': detection_method
                    })
                else:
                    print(f"    ℹ️  Not linear scale")
                    
            except Exception as e:
                print(f"[{idx}] Error: {e}")
        
        # Hiển thị kết quả
        print("\n" + "="*80)
        print(f"✅ TÌM THẤY {len(linear_scale_questions)} LINEAR SCALE QUESTIONS:")
        print("="*80)
        
        for lq in linear_scale_questions:
            print(f"\n[{lq['index']}] {lq['text']}")
            print(f"    Method: {lq['method']}")
        
        # Test click vào một linear scale question
        if linear_scale_questions:
            print("\n" + "="*80)
            print("🖱️  TEST CLICK VÀO LINEAR SCALE:")
            print("="*80)
            
            test_q = linear_scale_questions[0]
            print(f"\nĐang test click vào question [{test_q['index']}]...")
            
            # Scroll to element
            driver.execute_script("arguments[0].scrollIntoView(true);", test_q['element'])
            time.sleep(1)
            
            # Tìm các options
            print("\n🔍 Tìm kiếm options để click:")
            
            selectors_to_try = [
                ("div[data-value='3']", "data-value='3'"),
                ("div.Od2TWd[data-value='3']", "Od2TWd with data-value='3'"),
                ("div[role='radio'][aria-label='3']", "role=radio aria-label='3'"),
                ("div[role='radio']", "all radio buttons")
            ]
            
            for selector, desc in selectors_to_try:
                try:
                    options = test_q['element'].find_elements(By.CSS_SELECTOR, selector)
                    print(f"\n  Selector: {selector}")
                    print(f"  Found: {len(options)} elements")
                    
                    if options:
                        for i, opt in enumerate(options[:5]):
                            aria_label = opt.get_attribute('aria-label')
                            data_value = opt.get_attribute('data-value')
                            print(f"    [{i}] aria-label='{aria_label}' data-value='{data_value}'")
                        
                        # Thử click vào option đầu tiên
                        if len(options) >= 3:
                            print(f"\n  ▶️  Đang click vào option thứ 3...")
                            try:
                                opt_to_click = options[2] if len(options) > 2 else options[0]
                                driver.execute_script("arguments[0].scrollIntoView(true);", opt_to_click)
                                time.sleep(0.5)
                                opt_to_click.click()
                                print(f"  ✅ Click thành công!")
                                time.sleep(2)
                            except Exception as e:
                                print(f"  ❌ Click failed: {e}")
                        
                except Exception as e:
                    print(f"  ❌ Selector failed: {e}")
        
        # Giữ browser mở
        print("\n" + "="*80)
        print("✅ DEBUG HOÀN TẤT!")
        print("="*80)
        print("\n⏸️  Chrome sẽ GIỮ MỞ để bạn kiểm tra.")
        print("   Nhấn Enter để đóng...")
        input()
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  Chrome sẽ giữ mở. Nhấn Enter để đóng...")
        input()
    
    finally:
        driver.quit()
        print("🔚 Đã đóng Chrome")

if __name__ == "__main__":
    debug_linear_scale()
