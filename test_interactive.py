"""
Interactive Test - Cho phép điều khiển từng câu hỏi
Commands:
  list - Xem danh sách questions
  show 1 - Xem chi tiết question 1
  fill 1 - Điền câu hỏi 1
  fill 1 2 3 - Điền câu 1, 2, 3
  click 2 option_3 - Click vào option 3 của câu 2
  fillall - Điền tất cả
  quit - Thoát
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractiveTester:
    def __init__(self):
        self.driver = None
        self.questions = []
        self.answers = {}
        self.question_elements = []
    
    def start(self):
        """Khởi động"""
        print("="*80)
        print("🎮 INTERACTIVE TEST - ĐIỀU KHIỂN TỪNG CÂU HỎI")
        print("="*80)
        
        # Input URLs
        editor_url = input("\n1️⃣  Editor URL (để extract questions): ").strip()
        if not editor_url:
            print("❌ Cần editor URL!")
            return
        
        viewform_url = input("\n2️⃣  Viewform URL (để fill form): ").strip()
        if not viewform_url:
            print("❌ Cần viewform URL!")
            return
        
        # Start Chrome
        print("\n🌐 Đang khởi động Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options)
        
        # Extract questions
        self._extract_questions(editor_url)
        
        # Open viewform
        print(f"\n📂 Đang mở viewform...")
        self.driver.get(viewform_url)
        time.sleep(3)
        
        # Get question elements
        self.question_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        print(f"✅ Found {len(self.question_elements)} question elements in viewform")
        
        # Interactive loop
        self._interactive_loop()
    
    def _extract_questions(self, editor_url):
        """Extract questions từ editor"""
        print(f"\n📋 Đang extract questions từ editor...")
        self.driver.get(editor_url)
        time.sleep(3)
        
        containers = self.driver.find_elements(By.CSS_SELECTOR, 
            "div[data-params*='FreebirdFormviewerComponentsQuestionBaseRoot']")
        
        if not containers:
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div.Qr7Oae")
        
        print(f"Found {len(containers)} containers")
        
        for idx, container in enumerate(containers):
            try:
                q_data = self._parse_question(container, idx)
                if q_data:
                    self.questions.append(q_data)
            except Exception as e:
                logger.error(f"Parse question {idx} error: {e}")
        
        print(f"✅ Extracted {len(self.questions)} questions")
        
        # Create default answers
        for idx, q in enumerate(self.questions):
            if q['type'] in ['multiple_choice', 'dropdown', 'linear_scale']:
                if q.get('options'):
                    self.answers[idx] = q['options'][0]['text']
            elif q['type'] == 'checkbox':
                if q.get('options'):
                    self.answers[idx] = [q['options'][0]['text']]
            elif q['type'] in ['short_answer', 'long_answer']:
                self.answers[idx] = "Test answer"
    
    def _parse_question(self, container, idx):
        """Parse question data"""
        try:
            # Title
            title_elem = container.find_element(By.CSS_SELECTOR, "div.M7eMe, div[role='heading']")
            title = title_elem.text.strip() if title_elem else f"Question {idx+1}"
            
            # Type
            q_type = self._detect_type(container)
            
            # Options
            options = []
            if q_type in ['multiple_choice', 'dropdown', 'checkbox', 'linear_scale']:
                options = self._extract_options(container, q_type)
            
            return {
                'title': title,
                'type': q_type,
                'options': options
            }
        except Exception as e:
            return None
    
    def _detect_type(self, container):
        """Detect question type"""
        try:
            class_names = container.get_attribute('class') or ""
            
            # Linear scale
            if 'Ht8Grd' in class_names or 'lLfZXe' in class_names:
                return "linear_scale"
            
            # Check radios
            radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
            if radios:
                labels = [r.get_attribute('aria-label') for r in radios[:5]]
                numeric_labels = [l for l in labels if l and l.strip().isdigit()]
                if len(numeric_labels) >= 2:
                    return "linear_scale"
                return "multiple_choice"
            
            # Checkboxes
            if container.find_elements(By.CSS_SELECTOR, "div[role='checkbox']"):
                return "checkbox"
            
            # Text inputs
            if container.find_elements(By.CSS_SELECTOR, "textarea"):
                return "long_answer"
            if container.find_elements(By.CSS_SELECTOR, "input[type='text']"):
                return "short_answer"
            
            return "unknown"
        except:
            return "unknown"
    
    def _extract_options(self, container, q_type):
        """Extract options"""
        options = []
        try:
            if q_type == 'linear_scale':
                # Try data-value
                data_values = container.find_elements(By.CSS_SELECTOR, "div[data-value]")
                for dv in data_values:
                    val = dv.get_attribute('data-value')
                    if val and val.isdigit():
                        options.append({'text': val, 'percentage': 100})
                
                if not options:
                    # Try radios
                    radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                    for radio in radios:
                        label = radio.get_attribute('aria-label')
                        if label and label.strip().isdigit():
                            options.append({'text': label.strip(), 'percentage': 100})
            else:
                elements = container.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox']")
                for elem in elements:
                    label = elem.get_attribute('aria-label')
                    if label:
                        options.append({'text': label, 'percentage': 100})
        except:
            pass
        
        return options
    
    def _interactive_loop(self):
        """Interactive command loop"""
        print("\n" + "="*80)
        print("🎮 INTERACTIVE MODE - Nhập lệnh để điều khiển")
        print("="*80)
        self._show_help()
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0]
                
                if action == 'quit' or action == 'q':
                    break
                
                elif action == 'help' or action == 'h':
                    self._show_help()
                
                elif action == 'list' or action == 'ls':
                    self._list_questions()
                
                elif action == 'show':
                    if len(parts) >= 2:
                        idx = int(parts[1])
                        self._show_question(idx)
                    else:
                        print("❌ Usage: show <question_number>")
                
                elif action == 'fill':
                    if len(parts) >= 2:
                        indices = [int(p) for p in parts[1:]]
                        self._fill_questions(indices)
                    else:
                        print("❌ Usage: fill <question_numbers...>")
                
                elif action == 'fillall':
                    indices = list(range(len(self.questions)))
                    self._fill_questions(indices)
                
                elif action == 'click':
                    if len(parts) >= 3:
                        q_idx = int(parts[1])
                        option_value = parts[2]
                        self._click_option(q_idx, option_value)
                    else:
                        print("❌ Usage: click <question_number> <option_value>")
                
                elif action == 'set':
                    if len(parts) >= 3:
                        q_idx = int(parts[1])
                        value = ' '.join(parts[2:])
                        self._set_answer(q_idx, value)
                    else:
                        print("❌ Usage: set <question_number> <value>")
                
                else:
                    print(f"❌ Unknown command: {action}")
                    print("   Type 'help' to see available commands")
            
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    def _show_help(self):
        """Show help"""
        print("""
📖 Available Commands:
  list, ls              - Xem danh sách tất cả questions
  show <n>              - Xem chi tiết question số n
  fill <n> [m] [k]      - Điền câu hỏi số n, m, k
  fillall               - Điền tất cả câu hỏi
  click <n> <value>     - Click option <value> của câu <n>
  set <n> <value>       - Đặt answer cho câu <n>
  help, h               - Hiển thị help
  quit, q               - Thoát

📝 Examples:
  list                  - Xem tất cả questions
  show 0                - Xem chi tiết câu 0
  fill 0                - Điền câu 0
  fill 0 1 2            - Điền câu 0, 1, 2
  click 0 3             - Click option "3" của câu 0 (linear scale)
  set 0 "Hello"         - Đặt answer "Hello" cho câu 0
  fillall               - Điền tất cả
        """)
    
    def _list_questions(self):
        """List all questions"""
        print("\n" + "="*80)
        print("📋 DANH SÁCH QUESTIONS:")
        print("="*80)
        
        for idx, q in enumerate(self.questions):
            answer = self.answers.get(idx, "(no answer)")
            print(f"\n[{idx}] {q['type'].upper()}")
            print(f"    Title: {q['title'][:60]}...")
            print(f"    Answer: {answer}")
            
            if q.get('options'):
                opts_preview = [o['text'] for o in q['options'][:5]]
                print(f"    Options: {opts_preview}")
    
    def _show_question(self, idx):
        """Show question details"""
        if idx < 0 or idx >= len(self.questions):
            print(f"❌ Question {idx} không tồn tại! (có 0-{len(self.questions)-1})")
            return
        
        q = self.questions[idx]
        answer = self.answers.get(idx, "(no answer)")
        
        print("\n" + "="*80)
        print(f"📝 QUESTION [{idx}]:")
        print("="*80)
        print(f"\nType: {q['type']}")
        print(f"Title: {q['title']}")
        print(f"Current Answer: {answer}")
        
        if q.get('options'):
            print(f"\nOptions ({len(q['options'])}):")
            for i, opt in enumerate(q['options']):
                print(f"  [{i}] {opt['text']}")
    
    def _set_answer(self, idx, value):
        """Set answer for question"""
        if idx < 0 or idx >= len(self.questions):
            print(f"❌ Question {idx} không tồn tại!")
            return
        
        self.answers[idx] = value
        print(f"✅ Set answer for Q{idx}: {value}")
    
    def _fill_questions(self, indices):
        """Fill multiple questions"""
        print(f"\n📝 Đang fill {len(indices)} questions...")
        
        success = 0
        failed = 0
        
        for idx in indices:
            if idx < 0 or idx >= len(self.questions):
                print(f"\n[{idx}] ❌ Không tồn tại!")
                failed += 1
                continue
            
            q = self.questions[idx]
            answer = self.answers.get(idx)
            
            print(f"\n[{idx}] {q['type']}: {q['title'][:50]}...")
            print(f"      Answer: {answer}")
            
            try:
                if idx >= len(self.question_elements):
                    print(f"      ❌ Không tìm thấy element!")
                    failed += 1
                    continue
                
                q_elem = self.question_elements[idx]
                
                if q['type'] == 'linear_scale':
                    if self._fill_linear_scale(q_elem, str(answer)):
                        print(f"      ✅ Filled")
                        success += 1
                    else:
                        print(f"      ❌ Failed")
                        failed += 1
                
                elif q['type'] in ['multiple_choice', 'dropdown']:
                    if self._fill_option(q_elem, str(answer)):
                        print(f"      ✅ Filled")
                        success += 1
                    else:
                        print(f"      ❌ Failed")
                        failed += 1
                
                elif q['type'] in ['short_answer', 'long_answer']:
                    if self._fill_text(q_elem, str(answer)):
                        print(f"      ✅ Filled")
                        success += 1
                    else:
                        print(f"      ❌ Failed")
                        failed += 1
                
                time.sleep(0.3)
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                failed += 1
        
        print(f"\n📊 Kết quả: ✅ {success} thành công | ❌ {failed} thất bại")
    
    def _click_option(self, q_idx, option_value):
        """Click specific option"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        if q_idx >= len(self.question_elements):
            print(f"❌ Không tìm thấy element!")
            return
        
        q = self.questions[q_idx]
        q_elem = self.question_elements[q_idx]
        
        print(f"\n🖱️  Đang click option '{option_value}' của Q{q_idx}...")
        
        try:
            if q['type'] == 'linear_scale':
                selectors = [
                    f"div[data-value='{option_value}']",
                    f"div.Od2TWd[data-value='{option_value}']",
                    f"div[role='radio'][data-value='{option_value}']",
                    f"div[role='radio'][aria-label='{option_value}']"
                ]
                
                for selector in selectors:
                    options = q_elem.find_elements(By.CSS_SELECTOR, selector)
                    if options:
                        print(f"   Found with selector: {selector}")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", options[0])
                        time.sleep(0.3)
                        options[0].click()
                        print(f"   ✅ Clicked!")
                        return
                
                print(f"   ❌ Không tìm thấy option '{option_value}'")
            
            else:
                options = q_elem.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox']")
                for opt in options:
                    label = opt.get_attribute('aria-label')
                    if label and option_value.lower() in label.lower():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", opt)
                        time.sleep(0.3)
                        opt.click()
                        print(f"   ✅ Clicked '{label}'")
                        return
                
                print(f"   ❌ Không tìm thấy option chứa '{option_value}'")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def _fill_linear_scale(self, q_elem, value):
        """Fill linear scale"""
        try:
            selectors = [
                f"div[data-value='{value}']",
                f"div.Od2TWd[data-value='{value}']",
                f"div[role='radio'][data-value='{value}']",
                f"div[role='radio'][aria-label='{value}']"
            ]
            
            for selector in selectors:
                options = q_elem.find_elements(By.CSS_SELECTOR, selector)
                if options:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", options[0])
                    time.sleep(0.2)
                    options[0].click()
                    return True
            
            return False
        except:
            return False
    
    def _fill_option(self, q_elem, option_text):
        """Fill option"""
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
        except:
            return False
    
    def _fill_text(self, q_elem, text):
        """Fill text"""
        try:
            inputs = q_elem.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
            if inputs:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", inputs[0])
                time.sleep(0.2)
                inputs[0].clear()
                inputs[0].send_keys(text)
                return True
            return False
        except:
            return False
    
    def close(self):
        """Close"""
        if self.driver:
            print("\n👋 Đóng Chrome...")
            self.driver.quit()
            print("🔚 Đã đóng")


def main():
    tester = InteractiveTester()
    try:
        tester.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.close()


if __name__ == "__main__":
    main()
