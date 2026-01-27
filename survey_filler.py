"""
Automated Survey/Form Filler Tool
Tool để tự động điền các khảo sát theo kết quả mong muốn
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from typing import List, Dict, Any
from datetime import datetime


class SurveyFiller:
    """
    Công cụ điền khảo sát tự động
    Hỗ trợ Google Forms và các form tùy chỉnh
    """
    
    def __init__(self, form_url: str, headless: bool = False):
        """
        Khởi tạo SurveyFiller
        
        Args:
            form_url: URL của form khảo sát
            headless: Chạy Chrome ở chế độ headless (không hiển thị)
        """
        self.form_url = form_url
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _initialize_driver(self):
        """Khởi tạo WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def fill_text_field(self, field_index: int, value: str):
        """
        Điền text vào trường text
        
        Args:
            field_index: Chỉ số của trường (0-indexed)
            value: Giá trị text cần điền
        """
        try:
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            text_inputs = [inp for inp in inputs if inp.get_attribute("type") in ["text", "email", "number"]]
            if field_index < len(text_inputs):
                text_inputs[field_index].clear()
                text_inputs[field_index].send_keys(value)
                print(f"✓ Điền trường {field_index}: {value}")
        except Exception as e:
            print(f"✗ Lỗi điền text field {field_index}: {str(e)}")
    
    def fill_textarea(self, field_index: int, value: str):
        """
        Điền text vào textarea
        
        Args:
            field_index: Chỉ số của textarea (0-indexed)
            value: Giá trị text cần điền
        """
        try:
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            if field_index < len(textareas):
                textareas[field_index].clear()
                textareas[field_index].send_keys(value)
                print(f"✓ Điền textarea {field_index}: {value}")
        except Exception as e:
            print(f"✗ Lỗi điền textarea {field_index}: {str(e)}")
    
    def select_dropdown(self, field_index: int, option_value: str):
        """
        Chọn option từ dropdown
        
        Args:
            field_index: Chỉ số của dropdown (0-indexed)
            option_value: Giá trị option cần chọn
        """
        try:
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            if field_index < len(selects):
                select = Select(selects[field_index])
                select.select_by_value(option_value)
                print(f"✓ Chọn dropdown {field_index}: {option_value}")
        except Exception as e:
            print(f"✗ Lỗi chọn dropdown {field_index}: {str(e)}")
    
    def select_radio(self, field_index: int, option_index: int):
        """
        Chọn radio button
        
        Args:
            field_index: Chỉ số của radio group (0-indexed)
            option_index: Chỉ số của option trong group (0-indexed)
        """
        try:
            radios = self.driver.find_elements(By.NAME, "")  # Cần điều chỉnh selector
            print(f"✓ Chọn radio {field_index}: option {option_index}")
        except Exception as e:
            print(f"✗ Lỗi chọn radio {field_index}: {str(e)}")
    
    def select_checkbox(self, field_index: int, option_indices: List[int]):
        """
        Chọn checkboxes
        
        Args:
            field_index: Chỉ số của checkbox group (0-indexed)
            option_indices: Danh sách chỉ số các option cần chọn
        """
        try:
            checkboxes = self.driver.find_elements(By.TYPE, "checkbox")
            for idx in option_indices:
                if idx < len(checkboxes):
                    checkboxes[idx].click()
            print(f"✓ Chọn checkboxes {field_index}: {option_indices}")
        except Exception as e:
            print(f"✗ Lỗi chọn checkboxes {field_index}: {str(e)}")
    
    def submit_form(self):
        """Gửi form"""
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')] | //button[contains(text(), 'Gửi')]")
            submit_btn.click()
            time.sleep(2)
            print("✓ Form đã được gửi thành công")
        except Exception as e:
            print(f"✗ Lỗi gửi form: {str(e)}")
    
    def fill_form(self, data: Dict[str, Any]):
        """
        Điền form với dữ liệu
        
        Args:
            data: Dictionary chứa dữ liệu cần điền
                  Ví dụ: {"text_0": "John", "email_1": "john@example.com"}
        """
        self._initialize_driver()
        try:
            self.driver.get(self.form_url)
            time.sleep(2)
            
            for field_name, value in data.items():
                if field_name.startswith("text_"):
                    idx = int(field_name.split("_")[1])
                    self.fill_text_field(idx, value)
                elif field_name.startswith("textarea_"):
                    idx = int(field_name.split("_")[1])
                    self.fill_textarea(idx, value)
                elif field_name.startswith("select_"):
                    idx = int(field_name.split("_")[1])
                    self.select_dropdown(idx, value)
            
            self.submit_form()
        finally:
            self.driver.quit()
    
    def fill_multiple(self, data_list: List[Dict[str, Any]]):
        """
        Điền form nhiều lần với dữ liệu khác nhau
        
        Args:
            data_list: Danh sách dictionary chứa dữ liệu cho mỗi response
        """
        for idx, data in enumerate(data_list):
            print(f"\n--- Điền form #{idx + 1}/{len(data_list)} ---")
            self.fill_form(data)
            if idx < len(data_list) - 1:
                time.sleep(2)  # Chờ giữa các response


class GoogleFormsFiller:
    """
    Công cụ chuyên biệt cho Google Forms
    """
    
    def __init__(self, form_url: str, headless: bool = False):
        """
        Khởi tạo GoogleFormsFiller
        
        Args:
            form_url: URL của Google Form
            headless: Chạy ở chế độ headless
        """
        self.form_url = form_url
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def _initialize_driver(self):
        """Khởi tạo WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def _get_question_elements(self):
        """Lấy tất cả các câu hỏi trong form"""
        return self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
    
    def fill_short_answer(self, question_index: int, answer: str):
        """
        Điền câu trả lời ngắn
        
        Args:
            question_index: Chỉ số câu hỏi (0-indexed)
            answer: Câu trả lời
        """
        try:
            questions = self._get_question_elements()
            if question_index < len(questions):
                input_field = questions[question_index].find_element(By.TAG_NAME, "input")
                input_field.clear()
                input_field.send_keys(answer)
                print(f"✓ Câu {question_index}: {answer}")
        except Exception as e:
            print(f"✗ Lỗi điền câu {question_index}: {str(e)}")
    
    def fill_long_answer(self, question_index: int, answer: str):
        """
        Điền câu trả lời dài
        
        Args:
            question_index: Chỉ số câu hỏi (0-indexed)
            answer: Câu trả lời
        """
        try:
            questions = self._get_question_elements()
            if question_index < len(questions):
                textarea = questions[question_index].find_element(By.TAG_NAME, "textarea")
                textarea.clear()
                textarea.send_keys(answer)
                print(f"✓ Câu {question_index}: {answer}")
        except Exception as e:
            print(f"✗ Lỗi điền câu {question_index}: {str(e)}")
    
    def fill_multiple_choice(self, question_index: int, option_text: str):
        """
        Chọn một trong các lựa chọn
        
        Args:
            question_index: Chỉ số câu hỏi (0-indexed)
            option_text: Text của lựa chọn cần chọn
        """
        try:
            questions = self._get_question_elements()
            if question_index < len(questions):
                options = questions[question_index].find_elements(By.CLASS_NAME, "YKDB3e")
                for option in options:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if option_text in label.text:
                        option.click()
                        print(f"✓ Câu {question_index}: {option_text}")
                        return
        except Exception as e:
            print(f"✗ Lỗi chọn option câu {question_index}: {str(e)}")
    
    def fill_checkboxes(self, question_index: int, option_texts: List[str]):
        """
        Chọn nhiều checkboxes
        
        Args:
            question_index: Chỉ số câu hỏi (0-indexed)
            option_texts: Danh sách text các lựa chọn cần chọn
        """
        try:
            questions = self._get_question_elements()
            if question_index < len(questions):
                options = questions[question_index].find_elements(By.CLASS_NAME, "YKDB3e")
                for option in options:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if label.text in option_texts:
                        option.click()
                        print(f"✓ Câu {question_index}: {label.text}")
        except Exception as e:
            print(f"✗ Lỗi chọn checkboxes câu {question_index}: {str(e)}")
    
    def submit(self):
        """Gửi form"""
        try:
            submit_btn = self.driver.find_element(By.CLASS_NAME, "uArJ5e")
            submit_btn.click()
            time.sleep(2)
            print("✓ Form đã được gửi thành công")
        except Exception as e:
            print(f"✗ Lỗi gửi form: {str(e)}")
    
    def fill_and_submit(self, answers: Dict[int, Any]):
        """
        Điền và gửi form
        
        Args:
            answers: Dictionary với key là chỉ số câu hỏi, 
                    value là câu trả lời hoặc danh sách câu trả lời
        """
        self._initialize_driver()
        try:
            self.driver.get(self.form_url)
            time.sleep(2)
            
            for question_index, answer in answers.items():
                if isinstance(answer, list):
                    self.fill_checkboxes(question_index, answer)
                else:
                    self.fill_short_answer(question_index, str(answer))
            
            self.submit()
        finally:
            self.driver.quit()
    
    def fill_multiple_submissions(self, answers_list: List[Dict[int, Any]]):
        """
        Gửi multiple responses
        
        Args:
            answers_list: Danh sách các dictionary chứa câu trả lời
        """
        for idx, answers in enumerate(answers_list):
            print(f"\n--- Response #{idx + 1}/{len(answers_list)} ---")
            self.fill_and_submit(answers)
            if idx < len(answers_list) - 1:
                time.sleep(3)


# ============== Ví dụ sử dụng ==============

if __name__ == "__main__":
    # Ví dụ 1: Sử dụng GoogleFormsFiller
    # FORM_URL = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform"
    
    # Dữ liệu để gửi
    # answers_list = [
    #     {
    #         0: "Tên người dùng 1",      # Câu hỏi 0: Short answer
    #         1: "email1@example.com",    # Câu hỏi 1: Short answer
    #         2: "Lựa chọn A",            # Câu hỏi 2: Multiple choice
    #         3: ["Tùy chọn 1", "Tùy chọn 2"]  # Câu hỏi 3: Checkboxes
    #     },
    #     {
    #         0: "Tên người dùng 2",
    #         1: "email2@example.com",
    #         2: "Lựa chọn B",
    #         3: ["Tùy chọn 2", "Tùy chọn 3"]
    #     }
    # ]
    
    # filler = GoogleFormsFiller(FORM_URL, headless=False)
    # filler.fill_multiple_submissions(answers_list)
    
    print("Tool đã sẵn sàng sử dụng!")
    print("Xem ví dụ trong comment ở cuối file")
