"""
Script để phân tích cấu trúc HTML của Linear Scale trong Google Form
Chạy script này để nghiên cứu cách lấy dữ liệu linear scale
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def analyze_form_structure(form_url: str):
    """Phân tích cấu trúc HTML của Google Form để hiểu linear scale"""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING GOOGLE FORM STRUCTURE")
    print(f"URL: {form_url}")
    print(f"{'='*80}\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Không dùng headless để dễ debug
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get(form_url)
        print("⏳ Waiting for form to load...")
        time.sleep(5)
        
        # Kiểm tra xem có cần đăng nhập không
        page_source = driver.page_source
        if "Đăng nhập" in page_source or "Sign in" in page_source:
            print("⚠️ Form yêu cầu đăng nhập. Vui lòng đăng nhập thủ công...")
            input("Nhấn Enter sau khi đăng nhập xong...")
            time.sleep(3)
        
        print("\n" + "="*80)
        print("SCANNING FOR LINEAR SCALE ELEMENTS")
        print("="*80)
        
        # 1. Tìm tất cả elements có class Ht8Grd (linear scale container)
        ht8grd_elements = driver.find_elements(By.CLASS_NAME, "Ht8Grd")
        print(f"\n📌 Found {len(ht8grd_elements)} elements with class 'Ht8Grd' (linear scale container)")
        
        # 2. Tìm các div có role="radiogroup" (thường dùng cho linear scale)
        radiogroups = driver.find_elements(By.XPATH, "//div[@role='radiogroup']")
        print(f"📌 Found {len(radiogroups)} elements with role='radiogroup'")
        
        # 3. Phân tích từng question container
        question_containers = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        print(f"\n📌 Found {len(question_containers)} question containers (Qr7Oae)")
        
        for i, container in enumerate(question_containers):
            print(f"\n{'='*60}")
            print(f"QUESTION {i+1}")
            print(f"{'='*60}")
            
            # Lấy tiêu đề câu hỏi
            try:
                title_elem = container.find_element(By.CLASS_NAME, "M7eMe")
                title = title_elem.text.strip()
                print(f"Title: {title}")
            except:
                print("Title: (không tìm thấy)")
            
            # Kiểm tra loại câu hỏi
            q_type = "unknown"
            
            # Check cho linear scale
            linear_scale_markers = container.find_elements(By.CLASS_NAME, "Ht8Grd")
            if linear_scale_markers:
                q_type = "linear_scale"
                print(f"Type: LINEAR SCALE ⭐")
                
                # Phân tích chi tiết linear scale
                analyze_linear_scale_detail(driver, container)
            else:
                # Check cho radio buttons
                radios = container.find_elements(By.XPATH, ".//div[@role='radio']")
                if radios:
                    q_type = "multiple_choice"
                    print(f"Type: Multiple Choice ({len(radios)} options)")
                else:
                    checkboxes = container.find_elements(By.XPATH, ".//div[@role='checkbox']")
                    if checkboxes:
                        q_type = "checkbox"
                        print(f"Type: Checkbox ({len(checkboxes)} options)")
                    else:
                        print(f"Type: Other/Unknown")
        
        # 4. Phân tích cấu trúc linear scale chi tiết
        print("\n" + "="*80)
        print("DETAILED LINEAR SCALE ANALYSIS")
        print("="*80)
        
        # Tìm tất cả radiogroup 
        for idx, rg in enumerate(radiogroups):
            print(f"\n📻 RadioGroup {idx+1}:")
            
            # Tìm các radio buttons bên trong
            radios = rg.find_elements(By.XPATH, ".//div[@role='radio']")
            print(f"  Contains {len(radios)} radio buttons")
            
            for j, radio in enumerate(radios):
                aria_label = radio.get_attribute("aria-label") or "(no aria-label)"
                data_value = radio.get_attribute("data-value") or "(no data-value)"
                print(f"    Radio {j+1}: aria-label='{aria_label}', data-value='{data_value}'")
            
            # Tìm labels ở 2 đầu scale (min/max labels)
            parent = rg.find_element(By.XPATH, ".//..")
            labels = parent.find_elements(By.CLASS_NAME, "OIC90c")
            if labels:
                print(f"  Scale labels:")
                for label in labels:
                    print(f"    - '{label.text}'")
        
        # 5. Tìm các class phổ biến trong linear scale
        print("\n" + "="*80)
        print("COMMON LINEAR SCALE CLASSES")
        print("="*80)
        
        # Classes thường thấy trong linear scale
        class_to_check = [
            "lLfZXe",  # Linear scale row container
            "i9xfbb",  # Scale number container
            "OaBhFe",  # Scale endpoints
            "Ht8Grd",  # Linear scale marker
            "AhH7Kc",  # Scale option container
            "Od2TWd",  # Another scale container
        ]
        
        for cls in class_to_check:
            elements = driver.find_elements(By.CLASS_NAME, cls)
            if elements:
                print(f"\n📌 Class '{cls}': {len(elements)} elements")
                for k, elem in enumerate(elements[:3]):  # Chỉ in 3 cái đầu
                    print(f"  [{k+1}] text='{elem.text[:50] if elem.text else '(empty)'}...'")
        
        print("\n✅ Analysis complete!")
        input("\nNhấn Enter để đóng browser...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


def analyze_linear_scale_detail(driver, container):
    """Phân tích chi tiết một câu hỏi linear scale"""
    print("\n  📊 LINEAR SCALE DETAILS:")
    
    # 1. Tìm radiogroup
    radiogroup = container.find_element(By.XPATH, ".//div[@role='radiogroup']") if container.find_elements(By.XPATH, ".//div[@role='radiogroup']") else None
    
    if radiogroup:
        # Lấy tất cả radio options
        radios = radiogroup.find_elements(By.XPATH, ".//div[@role='radio']")
        print(f"  Scale has {len(radios)} points")
        
        scale_values = []
        for radio in radios:
            # Lấy giá trị từ aria-label hoặc data-value
            aria_label = radio.get_attribute("aria-label") or ""
            data_value = radio.get_attribute("data-value") or ""
            
            # Tìm text label bên trong (thường là số)
            inner_text = radio.text.strip() if radio.text else ""
            
            value = data_value or aria_label or inner_text
            scale_values.append(value)
            print(f"    - Value: '{value}' (aria-label='{aria_label}', data-value='{data_value}')")
        
        print(f"  Scale values: {scale_values}")
    
    # 2. Tìm min/max labels
    # Linear scale thường có labels ở 2 đầu
    try:
        # Tìm class OaBhFe (endpoint labels)
        endpoint_labels = container.find_elements(By.CLASS_NAME, "OaBhFe")
        if endpoint_labels:
            print(f"  Endpoint labels:")
            for label in endpoint_labels:
                print(f"    - '{label.text}'")
    except:
        pass


if __name__ == "__main__":
    # URL để test - có thể thay bằng URL của bạn
    test_url = input("Nhập URL Google Form (viewform hoặc edit): ").strip()
    if not test_url:
        test_url = "https://docs.google.com/forms/d/1V3LZd-3gIrzRczrSwkWwqE7OB_w1pzNWoJnIYaqaG6M/viewform"
    
    analyze_form_structure(test_url)
