"""
🔍 DEBUG: So sánh câu hỏi click được vs không click được
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def debug_viewform():
    print("🌐 Khởi động Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    print("\n📝 Nhập VIEWFORM URL (link /viewform):")
    url = input("URL: ").strip()
    
    if not url:
        print("❌ Cần URL!")
        driver.quit()
        return
    
    # Convert edit to viewform if needed
    if '/edit' in url:
        url = url.replace('/edit', '/viewform')
        print(f"⚠️  Đã convert sang viewform: {url}")
    
    print(f"\n📂 Mở form: {url}")
    driver.get(url)
    time.sleep(3)
    
    page = 1
    total_questions = 0
    linear_questions = []
    other_questions = []
    
    while True:
        print(f"\n{'='*80}")
        print(f"📄 PAGE {page}")
        print(f"{'='*80}")
        
        # Tìm question containers
        containers = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        print(f"Found {len(containers)} question containers")
        
        for idx, container in enumerate(containers):
            global_idx = total_questions + idx
            
            try:
                # Get title
                try:
                    title = container.find_element(By.CSS_SELECTOR, "div.M7eMe, span.M7eMe").text[:60]
                except:
                    title = "(no title)"
                
                # Check type
                data_values = container.find_elements(By.CSS_SELECTOR, "div[data-value]")
                radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                checkboxes = container.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
                text_inputs = container.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
                
                # Detect if linear scale
                is_linear = False
                if radios:
                    labels = [r.get_attribute('aria-label') for r in radios]
                    numeric = [l for l in labels if l and l.strip().isdigit()]
                    if len(numeric) >= 3:
                        is_linear = True
                
                q_type = "unknown"
                if is_linear:
                    q_type = "LINEAR_SCALE"
                elif len(radios) > 0:
                    q_type = "multiple_choice"
                elif len(checkboxes) > 0:
                    q_type = "checkbox"
                elif len(text_inputs) > 0:
                    q_type = "text"
                
                q_info = {
                    'idx': global_idx,
                    'title': title,
                    'type': q_type,
                    'element': container,
                    'data_values': len(data_values),
                    'radios': len(radios),
                    'page': page
                }
                
                if is_linear:
                    linear_questions.append(q_info)
                else:
                    other_questions.append(q_info)
                
                print(f"\n[Q{global_idx}] {q_type}")
                print(f"    Title: {title}")
                print(f"    data-value: {len(data_values)} | radios: {len(radios)} | checkboxes: {len(checkboxes)}")
                
            except Exception as e:
                print(f"[Q{global_idx}] Error: {e}")
        
        total_questions += len(containers)
        
        # Check for next button
        next_btn = None
        for xpath in [
            "//span[contains(text(),'Tiếp')]/ancestor::div[@role='button']",
            "//span[contains(text(),'Next')]/ancestor::div[@role='button']",
            "//div[@role='button' and contains(.,'Tiếp')]"
        ]:
            btns = driver.find_elements(By.XPATH, xpath)
            if btns:
                next_btn = btns[0]
                break
        
        if next_btn:
            print(f"\n⏭️  Tìm thấy nút Tiếp - chuyển trang...")
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(0.5)
            next_btn.click()
            time.sleep(2)
            page += 1
        else:
            print(f"\n✓ Không còn nút Tiếp - đây là trang cuối")
            break
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY")
    print(f"{'='*80}")
    print(f"Total questions: {total_questions}")
    print(f"Linear scale: {len(linear_questions)}")
    print(f"Other types: {len(other_questions)}")
    
    # Test LINEAR SCALE questions
    if linear_questions:
        print(f"\n{'='*80}")
        print(f"🧪 TEST LINEAR SCALE QUESTIONS")
        print(f"{'='*80}")
        
        for q in linear_questions:
            print(f"\n[Q{q['idx']}] {q['title']}")
            print(f"    Page: {q['page']}")
            
            elem = q['element']
            
            # Scroll to element
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                time.sleep(0.3)
            except:
                print(f"    ⚠️  Element may be stale (on different page)")
                continue
            
            # Tìm options
            print(f"\n    🔍 Tìm kiếm clickable options:")
            
            # Method 1: div[data-value]
            dv_elems = elem.find_elements(By.CSS_SELECTOR, "div[data-value]")
            print(f"    Method 1 (div[data-value]): {len(dv_elems)} elements")
            
            for i, dv in enumerate(dv_elems[:5]):
                val = dv.get_attribute('data-value')
                aria = dv.get_attribute('aria-label')
                checked = dv.get_attribute('aria-checked')
                displayed = dv.is_displayed()
                print(f"      [{i}] value='{val}' aria='{aria}' checked={checked} visible={displayed}")
            
            # Method 2: div[role='radio']
            radios = elem.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            print(f"\n    Method 2 (div[role='radio']): {len(radios)} elements")
            
            for i, r in enumerate(radios[:5]):
                val = r.get_attribute('data-value')
                aria = r.get_attribute('aria-label')
                checked = r.get_attribute('aria-checked')
                displayed = r.is_displayed()
                print(f"      [{i}] value='{val}' aria='{aria}' checked={checked} visible={displayed}")
            
            # TRY CLICK
            print(f"\n    🖱️  TEST CLICK:")
            
            clicked = False
            
            # Try clicking value "3"
            for selector in [
                "div[data-value='3']",
                "div.Od2TWd[data-value='3']",
                "div[role='radio'][data-value='3']",
                "div[role='radio'][aria-label='3']"
            ]:
                try:
                    targets = elem.find_elements(By.CSS_SELECTOR, selector)
                    if targets:
                        target = targets[0]
                        before = target.get_attribute('aria-checked')
                        
                        # Highlight
                        driver.execute_script("""
                            arguments[0].style.outline = '3px solid red';
                        """, target)
                        
                        # Click
                        target.click()
                        time.sleep(0.3)
                        
                        after = target.get_attribute('aria-checked')
                        
                        if after == 'true':
                            print(f"      ✅ SUCCESS with '{selector}'")
                            print(f"         before={before} → after={after}")
                            clicked = True
                            break
                        else:
                            print(f"      ⚠️  '{selector}' - clicked but not selected (before={before}, after={after})")
                except Exception as e:
                    print(f"      ❌ '{selector}' failed: {e}")
            
            if not clicked:
                print(f"\n    ❌ KHÔNG THỂ CLICK! Kiểm tra HTML:")
                
                # Show HTML snippet
                try:
                    inner = elem.get_attribute('innerHTML')[:500]
                    print(f"    HTML: {inner}...")
                except:
                    pass
    
    # Test một câu hỏi OTHER (multiple choice hoặc checkbox) để so sánh
    if other_questions:
        print(f"\n{'='*80}")
        print(f"🧪 TEST OTHER QUESTION (để so sánh)")
        print(f"{'='*80}")
        
        # Tìm một multiple choice để test
        mc = [q for q in other_questions if q['type'] == 'multiple_choice']
        if mc:
            q = mc[0]
            print(f"\n[Q{q['idx']}] {q['title']}")
            
            elem = q['element']
            
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                time.sleep(0.3)
                
                radios = elem.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                if radios:
                    target = radios[0]
                    aria = target.get_attribute('aria-label')
                    before = target.get_attribute('aria-checked')
                    
                    target.click()
                    time.sleep(0.3)
                    
                    after = target.get_attribute('aria-checked')
                    
                    if after == 'true':
                        print(f"    ✅ Multiple choice click SUCCESS!")
                        print(f"    Clicked option: '{aria}'")
                    else:
                        print(f"    ⚠️  Click executed but not selected")
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print(f"📋 KẾT LUẬN")
    print(f"{'='*80}")
    
    if linear_questions:
        print("\n🔴 LINEAR SCALE ISSUES:")
        print("   - Các câu hỏi linear scale có thể nằm ở trang KHÁC")
        print("   - Khi chuyển trang, element bị 'stale' (không còn valid)")
        print("   - Tool cần điền NGAY khi ở trang đó, không lưu element để dùng sau")
    
    print("\n⏸️  Chrome giữ mở. Nhấn Enter để đóng...")
    input()
    driver.quit()

if __name__ == "__main__":
    debug_viewform()
