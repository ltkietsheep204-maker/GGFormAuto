"""
Script để inspect Google Form và trích xuất thông tin câu hỏi
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json


class GoogleFormInspector:
    """
    Công cụ để lấy thông tin chi tiết từ Google Form
    Giúp xác định câu hỏi, loại câu hỏi, và các lựa chọn
    """
    
    def __init__(self, form_url: str):
        """
        Khởi tạo FormInspector
        
        Args:
            form_url: URL của Google Form
        """
        self.form_url = form_url
        self.driver = None
        self.wait = None
        self.questions = []
    
    def _initialize_driver(self):
        """Khởi tạo WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def _extract_question_text(self, question_element):
        """Lấy text của câu hỏi"""
        try:
            # Tìm text câu hỏi
            title = question_element.find_element(By.CLASS_NAME, "Uc2Deb")
            return title.text
        except:
            return "Untitled Question"
    
    def _extract_question_type(self, question_element):
        """Xác định loại câu hỏi"""
        try:
            # Kiểm tra các loại câu hỏi khác nhau
            
            # Multiple choice
            if question_element.find_elements(By.CLASS_NAME, "YuiAyd"):
                return "multiple_choice"
            
            # Checkbox
            if question_element.find_elements(By.CLASS_NAME, "YuiAyd"):
                radio_btns = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkboxes and len(checkboxes) > 1:
                    return "checkbox"
            
            # Dropdown
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            # Text field
            if question_element.find_elements(By.CSS_SELECTOR, "input[type='text']"):
                return "short_answer"
            
            # Textarea
            if question_element.find_elements(By.TAG_NAME, "textarea"):
                return "long_answer"
            
            # Default
            return "unknown"
        except:
            return "unknown"
    
    def _extract_options(self, question_element):
        """Lấy danh sách lựa chọn (nếu có)"""
        options = []
        try:
            # Tìm tất cả các option container
            option_elements = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for idx, option in enumerate(option_elements):
                try:
                    # Lấy text của option
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
    
    def inspect_form(self):
        """Trích xuất toàn bộ thông tin câu hỏi từ form"""
        self._initialize_driver()
        
        try:
            print(f"🔍 Đang inspect form: {self.form_url}")
            self.driver.get(self.form_url)
            time.sleep(3)
            
            # Lấy tất cả các câu hỏi
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            print(f"✓ Tìm thấy {len(question_elements)} câu hỏi")
            
            self.questions = []
            
            for idx, question_element in enumerate(question_elements):
                question_data = {
                    "index": idx,
                    "title": self._extract_question_text(question_element),
                    "type": self._extract_question_type(question_element),
                    "required": self._is_required(question_element),
                    "options": self._extract_options(question_element)
                }
                
                self.questions.append(question_data)
                print(f"\n📋 Câu {idx}:")
                print(f"   Loại: {question_data['type']}")
                print(f"   Câu: {question_data['title']}")
                print(f"   Bắt buộc: {'✓ Có' if question_data['required'] else '✗ Không'}")
                
                if question_data['options']:
                    print(f"   Lựa chọn:")
                    for opt in question_data['options']:
                        print(f"     - {opt['text']}")
            
            return self.questions
        
        finally:
            self.driver.quit()
    
    def _is_required(self, question_element):
        """Kiểm tra câu hỏi có bắt buộc không"""
        try:
            required_indicator = question_element.find_element(By.CLASS_NAME, "geHIc")
            return True
        except:
            return False
    
    def save_to_json(self, filename: str = "form_structure.json"):
        """Lưu thông tin form vào file JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.questions, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Đã lưu thông tin vào {filename}")


if __name__ == "__main__":
    # Nhập URL form từ người dùng
    form_url = input("📌 Nhập URL Google Form: ").strip()
    
    if not form_url:
        print("❌ URL không được để trống")
        exit(1)
    
    # Inspect form
    inspector = GoogleFormInspector(form_url)
    questions = inspector.inspect_form()
    
    # Lưu thông tin
    inspector.save_to_json()
    
    print("\n✅ Hoàn tất! Dữ liệu đã được lưu trong 'form_structure.json'")
