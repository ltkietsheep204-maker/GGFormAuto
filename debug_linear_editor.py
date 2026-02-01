#!/usr/bin/env python3
"""
Debug script để phân tích chi tiết cấu trúc Linear Scale trong Editor link
Chạy script này, đăng nhập Google, rồi script sẽ in ra cấu trúc HTML
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# URL editor link
EDITOR_URL = "https://docs.google.com/forms/d/1V3LZd-3gIrzRczrSwkWwqE7OB_w1pzNWoJnIYaqaG6M/edit"

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
# KHÔNG headless để có thể đăng nhập
# options.add_argument('--headless')

print("🚀 Khởi động Chrome...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print(f"📂 Mở URL: {EDITOR_URL}")
driver.get(EDITOR_URL)

print("\n⚠️  Nếu cần đăng nhập Google, hãy đăng nhập trong browser...")
print("⏳ Chờ 15 giây hoặc nhấn Enter khi form đã load xong...")

try:
    input(">>> Nhấn Enter khi sẵn sàng... ")
except:
    time.sleep(15)

print("\n" + "="*80)
print("PHÂN TÍCH CẤU TRÚC LINEAR SCALE TRONG EDITOR")
print("="*80)

# Tìm tất cả question containers (data-item-id)
questions = driver.find_elements(By.XPATH, "//*[@data-item-id]")
print(f"\n📌 Tìm thấy {len(questions)} câu hỏi với data-item-id")

for i, q in enumerate(questions):
    print(f"\n{'='*60}")
    print(f"CÂU HỎI {i+1}")
    print(f"{'='*60}")
    
    # Lấy toàn bộ text trong câu hỏi
    all_text = q.text or ""
    print(f"📄 Toàn bộ text: {all_text[:200]}...")
    
    # Kiểm tra có "đến" không (dấu hiệu linear scale)
    if "đến" in all_text:
        print("\n🎯 PHÁT HIỆN 'đến' - Có thể là LINEAR SCALE!")
        
        # Tìm các phần tử dropdown/listbox
        print("\n--- Tìm listbox ---")
        listboxes = q.find_elements(By.XPATH, ".//div[@role='listbox']")
        print(f"  Số listbox: {len(listboxes)}")
        for j, lb in enumerate(listboxes):
            print(f"    [{j}] text='{lb.text}', class='{lb.get_attribute('class')}'")
        
        # Tìm các button
        print("\n--- Tìm button ---")
        buttons = q.find_elements(By.XPATH, ".//div[@role='button']")
        print(f"  Số button: {len(buttons)}")
        for j, btn in enumerate(buttons[:10]):
            txt = btn.text.strip() if btn.text else ""
            aria = btn.get_attribute('aria-label') or ""
            if txt.isdigit() or "đến" in txt or txt in ["0", "1", "5", "10"]:
                print(f"    [{j}] text='{txt}', aria-label='{aria}'")
        
        # Tìm các dropdown với aria-haspopup
        print("\n--- Tìm dropdown (aria-haspopup) ---")
        dropdowns = q.find_elements(By.XPATH, ".//*[@aria-haspopup='listbox' or @aria-haspopup='true']")
        print(f"  Số dropdown: {len(dropdowns)}")
        for j, dd in enumerate(dropdowns):
            txt = dd.text.strip() if dd.text else ""
            aria = dd.get_attribute('aria-label') or ""
            print(f"    [{j}] text='{txt}', aria-label='{aria}'")
        
        # Tìm các span chứa số
        print("\n--- Tìm span có số ---")
        spans = q.find_elements(By.TAG_NAME, "span")
        numeric_spans = []
        for sp in spans:
            txt = sp.text.strip() if sp.text else ""
            if txt.isdigit():
                numeric_spans.append((txt, sp.get_attribute('class') or ""))
        print(f"  Spans với số: {numeric_spans[:10]}")
        
        # Tìm các input text (labels ở 2 đầu)
        print("\n--- Tìm input text (labels) ---")
        inputs = q.find_elements(By.XPATH, ".//input[@type='text']")
        print(f"  Số input: {len(inputs)}")
        for j, inp in enumerate(inputs):
            val = inp.get_attribute('value') or ""
            aria = inp.get_attribute('aria-label') or ""
            placeholder = inp.get_attribute('placeholder') or ""
            if val or "nhãn" in aria.lower() or "label" in aria.lower():
                print(f"    [{j}] value='{val}', aria='{aria}', placeholder='{placeholder}'")
        
        # Tìm div chứa "1" và "5" (hoặc min/max)
        print("\n--- Tìm div/span với class đặc biệt ---")
        # Các class phổ biến trong linear scale editor
        for cls in ["Od2TWd", "vnumgf", "jDAIHe", "rEjz8e", "MRb9Ab"]:
            elems = q.find_elements(By.CLASS_NAME, cls)
            if elems:
                print(f"  Class '{cls}': {len(elems)} elements")
                for k, el in enumerate(elems[:5]):
                    txt = el.text.strip() if el.text else ""
                    if txt:
                        print(f"    [{k}] text='{txt}'")

print("\n" + "="*80)
print("✅ HOÀN TẤT PHÂN TÍCH")
print("="*80)

input("\n>>> Nhấn Enter để đóng browser... ")
driver.quit()
