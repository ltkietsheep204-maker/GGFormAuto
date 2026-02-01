"""
🔍 TERMINAL DEBUG TOOL - Scan & Click bất kỳ câu hỏi nào
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import sys

class TerminalDebugger:
    def __init__(self):
        self.driver = None
        self.questions = []  # List of {element, title, type, options}
    
    def start(self, url):
        """Khởi động với URL"""
        print("\n🌐 Đang khởi động Chrome...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        print(f"📂 Đang mở: {url}")
        self.driver.get(url)
        time.sleep(3)
        
        print("✅ Chrome ready!")
        self.scan()
        self.interactive()
    
    def scan(self):
        """Scan tất cả questions và options"""
        print("\n" + "="*80)
        print("🔍 SCANNING PAGE...")
        print("="*80)
        
        self.questions = []
        
        # Tìm tất cả question containers
        containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        
        if not containers:
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div.Qr7Oae")
        
        print(f"\n📊 Found {len(containers)} question containers")
        
        for idx, container in enumerate(containers):
            try:
                q_data = self._analyze_question(container, idx)
                self.questions.append(q_data)
            except Exception as e:
                self.questions.append({
                    'idx': idx,
                    'element': container,
                    'title': f"(Error: {e})",
                    'type': 'error',
                    'options': []
                })
        
        # Hiển thị kết quả
        self._show_summary()
    
    def _analyze_question(self, container, idx):
        """Phân tích chi tiết một question"""
        q_data = {
            'idx': idx,
            'element': container,
            'title': '',
            'type': 'unknown',
            'options': [],
            'html_classes': container.get_attribute('class')
        }
        
        # Lấy title
        try:
            title_elem = container.find_element(By.CSS_SELECTOR, "div.M7eMe, div[role='heading'], span.M7eMe")
            q_data['title'] = title_elem.text.strip()[:80] if title_elem.text else "(no title)"
        except:
            q_data['title'] = container.text[:50] if container.text else "(no text)"
        
        # Tìm tất cả clickable options
        options = []
        
        # Method 1: div[data-value] (linear scale)
        data_values = container.find_elements(By.CSS_SELECTOR, "div[data-value]")
        for dv in data_values:
            val = dv.get_attribute('data-value')
            aria = dv.get_attribute('aria-label')
            if val:
                options.append({
                    'element': dv,
                    'type': 'data-value',
                    'value': val,
                    'aria-label': aria,
                    'selector': f"div[data-value='{val}']"
                })
        
        # Method 2: div[role='radio']
        radios = container.find_elements(By.CSS_SELECTOR, "div[role='radio']")
        for radio in radios:
            aria = radio.get_attribute('aria-label')
            dv = radio.get_attribute('data-value')
            # Chỉ thêm nếu chưa có trong data-value
            if not any(o['element'] == radio for o in options):
                options.append({
                    'element': radio,
                    'type': 'radio',
                    'value': dv or aria or '?',
                    'aria-label': aria,
                    'selector': f"div[role='radio'][aria-label='{aria}']" if aria else "div[role='radio']"
                })
        
        # Method 3: div[role='checkbox']
        checkboxes = container.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
        for cb in checkboxes:
            aria = cb.get_attribute('aria-label')
            options.append({
                'element': cb,
                'type': 'checkbox',
                'value': aria or '?',
                'aria-label': aria,
                'selector': f"div[role='checkbox'][aria-label='{aria}']" if aria else "div[role='checkbox']"
            })
        
        # Method 4: input[type='text'], textarea
        text_inputs = container.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        for ti in text_inputs:
            options.append({
                'element': ti,
                'type': 'text-input',
                'value': '(text field)',
                'aria-label': ti.get_attribute('aria-label'),
                'selector': 'input' if ti.tag_name == 'input' else 'textarea'
            })
        
        q_data['options'] = options
        
        # Detect type
        if any(o['type'] == 'data-value' for o in options):
            # Check if numeric (linear scale)
            numeric_options = [o for o in options if o['type'] == 'data-value' and o['value'].isdigit()]
            if len(numeric_options) >= 2:
                q_data['type'] = 'linear_scale'
            else:
                q_data['type'] = 'multiple_choice'
        elif any(o['type'] == 'radio' for o in options):
            # Check if all numeric
            radio_opts = [o for o in options if o['type'] == 'radio']
            numeric_radios = [o for o in radio_opts if o['aria-label'] and o['aria-label'].strip().isdigit()]
            if len(numeric_radios) >= 2:
                q_data['type'] = 'linear_scale'
            else:
                q_data['type'] = 'multiple_choice'
        elif any(o['type'] == 'checkbox' for o in options):
            q_data['type'] = 'checkbox'
        elif any(o['type'] == 'text-input' for o in options):
            q_data['type'] = 'text_input'
        
        return q_data
    
    def _show_summary(self):
        """Hiển thị summary"""
        print("\n" + "="*80)
        print("📋 QUESTIONS SUMMARY:")
        print("="*80)
        
        type_count = {}
        
        for q in self.questions:
            t = q['type']
            type_count[t] = type_count.get(t, 0) + 1
            
            print(f"\n[Q{q['idx']}] {q['type'].upper()}")
            print(f"    Title: {q['title']}")
            print(f"    Options: {len(q['options'])} clickable elements")
            
            for i, opt in enumerate(q['options'][:5]):
                checked = opt['element'].get_attribute('aria-checked')
                status = " ✓" if checked == 'true' else ""
                print(f"      [{i}] {opt['type']}: {opt['value']}{status}")
            
            if len(q['options']) > 5:
                print(f"      ... và {len(q['options'])-5} options khác")
        
        print("\n📊 Statistics:")
        for t, c in type_count.items():
            print(f"   {t}: {c}")
    
    def interactive(self):
        """Interactive mode"""
        print("\n" + "="*80)
        print("🎮 INTERACTIVE DEBUG MODE")
        print("="*80)
        self._show_help()
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0].lower()
                
                if action in ['quit', 'q', 'exit']:
                    break
                
                elif action in ['help', 'h', '?']:
                    self._show_help()
                
                elif action in ['scan', 'refresh', 'r']:
                    self.scan()
                
                elif action in ['list', 'ls', 'l']:
                    self._list_all()
                
                elif action in ['show', 's']:
                    if len(parts) >= 2:
                        self._show_question(int(parts[1]))
                    else:
                        print("❌ Usage: show <question_number>")
                
                elif action in ['click', 'c']:
                    if len(parts) >= 3:
                        q_idx = int(parts[1])
                        opt_idx = int(parts[2])
                        self._click_option(q_idx, opt_idx)
                    elif len(parts) == 2:
                        # click Q.O format
                        if '.' in parts[1]:
                            q_idx, opt_idx = parts[1].split('.')
                            self._click_option(int(q_idx), int(opt_idx))
                        else:
                            print("❌ Usage: click <q> <opt> or click <q.opt>")
                    else:
                        print("❌ Usage: click <q> <opt> or click <q.opt>")
                
                elif action in ['type', 't']:
                    if len(parts) >= 3:
                        q_idx = int(parts[1])
                        text = ' '.join(parts[2:])
                        self._type_text(q_idx, text)
                    else:
                        print("❌ Usage: type <question_number> <text>")
                
                elif action in ['debug', 'd']:
                    if len(parts) >= 2:
                        self._debug_question(int(parts[1]))
                    else:
                        print("❌ Usage: debug <question_number>")
                
                elif action in ['scroll', 'goto']:
                    if len(parts) >= 2:
                        self._scroll_to(int(parts[1]))
                    else:
                        print("❌ Usage: scroll <question_number>")
                
                elif action in ['html']:
                    if len(parts) >= 2:
                        self._show_html(int(parts[1]))
                    else:
                        print("❌ Usage: html <question_number>")
                
                elif action in ['test']:
                    self._test_all_linear()
                
                else:
                    print(f"❌ Unknown command: {action}")
                    print("   Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n⚠️  Ctrl+C detected")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        self.close()
    
    def _show_help(self):
        """Show help"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    📖 AVAILABLE COMMANDS                          ║
╠══════════════════════════════════════════════════════════════════╣
║  scan, r          - Scan lại toàn bộ page                        ║
║  list, ls         - Xem danh sách tất cả questions               ║
║  show <n>         - Xem chi tiết question n                      ║
║  click <q> <opt>  - Click option <opt> của question <q>          ║
║  click <q.opt>    - Hoặc format: click 0.2 (Q0, option 2)        ║
║  type <q> <text>  - Nhập text vào question <q>                   ║
║  scroll <n>       - Scroll đến question <n>                      ║
║  debug <n>        - Debug chi tiết question <n> (HTML info)      ║
║  html <n>         - Xem HTML của question <n>                    ║
║  test             - Test click tất cả linear scale questions     ║
║  help, h          - Hiển thị help này                            ║
║  quit, q          - Thoát                                        ║
╚══════════════════════════════════════════════════════════════════╝

📝 Examples:
  > list                    Xem tất cả questions  
  > show 0                  Xem chi tiết question 0
  > click 0 2               Click option 2 của question 0
  > click 5.3               Click option 3 của question 5
  > type 1 "Hello World"    Nhập "Hello World" vào question 1
  > debug 0                 Xem debug info của question 0
  > test                    Test tất cả linear scale
        """)
    
    def _list_all(self):
        """List all questions"""
        print("\n📋 ALL QUESTIONS:")
        print("-"*80)
        
        for q in self.questions:
            status = ""
            # Check if any option is checked
            for opt in q['options']:
                try:
                    if opt['element'].get_attribute('aria-checked') == 'true':
                        status = " ✅"
                        break
                except:
                    pass
            
            opts_preview = [o['value'] for o in q['options'][:4]]
            print(f"[Q{q['idx']}] {q['type']:15} | {q['title'][:40]:40} | opts: {opts_preview}{status}")
    
    def _show_question(self, idx):
        """Show question details"""
        if idx < 0 or idx >= len(self.questions):
            print(f"❌ Question {idx} không tồn tại! (có Q0 - Q{len(self.questions)-1})")
            return
        
        q = self.questions[idx]
        
        print("\n" + "="*80)
        print(f"📝 QUESTION [{idx}] - {q['type'].upper()}")
        print("="*80)
        print(f"\nTitle: {q['title']}")
        print(f"Type: {q['type']}")
        print(f"Classes: {q['html_classes'][:60]}..." if q.get('html_classes') else "Classes: N/A")
        
        print(f"\n🎯 Clickable Options ({len(q['options'])}):")
        for i, opt in enumerate(q['options']):
            try:
                checked = opt['element'].get_attribute('aria-checked')
                displayed = opt['element'].is_displayed()
                status = ""
                if checked == 'true':
                    status += " ✅ SELECTED"
                if not displayed:
                    status += " 🔲 HIDDEN"
            except:
                status = " ⚠️ STALE"
            
            print(f"  [{i}] {opt['type']:12} | value: {str(opt['value'])[:20]:20} | aria: {str(opt.get('aria-label', ''))[:20]}{status}")
    
    def _click_option(self, q_idx, opt_idx):
        """Click specific option"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        q = self.questions[q_idx]
        
        if opt_idx < 0 or opt_idx >= len(q['options']):
            print(f"❌ Option {opt_idx} không tồn tại! (có 0-{len(q['options'])-1})")
            return
        
        opt = q['options'][opt_idx]
        
        print(f"\n🖱️  Clicking Q{q_idx} option [{opt_idx}]...")
        print(f"    Type: {opt['type']}")
        print(f"    Value: {opt['value']}")
        print(f"    Selector: {opt['selector']}")
        
        try:
            elem = opt['element']
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(0.3)
            
            # Highlight element (for visual feedback)
            self.driver.execute_script("""
                arguments[0].style.outline = '3px solid red';
                setTimeout(() => { arguments[0].style.outline = ''; }, 1000);
            """, elem)
            
            # Check before click
            checked_before = elem.get_attribute('aria-checked')
            print(f"    Before click: aria-checked = {checked_before}")
            
            # Try click
            try:
                elem.click()
                print(f"    ✅ Standard click successful!")
            except:
                # Fallback to JS click
                self.driver.execute_script("arguments[0].click();", elem)
                print(f"    ✅ JavaScript click successful!")
            
            time.sleep(0.3)
            
            # Check after click
            try:
                checked_after = elem.get_attribute('aria-checked')
                print(f"    After click: aria-checked = {checked_after}")
                
                if checked_after == 'true':
                    print(f"    🎉 SUCCESS! Option is now selected!")
                elif checked_before == 'true' and checked_after != 'true':
                    print(f"    ⚠️  Option was deselected")
                else:
                    print(f"    ⚠️  State unchanged - may need different approach")
            except:
                print(f"    ⚠️  Could not verify click result")
            
        except Exception as e:
            print(f"    ❌ Click failed: {e}")
    
    def _type_text(self, q_idx, text):
        """Type text into question"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        q = self.questions[q_idx]
        text_opts = [o for o in q['options'] if o['type'] == 'text-input']
        
        if not text_opts:
            print(f"❌ Question {q_idx} không có text input!")
            return
        
        elem = text_opts[0]['element']
        
        print(f"\n⌨️  Typing into Q{q_idx}...")
        
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(0.2)
            elem.clear()
            elem.send_keys(text)
            print(f"    ✅ Typed: {text}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    def _scroll_to(self, q_idx):
        """Scroll to question"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        q = self.questions[q_idx]
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", q['element'])
        
        # Highlight
        self.driver.execute_script("""
            arguments[0].style.outline = '3px solid blue';
            setTimeout(() => { arguments[0].style.outline = ''; }, 2000);
        """, q['element'])
        
        print(f"✅ Scrolled to Q{q_idx}")
    
    def _debug_question(self, q_idx):
        """Debug question in detail"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        q = self.questions[q_idx]
        elem = q['element']
        
        print("\n" + "="*80)
        print(f"🔧 DEBUG Q{q_idx}")
        print("="*80)
        
        print(f"\nTitle: {q['title']}")
        print(f"Detected Type: {q['type']}")
        
        print("\n📋 Element Attributes:")
        for attr in ['class', 'role', 'aria-label', 'data-params']:
            val = elem.get_attribute(attr)
            if val:
                print(f"   {attr}: {val[:100]}{'...' if len(val or '') > 100 else ''}")
        
        print("\n🔍 Child Elements Analysis:")
        
        # Check for linear scale indicators
        linear_classes = ['Ht8Grd', 'lLfZXe', 'Od2TWd', 'PY6Xd']
        for cls in linear_classes:
            found = elem.find_elements(By.CLASS_NAME, cls)
            if found:
                print(f"   ✓ Found .{cls}: {len(found)} elements")
        
        # Check data-value elements
        dv_elems = elem.find_elements(By.CSS_SELECTOR, "div[data-value]")
        if dv_elems:
            values = [e.get_attribute('data-value') for e in dv_elems[:10]]
            print(f"   ✓ Found div[data-value]: {values}")
        
        # Check radios
        radios = elem.find_elements(By.CSS_SELECTOR, "div[role='radio']")
        if radios:
            labels = [r.get_attribute('aria-label') for r in radios[:10]]
            print(f"   ✓ Found div[role='radio']: {labels}")
        
        print("\n🎯 Recommended Click Selectors:")
        for i, opt in enumerate(q['options'][:5]):
            print(f"   [{i}] {opt['selector']}")
    
    def _show_html(self, q_idx):
        """Show HTML of question"""
        if q_idx < 0 or q_idx >= len(self.questions):
            print(f"❌ Question {q_idx} không tồn tại!")
            return
        
        q = self.questions[q_idx]
        html = q['element'].get_attribute('outerHTML')
        
        # Truncate if too long
        if len(html) > 3000:
            html = html[:3000] + "\n... (truncated)"
        
        print(f"\n📄 HTML của Q{q_idx}:")
        print("-"*80)
        print(html)
    
    def _test_all_linear(self):
        """Test all linear scale questions"""
        linear_qs = [q for q in self.questions if q['type'] == 'linear_scale']
        
        print(f"\n🧪 Testing {len(linear_qs)} linear scale questions...")
        
        for q in linear_qs:
            print(f"\n[Q{q['idx']}] {q['title'][:50]}...")
            
            # Find middle option to click
            if q['options']:
                mid_idx = len(q['options']) // 2
                opt = q['options'][mid_idx]
                
                print(f"    Clicking option [{mid_idx}]: {opt['value']}")
                
                try:
                    elem = opt['element']
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    time.sleep(0.2)
                    elem.click()
                    time.sleep(0.3)
                    
                    checked = elem.get_attribute('aria-checked')
                    if checked == 'true':
                        print(f"    ✅ Success!")
                    else:
                        print(f"    ⚠️  Click executed but not selected")
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            print("\n👋 Closing Chrome...")
            self.driver.quit()
            print("🔚 Done!")


def main():
    print("="*80)
    print("🔍 TERMINAL DEBUG TOOL - Scan & Click")
    print("="*80)
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\n📝 Nhập URL (viewform hoặc edit link): ").strip()
    
    if not url:
        print("❌ Cần URL!")
        return
    
    debugger = TerminalDebugger()
    debugger.start(url)


if __name__ == "__main__":
    main()
