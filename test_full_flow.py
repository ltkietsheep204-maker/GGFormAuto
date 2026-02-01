"""
Test FULL FLOW - Giống như tool thực tế:
1. Extract từ editor link
2. Hiển thị questions được extract
3. Fill vào viewform link
4. Kiểm tra kết quả
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormTester:
    def __init__(self):
        self.driver = None
        self.questions = []
        self.answers = {}
    
    def start_chrome(self):
        """Khởi động Chrome"""
        print("\n🌐 Đang khởi động Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        print("✅ Chrome started")
    
    def extract_questions(self, editor_url):
        """Extract questions từ editor link"""
        print("\n" + "="*80)
        print("📋 BƯỚC 1: EXTRACT QUESTIONS TỪ EDITOR")
        print("="*80)
        
        print(f"\n📂 Đang mở editor: {editor_url}")
        self.driver.get(editor_url)
        time.sleep(3)
        
        # Tìm question containers
        print("\n🔍 Đang tìm question containers...")
        
        selectors = [
            "div[data-params*='FreebirdFormviewerComponentsQuestionBaseRoot']",
            "div.freebirdFormviewerComponentsQuestionBaseRoot",
            "div.Qr7Oae"
        ]
        
        all_containers = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  ✓ Found {len(elements)} with '{selector}'")
                    all_containers.extend(elements)
            except:
                pass
        
        print(f"\n📊 Total containers: {len(all_containers)}")
        
        # Extract từng question
        for idx, container in enumerate(all_containers):
            try:
                question_data = self._extract_question(container, idx)
                if question_data:
                    self.questions.append(question_data)
                    print(f"\n[{idx}] Type: {question_data['type']}")
                    print(f"    Title: {question_data['title'][:80]}")
                    print(f"    Options: {len(question_data.get('options', []))} options")
                    
                    if question_data['type'] == 'linear_scale':
                        print(f"    ✅ LINEAR SCALE: {question_data.get('options', [])}")
            except Exception as e:
                print(f"[{idx}] Error: {e}")
        
        print(f"\n✅ Extracted {len(self.questions)} questions")
        
        # Tạo dummy answers (chọn option đầu tiên cho mỗi câu)
        for idx, q in enumerate(self.questions):
            if q['type'] in ['multiple_choice', 'dropdown', 'linear_scale']:
                if q.get('options'):
                    self.answers[idx] = q['options'][0]['text']
            elif q['type'] == 'checkbox':
                if q.get('options'):
                    self.answers[idx] = [q['options'][0]['text']]
            elif q['type'] in ['short_answer', 'long_answer']:
                self.answers[idx] = "Test answer"
        
        print(f"\n✅ Created {len(self.answers)} dummy answers")
        
        return self.questions
    
    def _extract_question(self, container, idx):
        """Extract một question"""
        try:
            # Get title
            title_elem = container.find_element(By.CSS_SELECTOR, "div.M7eMe, div[role='heading']")
            title = title_elem.text.strip() if title_elem else f"Question {idx+1}"
            
            # Detect type
            q_type = self._detect_question_type(container)
            
            # Get options
            options = []
            if q_type in ['multiple_choice', 'dropdown', 'checkbox', 'linear_scale']:
                options = self._extract_options(container, q_type)
            
            return {
                'title': title,
                'type': q_type,
                'options': options,
                'required': False
            }
        except Exception as e:
            logger.error(f"Extract question error: {e}")
            return None
    
    def _detect_question_type(self, container):
        """Phát hiện loại câu hỏi"""
        try:
            # Check for linear scale FIRST
            class_names = container.get_attribute('class') or ""
            
            # Method 1: Class check
            if 'Ht8Grd' in class_names or 'lLfZXe' in class_names:
                return "linear_scale"
            
            # Method 2: Check for numbered radio buttons
            try:
                radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                if radios and len(radios) >= 2:
                    labels = [r.get_attribute('aria-label') for r in radios[:10]]
                    numeric_labels = [l for l in labels if l and l.strip().isdigit()]
                    
                    if len(numeric_labels) >= 2:
                        # Check if consecutive numbers
                        nums = sorted([int(l) for l in numeric_labels])
                        if len(nums) >= 2 and nums[-1] - nums[0] == len(nums) - 1:
                            return "linear_scale"
            except:
                pass
            
            # Check for other types
            if container.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea"):
                if container.find_elements(By.CSS_SELECTOR, "textarea"):
                    return "long_answer"
                return "short_answer"
            
            if container.find_elements(By.CSS_SELECTOR, "div[role='checkbox']"):
                return "checkbox"
            
            if container.find_elements(By.CSS_SELECTOR, "div[role='radio']"):
                return "multiple_choice"
            
            return "unknown"
            
        except Exception as e:
            return "unknown"
    
    def _extract_options(self, container, q_type):
        """Extract options"""
        options = []
        try:
            if q_type == 'linear_scale':
                # Try data-value first
                data_values = container.find_elements(By.CSS_SELECTOR, "div[data-value]")
                if data_values:
                    for dv in data_values:
                        val = dv.get_attribute('data-value')
                        if val and val.isdigit():
                            options.append({'text': val, 'percentage': 100})
                    return options
                
                # Try radio buttons
                radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                for radio in radios:
                    label = radio.get_attribute('aria-label')
                    if label and label.strip().isdigit():
                        options.append({'text': label.strip(), 'percentage': 100})
                
            else:
                # Other types
                elements = container.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox']")
                for elem in elements:
                    label = elem.get_attribute('aria-label')
                    if label:
                        options.append({'text': label, 'percentage': 100})
        
        except Exception as e:
            logger.error(f"Extract options error: {e}")
        
        return options
    
    def fill_form(self, viewform_url):
        """Fill form vào viewform"""
        print("\n" + "="*80)
        print("✏️  BƯỚC 2: FILL FORM VÀO VIEWFORM")
        print("="*80)
        
        print(f"\n📂 Đang mở viewform: {viewform_url}")
        self.driver.get(viewform_url)
        time.sleep(3)
        
        # Tìm question elements
        print("\n🔍 Đang tìm question elements...")
        question_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        print(f"  Found {len(question_elements)} question elements")
        
        # Fill từng câu
        filled_count = 0
        failed_questions = []
        
        for idx, answer in self.answers.items():
            if idx >= len(question_elements):
                print(f"\n[{idx}] ⚠️  Không tìm thấy element (chỉ có {len(question_elements)} elements)")
                continue
            
            q_elem = question_elements[idx]
            q_data = self.questions[idx]
            
            print(f"\n[{idx}] {q_data['type']}: {q_data['title'][:50]}...")
            print(f"      Answer: {answer}")
            
            try:
                if q_data['type'] == 'linear_scale':
                    success = self._fill_linear_scale(q_elem, str(answer))
                    if success:
                        filled_count += 1
                        print(f"      ✅ Filled")
                    else:
                        failed_questions.append({'idx': idx, 'type': q_data['type'], 'title': q_data['title']})
                        print(f"      ❌ Failed")
                
                elif q_data['type'] in ['multiple_choice', 'dropdown']:
                    success = self._fill_option(q_elem, str(answer))
                    if success:
                        filled_count += 1
                        print(f"      ✅ Filled")
                    else:
                        failed_questions.append({'idx': idx, 'type': q_data['type'], 'title': q_data['title']})
                        print(f"      ❌ Failed")
                
                elif q_data['type'] in ['short_answer', 'long_answer']:
                    success = self._fill_text(q_elem, str(answer))
                    if success:
                        filled_count += 1
                        print(f"      ✅ Filled")
                    else:
                        failed_questions.append({'idx': idx, 'type': q_data['type'], 'title': q_data['title']})
                        print(f"      ❌ Failed")
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                failed_questions.append({'idx': idx, 'type': q_data['type'], 'title': q_data['title'], 'error': str(e)})
        
        # Báo cáo kết quả
        print("\n" + "="*80)
        print("📊 KẾT QUẢ FILL FORM:")
        print("="*80)
        print(f"\n✅ Đã fill: {filled_count}/{len(self.answers)} câu")
        print(f"❌ Thất bại: {len(failed_questions)} câu")
        
        if failed_questions:
            print("\n❌ CÁC CÂU HỎI THẤT BẠI:")
            for fq in failed_questions:
                print(f"\n  [{fq['idx']}] {fq['type']}")
                print(f"       {fq['title'][:60]}...")
                if 'error' in fq:
                    print(f"       Error: {fq['error']}")
        
        return filled_count, failed_questions
    
    def _fill_linear_scale(self, q_elem, value):
        """Fill linear scale question"""
        try:
            # Method 1: data-value selector
            selectors = [
                f"div[data-value='{value}']",
                f"div.Od2TWd[data-value='{value}']",
                f"div[role='radio'][data-value='{value}']",
                f"div[role='radio'][aria-label='{value}']"
            ]
            
            for selector in selectors:
                try:
                    options = q_elem.find_elements(By.CSS_SELECTOR, selector)
                    if options:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", options[0])
                        time.sleep(0.2)
                        options[0].click()
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Fill linear scale error: {e}")
            return False
    
    def _fill_option(self, q_elem, option_text):
        """Fill multiple choice / dropdown"""
        try:
            options = q_elem.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            for opt in options:
                label = opt.get_attribute('aria-label')
                if label and label.strip() == option_text.strip():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", opt)
                    time.sleep(0.2)
                    opt.click()
                    return True
            return False
        except Exception as e:
            logger.error(f"Fill option error: {e}")
            return False
    
    def _fill_text(self, q_elem, text):
        """Fill text field"""
        try:
            inputs = q_elem.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
            if inputs:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", inputs[0])
                time.sleep(0.2)
                inputs[0].clear()
                inputs[0].send_keys(text)
                return True
            return False
        except Exception as e:
            logger.error(f"Fill text error: {e}")
            return False
    
    def close(self):
        """Đóng browser"""
        if self.driver:
            print("\n⏸️  Browser sẽ GIỮ MỞ để bạn kiểm tra.")
            print("   Nhấn Enter để đóng...")
            input()
            self.driver.quit()
            print("🔚 Đã đóng Chrome")


def main():
    print("="*80)
    print("🧪 TEST FULL FLOW - GIỐNG TOOL THỰC TẾ")
    print("="*80)
    
    # Nhập URLs
    print("\n📝 Nhập thông tin form:")
    editor_url = input("\n1️⃣  Editor URL (link /edit): ").strip()
    if not editor_url:
        print("❌ Không có editor URL!")
        return
    
    viewform_url = input("\n2️⃣  Viewform URL (link /viewform): ").strip()
    if not viewform_url:
        print("❌ Không có viewform URL!")
        return
    
    # Run test
    tester = FormTester()
    
    try:
        tester.start_chrome()
        
        # Extract
        questions = tester.extract_questions(editor_url)
        
        if not questions:
            print("\n❌ Không extract được câu hỏi nào!")
            return
        
        # Fill
        filled, failed = tester.fill_form(viewform_url)
        
        # Summary
        print("\n" + "="*80)
        print("✅ TEST HOÀN TẤT!")
        print("="*80)
        print(f"\n📊 Tổng kết:")
        print(f"   - Questions extracted: {len(questions)}")
        print(f"   - Questions filled: {filled}")
        print(f"   - Questions failed: {len(failed)}")
        print(f"   - Success rate: {filled}/{len(questions)} ({filled*100//max(len(questions),1)}%)")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tester.close()


if __name__ == "__main__":
    main()
