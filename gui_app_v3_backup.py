"""
Google Form Auto Filler - Desktop App v3 (UI like Google Form)
- Hiển thị y như Google Form
- Click chọn trực tiếp
- Lấy đầy đủ tất cả options
"""

import sys
import json
import time
import logging
import traceback
import random
from pathlib import Path
from typing import Dict, List, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QTabWidget, QProgressBar, QMessageBox,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QScrollArea, QSlider, 
    QDoubleSpinBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError as e:
    logger.error(f"Selenium import error: {e}")


class GoogleFormWorker(QThread):
    """Worker thread để trích xuất câu hỏi"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, form_url: str):
        super().__init__()
        self.form_url = form_url
        self.questions = []
        self.driver = None
    
    def run(self):
        """Chạy trong background thread"""
        try:
            self.progress.emit("🔍 Đang lấy thông tin form...")
            
            # Handle different URL types
            form_url = self.form_url
            is_editor_link = "/edit" in form_url  # Editor links show all questions on 1 page
            
            # Only convert formResponse to viewform (don't convert editor links!)
            if "/formResponse" in form_url:
                form_url = form_url.replace("/formResponse", "/viewform")
                logger.info(f"Auto-converted formResponse to viewform URL")
            
            logger.info(f"Loading form: {form_url}")
            logger.info(f"Is editor link: {is_editor_link}")
            
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--headless")  # 🆕 Ẩn Chrome
            options.add_argument("--disable-gpu")  # 🆕 Tăng ổn định headless
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(form_url)
            
            # Wait for form to load - try multiple selectors
            logger.info("Waiting for form to load...")
            time.sleep(2)
            
            # For EDITOR links: Skip the "Continue" button check (all questions visible)
            # For VIEWFORM links: Check for continue button
            if not is_editor_link:
                self.progress.emit("🔐 Kiểm tra nút tiếp tục...")
                page_source = self.driver.page_source
                
                # Check for "Tiếp" (Continue) button - appears on login screen
                if "Đăng nhập vào Google" in page_source or "Sign in" in page_source or "Tiếp" in page_source:
                    logger.warning("Continue/Login screen detected - trying to find 'Tiếp' button")
                    self.progress.emit("⚠️ Phát hiện cần click nút 'Tiếp'...")
                    
                    # Try to find and click the "Tiếp" (Continue) button
                    # The button usually appears after the "Đăng nhập vào Google" link
                    continue_buttons = [
                        ("//button//span[contains(text(), 'Tiếp')]", "Tiếp span in button"),
                        ("//button[contains(@aria-label, 'Tiếp')]", "Tiếp aria label button"),
                        ("//div[@role='button']//span[contains(text(), 'Tiếp')]", "Tiếp in div button"),
                        ("//*[contains(text(), 'Tiếp')]", "Any Tiếp text"),
                    ]
                    
                    clicked = False
                    for button_xpath, button_name in continue_buttons:
                        try:
                            elements = self.driver.find_elements(By.XPATH, button_xpath)
                            if elements:
                                for element in elements:
                                    try:
                                        # Scroll to element and click
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                        time.sleep(0.5)
                                        element.click()
                                        logger.info(f"Clicked {button_name}")
                                        self.progress.emit(f"✓ Đã click nút 'Tiếp'")
                                        time.sleep(2)  # Wait for form to load
                                        clicked = True
                                        break
                                    except:
                                        pass
                                if clicked:
                                    break
                        except Exception as e:
                            logger.debug(f"Could not find {button_name}: {e}")
                    
                    if not clicked:
                        self.error.emit("❌ Không thể tự động click nút tiếp. Vui lòng đăng nhập Google trước khi sử dụng tool.")
                        return
            else:
                # For editor links: Skip the continue button check
                logger.info("Editor link detected - skipping continue button check")
                self.progress.emit("📋 Đây là link editor - toàn bộ câu hỏi sẽ hiển thị trên 1 trang")
            # 🆕 Loop through multiple pages until submit button appears
            page_count = 1
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"EXTRACTING QUESTIONS FROM PAGE {page_count}")
                logger.info(f"{'='*60}")
                
                # Try to find questions using multiple strategies
                question_elements = []
                
                # Strategy 1: Try divs with role="listitem" (more reliable)
                try:
                    question_elements = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
                    logger.info(f"Found {len(question_elements)} elements with role='listitem'")
                except:
                    logger.debug("Could not find elements with role='listitem'")
                
                # Strategy 2: If not found, try old class name
                if len(question_elements) == 0:
                    try:
                        question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                        logger.info(f"Found {len(question_elements)} elements with class 'Qr7Oae'")
                    except:
                        logger.debug("Could not find elements with class 'Qr7Oae'")
                
                # Strategy 3: Find all divs that contain form question patterns
                if len(question_elements) == 0:
                    try:
                        all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                        # Filter divs that have both title and input elements
                        for div in all_divs:
                            spans = div.find_elements(By.TAG_NAME, "span")
                            inputs = div.find_elements(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox'], input[type='text'], textarea")
                            if spans and inputs:
                                question_elements.append(div)
                        logger.info(f"Found {len(question_elements)} potential question elements")
                    except:
                        logger.debug("Could not find elements using div filtering")
                
                # If still no elements, log detailed debug info
                if len(question_elements) == 0:
                    page_source = self.driver.page_source
                    if "No questions in this form" in page_source or len(page_source) < 1000:
                        self.error.emit("❌ Form trống hoặc URL không hợp lệ!")
                        return

                page_question_count = len(question_elements)
                self.progress.emit(f"📄 Trang {page_count}: Tìm thấy {page_question_count} câu hỏi")
                logger.info(f"Page {page_count}: Found {page_question_count} questions")
                
                # Extract questions from current page
                page_start_idx = len(self.questions)
                for idx, question_element in enumerate(question_elements):
                    try:
                        title = self._get_question_text(question_element)
                        q_type = self._get_question_type(question_element)
                        options_list = self._get_options_complete(question_element)
                        
                        question_data = {
                            "index": len(self.questions),
                            "title": title,
                            "type": q_type,
                            "options": options_list,
                            "required": self._is_required(question_element),
                            "element": question_element
                        }
                        
                        self.questions.append(question_data)
                        self.progress.emit(f"✓ Câu {len(self.questions)}: {title[:40]}... ({self._format_type(q_type)}) - {len(options_list)} lựa chọn")
                        logger.info(f"Question {len(self.questions)}: {title[:40]} ({q_type}) - {len(options_list)} options")
                        
                        # Debug: log all options
                        if options_list:
                            for opt in options_list:
                                logger.debug(f"    - {opt['text']}")
                    except Exception as e:
                        logger.error(f"Error processing question {idx}: {e}\n{traceback.format_exc()}")
                        self.progress.emit(f"⚠️ Lỗi câu {len(self.questions)}: {str(e)}")
                
                # 🆕 Check if there's a next page button or submit button
                time.sleep(1)
                page_source = self.driver.page_source
                
                # Check for submit button (Gửi)
                submit_buttons = [
                    ("//button//span[contains(text(), 'Gửi')]", "Gửi"),
                    ("//button[contains(@aria-label, 'Gửi')]", "Gửi button"),
                    ("//*[contains(text(), 'Gửi')]", "Any Gửi text"),
                    ("//button[contains(text(), 'Submit')]", "Submit"),
                ]
                
                has_submit = False
                for button_xpath, button_name in submit_buttons:
                    try:
                        submit_elem = self.driver.find_elements(By.XPATH, button_xpath)
                        if submit_elem and len(submit_elem) > 0:
                            logger.info(f"✓ Found submit button: {button_name}")
                            has_submit = True
                            break
                    except:
                        pass
                
                if has_submit:
                    logger.info("✓ Found submit button - form is complete!")
                    self.progress.emit(f"✓ Hoàn thành! Tổng cộng {len(self.questions)} câu hỏi")
                    break  # Exit loop when submit button found
                
                # Check for next/continue button for next page
                continue_xpaths = [
                    ("//button//span[contains(text(), 'Tiếp')]", "Tiếp"),
                    ("//button[contains(@aria-label, 'Tiếp')]", "Tiếp button"),
                    ("//*[contains(text(), 'Tiếp')]", "Any Tiếp"),
                    ("//button[contains(text(), 'Next')]", "Next"),
                ]
                
                next_button_found = False
                stuck_attempts = 0  # Track if we're stuck on same page
                previous_question_count = len(self.questions)
                
                for button_xpath, button_name in continue_xpaths:
                    try:
                        next_buttons = self.driver.find_elements(By.XPATH, button_xpath)
                        if next_buttons and len(next_buttons) > 0:
                            for btn in next_buttons:
                                try:
                                    # Make sure button is visible and clickable
                                    if btn.is_displayed():
                                        logger.info(f"✓ Found next page button: {button_name}")
                                        
                                        # Try to click up to 3 times if stuck
                                        for attempt in range(3):
                                            self.progress.emit(f"⏭️ Chuyển sang trang tiếp theo (lần {attempt + 1})...")
                                            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                            time.sleep(0.5)
                                            
                                            try:
                                                btn.click()
                                                time.sleep(2)  # Wait for page to change
                                                
                                                # Check if page actually changed by counting questions
                                                new_question_count = len(self.driver.find_elements(By.XPATH, "//div[@role='listitem']"))
                                                
                                                if new_question_count == page_question_count:
                                                    # Same number of questions - might be stuck
                                                    logger.warning(f"⚠️ Attempt {attempt + 1}: Page didn't change ({page_question_count} questions)")
                                                    
                                                    if attempt < 2:  # Not last attempt
                                                        logger.info(f"⏳ Lần thứ {attempt + 1}: Phát hiện câu hỏi bắt buộc - tự động trả lời...")
                                                        self.progress.emit(f"⚠️ Trả lời tự động các câu bắt buộc (lần {attempt + 1})...")
                                                        self._auto_answer_required_fields()
                                                        time.sleep(1)
                                                        # Continue to next attempt (retry click)
                                                        continue
                                                else:
                                                    # Page changed! New questions loaded
                                                    logger.info(f"✓ Successfully moved to next page!")
                                                    page_count += 1
                                                    next_button_found = True
                                                    break
                                            except Exception as click_error:
                                                logger.debug(f"Click error on attempt {attempt + 1}: {click_error}")
                                                if attempt == 2:
                                                    raise click_error
                                        
                                        if next_button_found:
                                            break
                                except Exception as btn_error:
                                    logger.debug(f"Button interaction error: {btn_error}")
                        if next_button_found:
                            break
                    except Exception as xpath_error:
                        logger.debug(f"XPath error: {xpath_error}")
                
                if not next_button_found:
                    # No next button and no submit button - form might be ended
                    logger.warning("⚠️ No next page button or submit button found - ending extraction")
                    self.progress.emit(f"✓ Hoàn thành! Tổng cộng {len(self.questions)} câu hỏi")
                    break
            
            self.finished.emit(self.questions)
            logger.info(f"\n{'='*60}")
            logger.info(f"FORM EXTRACTION COMPLETE")
            logger.info(f"Total pages processed: {page_count}")
            logger.info(f"Total questions found: {len(self.questions)}")
            logger.info(f"{'='*60}\n")
        
        except Exception as e:
            logger.error(f"Worker error: {e}\n{traceback.format_exc()}")
            self.error.emit(f"❌ Lỗi: {str(e)}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _format_type(self, q_type: str) -> str:
        type_map = {
            "multiple_choice": "Chọn một",
            "checkbox": "Chọn nhiều",
            "dropdown": "Dropdown",
            "short_answer": "Trả lời ngắn",
            "long_answer": "Trả lời dài",
            "linear_scale": "Thang điểm",
            "multiple_choice_grid": "Bảng chọn",
            "unknown": "Unknown"
        }
        return type_map.get(q_type, "Unknown")
    
    def _get_question_text(self, question_element) -> str:
        """Lấy text câu hỏi - Using verified class name"""
        try:
            # Primary method: Use the proven class "Uc2Deb" from working code
            try:
                title = question_element.find_element(By.CLASS_NAME, "Uc2Deb")
                text = title.text.strip()
                if text and len(text) > 2:
                    logger.debug(f"  Found question via Uc2Deb class: {text[:50]}")
                    return text
            except:
                logger.debug("  Could not find Uc2Deb class")
                pass
            
            # Fallback 1: Try heading role
            try:
                title = question_element.find_element(By.XPATH, ".//div[@role='heading']")
                text = title.text.strip()
                if text and len(text) > 2 and len(text) < 500:
                    logger.debug(f"  Found question via heading role: {text[:50]}")
                    return text
            except:
                pass
            
            # Fallback 2: Get longest span text (likely to be question)
            try:
                spans = question_element.find_elements(By.TAG_NAME, "span")
                longest_text = ""
                for span in spans:
                    text = span.text.strip()
                    if (text and len(text) > len(longest_text) and len(text) < 500 and 
                        "Required" not in text and "Optional" not in text and "\n" not in text):
                        longest_text = text
                if longest_text:
                    logger.debug(f"  Found question via longest span: {longest_text[:50]}")
                    return longest_text
            except:
                pass
            
            logger.debug("  Could not find question text, returning default")
            return "Untitled Question"
        except:
            return "Untitled Question"
    
    def _get_question_type(self, question_element) -> str:
        """Xác định loại câu hỏi - Using verified method from interactive_filler.py"""
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
            
            # Radio buttons (multiple choice)
            radio_buttons = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons and len(radio_buttons) > 0:
                logger.debug(f"Detected as multiple_choice (found {len(radio_buttons)} radios)")
                return "multiple_choice"
            
            # Checkboxes
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes and len(checkboxes) > 0:
                logger.debug(f"Detected as checkbox (found {len(checkboxes)} checkboxes)")
                return "checkbox"
            
            # Dropdown
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            # Long answer
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            if textareas and len(textareas) > 0:
                return "long_answer"
            
            # Short answer
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if text_inputs and len(text_inputs) > 0:
                return "short_answer"
            
            # Check for YKDB3e options container
            if question_element.find_elements(By.CLASS_NAME, "YKDB3e"):
                if question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                    return "multiple_choice"
                elif question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                    return "checkbox"
            
            # Check for data-params - if it has options array, it's likely multiple choice
            try:
                data_params = question_element.get_attribute('data-params')
                if data_params and '[[' in data_params:  # Has nested arrays (likely options)
                    logger.debug("Detected as multiple_choice (from data-params with options)")
                    return "multiple_choice"
            except:
                pass
            
            # Look for spans that might indicate options (fallback)
            spans = question_element.find_elements(By.TAG_NAME, "span")
            span_texts = []
            for span in spans:
                text = span.text.strip()
                if (text and len(text) > 1 and len(text) < 100 and 
                    "Required" not in text and "\n" not in text):
                    span_texts.append(text)
            
            # If we found multiple short text spans, likely multiple choice
            if len(span_texts) > 2:
                logger.debug(f"Detected as multiple_choice (from {len(span_texts)} option-like spans)")
                return "multiple_choice"
            
            logger.warning(f"Could not determine question type, defaulting to short_answer")
            return "short_answer"  # Default to short_answer instead of unknown
        except Exception as e:
            logger.error(f"Error detecting type: {e}")
            return "short_answer"  # Default to short_answer instead of unknown
    
    def _get_options_complete(self, question_element) -> List[Dict]:
        """Lấy danh sách lựa chọn - Exact copy from working interactive_filler.py"""
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
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error in auto-answer: {e}\n{traceback.format_exc()}")


class SubmissionWorker(QThread):
    """Worker thread để gửi responses - hỗ trợ parallel processing"""
    progress = pyqtSignal(str)
    count_progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, form_url: str, answers: Dict, count: int, questions: List, max_parallel: int = 1):
        super().__init__()
        self.form_url = form_url
        self.answers = answers
        self.count = count
        self.questions = questions
        self.max_parallel = max(1, min(max_parallel, 5))  # 🆕 Clamp 1-5 tabs
        self.driver = None
    
    def run(self):
        """Chạy gửi responses - hỗ trợ parallel processing"""
        try:
            # Validate count
            logger.info(f"[WORKER START] Raw count={self.count}, type={type(self.count)}")
            
            try:
                count_int = int(self.count)
            except (TypeError, ValueError) as e:
                logger.error(f"[WORKER] Cannot convert count to int: {e}")
                self.error.emit(f"❌ Lỗi: Số responses không hợp lệ: {self.count}")
                return
            
            if count_int <= 0:
                logger.error(f"[WORKER] Invalid count: {count_int}")
                self.error.emit(f"❌ Lỗi: Số responses phải > 0 (nhập: {count_int})")
                return
            
            logger.info(f"[WORKER START] Using count={count_int}, max_parallel={self.max_parallel}")
            
            # 🆕 Chọn chế độ chạy
            if self.max_parallel > 1:
                logger.info(f"[WORKER] Starting PARALLEL mode with {self.max_parallel} tabs")
                self._run_parallel(count_int)
            else:
                logger.info(f"[WORKER] Starting SEQUENTIAL mode (1 tab)")
                self._run_sequential(count_int)
        
        except Exception as e:
            logger.error(f"[WORKER ERROR] Fatal error: {e}", exc_info=True)
            self.error.emit(f"❌ Lỗi: {str(e)}")
        
        finally:
            logger.info("[WORKER CLEANUP] Closing browser...")
            if self.driver:
                try:
                    logger.info("[WORKER] Calling driver.quit()...")
                    self.driver.quit()
                    logger.info("[WORKER] ✓ Browser quit successfully")
                except Exception as e:
                    logger.warning(f"[WORKER] Error on driver.quit(): {e}")
            logger.info("[WORKER] ✓ Cleanup complete")
    
    def _run_sequential(self, count_int: int):
        """🆕 Chạy submit tuần tự (1 tab)"""
        import threading
        
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        
        self.driver = webdriver.Chrome(options=options)
        logger.info(f"[WORKER] Browser started in sequential mode")
        
        submitted_count = 0
        for i in range(count_int):
            logger.info(f"\n{'='*50}")
            logger.info(f"[LOOP {i}] Starting response {i + 1}/{count_int}")
            logger.info(f"{'='*50}")
            
            try:
                self.progress.emit(f"📮 Gửi response {i + 1}/{count_int}...")
                self.driver.get(self.form_url)
                time.sleep(2)
                
                logger.info(f"[LOOP {i}] Filling form...")
                self._fill_form()
                
                logger.info(f"[LOOP {i}] Submitting form...")
                self._submit_form()
                
                submitted_count += 1
                self.progress.emit(f"✓ Response {i + 1} đã gửi")
                self.count_progress.emit(i + 1)
                logger.info(f"[LOOP {i}] ✓ Response {i + 1}/{count_int} submitted successfully")
                
                if i < count_int - 1:
                    logger.info(f"[LOOP {i}] Waiting before next submission...")
                    time.sleep(2)
            
            except Exception as e:
                logger.error(f"[LOOP {i}] Error submitting response {i + 1}: {e}", exc_info=True)
                self.progress.emit(f"⚠️ Lỗi response {i + 1}: {str(e)}")
                self.count_progress.emit(i + 1)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"[WORKER END] Sequential completed: submitted_count={submitted_count}, total={count_int}")
        logger.info(f"{'='*50}")
        
        if submitted_count == count_int:
            self.progress.emit(f"✅ Hoàn tất! Đã gửi {count_int} responses (Sequential)")
            logger.info(f"✅ Success: All {count_int} responses submitted!")
        else:
            logger.warning(f"⚠️ Only {submitted_count}/{count_int} responses submitted")
            self.progress.emit(f"⚠️ Chỉ gửi được {submitted_count}/{count_int} responses")
        
        self.finished.emit()
    
    def _run_parallel(self, count_int: int):
        """🆕 Chạy submit song song (multiple tabs)"""
        import threading
        from queue import Queue
        
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        
        # Tạo queue chứa chỉ số response cần gửi
        task_queue = Queue()
        for i in range(count_int):
            task_queue.put(i)
        
        # Lock để tracking số responses đã gửi
        submitted_lock = threading.Lock()
        submitted_count = [0]  # Dùng list để mutable trong nested function
        
        def worker_thread(thread_id):
            """Hàm chạy trong mỗi thread"""
            driver = None
            try:
                driver = webdriver.Chrome(options=options)
                logger.info(f"[THREAD {thread_id}] Browser started")
                
                while True:
                    try:
                        response_idx = task_queue.get_nowait()
                    except:
                        break  # Queue rỗng
                    
                    logger.info(f"[THREAD {thread_id}] Processing response {response_idx + 1}/{count_int}")
                    
                    try:
                        self.progress.emit(f"📮 [Tab {thread_id}] Gửi response {response_idx + 1}/{count_int}...")
                        
                        driver.get(self.form_url)
                        time.sleep(2)
                        
                        logger.info(f"[THREAD {thread_id}] Filling form...")
                        self._fill_form_for_thread(driver)
                        
                        logger.info(f"[THREAD {thread_id}] Submitting form...")
                        self._submit_form_for_thread(driver)
                        
                        with submitted_lock:
                            submitted_count[0] += 1
                        
                        self.progress.emit(f"✓ [Tab {thread_id}] Response {response_idx + 1} gửi xong")
                        self.count_progress.emit(submitted_count[0])
                        logger.info(f"[THREAD {thread_id}] ✓ Response {response_idx + 1} submitted")
                        
                        time.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"[THREAD {thread_id}] Error: {e}", exc_info=True)
                        self.progress.emit(f"⚠️ [Tab {thread_id}] Lỗi response {response_idx + 1}")
            
            except Exception as e:
                logger.error(f"[THREAD {thread_id}] Fatal error: {e}", exc_info=True)
            
            finally:
                if driver:
                    try:
                        driver.quit()
                        logger.info(f"[THREAD {thread_id}] Browser closed")
                    except:
                        pass
        
        # Tạo và chạy threads
        threads = []
        logger.info(f"[WORKER] Creating {self.max_parallel} worker threads")
        
        for tid in range(self.max_parallel):
            t = threading.Thread(target=worker_thread, args=(tid,), daemon=False)
            threads.append(t)
            t.start()
            logger.info(f"[WORKER] Thread {tid} started")
        
        # Đợi tất cả threads kết thúc
        logger.info(f"[WORKER] Waiting for all threads to complete...")
        for t in threads:
            t.join()
        
        logger.info(f"\n{'='*50}")
        logger.info(f"[WORKER END] Parallel completed: submitted_count={submitted_count[0]}, total={count_int}")
        logger.info(f"{'='*50}")
        
        if submitted_count[0] == count_int:
            self.progress.emit(f"✅ Hoàn tất! Đã gửi {count_int} responses ({self.max_parallel} tabs parallel)")
            logger.info(f"✅ Success: All {count_int} responses submitted!")
        else:
            logger.warning(f"⚠️ Only {submitted_count[0]}/{count_int} responses submitted")
            self.progress.emit(f"⚠️ Chỉ gửi được {submitted_count[0]}/{count_int} responses")
        
        self.finished.emit()
    
    def _fill_form(self):
        """Điền form - hỗ trợ cả chế độ bình thường và random, tự động chuyển trang"""
        logger.info(f"Starting to fill form with {len(self.answers)} answers (multi-page support)")
        
        page_number = 1
        questions_filled = 0
        
        while True:
            logger.info(f"\n{'='*60}")
            logger.info(f"FILLING PAGE {page_number}")
            logger.info(f"{'='*60}")
            
            time.sleep(1)
            
            # Find all question elements on current page
            question_elements = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
            if len(question_elements) == 0:
                # Fallback to old class name
                question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            
            logger.info(f"Found {len(question_elements)} questions on page {page_number}")
            
            if len(question_elements) == 0:
                logger.warning("No question elements found on this page - might be at end")
                break
            
            # Fill all questions on current page
            for local_idx, question_element in enumerate(question_elements):
                try:
                    # Calculate global question index
                    idx = questions_filled + local_idx
                    
                    if idx >= len(self.answers):
                        logger.warning(f"Question {idx} exceeds answers count")
                        continue
                    
                    answer = self.answers[idx]
                    q_type = self.questions[idx]['type']
                    question_title = self.questions[idx]['title']
                    
                    # Handle random mode
                    if isinstance(answer, tuple) and answer[0] == 'random':
                        options_list = answer[1]
                        selected_option = self._select_by_percentage(options_list)
                        logger.info(f"Filling Q{idx + 1} ({q_type}): {question_title}")
                        logger.info(f"  Random Mode - Selected: {selected_option}")
                        self._select_option(question_element, selected_option)
                    
                    elif q_type == "short_answer" or q_type == "long_answer":
                        logger.info(f"Filling Q{idx + 1} ({q_type}): {question_title}")
                        logger.info(f"  Answer: {answer}")
                        self._fill_text_field(question_element, str(answer))
                    
                    elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                        logger.info(f"Filling Q{idx + 1} ({q_type}): {question_title}")
                        logger.info(f"  Answer: {answer}")
                        self._select_option(question_element, str(answer))
                    
                    elif q_type == "checkbox":
                        logger.info(f"Filling Q{idx + 1} ({q_type}): {question_title}")
                        logger.info(f"  Answer: {answer}")
                        if isinstance(answer, list):
                            for option_text in answer:
                                self._select_option(question_element, str(option_text))
                        else:
                            self._select_option(question_element, str(answer))
                
                except Exception as e:
                    logger.warning(f"Error filling question {idx}: {e}", exc_info=True)
            
            questions_filled += len(question_elements)
            
            # Check if we need to go to next page
            logger.info(f"\nPage {page_number} filled - checking for next page button...")
            time.sleep(1)
            
            # Look for "Tiếp" (Continue) button
            next_button = None
            continue_xpaths = [
                ("//button//span[contains(text(), 'Tiếp')]", "Tiếp span in button"),
                ("//button[contains(@aria-label, 'Tiếp')]", "Tiếp aria button"),
                ("//div[@role='button']//span[contains(text(), 'Tiếp')]", "Tiếp in div button"),
            ]
            
            for button_xpath, button_name in continue_xpaths:
                try:
                    buttons = self.driver.find_elements(By.XPATH, button_xpath)
                    if buttons and len(buttons) > 0:
                        next_button = buttons[0]
                        logger.info(f"✓ Found next page button: {button_name}")
                        break
                except:
                    pass
            
            if next_button:
                try:
                    logger.info(f"⏭️ Clicking 'Tiếp' button to go to page {page_number + 1}...")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    page_number += 1
                    continue  # Go to next iteration
                except Exception as e:
                    logger.error(f"Error clicking next button: {e}")
                    break
            else:
                logger.info("✓ No more 'Tiếp' buttons found - reached last page")
                break
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Form filling complete - filled {questions_filled} questions")
        logger.info(f"{'='*60}\n")
    
    def _select_by_percentage(self, options_list: List[Dict]) -> str:
        """Chọn option dựa trên tỉ lệ phần trăm"""
        import random as rand
        
        # Build a list where each option appears based on its percentage
        weighted_options = []
        for option_data in options_list:
            text = option_data['text']
            percentage = option_data['percentage']
            # Repeat the option based on percentage (100 times total)
            weighted_options.extend([text] * percentage)
        
        # Randomly select one
        selected = rand.choice(weighted_options)
        logger.info(f"Random selection: {selected} (from {len(options_list)} options with percentages)")
        return selected
    
    def _fill_text_field(self, question_element, value: str):
        """Điền text field"""
        try:
            input_field = None
            try:
                input_field = question_element.find_element(By.CSS_SELECTOR, "input[type='text']")
            except:
                try:
                    input_field = question_element.find_element(By.TAG_NAME, "textarea")
                except:
                    pass
            
            if input_field:
                input_field.click()
                input_field.clear()
                input_field.send_keys(value)
                time.sleep(0.5)
        
        except Exception as e:
            logger.warning(f"Error filling text field: {e}")
    
    def _select_option(self, question_element, option_text: str):
        """Chọn option - try multiple methods"""
        try:
            logger.debug(f"Trying to select: {option_text}")
            
            # Method 1: Try via YKDB3e class (old way)
            try:
                options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
                for option in options:
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        if label.text.strip() == option_text.strip():
                            option.click()
                            logger.info(f"✓ Clicked option via YKDB3e: {option_text}")
                            time.sleep(0.5)
                            return
                    except:
                        pass
            except:
                pass
            
            # Method 2: Find radio button by label text
            try:
                radios = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                for radio in radios:
                    parent = radio.find_element(By.XPATH, "..")
                    labels = parent.find_elements(By.TAG_NAME, "label")
                    for lbl in labels:
                        if lbl.text.strip() == option_text.strip():
                            radio.click()
                            logger.info(f"✓ Clicked radio option: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
            
            # Method 3: Find checkbox by label text
            try:
                checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                for checkbox in checkboxes:
                    parent = checkbox.find_element(By.XPATH, "..")
                    labels = parent.find_elements(By.TAG_NAME, "label")
                    for lbl in labels:
                        if lbl.text.strip() == option_text.strip():
                            checkbox.click()
                            logger.info(f"✓ Clicked checkbox option: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
            
            # Method 4: Find by span containing exact text and click parent
            try:
                spans = question_element.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    if span.text.strip() == option_text.strip():
                        # Try to click the span or its parent container
                        try:
                            span.click()
                            logger.info(f"✓ Clicked span: {option_text}")
                            time.sleep(0.5)
                            return
                        except:
                            # Try clicking parent
                            parent = span.find_element(By.XPATH, "..")
                            parent.click()
                            logger.info(f"✓ Clicked parent of span: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
            
            logger.warning(f"Could not select option: {option_text}")
        
        except Exception as e:
            logger.warning(f"Error selecting option '{option_text}': {e}")
    
    def _submit_form(self):
        """Gửi form - click nút Gửi tím lớn"""
        try:
            logger.info("Looking for submit button...")
            submit_btn = None
            
            # Scroll to bottom first
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Method 1: Find by unique class Y5sE8d (only submit button has this)
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'Y5sE8d')]")
                logger.info(f"Found submit button by class Y5sE8d: '{submit_btn.text}'")
            except Exception as e:
                logger.debug(f"Method 1 (Y5sE8d) error: {e}")
            
            # Method 2: Find by class QvWxOd (submit button specific)
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by class QvWxOd: '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 2 (QvWxOd) error: {e}")
            
            # Method 3: Find by all unique classes together
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e') and contains(@class, 'Y5sE8d') and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by combined classes: '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 3 (combined) error: {e}")
            
            # Method 4: Find the second displayed uArJ5e div (first is clear, second is submit)
            if not submit_btn:
                try:
                    uarj5e_divs = self.driver.find_elements(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e')]")
                    logger.info(f"Found {len(uarj5e_divs)} divs with class uArJ5e")
                    for i, div in enumerate(uarj5e_divs):
                        is_displayed = div.is_displayed()
                        div_text = div.text.strip()
                        logger.debug(f"  [{i}] displayed={is_displayed}, text='{div_text}'")
                        if is_displayed and div_text and div_text not in ['Xóa hết câu trả lời', 'Clear']:
                            submit_btn = div
                            logger.info(f"Found submit button (uArJ5e): '{div_text}'")
                            break
                except Exception as e:
                    logger.debug(f"Method 4 (uArJ5e loop) error: {e}")
            
            if submit_btn:
                # Scroll to make sure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                time.sleep(1)
                
                # Try to click it
                btn_text = submit_btn.text.strip() if submit_btn.text else "Submit"
                logger.info(f"Attempting to click submit button: '{btn_text}'")
                try:
                    submit_btn.click()
                    logger.info("✓ Clicked submit button successfully")
                except Exception as e:
                    logger.warning(f"Normal click failed: {e}, trying JavaScript click")
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    logger.info("✓ JavaScript clicked submit button")
                
                time.sleep(3)
                logger.info("✓ Form submitted successfully")
            else:
                logger.error("❌ Could not find submit button")
                # Debug: list all divs with role=button
                try:
                    all_role_buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
                    logger.error(f"All role=button elements ({len(all_role_buttons)}):")
                    for i, btn in enumerate(all_role_buttons):
                        logger.error(f"  [{i}] text='{btn.text}' | class='{btn.get_attribute('class')}' | displayed={btn.is_displayed()}")
                except Exception as e:
                    logger.error(f"Error listing buttons: {e}")
        
        except Exception as e:
            logger.error(f"Error submitting form: {e}", exc_info=True)
    
    def _fill_form_for_thread(self, driver):
        """🆕 Điền form - phiên bản thread-safe (dùng driver được pass vào), hỗ trợ multi-page"""
        logger.info(f"Starting to fill form with {len(self.answers)} answers (thread-safe, multi-page)")
        
        page_number = 1
        questions_filled = 0
        
        while True:
            logger.info(f"\n{'='*60}")
            logger.info(f"FILLING PAGE {page_number} (thread-safe)")
            logger.info(f"{'='*60}")
            
            time.sleep(1)
            
            # Find all question elements on current page
            question_elements = driver.find_elements(By.XPATH, "//div[@role='listitem']")
            if len(question_elements) == 0:
                question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            
            logger.info(f"Found {len(question_elements)} questions on page {page_number}")
            
            if len(question_elements) == 0:
                logger.warning("No question elements found - might be at end")
                break
            
            # Fill all questions on current page
            for local_idx, question_element in enumerate(question_elements):
                try:
                    idx = questions_filled + local_idx
                    
                    if idx >= len(self.answers):
                        logger.warning(f"Question {idx} exceeds answers count")
                        continue
                    
                    answer = self.answers[idx]
                    q_type = self.questions[idx]['type']
                    question_title = self.questions[idx]['title']
                    
                    logger.info(f"Filling Q{idx + 1} ({q_type}): {question_title}")
                    logger.info(f"  Answer: {answer}")
                    
                    if q_type == "short_answer" or q_type == "long_answer":
                        self._fill_text_field_for_thread(driver, question_element, str(answer))
                    
                    elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                        if isinstance(answer, tuple) and answer[0] == 'random':
                            options_list = answer[1]
                            selected_option = self._select_by_percentage(options_list)
                            logger.info(f"Random Mode - Selected: {selected_option}")
                            self._select_option_for_thread(driver, question_element, selected_option)
                        else:
                            self._select_option_for_thread(driver, question_element, str(answer))
                    
                    elif q_type == "checkbox":
                        if isinstance(answer, tuple) and answer[0] == 'random':
                            options_list = answer[1]
                            selected_option = self._select_by_percentage(options_list)
                            logger.info(f"Random Mode - Selected: {selected_option}")
                            self._select_option_for_thread(driver, question_element, selected_option)
                        else:
                            if isinstance(answer, list):
                                for option_text in answer:
                                    self._select_option_for_thread(driver, question_element, str(option_text))
                            else:
                                self._select_option_for_thread(driver, question_element, str(answer))
                
                except Exception as e:
                    logger.warning(f"Error filling question {idx}: {e}", exc_info=True)
            
            questions_filled += len(question_elements)
            
            # Check for next page button
            logger.info(f"\nPage {page_number} filled - checking for next page button...")
            time.sleep(1)
            
            next_button = None
            continue_xpaths = [
                ("//button//span[contains(text(), 'Tiếp')]", "Tiếp span in button"),
                ("//button[contains(@aria-label, 'Tiếp')]", "Tiếp aria button"),
                ("//div[@role='button']//span[contains(text(), 'Tiếp')]", "Tiếp in div button"),
            ]
            
            for button_xpath, button_name in continue_xpaths:
                try:
                    buttons = driver.find_elements(By.XPATH, button_xpath)
                    if buttons and len(buttons) > 0:
                        next_button = buttons[0]
                        logger.info(f"✓ Found next page button: {button_name}")
                        break
                except:
                    pass
            
            if next_button:
                try:
                    logger.info(f"⏭️ Clicking 'Tiếp' button to go to page {page_number + 1}...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    page_number += 1
                    continue
                except Exception as e:
                    logger.error(f"Error clicking next button: {e}")
                    break
            else:
                logger.info("✓ No more 'Tiếp' buttons found - reached last page")
                break
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Form filling complete - filled {questions_filled} questions")
        logger.info(f"{'='*60}\n")
    
    def _fill_text_field_for_thread(self, driver, question_element, value: str):
        """🆕 Điền text field - thread-safe"""
        try:
            input_field = None
            try:
                input_field = question_element.find_element(By.CSS_SELECTOR, "input[type='text']")
            except:
                try:
                    input_field = question_element.find_element(By.TAG_NAME, "textarea")
                except:
                    pass
            
            if input_field:
                input_field.click()
                input_field.clear()
                input_field.send_keys(value)
                time.sleep(0.5)
        
        except Exception as e:
            logger.warning(f"Error filling text field: {e}")
    
    def _select_option_for_thread(self, driver, question_element, option_text: str):
        """🆕 Chọn option - thread-safe"""
        try:
            logger.debug(f"Trying to select: {option_text}")
            
            # Method 1: Try via YKDB3e class (old way)
            try:
                options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
                for option in options:
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        if label.text.strip() == option_text.strip():
                            option.click()
                            logger.info(f"✓ Clicked option via YKDB3e: {option_text}")
                            time.sleep(0.5)
                            return
                    except:
                        pass
            except:
                pass
            
            # Method 2: Find radio button by label text
            try:
                radios = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                for radio in radios:
                    parent = radio.find_element(By.XPATH, "..")
                    labels = parent.find_elements(By.TAG_NAME, "label")
                    for lbl in labels:
                        if lbl.text.strip() == option_text.strip():
                            radio.click()
                            logger.info(f"✓ Clicked radio by label: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
            
            # Method 3: Find checkbox by label text
            try:
                checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                for cb in checkboxes:
                    parent = cb.find_element(By.XPATH, "..")
                    labels = parent.find_elements(By.TAG_NAME, "label")
                    for lbl in labels:
                        if lbl.text.strip() == option_text.strip():
                            cb.click()
                            logger.info(f"✓ Clicked checkbox by label: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
            
            # Method 4: Find by span text
            try:
                spans = question_element.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    if span.text.strip() == option_text.strip():
                        try:
                            span.click()
                            logger.info(f"✓ Clicked span: {option_text}")
                            time.sleep(0.5)
                            return
                        except:
                            parent = span.find_element(By.XPATH, "..")
                            parent.click()
                            logger.info(f"✓ Clicked span parent: {option_text}")
                            time.sleep(0.5)
                            return
            except:
                pass
        
        except Exception as e:
            logger.error(f"Error selecting option '{option_text}': {e}")
    
    def _submit_form_for_thread(self, driver):
        """🆕 Gửi form - thread-safe version"""
        try:
            logger.info("Looking for submit button...")
            submit_btn = None
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Method 1: Find by unique class Y5sE8d
            try:
                submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'Y5sE8d')]")
                logger.info(f"Found submit button by class Y5sE8d")
            except:
                pass
            
            # Method 2: Find by class QvWxOd
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by class QvWxOd")
                except:
                    pass
            
            # Method 3: Find by combined classes
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e') and contains(@class, 'Y5sE8d') and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by combined classes")
                except:
                    pass
            
            # Method 4: Find second uArJ5e div
            if not submit_btn:
                try:
                    uarj5e_divs = driver.find_elements(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e')]")
                    for i, div in enumerate(uarj5e_divs):
                        is_displayed = div.is_displayed()
                        div_text = div.text.strip()
                        if is_displayed and div_text and div_text not in ['Xóa hết câu trả lời', 'Clear']:
                            submit_btn = div
                            logger.info(f"Found submit button (uArJ5e)")
                            break
                except:
                    pass
            
            if submit_btn:
                try:
                    driver.execute_script("arguments[0].click();", submit_btn)
                    logger.info(f"✓ Clicked submit button via JS")
                except:
                    submit_btn.click()
                    logger.info(f"✓ Clicked submit button")
                
                time.sleep(3)
            else:
                logger.error("❌ Could not find submit button")
        
        except Exception as e:
            logger.error(f"Error submitting form: {e}", exc_info=True)


class GoogleFormFillerApp(QMainWindow):
    """Ứng dụng chính"""
    
    def __init__(self):
        super().__init__()
        self.form_url = ""
        self.questions = []
        self.answers = {}
        self.worker = None
        self.random_mode = False  # Toggle random mode
        self.max_parallel_tabs = 1  # 🆕 Số tabs parallel (1-5)
        
        self.initUI()
    
    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("🤖 Google Form Auto Filler v3 - Like Google Form")
        self.setGeometry(100, 100, 1200, 850)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #003d82;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
                color: black;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #ddd;
            }
            QTabBar::tab:selected {
                background-color: white;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab 1: Input
        tab1 = self.createInputTab()
        tabs.addTab(tab1, "📌 Nhập URL")
        
        # Tab 2: Questions
        tab2 = self.createQuestionsTab()
        tabs.addTab(tab2, "📋 Câu Hỏi")
        
        # Tab 3: Answers
        tab3 = self.createAnswersTab()
        tabs.addTab(tab3, "✏️ Chọn Đáp Án")
        
        # Tab 4: Submission
        tab4 = self.createSubmissionTab()
        tabs.addTab(tab4, "📤 Gửi")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Sẵn sàng")
    
    def createInputTab(self) -> QWidget:
        """Tạo tab nhập URL"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Nhập URL Google Form")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Info
        info = QLabel("Sao chép URL từ thanh địa chỉ của Google Form")
        info.setFont(QFont("Arial", 10))
        layout.addWidget(info)
        
        # URL input
        layout.addWidget(QLabel("Google Form URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.google.com/forms/d/e/...")
        layout.addWidget(self.url_input)
        
        # Load button
        self.load_btn = QPushButton("🔍 Lấy Thông Tin Form")
        self.load_btn.clicked.connect(self.loadFormInfo)
        layout.addWidget(self.load_btn)
        
        # Progress
        self.load_progress = QTextEdit()
        self.load_progress.setReadOnly(True)
        self.load_progress.setMaximumHeight(250)
        layout.addWidget(self.load_progress)
        
        layout.addStretch()
        
        return widget
    
    def createQuestionsTab(self) -> QWidget:
        """Tạo tab câu hỏi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Danh Sách Câu Hỏi")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        self.questions_list = QListWidget()
        layout.addWidget(self.questions_list)
        
        return widget
    
    def createAnswersTab(self) -> QWidget:
        """Tạo tab chọn đáp án (giống Google Form)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Chọn Đáp Án (Click như Google Form)")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Random mode toggle
        random_mode_layout = QHBoxLayout()
        self.random_mode_checkbox = QCheckBox("🎲 Chế Độ Chọn Ngẫu Nhiên (Random Mode)")
        self.random_mode_checkbox.stateChanged.connect(self.onRandomModeToggled)
        self.random_mode_checkbox.setStyleSheet("QCheckBox { color: black; font-weight: bold; }")
        random_mode_layout.addWidget(self.random_mode_checkbox)
        random_mode_layout.addStretch()
        layout.addLayout(random_mode_layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        
        self.answers_container = QWidget()
        self.answers_container.setStyleSheet("background-color: white;")
        self.answers_layout = QVBoxLayout(self.answers_container)
        
        scroll.setWidget(self.answers_container)
        layout.addWidget(scroll)
        
        return widget
    
    def createSubmissionTab(self) -> QWidget:
        """Tạo tab gửi responses"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Gửi Responses")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Count spinbox
        layout.addWidget(QLabel("Số lượng responses:"))
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setMinimum(1)
        self.count_spinbox.setMaximum(1000)
        self.count_spinbox.setValue(1)
        layout.addWidget(self.count_spinbox)
        
        # 🆕 Parallel tabs control
        parallel_layout = QHBoxLayout()
        parallel_label = QLabel("⚡ Số tabs Chrome chạy song song:")
        parallel_label.setFont(QFont("Arial", 10))
        parallel_layout.addWidget(parallel_label)
        
        self.parallel_spinbox = QSpinBox()
        self.parallel_spinbox.setMinimum(1)
        self.parallel_spinbox.setMaximum(5)
        self.parallel_spinbox.setValue(1)
        self.parallel_spinbox.setToolTip("1 = Tuần tự\n2-5 = Parallel (nhanh hơn)\nVí dụ: 5 tabs = 5x nhanh")
        self.parallel_spinbox.setMaximumWidth(80)
        parallel_layout.addWidget(self.parallel_spinbox)
        
        parallel_info = QLabel("(1=tuần tự, 2-5=song song)")
        parallel_info.setFont(QFont("Arial", 9))
        parallel_info.setStyleSheet("color: #666;")
        parallel_layout.addWidget(parallel_info)
        parallel_layout.addStretch()
        
        layout.addLayout(parallel_layout)
        
        # Submit button
        self.submit_btn = QPushButton("📤 Bắt Đầu Gửi")
        self.submit_btn.clicked.connect(self.startSubmission)
        layout.addWidget(self.submit_btn)
        
        # Progress bar
        self.submission_progress = QProgressBar()
        layout.addWidget(self.submission_progress)
        
        # Log
        self.submission_log = QTextEdit()
        self.submission_log.setReadOnly(True)
        layout.addWidget(self.submission_log)
        
        return widget
    
    def loadFormInfo(self):
        """Lấy thông tin form"""
        self.form_url = self.url_input.text().strip()
        
        if not self.form_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL form")
            return
        
        self.load_btn.setEnabled(False)
        self.load_progress.clear()
        self.load_progress.append("⏳ Đang tải thông tin form...\n")
        
        self.worker = GoogleFormWorker(self.form_url)
        self.worker.progress.connect(self.updateLoadProgress)
        self.worker.finished.connect(self.onFormLoaded)
        self.worker.error.connect(self.onLoadError)
        self.worker.start()
    
    def updateLoadProgress(self, message: str):
        """Cập nhật progress"""
        self.load_progress.append(message)
    
    def onFormLoaded(self, questions: List[Dict]):
        """Khi form được tải thành công"""
        self.questions = questions
        self.load_progress.append(f"\n✅ Đã tải {len(questions)} câu hỏi thành công!")
        self.load_btn.setEnabled(True)
        
        # Cập nhật tab questions
        self.questions_list.clear()
        for q in questions:
            q_type = q['type']
            num_options = len(q['options'])
            
            type_map = {
                "multiple_choice": "Chọn một",
                "checkbox": "Chọn nhiều",
                "dropdown": "Dropdown",
                "short_answer": "Trả lời ngắn",
                "long_answer": "Trả lời dài",
                "linear_scale": "Thang điểm",
                "multiple_choice_grid": "Bảng chọn",
                "unknown": "❓ Unknown"
            }
            type_str = type_map.get(q_type, "Unknown")
            
            if num_options > 0:
                item_text = f"{q['index'] + 1}. {q['title'][:50]}... ({type_str}) - {num_options} lựa chọn"
            else:
                item_text = f"{q['index'] + 1}. {q['title'][:50]}... ({type_str})"
            
            item = QListWidgetItem(item_text)
            self.questions_list.addItem(item)
        
        # Tạo input fields cho answers
        self.createAnswerInputs()
        
        QMessageBox.information(self, "Thành Công", f"✅ Đã tải {len(questions)} câu hỏi!\n\nChuyển sang tab 'Chọn Đáp Án' để chọn câu trả lời")
    
    def onLoadError(self, error: str):
        """Khi có lỗi"""
        self.load_progress.append(f"\n❌ {error}")
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi", error)
    
    def createAnswerInputs(self):
        """Tạo input fields cho đáp án - UI giống Google Form"""
        # Clear previous
        while self.answers_layout.count():
            widget = self.answers_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        self.answer_widgets = {}
        
        for q in self.questions:
            idx = q['index']
            q_type = q['type']
            title = q['title']
            options = q['options']
            
            # Question frame
            question_frame = QFrame()
            question_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0px;
                }
            """)
            question_layout = QVBoxLayout(question_frame)
            
            # Question title
            label = QLabel(f"{idx + 1}. {title}")
            label.setFont(QFont("Arial", 12, QFont.Bold))
            label.setWordWrap(True)
            question_layout.addWidget(label)
            
            # Required indicator
            if q['required']:
                required_label = QLabel("* Bắt buộc")
                required_label.setFont(QFont("Arial", 9))
                required_label.setStyleSheet("color: #d32f2f;")
                question_layout.addWidget(required_label)
            
            question_layout.addSpacing(10)
            
            # Options or input
            # Smart logic: if we have options, use them regardless of detected type
            if options and len(options) > 0:
                # If we extracted options, treat as multiple choice
                if self.random_mode:
                    # Random mode: use checkboxes with percentage inputs
                    checkbox_list = []
                    for opt in options:
                        # Create a row with checkbox and percentage spinbox
                        row_layout = QHBoxLayout()
                        
                        cb = QCheckBox(opt['text'])
                        cb.setMinimumHeight(40)
                        font = QFont()
                        font.setPointSize(12)
                        cb.setFont(font)
                        cb.setStyleSheet("""
                            QCheckBox {
                                font-size: 12px;
                                padding: 8px 5px;
                                spacing: 8px;
                                color: black;
                            }
                            QCheckBox:hover {
                                background-color: #f5f5f5;
                                border-radius: 4px;
                            }
                            QCheckBox::indicator {
                                width: 18px;
                                height: 18px;
                            }
                        """)
                        
                        # Percentage spinbox
                        percent_label = QLabel("Tỉ lệ (%):")
                        percent_label.setFont(QFont("Arial", 10))
                        
                        percent_spinbox = QSpinBox()
                        percent_spinbox.setMinimum(0)
                        percent_spinbox.setMaximum(100)
                        percent_spinbox.setValue(0)
                        percent_spinbox.setMaximumWidth(80)
                        percent_spinbox.setStyleSheet("""
                            QSpinBox {
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                padding: 5px;
                                color: black;
                                font-size: 11px;
                            }
                        """)
                        
                        row_layout.addWidget(cb)
                        row_layout.addStretch()
                        row_layout.addWidget(percent_label)
                        row_layout.addWidget(percent_spinbox)
                        
                        question_layout.addLayout(row_layout)
                        checkbox_list.append((cb, percent_spinbox, opt['text']))
                    
                    self.answer_widgets[idx] = ('random', checkbox_list)
                else:
                    # Normal mode: use radio buttons (single select)
                    group = QButtonGroup()
                    self.answer_widgets[idx] = group
                    
                    for opt in options:
                        radio_btn = QRadioButton(opt['text'])
                        radio_btn.setMinimumHeight(40)
                        font = QFont()
                        font.setPointSize(12)
                        radio_btn.setFont(font)
                        radio_btn.setStyleSheet("""
                            QRadioButton {
                                font-size: 12px;
                                padding: 8px 5px;
                                spacing: 8px;
                                color: black;
                            }
                            QRadioButton:hover {
                                background-color: #f5f5f5;
                                border-radius: 4px;
                            }
                            QRadioButton::indicator {
                                width: 18px;
                                height: 18px;
                            }
                        """)
                        group.addButton(radio_btn, opt['index'])
                        question_layout.addWidget(radio_btn)
            
            elif q_type == "short_answer":
                widget = QLineEdit()
                widget.setPlaceholderText("Nhập câu trả lời của bạn")
                widget.setMinimumHeight(40)
                question_layout.addWidget(widget)
                self.answer_widgets[idx] = widget
            
            elif q_type == "long_answer":
                widget = QTextEdit()
                widget.setPlaceholderText("Nhập câu trả lời của bạn")
                widget.setMinimumHeight(100)
                question_layout.addWidget(widget)
                self.answer_widgets[idx] = widget
            
            elif q_type == "checkbox":
                # Multiple select - use checkboxes
                checkboxes = []
                for opt in options:
                    cb = QCheckBox(opt['text'])
                    cb.setMinimumHeight(40)
                    font = QFont()
                    font.setPointSize(12)
                    cb.setFont(font)
                    cb.setStyleSheet("""
                        QCheckBox {
                            font-size: 12px;
                            padding: 8px 5px;
                            spacing: 8px;
                            color: black;
                        }
                        QCheckBox:hover {
                            background-color: #f5f5f5;
                            border-radius: 4px;
                        }
                        QCheckBox::indicator {
                            width: 18px;
                            height: 18px;
                        }
                    """)
                    checkboxes.append((cb, opt['text']))
                    question_layout.addWidget(cb)
                self.answer_widgets[idx] = checkboxes
            
            elif q_type == "dropdown":
                combo = QComboBox()
                combo.addItem("-- Chọn --")
                if options:
                    for opt in options:
                        combo.addItem(opt['text'])
                combo.setMinimumHeight(40)
                question_layout.addWidget(combo)
                self.answer_widgets[idx] = combo
            
            elif q_type in ["linear_scale", "multiple_choice_grid"]:
                # These types have options
                if options:
                    group = QButtonGroup()
                    self.answer_widgets[idx] = group
                    
                    for opt in options:
                        radio_btn = QRadioButton(opt['text'])
                        radio_btn.setMinimumHeight(40)
                        font = QFont()
                        font.setPointSize(12)
                        radio_btn.setFont(font)
                        radio_btn.setStyleSheet("""
                            QRadioButton {
                                font-size: 12px;
                                padding: 8px 5px;
                                spacing: 8px;
                                color: black;
                            }
                            QRadioButton:hover {
                                background-color: #f5f5f5;
                                border-radius: 4px;
                            }
                            QRadioButton::indicator {
                                width: 18px;
                                height: 18px;
                            }
                        """)
                        group.addButton(radio_btn, opt['index'])
                        question_layout.addWidget(radio_btn)
                else:
                    # Fallback to text input
                    widget = QLineEdit()
                    widget.setPlaceholderText("Nhập câu trả lời của bạn")
                    widget.setMinimumHeight(40)
                    question_layout.addWidget(widget)
                    self.answer_widgets[idx] = widget
            
            else:
                # For any unknown type, default to text input (safer than error)
                widget = QLineEdit()
                widget.setPlaceholderText("Nhập câu trả lời của bạn")
                widget.setMinimumHeight(40)
                question_layout.addWidget(widget)
                self.answer_widgets[idx] = widget
            
            question_layout.addStretch()
            
            self.answers_layout.addWidget(question_frame)
        
        self.answers_layout.addStretch()
    
    def onRandomModeToggled(self, state):
        """Xử lý toggle chế độ random"""
        self.random_mode = (state == Qt.Checked)
        logger.info(f"Random mode toggled: {self.random_mode}")
        # Recreate answer inputs when random mode changes
        if self.questions:
            self.createAnswerInputs()
    
    def startSubmission(self):
        """Bắt đầu gửi responses"""
        if not self.questions:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tải form trước")
            return
        
        # Lấy đáp án từ widgets
        self.answers = self.getAnswersFromWidgets()
        
        if not self.answers:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một câu trả lời")
            return
        
        count = self.count_spinbox.value()
        max_parallel = self.parallel_spinbox.value()  # 🆕 Lấy số tabs parallel
        logger.info(f"[SUBMIT] count_spinbox.value() = {count}, max_parallel = {max_parallel}")
        
        if count <= 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số responses > 0")
            return
        
        if count > 100:
            reply = QMessageBox.question(
                self, "Xác nhận",
                f"Bạn sắp gửi {count} responses với {max_parallel} tabs. Tiếp tục?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.submission_log.clear()
        self.submission_progress.setMaximum(count)
        self.submission_progress.setValue(0)
        self.submit_btn.setEnabled(False)
        
        logger.info(f"[SUBMIT] Creating SubmissionWorker with count={count}, max_parallel={max_parallel}")
        self.worker = SubmissionWorker(self.form_url, self.answers, count, self.questions, max_parallel)  # 🆕 Pass max_parallel
        self.worker.progress.connect(self.updateSubmissionLog)
        self.worker.count_progress.connect(self.submission_progress.setValue)
        self.worker.finished.connect(self.onSubmissionFinished)
        self.worker.error.connect(self.onSubmissionError)
        logger.info(f"[SUBMIT] Starting worker thread")
        self.worker.start()
        logger.info(f"[SUBMIT] Worker thread started")
    
    def getAnswersFromWidgets(self) -> Dict:
        """Lấy đáp án từ widgets - hỗ trợ cả chế độ bình thường và random"""
        answers = {}
        
        for idx, widget in self.answer_widgets.items():
            # Handle random mode with checkboxes and percentages
            if isinstance(widget, tuple) and widget[0] == 'random':
                checkbox_list = widget[1]
                random_answer = []
                for cb, percent_spinbox, option_text in checkbox_list:
                    if cb.isChecked():
                        percent_value = percent_spinbox.value()
                        if percent_value > 0:
                            random_answer.append({
                                'text': option_text,
                                'percentage': percent_value
                            })
                
                if random_answer:
                    # Validate percentages sum to 100%
                    total_percent = sum(item['percentage'] for item in random_answer)
                    if total_percent != 100:
                        QMessageBox.warning(
                            self, "Lỗi",
                            f"Câu {idx + 1}: Tổng tỉ lệ phải bằng 100% (hiện tại: {total_percent}%)"
                        )
                        return {}
                    answers[idx] = ('random', random_answer)
            
            elif isinstance(widget, QLineEdit):
                if widget.text().strip():
                    answers[idx] = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                if widget.toPlainText().strip():
                    answers[idx] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                if widget.currentIndex() > 0:
                    answers[idx] = widget.currentText()
            elif isinstance(widget, QButtonGroup):
                # Radio button group
                checked_btn = widget.checkedButton()
                if checked_btn:
                    answers[idx] = checked_btn.text()
            elif isinstance(widget, list):
                # Checkboxes list
                selected = [text for cb, text in widget if cb.isChecked()]
                if selected:
                    answers[idx] = selected
        
        return answers
    
    def updateSubmissionLog(self, message: str):
        """Cập nhật log gửi"""
        self.submission_log.append(message)
        self.submission_log.verticalScrollBar().setValue(
            self.submission_log.verticalScrollBar().maximum()
        )
    
    def onSubmissionFinished(self):
        """Khi gửi xong"""
        self.submission_log.append("\n✅ Hoàn tất! Đã gửi tất cả responses")
        self.submit_btn.setEnabled(True)
        QMessageBox.information(self, "Thành Công", "✅ Đã gửi tất cả responses thành công!")
    
    def onSubmissionError(self, error: str):
        """Khi có lỗi gửi"""
        self.submission_log.append(f"\n❌ {error}")
        self.submit_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi", error)
    
    def closeEvent(self, event):
        """Xử lý khi đóng app"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Xác nhận",
                "Tác vụ đang chạy. Bạn có muốn đóng?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()


def main():
    """Hàm main"""
    app = QApplication(sys.argv)
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = exception_handler
    
    window = GoogleFormFillerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
