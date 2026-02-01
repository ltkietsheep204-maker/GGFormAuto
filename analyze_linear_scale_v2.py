"""
Script phân tích cấu trúc Linear Scale từ Google Form
Chạy script này để nghiên cứu cách lấy dữ liệu phạm vi tuyến tính
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def analyze_viewform(form_url: str):
    """Phân tích viewform để xem cấu trúc linear scale"""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING VIEWFORM - LINEAR SCALE STRUCTURE")
    print(f"URL: {form_url}")
    print(f"{'='*80}\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Không headless để dễ debug
    # options.add_argument("--headless")
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get(form_url)
        print("⏳ Waiting for form to load...")
        time.sleep(5)
        
        # Tìm tất cả question containers
        questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
        print(f"\n📌 Found {len(questions)} question containers (Qr7Oae)")
        
        for i, q in enumerate(questions):
            print(f"\n{'='*60}")
            print(f"QUESTION {i+1}")
            print(f"{'='*60}")
            
            # Lấy tiêu đề
            try:
                title = q.find_element(By.CLASS_NAME, "M7eMe").text
                print(f"Title: {title[:80]}...")
            except:
                print("Title: (not found)")
            
            # Kiểm tra linear scale
            # Linear scale có các class đặc trưng
            
            # 1. Tìm radiogroup
            radiogroups = q.find_elements(By.XPATH, ".//div[@role='radiogroup']")
            if radiogroups:
                print(f"\n📻 Found {len(radiogroups)} radiogroup(s)")
                
                for rg in radiogroups:
                    # Tìm radio buttons
                    radios = rg.find_elements(By.XPATH, ".//div[@role='radio']")
                    print(f"  Radio buttons: {len(radios)}")
                    
                    # In chi tiết từng radio
                    for j, radio in enumerate(radios):
                        aria_label = radio.get_attribute("aria-label") or ""
                        data_value = radio.get_attribute("data-value") or ""
                        data_answer = radio.get_attribute("data-answer-value") or ""
                        inner_text = radio.text.strip() if radio.text else ""
                        
                        print(f"    [{j}] aria-label='{aria_label}', data-value='{data_value}', data-answer='{data_answer}', text='{inner_text}'")
            
            # 2. Tìm scale labels (ở 2 đầu)
            # Thường có class i2lyTd (chứa toàn bộ scale row)
            scale_rows = q.find_elements(By.CLASS_NAME, "i2lyTd")
            if scale_rows:
                print(f"\n📊 Found scale row (i2lyTd)")
                for sr in scale_rows:
                    # Tìm labels ở 2 đầu
                    labels = sr.find_elements(By.CLASS_NAME, "Xb9hP")
                    print(f"  Scale endpoint labels (Xb9hP): {len(labels)}")
                    for lbl in labels:
                        print(f"    - '{lbl.text}'")
            
            # 3. Tìm numbers row (1, 2, 3, 4, 5)
            # Thường có class lLfZXe (linear scale container)
            linear_containers = q.find_elements(By.CLASS_NAME, "lLfZXe")
            if linear_containers:
                print(f"\n📏 Found linear scale container (lLfZXe)")
            
            # 4. Tìm tất cả class liên quan đến linear scale
            check_classes = ["Ht8Grd", "lLfZXe", "i2lyTd", "Od2TWd", "AhH7Kc", "i9xfbb", "Xb9hP"]
            for cls in check_classes:
                elements = q.find_elements(By.CLASS_NAME, cls)
                if elements:
                    print(f"\n  Class '{cls}': {len(elements)} elements")
                    for k, el in enumerate(elements[:3]):
                        txt = el.text[:50] if el.text else "(empty)"
                        print(f"    [{k}] text='{txt}'")
        
        print("\n" + "="*80)
        print("FULL HTML DUMP OF LINEAR SCALE QUESTIONS")
        print("="*80)
        
        # Dump HTML của câu hỏi linear scale
        for i, q in enumerate(questions):
            radiogroups = q.find_elements(By.XPATH, ".//div[@role='radiogroup']")
            if radiogroups:
                radios = radiogroups[0].find_elements(By.XPATH, ".//div[@role='radio']")
                if radios:
                    first_aria = radios[0].get_attribute("aria-label") or ""
                    if first_aria.isdigit():  # Likely linear scale
                        print(f"\n--- Question {i+1} HTML (LINEAR SCALE) ---")
                        # Get inner HTML
                        html = q.get_attribute("innerHTML")
                        # Save to file
                        with open(f"linear_scale_q{i+1}_html.txt", "w", encoding="utf-8") as f:
                            f.write(html)
                        print(f"  Saved to linear_scale_q{i+1}_html.txt")
        
        print("\n✅ Analysis complete!")
        input("\nNhấn Enter để đóng browser...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


def analyze_editor_link(form_url: str):
    """Phân tích editor link để xem cấu trúc linear scale"""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING EDITOR LINK - LINEAR SCALE STRUCTURE")
    print(f"URL: {form_url}")
    print(f"{'='*80}\n")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get(form_url)
        print("⏳ Waiting for form to load...")
        print("⚠️ Nếu cần đăng nhập, hãy đăng nhập thủ công trong browser...")
        
        input("Nhấn Enter sau khi form đã load xong...")
        
        # Tìm tất cả elements có data-item-id (question containers trong editor)
        questions = driver.find_elements(By.XPATH, "//*[@data-item-id]")
        print(f"\n📌 Found {len(questions)} question containers with data-item-id")
        
        for i, q in enumerate(questions):
            print(f"\n{'='*60}")
            print(f"QUESTION {i+1}")
            print(f"{'='*60}")
            
            # Lấy tiêu đề từ aria-label="Câu hỏi"
            try:
                title_elem = q.find_element(By.XPATH, ".//div[@aria-label='Câu hỏi']")
                title = title_elem.text
                print(f"Title: {title[:80]}...")
            except:
                try:
                    title_elem = q.find_element(By.CLASS_NAME, "M7eMe")
                    title = title_elem.text
                    print(f"Title (M7eMe): {title[:80]}...")
                except:
                    print("Title: (not found)")
            
            # Tìm dropdown "Phạm vi tuyến tính" để xác định loại câu hỏi
            try:
                type_dropdown = q.find_element(By.XPATH, ".//div[contains(@aria-label, 'loại câu hỏi')]")
                q_type = type_dropdown.text
                print(f"Question Type: {q_type}")
            except:
                pass
            
            # Đối với Linear Scale trong editor:
            # - Có dropdown chọn min (1) và max (5)
            # - Có 2 input field cho label min và label max
            
            # Tìm các dropdown chứa giá trị scale
            dropdowns = q.find_elements(By.XPATH, ".//div[@role='listbox']")
            print(f"\n📊 Found {len(dropdowns)} dropdown(s) (listbox)")
            for j, dd in enumerate(dropdowns):
                text = dd.text.strip() if dd.text else ""
                aria_label = dd.get_attribute("aria-label") or ""
                print(f"  [{j}] text='{text}', aria-label='{aria_label}'")
            
            # Tìm các input field cho scale labels
            inputs = q.find_elements(By.XPATH, ".//input[@type='text']")
            print(f"\n📝 Found {len(inputs)} text input(s)")
            for j, inp in enumerate(inputs):
                value = inp.get_attribute("value") or ""
                aria_label = inp.get_attribute("aria-label") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                print(f"  [{j}] value='{value}', aria-label='{aria_label}', placeholder='{placeholder}'")
            
            # Tìm các elements có chứa số (1, 5, etc)
            # Trong editor, linear scale hiển thị "1 đến 5"
            spans = q.find_elements(By.TAG_NAME, "span")
            for span in spans:
                text = span.text.strip() if span.text else ""
                if text and ("đến" in text or text.isdigit()):
                    print(f"  Scale indicator: '{text}'")
        
        print("\n✅ Analysis complete!")
        input("\nNhấn Enter để đóng browser...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    print("="*80)
    print("LINEAR SCALE ANALYZER")
    print("="*80)
    print("\nChọn loại link:")
    print("1. Viewform link (public)")
    print("2. Editor link (cần đăng nhập)")
    
    choice = input("\nNhập lựa chọn (1/2): ").strip()
    
    if choice == "1":
        url = input("Nhập viewform URL: ").strip()
        if not url:
            url = "https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform"
        analyze_viewform(url)
    elif choice == "2":
        url = input("Nhập editor URL: ").strip()
        if not url:
            url = "https://docs.google.com/forms/d/1V3LZd-3gIrzRczrSwkWwqE7OB_w1pzNWoJnIYaqaG6M/edit"
        analyze_editor_link(url)
    else:
        print("Lựa chọn không hợp lệ")
