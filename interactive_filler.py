"""
Script tương tác để điền Google Form
- Tự động lấy câu hỏi từ form
- Hỏi người dùng nhập đáp án
- Người dùng chỉ định số lượng responses
- Tự động gửi responses
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from typing import Dict, List, Any


class InteractiveGoogleFormFiller:
    """
    Tool tương tác để điền Google Form
    """
    
    def __init__(self, form_url: str, headless: bool = False):
        """
        Khởi tạo
        
        Args:
            form_url: URL của Google Form
            headless: Chạy ở chế độ headless
        """
        self.form_url = form_url
        self.headless = headless
        self.driver = None
        self.wait = None
        self.questions = []
    
    def _initialize_driver(self):
        """Khởi tạo WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def extract_questions(self):
        """
        Trích xuất tất cả câu hỏi từ form
        💡 TIP: Sử dụng link editor (với quyền "người chỉnh sửa") để lấy toàn bộ câu hỏi 1 trang
        Hiển thị cho người dùng để review
        """
        self._initialize_driver()
        
        try:
            print("\n🔍 Đang lấy thông tin form...")
            print("💡 Nếu form có nhiều trang, sẽ lấy tất cả câu hỏi tại đây")
            
            self.driver.get(self.form_url)
            time.sleep(3)
            
            # Lấy tất cả câu hỏi
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            print(f"✓ Tìm thấy {len(question_elements)} câu hỏi\n")
            
            self.questions = []
            
            for idx, question_element in enumerate(question_elements):
                question_data = {
                    "index": idx,
                    "title": self._get_question_text(question_element),
                    "type": self._get_question_type(question_element),
                    "options": self._get_options(question_element),
                    "required": self._is_required(question_element)
                }
                
                self.questions.append(question_data)
                
                # Hiển thị câu hỏi
                print(f"📋 Câu {idx + 1}: {question_data['title']}")
                print(f"   Loại: {self._format_type(question_data['type'])}")
                
                if question_data['options']:
                    print(f"   Lựa chọn:")
                    for opt in question_data['options']:
                        print(f"      {opt['index'] + 1}. {opt['text']}")
                
                print()
            
            return self.questions
        
        finally:
            self.driver.quit()
    
    def _format_type(self, question_type: str) -> str:
        """Format kiểu câu hỏi thành tiếng Việt"""
        type_map = {
            "multiple_choice": "Chọn một lựa chọn",
            "checkbox": "Chọn nhiều lựa chọn",
            "dropdown": "Chọn từ danh sách",
            "short_answer": "Trả lời ngắn",
            "long_answer": "Trả lời dài",
            "unknown": "Không xác định"
        }
        return type_map.get(question_type, "Không xác định")
    
    def _get_question_text(self, question_element) -> str:
        """Lấy text câu hỏi"""
        try:
            title = question_element.find_element(By.CLASS_NAME, "Uc2Deb")
            return title.text
        except:
            return "Untitled Question"
    
    def _get_question_type(self, question_element) -> str:
        """Xác định loại câu hỏi"""
        try:
            # Kiểm tra radio button (multiple choice)
            radio_buttons = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                return "multiple_choice"
            
            # Kiểm tra checkbox
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes and len(checkboxes) > 0:
                return "checkbox"
            
            # Kiểm tra dropdown
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            # Kiểm tra textarea (long answer)
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            if textareas:
                return "long_answer"
            
            # Kiểm tra text input (short answer)
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if text_inputs:
                return "short_answer"
            
            return "unknown"
        except:
            return "unknown"
    
    def _get_options(self, question_element) -> List[Dict]:
        """Lấy danh sách lựa chọn"""
        options = []
        try:
            option_elements = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for idx, option in enumerate(option_elements):
                try:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    options.append({
                        "index": idx,
                        "text": label.text
                    })
                except:
                    pass
        except:
            pass
        
        return options
    
    def _is_required(self, question_element) -> bool:
        """Kiểm tra câu hỏi có bắt buộc không"""
        try:
            question_element.find_element(By.CLASS_NAME, "geHIc")
            return True
        except:
            return False
    
    def get_user_answers(self) -> Dict[int, Any]:
        """
        Hỏi người dùng nhập đáp án cho mỗi câu hỏi
        Chỉ cần nhập 1 lần cho tất cả responses
        
        Returns:
            Dictionary với key là index câu hỏi, value là đáp án
        """
        answers = {}
        
        print("\n" + "="*60)
        print("📝 NHẬP ĐÁP ÁN CHO CÁC CÂU HỎI")
        print("="*60 + "\n")
        
        for question in self.questions:
            idx = question['index']
            q_type = question['type']
            q_title = question['title']
            
            print(f"Câu {idx + 1}: {q_title}")
            
            try:
                if q_type == "multiple_choice" or q_type == "dropdown":
                    # Hiển thị các lựa chọn
                    if question['options']:
                        for opt in question['options']:
                            print(f"  {opt['index'] + 1}. {opt['text']}")
                        
                        while True:
                            try:
                                choice = int(input(f"→ Chọn số (1-{len(question['options'])}): ").strip())
                                if 1 <= choice <= len(question['options']):
                                    selected_text = question['options'][choice - 1]['text']
                                    answers[idx] = selected_text
                                    print(f"  ✓ Đã chọn: {selected_text}\n")
                                    break
                                else:
                                    print(f"  ❌ Vui lòng nhập số từ 1 đến {len(question['options'])}")
                            except ValueError:
                                print("  ❌ Vui lòng nhập một số")
                
                elif q_type == "checkbox":
                    # Cho phép chọn nhiều
                    if question['options']:
                        for opt in question['options']:
                            print(f"  {opt['index'] + 1}. {opt['text']}")
                        
                        choices_str = input(f"→ Chọn số cách nhau bởi dấu phẩy (ví dụ: 1,2,3): ").strip()
                        if choices_str:
                            try:
                                choice_nums = [int(x.strip()) for x in choices_str.split(',')]
                                selected_texts = []
                                for choice in choice_nums:
                                    if 1 <= choice <= len(question['options']):
                                        selected_texts.append(question['options'][choice - 1]['text'])
                                
                                if selected_texts:
                                    answers[idx] = selected_texts
                                    print(f"  ✓ Đã chọn: {', '.join(selected_texts)}\n")
                                else:
                                    print("  ❌ Không có lựa chọn hợp lệ\n")
                            except ValueError:
                                print("  ❌ Vui lòng nhập các số cách nhau bởi dấu phẩy\n")
                
                else:  # short_answer, long_answer
                    answer = input("→ Nhập đáp án: ").strip()
                    if answer:
                        answers[idx] = answer
                        print(f"  ✓ Đã lưu\n")
                    else:
                        print("  ⚠️  Bỏ qua câu hỏi này\n")
            
            except KeyboardInterrupt:
                print("\n❌ Đã hủy")
                return None
        
        return answers
    
    def get_response_count(self) -> int:
        """Hỏi người dùng muốn tạo bao nhiêu responses"""
        print("\n" + "="*60)
        
        while True:
            try:
                count_str = input("❓ Bạn muốn tạo bao nhiêu responses? (nhập số): ").strip()
                count = int(count_str)
                
                if count <= 0:
                    print("❌ Số lượng phải lớn hơn 0")
                    continue
                
                if count > 100:
                    confirm = input(f"⚠️  Bạn sắp tạo {count} responses. Tiếp tục? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("Đã hủy")
                        return None
                
                print(f"✓ Sẽ tạo {count} responses\n")
                return count
            
            except ValueError:
                print("❌ Vui lòng nhập một số")
    
    def fill_and_submit(self, answers: Dict[int, Any]):
        """
        Điền form với dữ liệu đã chuẩn bị
        Tự động chuyển trang bằng nút "Tiếp" 
        
        Args:
            answers: Dictionary với câu trả lời
        """
        self.driver.get(self.form_url)
        time.sleep(2)
        
        try:
            current_question_idx = 0
            page_num = 1
            
            while True:
                print(f"📄 Trang {page_num}")
                
                # Lấy câu hỏi trên trang hiện tại
                question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                questions_on_page = []
                
                # Chỉ xử lý câu hỏi "hiển thị" trên trang này
                for q_elem in question_elements:
                    try:
                        # Kiểm tra nếu câu hỏi này visible
                        if q_elem.is_displayed():
                            questions_on_page.append(q_elem)
                    except:
                        pass
                
                # Điền câu trả lời cho các câu hỏi trên trang này
                for page_q_idx, q_element in enumerate(questions_on_page):
                    question_idx = current_question_idx + page_q_idx
                    
                    if question_idx in answers:
                        answer = answers[question_idx]
                        question_data = self.questions[question_idx]
                        q_type = question_data['type']
                        q_title = question_data['title']
                        
                        print(f"  → {q_title}: ", end="")
                        
                        if q_type == "short_answer" or q_type == "long_answer":
                            self._fill_text_field_element(q_element, answer)
                            print(f"✓")
                        
                        elif q_type == "multiple_choice" or q_type == "dropdown":
                            self._select_option_element(q_element, answer)
                            print(f"✓")
                        
                        elif q_type == "checkbox":
                            if isinstance(answer, list):
                                for option_text in answer:
                                    self._select_option_element(q_element, option_text)
                                print(f"✓")
                
                # Tìm nút "Tiếp" (Next button)
                next_btn = self._find_next_button()
                
                if next_btn:
                    # Còn trang tiếp theo
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(0.5)
                    next_btn.click()
                    time.sleep(1.5)
                    current_question_idx += len(questions_on_page)
                    page_num += 1
                else:
                    # Trang cuối cùng - gửi form
                    print(f"  ✅ Trang cuối cùng - Gửi form")
                    self._submit_form()
                    break
        
        except Exception as e:
            print(f"❌ Lỗi điền form: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _fill_text_field(self, question_idx: int, value: str):
        """Điền text field"""
        try:
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            question_element = question_elements[question_idx]
            
            # Tìm input hoặc textarea
            input_field = None
            try:
                input_field = question_element.find_element(By.CSS_SELECTOR, "input[type='text']")
            except:
                try:
                    input_field = question_element.find_element(By.TAG_NAME, "textarea")
                except:
                    pass
            
            if input_field:
                input_field.clear()
                input_field.send_keys(value)
        
        except Exception as e:
            print(f"⚠️  Lỗi điền text field {question_idx}: {str(e)}")
    
    def _fill_text_field_element(self, question_element, value: str):
        """Điền text field từ element"""
        try:
            # Tìm input hoặc textarea
            input_field = None
            try:
                input_field = question_element.find_element(By.CSS_SELECTOR, "input[type='text']")
            except:
                try:
                    input_field = question_element.find_element(By.TAG_NAME, "textarea")
                except:
                    pass
            
            if input_field:
                input_field.clear()
                input_field.send_keys(value)
        
        except Exception as e:
            print(f"⚠️  Lỗi điền text field: {str(e)}")
    
    def _select_option(self, question_idx: int, option_text: str):
        """Chọn option"""
        try:
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            question_element = question_elements[question_idx]
            
            # Tìm option với text tương ứng
            options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for option in options:
                try:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if label.text == option_text:
                        option.click()
                        return
                except:
                    pass
        
        except Exception as e:
            print(f"⚠️  Lỗi chọn option câu {question_idx}: {str(e)}")
    
    def _select_option_element(self, question_element, option_text: str):
        """Chọn option từ element"""
        try:
            # Tìm option với text tương ứng
            options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for option in options:
                try:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if label.text == option_text:
                        option.click()
                        time.sleep(0.3)
                        return
                except:
                    pass
        
        except Exception as e:
            print(f"⚠️  Lỗi chọn option: {str(e)}")
    
    def _find_next_button(self):
        """Tìm nút 'Tiếp' (Next button)"""
        try:
            # Tìm nút tiếp theo - thường có class "uArJ5e" và text "Tiếp" hoặc "Next"
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Tiếp')] | //button[contains(., 'Next')]")
            if buttons and len(buttons) > 0:
                # Lấy button visible
                for btn in buttons:
                    if btn.is_displayed():
                        return btn
            
            # Thử tìm với class
            buttons = self.driver.find_elements(By.CLASS_NAME, "uArJ5e")
            for btn in buttons:
                if btn.is_displayed():
                    # Kiểm tra nếu không phải submit button
                    aria_label = btn.get_attribute("aria-label")
                    if aria_label and ("Tiếp" in aria_label or "Next" in aria_label):
                        return btn
        except:
            pass
        
        return None
    
    def _submit_form(self):
        """Gửi form"""
        try:
            # Tìm nút submit - có class "uArJ5e" nhưng KHÔNG phải nút tiếp
            submit_btn = None
            
            # Cách 1: Tìm button với text "Gửi" hoặc "Submit"
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'Gửi')] | //button[contains(., 'Submit')]")
            except:
                pass
            
            # Cách 2: Tìm button class "uArJ5e" mà không phải "Tiếp"
            if not submit_btn:
                try:
                    buttons = self.driver.find_elements(By.CLASS_NAME, "uArJ5e")
                    for btn in buttons:
                        if btn.is_displayed():
                            aria_label = btn.get_attribute("aria-label") or ""
                            if "Tiếp" not in aria_label and "Next" not in aria_label:
                                submit_btn = btn
                                break
                except:
                    pass
            
            if submit_btn:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                time.sleep(1)
                submit_btn.click()
                time.sleep(2)
                print("✅ Form đã gửi")
            else:
                print("⚠️  Không tìm thấy nút gửi")
        
        except Exception as e:
            print(f"❌ Lỗi gửi form: {str(e)}")
    
    def run_interactive(self):
        """
        Chạy tool tương tác
        Quy trình: 
        1. Lấy câu hỏi từ link editor (1 trang)
        2. Hỏi đáp án
        3. Hỏi số lượng
        4. Tạo responses - tự động chuyển trang
        """
        print("\n" + "="*60)
        print("🤖 GOOGLE FORM AUTO FILLER - INTERACTIVE MODE")
        print("="*60)
        
        # Bước 1: Trích xuất câu hỏi
        self.extract_questions()
        
        # Bước 2: Hỏi người dùng nhập đáp án
        answers = self.get_user_answers()
        if answers is None:
            return
        
        # Bước 3: Hỏi số lượng responses
        response_count = self.get_response_count()
        if response_count is None:
            return
        
        # Bước 4: Tạo responses
        print("\n" + "="*60)
        print("📤 ĐANG GỬI RESPONSES")
        print("="*60 + "\n")
        print("💡 Lưu ý:")
        print("- Khi trả lời form, nó có thể chia thành nhiều trang")
        print("- Tool sẽ tự động bấm 'Tiếp' để chuyển trang")
        print("- Cuối cùng sẽ bấm 'Gửi' để hoàn tất response\n")
        
        self._initialize_driver()
        
        try:
            for i in range(response_count):
                print(f"📮 Response {i + 1}/{response_count}")
                self.fill_and_submit(answers)
                
                if i < response_count - 1:
                    print("⏳ Chờ 2 giây trước response tiếp theo...")
                    time.sleep(2)
            
            print("\n✅ Hoàn tất! Đã gửi tất cả responses")
        
        finally:
            self.driver.quit()


def main():
    """Hàm main"""
    print("\n╔" + "="*58 + "╗")
    print("║  🤖 GOOGLE FORM INTERACTIVE FILLER  ║")
    print("║  Công cụ tự động điền khảo sát Google Forms  ║")
    print("╚" + "="*58 + "╝\n")
    
    print("📌 HƯỚNG DẪN SỬ DỤNG:")
    print("1. Copy link 'người chỉnh sửa' (editor link) của form")
    print("   - Bạn sẽ lấy được tất cả câu hỏi từ 1 trang")
    print("2. Tool sẽ tự động điền và chuyển trang")
    print("3. Khi trả lời thực tế, form được chia thành nhiều trang")
    print("4. Tool tự động bấm 'Tiếp' để chuyển trang")
    print("5. Cuối cùng bấm 'Gửi' để hoàn tất\n")
    
    # Nhập URL form
    form_url = input("📌 Nhập URL Google Form (editor link): ").strip()
    
    if not form_url:
        print("❌ URL không được để trống")
        return
    
    # Tạo filler và chạy
    filler = InteractiveGoogleFormFiller(form_url, headless=False)
    filler.run_interactive()


if __name__ == "__main__":
    main()
