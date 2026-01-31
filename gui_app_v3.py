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
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
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
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            
            # Use webdriver_manager to handle chromedriver automatically
            try:
                try:
                    self.driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=options
                    )
                except Exception as e1:
                    logger.warning(f"webdriver_manager failed: {e1}")
                    # Fallback: Use system Chrome
                    self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                logger.error(f"Failed to initialize Chrome: {e}")
                self.error_signal.emit(f"Không thể khởi động Chrome: {e}")
                return
            
            self.driver.get(form_url)
            
            # Wait for form to load - try multiple selectors
            logger.info("Waiting for form to load...")
            time.sleep(8)  # Increased to 8 seconds to ensure elements load
            
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
                # For editor links: All questions on 1 page, no need to click "Tiếp"
                logger.info("✓ Editor link detected - extracting all questions from single page")
                self.progress.emit("📋 Link editor - tất cả câu hỏi được hiển thị trên 1 trang")
                is_editor_link = True
            
            # 🆕 SIMPLIFIED EXTRACTION FOR EDITOR LINK
            if is_editor_link:
                logger.info(f"\n{'='*60}")
                logger.info(f"EXTRACTING FROM EDITOR LINK (Single Page)")
                logger.info(f"{'='*60}")
                # Find all questions on editor link (all on 1 page)
                time.sleep(3)  # Wait for page to fully load
                
                # NEW METHOD: Get questions directly from .editable divs with aria-label
                # The form editor uses contenteditable divs with specific aria-labels
                try:
                    import unicodedata
                    
                    # Find ALL .editable divs that are questions or section headers
                    all_editable = self.driver.find_elements(By.CLASS_NAME, "editable")
                    
                    logger.info(f"Found {len(all_editable)} .editable divs total")
                    
                    # Store data immediately to avoid stale references
                    editable_data = []
                    for elem in all_editable:
                        aria = elem.get_attribute('aria-label') or ""
                        text = elem.text.strip() if elem.text else ""
                        # Normalize Unicode for proper comparison
                        aria_normalized = unicodedata.normalize('NFC', aria)
                        editable_data.append({
                            'aria': aria_normalized,
                            'text': text,
                            'elem': elem
                        })
                    
                    # Process elements
                    combined = []
                    for item in editable_data:
                        aria = item['aria']
                        text = item['text']
                        elem = item['elem']
                        
                        # Check if question (aria-label="Câu hỏi")
                        if aria == "Câu hỏi" and text:
                            combined.append(("question", elem, text))
                        # Check if section header
                        elif aria in ("Tiêu đề phần (không bắt buộc)", "Tiêu đề phần") and text:
                            combined.append(("section", elem, text))
                    
                    if len(combined) == 0:
                        self.error.emit("❌ Form trống hoặc URL không hợp lệ!")
                        return
                    
                    logger.info(f"Processing {len(combined)} items (questions + sections)")
                    
                except Exception as e:
                    logger.debug(f"New method failed: {e}")
                    logger.debug(f"Error: {traceback.format_exc()}")
                    self.error.emit(f"❌ Lỗi khi đọc form: {str(e)}")
                    return
                
                # Extract all questions and sections
                for item_type, elem, title in combined:
                    try:
                        if item_type == "section":
                            # This is a section header
                            logger.info(f"  📌 Section header: '{title}'")
                            
                            section_data = {
                                "index": len(self.questions),
                                "title": title,
                                "type": "section_header",
                                "options": [],
                                "required": False,
                                "element": elem,
                                "is_page_title": True
                            }
                            self.questions.append(section_data)
                            self.progress.emit(f"📌 {title}")
                            continue
                        
                        # This is a question
                        if not title:
                            logger.debug(f"  Skipping question with empty text")
                            continue
                        
                        # Find parent container to get options
                        parent_container = self.driver.execute_script("""
                            let el = arguments[0];
                            while (el && el.parentElement) {
                                if (el.getAttribute('data-item-id')) {
                                    return el;
                                }
                                el = el.parentElement;
                            }
                            return null;
                        """, elem)
                        
                        if not parent_container:
                            logger.debug(f"  Skipping - no parent container found")
                            continue
                        
                        q_type = self._get_question_type(parent_container)
                        options_list = self._get_options_complete(parent_container)
                        
                        question_data = {
                            "index": len(self.questions),
                            "title": title,
                            "type": q_type,
                            "options": options_list,
                            "required": self._is_required(elem),
                            "element": elem,
                            "is_page_title": False
                        }
                        
                        self.questions.append(question_data)
                        self.progress.emit(f"✓ Câu {len(self.questions)}: {title[:40]}... ({self._format_type(q_type)}) - {len(options_list)} lựa chọn")
                        logger.info(f"Question {len(self.questions)}: {title[:40]} ({q_type}) - {len(options_list)} options")
                        
                        if options_list:
                            for opt in options_list:
                                logger.debug(f"    - {opt['text']}")
                    except Exception as e:
                        logger.error(f"Error processing question: {e}\n{traceback.format_exc()}")
                        self.progress.emit(f"⚠️ Lỗi câu {len(self.questions)}: {str(e)}")
                
                logger.info(f"\n{'='*60}")
                logger.info(f"✓ EXTRACTION COMPLETE")
                logger.info(f"Total questions: {len(self.questions)}")
                logger.info(f"{'='*60}\n")
                self.progress.emit(f"✅ Hoàn thành! Tổng cộng {len(self.questions)} câu hỏi")
                self.finished.emit(self.questions)
                return
            
            # 🆕 Loop through multiple pages until submit button appears (for viewform links)
            # NOTE: Not used for editor links since we exit above
            page_count = 1
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"EXTRACTING QUESTIONS FROM PAGE {page_count}")
                logger.info(f"{'='*60}")
                
                # Try to find questions using multiple strategies
                question_elements = []
                
                # Try new selector first (data-item-id), fallback to role='listitem', then Qr7Oae
                try:
                    question_elements = self.driver.find_elements(By.XPATH, "//*[@data-item-id]")
                    if len(question_elements) > 0:
                        logger.info(f"Found {len(question_elements)} elements with data-item-id")
                    else:
                        question_elements = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
                        if len(question_elements) > 0:
                            logger.info(f"Found {len(question_elements)} elements with role='listitem'")
                        else:
                            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                            logger.info(f"Found {len(question_elements)} elements with class 'Qr7Oae'")
                except Exception as e:
                    logger.debug(f"Error finding questions: {e}")
                    try:
                        question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                        logger.info(f"Found {len(question_elements)} elements with class 'Qr7Oae'")
                    except:
                        pass
                
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
                        # Check if this is a section header/page break
                        is_section_header = self._is_section_header(question_element)
                        if is_section_header:
                            # Get the section header text (e.g., "Phần 1 / 2")
                            header_text = self._get_section_header_text(question_element)
                            logger.info(f"  📌 Section header detected: '{header_text}'")
                            
                            # Save section header as metadata
                            section_data = {
                                "index": len(self.questions),
                                "title": header_text,
                                "type": "section_header",
                                "options": [],
                                "required": False,
                                "element": question_element,
                                "is_page_title": True
                            }
                            self.questions.append(section_data)
                            self.progress.emit(f"📌 Trang: {header_text}")
                            logger.info(f"Saved section header: {header_text}")
                            page_count += 1
                            continue
                        
                        title = self._get_question_text(question_element)
                        q_type = self._get_question_type(question_element)
                        
                        # Skip if no title found
                        if not title or title == "Untitled Question":
                            logger.debug(f"  Skipping element with no title")
                            continue
                        
                        options_list = self._get_options_complete(question_element)
                        
                        question_data = {
                            "index": len(self.questions),
                            "title": title,
                            "type": q_type,
                            "options": options_list,
                            "required": self._is_required(question_element),
                            "element": question_element,
                            "is_page_title": False
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
                # 🆕 KHÔNG TỰ ĐỘNG CLICK - chỉ detect và dừng
                # Form sẽ tự động scroll/chuyển trang khi user submit
                continue_xpaths = [
                    ("//button//span[contains(text(), 'Tiếp')]", "Tiếp"),
                    ("//button[contains(@aria-label, 'Tiếp')]", "Tiếp button"),
                    ("//*[contains(text(), 'Tiếp')]", "Any Tiếp"),
                    ("//button[contains(text(), 'Next')]", "Next"),
                ]
                
                has_next_button = False
                for button_xpath, button_name in continue_xpaths:
                    try:
                        next_buttons = self.driver.find_elements(By.XPATH, button_xpath)
                        if next_buttons and len(next_buttons) > 0:
                            for btn in next_buttons:
                                try:
                                    if btn.is_displayed():
                                        logger.info(f"✓ Found next page button: {button_name}")
                                        has_next_button = True
                                        break
                                except:
                                    pass
                            if has_next_button:
                                break
                    except:
                        pass
                
                if not has_next_button:
                    # No next button and no submit button - form might be ended or single page
                    logger.warning("⚠️ No next page button or submit button found - ending extraction")
                    self.progress.emit(f"✓ Hoàn thành! Tổng cộng {len(self.questions)} câu hỏi")
                    break
                
                # 🆕 If next button found, exit extraction
                # User will see all questions on current page
                # When user submits (click Tiếp in UI or our submission), form will handle page navigation
                logger.info(f"Next page button detected - extraction paused at page {page_count}")
                logger.info(f"Extracted {len(self.questions)} questions so far")
                self.progress.emit(f"✓ Hoàn thành trang {page_count}! Tổng cộng {len(self.questions)} câu hỏi")
                break  # Exit extraction loop - let user answer and submit
            
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
    def _is_actual_question(self, question_element) -> bool:
        """Kiểm tra xem element này có phải câu hỏi thực không (aria-label='Câu hỏi')"""
        try:
            # BEST METHOD: Check for aria-label="Câu hỏi" directly
            question_div = question_element.find_element(By.XPATH, ".//div[@aria-label='Câu hỏi']")
            if question_div:
                title_text = question_div.text.strip() if question_div.text else ""
                logger.debug(f"  Question found via aria-label: '{title_text}'")
                return True
        except:
            pass
        
        # Fallback: Old method - check for title + options
        try:
            # Check if has M7eMe (title)
            spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
            has_title = False
            title_text = ""
            
            for span in spans:
                text = span.get_attribute('innerText') or span.get_attribute('textContent')
                if text:
                    text = text.strip().replace('\xa0', ' ').strip()
                    # Skip section headers and empty titles
                    if "Phần" not in text and "Mục không có tiêu đề" not in text and text:
                        has_title = True
                        title_text = text
                        break
            
            if not has_title:
                return False
            
            # Check if has options - TRY MULTIPLE METHODS
            # Method 1: Check for radio/checkbox (VIEWFORM)
            radios = question_element.find_elements(By.XPATH, ".//div[@role='radio']")
            checkboxes = question_element.find_elements(By.XPATH, ".//div[@role='checkbox']")
            has_options = len(radios) > 0 or len(checkboxes) > 0
            
            # Method 2: Check for text input options (EDIT link)
            if not has_options:
                text_inputs = question_element.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf')]")
                has_options = len(text_inputs) > 0
            
            # Method 3: Check for YKDB3e (VIEWFORM fallback)
            if not has_options:
                ykdb_elements = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
                has_options = len(ykdb_elements) > 0
            
            if has_options:
                logger.debug(f"  Actual question found: {title_text[:40]} (has {len(radios)} radios, {len(checkboxes)} checkboxes)")
                return True
            
            return False
        except Exception as e:
            logger.debug(f"  _is_actual_question error: {e}")
            return False
    
    def _is_section_header(self, question_element) -> bool:
        """Kiểm tra xem element này có phải section header/page title không (aria-label='Tiêu đề phần' hoặc 'Tiêu đề biểu mẫu')
        NOTE: Bỏ qua form title (Tiêu đề biểu mẫu) - chỉ lấy section headers (Tiêu đề phần)"""
        try:
            # BEST METHOD: Check for aria-label containing "Tiêu đề"
            textboxes = question_element.find_elements(By.XPATH, ".//div[@role='textbox']")
            for tb in textboxes:
                aria = (tb.get_attribute('aria-label') or '').strip()
                
                # ONLY take section headers, skip form title
                if aria == "Tiêu đề phần (không bắt buộc)" or aria == "Tiêu đề phần":
                    logger.debug(f"  Section header detected: aria-label={aria}")
                    return True
                
                # Skip form title (Tiêu đề biểu mẫu)
                if aria == "Tiêu đề biểu mẫu":
                    logger.debug(f"  Skipping form title: aria-label={aria}")
                    return False
            
            # Fallback: Check for M7eMe span text
            spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
            for span in spans:
                text = span.get_attribute('innerText') or span.get_attribute('textContent')
                if text:
                    text = text.strip().replace('\xa0', ' ').strip()
                    # Check for "Phần X / Y" pattern (page/section header)
                    if "Phần" in text and "/" in text:
                        logger.debug(f"  Page title detected: {text}")
                        return True
                    if "Mục không có tiêu đề" in text:
                        logger.debug(f"  Section header detected: {text}")
                        return True
            
            return False
        except Exception as e:
            logger.debug(f"  _is_section_header error: {e}")
        
        return False
    
    def _get_section_header_text(self, question_element) -> str:
        """Lấy text tiêu đề phần (Phần 1 / 2, ...)"""
        try:
            # Try to find M7eMe span with page title text
            spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
            for span in spans:
                text = span.get_attribute('innerText') or span.get_attribute('textContent')
                if text:
                    text = text.strip().replace('\xa0', ' ').strip()
                    # Return if it's "Phần X / Y" or any section header
                    if text and ("Phần" in text or "Mục không có tiêu đề" in text):
                        logger.debug(f"  Got section header text: {text}")
                        return text
            return "Untitled Section"
        except Exception as e:
            logger.debug(f"  _get_section_header_text error: {e}")
            return "Untitled Section"
    
    
        type_map = {
            "multiple_choice": "Chọn một",
            "checkbox": "Chọn nhiều",
            "dropdown": "Dropdown",
            "short_answer": "Trả lời ngắn",
            "long_answer": "Trả lời dài",
            "linear_scale": "Thang điểm",
            "multiple_choice_grid": "Bảng chọn",
            "section": "Section",
            "unknown": "Unknown"
        }
        return type_map.get(q_type, "Unknown")
    
    def _auto_answer_required_fields(self):
        """Tự động trả lời các câu hỏi bắt buộc trên trang hiện tại"""
        try:
            # Find all required questions (those with red asterisk)
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            logger.info(f"Attempting to auto-answer {len(question_elements)} questions...")
            
            for q_elem in question_elements:
                try:
                    # Check if required
                    is_required = self._is_required(q_elem)
                    if not is_required:
                        continue
                    
                    logger.info(f"  Auto-answering required question...")
                    
                    # Try radio button (multiple choice)
                    radios = q_elem.find_elements(By.XPATH, ".//div[@role='radio']")
                    if radios and len(radios) > 0:
                        logger.debug(f"    Found radio - clicking first option")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", radios[0])
                        time.sleep(0.3)
                        radios[0].click()
                        continue
                    
                    # Try checkbox (select all)
                    checkboxes = q_elem.find_elements(By.XPATH, ".//div[@role='checkbox']")
                    if checkboxes and len(checkboxes) > 0:
                        logger.debug(f"    Found checkbox - clicking first option")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkboxes[0])
                        time.sleep(0.3)
                        checkboxes[0].click()
                        continue
                    
                    # Try text input
                    textareas = q_elem.find_elements(By.XPATH, ".//textarea")
                    if textareas and len(textareas) > 0:
                        logger.debug(f"    Found textarea - typing default answer")
                        textareas[0].send_keys("N/A")
                        continue
                    
                    textinputs = q_elem.find_elements(By.XPATH, ".//input[@type='text']")
                    if textinputs and len(textinputs) > 0:
                        logger.debug(f"    Found text input - typing default answer")
                        textinputs[0].send_keys("N/A")
                        continue
                        
                except Exception as e:
                    logger.debug(f"    Error auto-answering: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Auto-answer error: {e}")
    
    def _get_question_text(self, question_element) -> str:
        """Lấy text câu hỏi - lấy M7eMe text đầu tiên không rỗng"""
        try:
            # Strategy 1: Try M7eMe span (works for editor links + new structure)
            try:
                spans = question_element.find_elements(By.CLASS_NAME, "M7eMe")
                if spans:
                    for span in spans:
                        # Use get_attribute('innerText') for editor links
                        text = span.get_attribute('innerText') or span.get_attribute('textContent')
                        if text:
                            text = text.strip().replace('\xa0', ' ').strip()
                            # Skip empty, section headers (Phần X / Y), and untitled
                            if (text and 
                                "Mục không có tiêu đề" not in text and 
                                "Phần" not in text and
                                len(text) > 2):  # Skip very short text
                                logger.debug(f"  Got title via M7eMe: {text[:50]}")
                                return text
            except Exception as e:
                logger.debug(f"  Strategy 1 failed: {e}")
                pass
            
            # Strategy 2: Try heading div with JS (fallback)
            try:
                heading = question_element.find_element(By.XPATH, ".//div[@role='heading']")
                # Use JavaScript to get text from heading
                text = self.driver.execute_script("return arguments[0].textContent", heading)
                if text:
                    text = text.strip().replace('\xa0', ' ').strip()
                    # Remove asterisk (required marker)
                    text = text.replace('*', '').strip()
                    if "Mục không có tiêu đề" not in text and text:
                        logger.debug(f"  Got title via heading: {text[:50]}")
                        return text
            except Exception as e:
                logger.debug(f"  Strategy 2 failed: {e}")
                pass
            
            # Strategy 3: Try contenteditable textboxes (for view forms)
            try:
                textboxes = question_element.find_elements(By.XPATH, ".//div[@role='textbox'][@contenteditable='true']")
                if textboxes:
                    for tb in textboxes:
                        text = tb.text.strip().replace('\xa0', ' ')
                        if text and "Mục không có tiêu đề" not in text:
                            logger.debug(f"  Got title via textbox: {text[:50]}")
                            return text
            except Exception as e:
                logger.debug(f"  Strategy 3 failed: {e}")
                pass
            
            logger.debug(f"  All strategies failed")
            return "Untitled Question"
        except Exception as e:
            logger.debug(f"  Exception in _get_question_text: {e}")
            return "Untitled Question"
    
    def _get_question_type(self, question_element) -> str:
        """Xác định loại câu hỏi"""
        try:
            # Method 1: Check for role='radio' (editor links)
            radio_divs = question_element.find_elements(By.XPATH, ".//div[@role='radio']")
            if radio_divs and len(radio_divs) > 0:
                return "multiple_choice"
            
            # Method 2: Check for role='checkbox' (editor links)
            checkbox_divs = question_element.find_elements(By.XPATH, ".//div[@role='checkbox']")
            if checkbox_divs and len(checkbox_divs) > 0:
                return "checkbox"
            
            # Method 3: Check for input[type='radio'] (viewform links)
            radio_buttons = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons and len(radio_buttons) > 0:
                return "multiple_choice"
            
            # Method 4: Check for input[type='checkbox'] (viewform links)
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes and len(checkboxes) > 0:
                return "checkbox"
            
            # Method 5: Kiểm tra dropdown
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            # Method 6: Kiểm tra textarea (long answer)
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            if textareas and len(textareas) > 0:
                return "long_answer"
            
            # Method 7: Kiểm tra text input (short answer) - EXCLUDE option inputs
            text_inputs = question_element.find_elements(By.XPATH, ".//input[@type='text' and not(contains(@class, 'Hvn9fb')) and not(contains(@class, 'zHQkBf'))]")
            if text_inputs and len(text_inputs) > 0:
                return "short_answer"
            
            return "unknown"
        except:
            return "unknown"
    
    def _get_options_complete(self, question_element) -> List[Dict]:
        """Lấy danh sách lựa chọn - chỉ trong question element này"""
        options = []
        
        # Strategy 1: Find text input options with aria-label='giá trị tùy chọn' (form editor)
        # CRITICAL: Only inputs with this aria-label are actual option display fields
        try:
            # Only get inputs that are actual option value fields (not "Thêm tùy chọn" or "Khác")
            text_inputs = question_element.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf') and @aria-label='giá trị tùy chọn']")
            logger.debug(f"  Found {len(text_inputs)} text input options (aria-label filter)")
            
            if text_inputs and len(text_inputs) > 0:
                seen_values = set()  # Track seen values to avoid duplicates
                for idx, inp in enumerate(text_inputs):
                    try:
                        value = inp.get_attribute('value')
                        if value and value.strip():
                            # Only add if we haven't seen this exact value yet (avoid duplicates)
                            if value.strip() not in seen_values:
                                options.append({
                                    "index": idx,
                                    "text": value.strip()
                                })
                                seen_values.add(value.strip())
                                logger.debug(f"    Option {idx}: {value.strip()}")
                    except:
                        pass
                
                if options:
                    logger.debug(f"  Extracted {len(options)} options from text inputs")
                    return options
        except Exception as e:
            logger.debug(f"  Text input aria-label strategy failed: {e}")
        
        # Strategy 2: Without aria-label filter but limit - fallback if strategy 1 fails
        try:
            text_inputs = question_element.find_elements(By.XPATH, ".//input[@type='text' and contains(@class, 'Hvn9fb') and contains(@class, 'zHQkBf')]")
            logger.debug(f"  Found {len(text_inputs)} text input options (no filter)")
            
            if text_inputs and len(text_inputs) > 0:
                # LIMIT: Only take first 20 (max realistic number of options per question)
                text_inputs_limited = text_inputs[:20]
                
                seen_values = set()
                for idx, inp in enumerate(text_inputs_limited):
                    try:
                        value = inp.get_attribute('value')
                        # Only add if value exists
                        if value and value.strip():
                            # Skip if value is clearly metadata (too long, contains special chars)
                            text_value = value.strip()
                            if not any(x in text_value for x in ['jsname', 'data-', 'aria-']) and text_value not in seen_values:
                                options.append({
                                    "index": idx,
                                    "text": text_value
                                })
                                seen_values.add(text_value)
                                logger.debug(f"    Option {idx}: '{text_value}'")
                    except:
                        pass
                
                if options:
                    logger.debug(f"  Extracted {len(options)} options from text inputs")
                    return options
        except Exception as e:
            logger.debug(f"  Text input fallback strategy failed: {e}")
        
        try:
            # Lấy tất cả radio buttons để đếm số options
            radio_divs = question_element.find_elements(By.XPATH, ".//div[@role='radio']")
            logger.debug(f"  Found {len(radio_divs)} radio buttons")
            
            if len(radio_divs) == 0:
                logger.debug(f"  No radio buttons, trying checkboxes")
                radio_divs = question_element.find_elements(By.XPATH, ".//div[@role='checkbox']")
            
            if radio_divs and len(radio_divs) > 0:
                # Lấy tất cả span.OIC90c
                all_oic_spans = question_element.find_elements(By.CLASS_NAME, "OIC90c")
                logger.debug(f"  Found {len(all_oic_spans)} total OIC90c spans, need to extract {len(radio_divs)} options")
                
                # Filter: lấy OIC90c spans mà có text và không phải "Mô tả", "Chú thích", v.v
                option_texts = []
                for span in all_oic_spans:
                    try:
                        text = self.driver.execute_script("return arguments[0].innerText || arguments[0].textContent", span)
                        text = text.strip() if text else ""
                        
                        # Skip empty, labels, and common non-option texts
                        if (text and 
                            not any(x in text.lower() for x in ['mô tả', 'chú thích', 'mục khác', 'bắt buộc', 'required']) and
                            len(text) > 0):
                            option_texts.append(text)
                            logger.debug(f"    Candidate text: '{text}'")
                    except:
                        pass
                
                # Chỉ lấy N options đầu tiên (N = số radio buttons)
                selected_options = option_texts[:len(radio_divs)]
                logger.debug(f"  Selected {len(selected_options)} options from candidates")
                
                for idx, text in enumerate(selected_options):
                    options.append({
                        "index": idx,
                        "text": text
                    })
                    logger.debug(f"    Option {idx}: {text}")
                
                if options:
                    logger.debug(f"  Extracted {len(options)} options")
                    return options
        except Exception as e:
            logger.debug(f"  Strategy OIC90c failed: {e}")
        
        # Fallback: For VIEWFORM link - find YKDB3e class
        try:
            option_elements = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            logger.debug(f"  Found {len(option_elements)} YKDB3e elements (viewform)")
            
            if option_elements:
                for idx, option in enumerate(option_elements):
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        text = label.text.strip()
                        if text:
                            options.append({
                                "index": idx,
                                "text": text
                            })
                            logger.debug(f"    Option {idx}: {text}")
                    except:
                        pass
                
                if options:
                    logger.debug(f"  Extracted {len(options)} options from YKDB3e")
                    return options
        except Exception as e:
            logger.debug(f"  Strategy YKDB3e failed: {e}")
        
        logger.debug(f"  No options found")
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
            "section": "Mục",
            "section_header": "📌 Tiêu đề trang",
            "unknown": "Không xác định"
        }
        return type_map.get(question_type, "Không xác định")


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
            logger.info(f"[WORKER START] count={self.count}, max_parallel={self.max_parallel}")
            
            # Validate count
            try:
                count_int = int(self.count)
            except (TypeError, ValueError) as e:
                logger.error(f"[WORKER] Cannot convert count to int: {e}")
                self.error.emit(f"❌ Lỗi: Số responses không hợp lệ: {self.count}")
                return
            
            if count_int <= 0:
                self.error.emit(f"❌ Lỗi: Số responses phải > 0")
                return
            
            # Chọn chế độ chạy
            if self.max_parallel <= 1:
                logger.info(f"[WORKER] Running in SEQUENTIAL mode (1 tab)")
                self._run_sequential(count_int)
            else:
                logger.info(f"[WORKER] Running in PARALLEL mode ({self.max_parallel} tabs)")
                self._run_parallel(count_int)
        
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
        
        try:
            try:
                # Try with webdriver_manager first
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=options
                )
            except Exception as e1:
                logger.warning(f"webdriver_manager failed: {e1}")
                # Fallback: Use system Chrome
                self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome: {e}")
            self.error.emit(f"Không thể khởi động Chrome: {e}")
            self.finished.emit()
            return
        
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
        """🆕 Chạy submit song số (multiple tabs)"""
        import threading
        from queue import Queue
        
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Parallel mode: use normal Chrome (not headless) for better stability with multiple threads
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
                try:
                    # Try with webdriver_manager first (auto-downloads matching chromedriver)
                    driver = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=options
                    )
                except Exception as e1:
                    logger.warning(f"[THREAD {thread_id}] webdriver_manager failed: {e1}")
                    try:
                        # Fallback: Use system Chrome without explicit driver path
                        driver = webdriver.Chrome(options=options)
                    except Exception as e2:
                        logger.error(f"[THREAD {thread_id}] Both methods failed: {e2}")
                        raise
                
                # 🆕 Set implicit wait to ensure elements can be found even if page is loading
                driver.implicitly_wait(10)
                
                # 🆕 Position windows to avoid overlap
                # Calculate window position based on thread_id
                window_width = 960
                window_height = 1080
                x_position = (thread_id % 2) * window_width  # Alternate left/right
                y_position = (thread_id // 2) * window_height  # Stack vertically
                driver.set_window_size(window_width, window_height)
                driver.set_window_position(x_position, y_position)
                
                logger.info(f"[THREAD {thread_id}] Browser started at position ({x_position}, {y_position})")
                
                while True:
                    try:
                        response_idx = task_queue.get_nowait()
                    except:
                        break  # Queue rỗng
                    
                    logger.info(f"[THREAD {thread_id}] Processing response {response_idx + 1}/{count_int}")
                    
                    try:
                        self.progress.emit(f"📮 [Tab {thread_id}] Gửi response {response_idx + 1}/{count_int}...")
                        
                        driver.get(self.form_url)
                        
                        # ⏳ Wait for form to fully load - check for form elements
                        logger.info(f"[THREAD {thread_id}] Waiting for form to load...")
                        wait_attempts = 0
                        max_attempts = 10
                        form_loaded = False
                        while wait_attempts < max_attempts and not form_loaded:
                            try:
                                # Check for any question element
                                questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                                if len(questions) > 0:
                                    logger.info(f"[THREAD {thread_id}] ✓ Form loaded (found {len(questions)} questions)")
                                    form_loaded = True
                                    break
                                
                                # Alternative check for viewform
                                m7eme = driver.find_elements(By.CLASS_NAME, "M7eMe")
                                if len(m7eme) > 0:
                                    logger.info(f"[THREAD {thread_id}] ✓ Form loaded (found M7eMe elements)")
                                    form_loaded = True
                                    break
                            except:
                                pass
                            
                            wait_attempts += 1
                            if not form_loaded:
                                logger.debug(f"[THREAD {thread_id}] Waiting for form... attempt {wait_attempts}/{max_attempts}")
                                time.sleep(1)
                        
                        if not form_loaded:
                            logger.warning(f"[THREAD {thread_id}] Form may not be fully loaded, proceeding anyway...")
                        
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
                    driver.quit()
        
        # 🆕 Tạo và chạy threads
        threads = []
        for i in range(self.max_parallel):
            t = threading.Thread(target=worker_thread, args=(i,))
            t.daemon = False
            threads.append(t)
            t.start()
            logger.info(f"Started thread {i}")
        
        # 🆕 Chờ tất cả threads hoàn thành
        for t in threads:
            t.join()
            logger.info(f"Thread {t.name} completed")
        
        logger.info(f"✓ All {submitted_count[0]} responses submitted successfully")
        self.progress.emit(f"✅ Hoàn tất! Đã gửi {submitted_count[0]} responses (Parallel)")
        self.finished.emit()
    
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
    
    def _fill_form(self):
        """Điền form - hỗ trợ chế độ bình thường và random, tự động chuyển trang"""
        logger.info(f"Starting to fill form with {len(self.answers)} answers (multi-page support)")
        
        current_question_idx = 0
        page_num = 1
        
        try:
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"FILLING PAGE {page_num}")
                logger.info(f"{'='*60}")
                
                time.sleep(1)
                
                # Lấy câu hỏi trên trang hiện tại - try multiple selectors for both editor and viewform
                question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                logger.info(f"Selector 'Qr7Oae' found {len(question_elements)} questions")
                
                # If no questions found, try alternative selectors for viewform
                if len(question_elements) == 0:
                    logger.debug("Qr7Oae found 0, trying to find by span.M7eMe (question text container)...")
                    # Find span elements with class M7eMe (question text in viewform)
                    # Then get their parent containers which should be the actual question element
                    question_text_elements = self.driver.find_elements(By.CLASS_NAME, "M7eMe")
                    logger.info(f"Found {len(question_text_elements)} span.M7eMe elements")
                    
                    # Get parent containers of these question texts
                    for span_elem in question_text_elements:
                        try:
                            # Go up to find the question container
                            parent = span_elem.find_element(By.XPATH, "ancestor::div[@data-item-id or @role='listitem'][1]")
                            if parent not in question_elements:
                                question_elements.append(parent)
                        except:
                            # If no data-item-id parent, try getting a generic parent div
                            try:
                                parent = span_elem.find_element(By.XPATH, "ancestor::div[contains(@class, 'mKEK5c') or contains(@class, 'LMRjW')][1]")
                                if parent not in question_elements:
                                    question_elements.append(parent)
                            except:
                                pass
                    
                    logger.info(f"Found {len(question_elements)} question containers from span.M7eMe parents")
                
                if len(question_elements) == 0:
                    logger.debug("Still found 0, trying data-item-id...")
                    question_elements = self.driver.find_elements(By.XPATH, "//*[@data-item-id]")
                    logger.info(f"Selector 'data-item-id' found {len(question_elements)} elements")
                
                if len(question_elements) == 0:
                    logger.debug("data-item-id found 0, trying div[role='listitem']...")
                    question_elements = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
                    logger.info(f"Selector 'div[role=listitem]' found {len(question_elements)} elements")
                
                if len(question_elements) == 0:
                    logger.debug("Nothing found yet, trying generic div with specific structure...")
                    question_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'item-')]")
                    logger.info(f"Selector 'class item-' found {len(question_elements)} elements")
                
                questions_on_page = []
                
                # Chỉ xử lý câu hỏi "hiển thị" trên trang này
                for q_elem in question_elements:
                    try:
                        if q_elem.is_displayed():
                            questions_on_page.append(q_elem)
                    except:
                        pass
                
                logger.info(f"Found {len(questions_on_page)} visible questions on page {page_num}")
                
                if len(questions_on_page) == 0:
                    logger.warning("No visible questions found on this page - checking if last page...")
                    # Maybe we're on the last page with the thank you message
                    # Check if next button exists
                    next_btn = self._find_next_button()
                    if not next_btn:
                        logger.info("✓ Confirmed: No next button - this is the last page")
                        break
                    else:
                        logger.warning("Found next button even with no visible questions - clicking to continue...")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        time.sleep(0.5)
                        next_btn.click()
                        time.sleep(1.5)
                        page_num += 1
                        continue
                
                # Điền câu trả lời cho các câu hỏi trên trang này
                for page_q_idx, q_element in enumerate(questions_on_page):
                    question_idx = current_question_idx + page_q_idx
                    
                    # Skip nếu không có đáp án cho câu này
                    if question_idx not in self.answers:
                        logger.info(f"  Q{question_idx + 1}: Skipped (no answer)")
                        continue
                    
                    try:
                        answer = self.answers[question_idx]
                        if question_idx >= len(self.questions):
                            logger.warning(f"Question index {question_idx} exceeds questions list")
                            continue
                        
                        question_data = self.questions[question_idx]
                        q_type = question_data['type']
                        q_title = question_data['title']
                        
                        logger.info(f"  Q{question_idx + 1} ({q_type}): {q_title}")
                        logger.info(f"    Answer: {answer}")
                        
                        if q_type == "short_answer" or q_type == "long_answer":
                            self._fill_text_field(q_element, str(answer))
                            logger.info(f"    ✓ Filled text")
                        
                        elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                            if isinstance(answer, tuple) and answer[0] == 'random':
                                options_list = answer[1]
                                selected_option = self._select_by_percentage(options_list)
                                logger.info(f"    Random Mode - Selected: {selected_option}")
                                self._select_option(q_element, selected_option)
                            else:
                                self._select_option(q_element, str(answer))
                            logger.info(f"    ✓ Selected option")
                        
                        elif q_type == "checkbox":
                            if isinstance(answer, tuple) and answer[0] == 'random':
                                options_list = answer[1]
                                selected_options = self._select_multiple_by_percentage(options_list)
                                logger.info(f"    Random Mode (Multiple) - Selected: {selected_options}")
                                for option_text in selected_options:
                                    self._select_option(q_element, option_text)
                            else:
                                if isinstance(answer, list):
                                    for option_text in answer:
                                        self._select_option(q_element, str(option_text))
                                else:
                                    self._select_option(q_element, str(answer))
                            logger.info(f"    ✓ Selected checkboxes")
                    
                    except Exception as e:
                        logger.error(f"  ✗ Error filling Q{question_idx}: {e}", exc_info=True)
                
                # Tìm nút "Tiếp" (Next button)
                logger.info(f"\nPage {page_num} filled - looking for next button...")
                time.sleep(0.5)
                
                next_btn = self._find_next_button()
                
                if next_btn:
                    # Còn trang tiếp theo
                    logger.info(f"  ⏭️ Found 'Tiếp' button - going to page {page_num + 1}...")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(0.5)
                    next_btn.click()
                    time.sleep(1.5)
                    current_question_idx += len(questions_on_page)
                    page_num += 1
                else:
                    # Trang cuối cùng - exit loop để gửi form
                    logger.info(f"  ✓ No next button found - last page reached")
                    break
        
        except Exception as e:
            logger.error(f"Error filling form: {e}", exc_info=True)
            raise
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Form filling complete")
        logger.info(f"{'='*60}\n")
        
        # 🆕 Gửi form sau khi điền xong
        logger.info("Now submitting the form...")
        self._submit_form()
    
    def _select_multiple_by_percentage(self, options_list):
        """Chọn nhiều options theo xác suất"""
        selected = []
        for opt in options_list:
            import random
            if random.random() * 100 < opt['percentage']:
                selected.append(opt['text'])
        return selected if selected else [options_list[0]['text']] if options_list else []
    
    def _find_next_button(self):
        """Tìm nút 'Tiếp' (Next button) - từ interactive_filler.py"""
        try:
            # Cách 1: Tìm button hoặc span có text "Tiếp" nhưng KHÔNG phải "Quay lại"
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'Tiếp')] | //button[contains(., 'Next')] | //div[@role='button' and contains(text(), 'Tiếp')] | //div[@role='button' and contains(text(), 'Next')]")
            if buttons and len(buttons) > 0:
                for btn in buttons:
                    try:
                        btn_text = btn.text.strip() if btn.text else ""
                        # Make sure it's not the back button and it IS displayed
                        if btn.is_displayed() and "Quay lại" not in btn_text and "Tiếp" in btn_text:
                            logger.info(f"Found next button: {btn_text}")
                            return btn
                    except:
                        pass
            
            # Cách 2: Tìm với class "uArJ5e" (button class) - tìm "Tiếp" button specifically
            buttons = self.driver.find_elements(By.CLASS_NAME, "uArJ5e")
            for btn in buttons:
                try:
                    if btn.is_displayed():
                        btn_text = btn.text.strip() if btn.text else ""
                        aria_label = btn.get_attribute("aria-label") or ""
                        # Kiểm tra nếu là nút tiếp (không phải back, không phải clear)
                        if btn_text == "Tiếp" and "Quay lại" not in btn_text and "Xóa" not in btn_text:
                            logger.info(f"Found next button (Tiếp): {btn_text}")
                            return btn
                        if "Tiếp" in aria_label and "Quay lại" not in aria_label:
                            logger.info(f"Found next button by aria-label: {aria_label}")
                            return btn
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error finding next button: {e}")
        
        return None
    
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
                input_field.clear()
                input_field.send_keys(value)
                time.sleep(0.3)
                logger.debug(f"Filled text field with: {value}")
        except Exception as e:
            logger.warning(f"Error filling text field: {e}")
    
    def _select_option(self, question_element, option_text: str):
        """Chọn option từ element - từ interactive_filler.py"""
        try:
            # Tìm option với text tương ứng
            options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for option in options:
                try:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if label.text == option_text:
                        option.click()
                        time.sleep(0.3)
                        logger.debug(f"Selected option: {option_text}")
                        return
                except:
                    pass
            
            logger.warning(f"Could not find option: {option_text}")
        
        except Exception as e:
            logger.warning(f"Error selecting option '{option_text}': {e}")
    
    def _select_by_percentage(self, options_list):
        """Chọn một option theo xác suất"""
        import random
        total = sum(opt['percentage'] for opt in options_list)
        if total == 0:
            return options_list[0]['text'] if options_list else ""
        
        rand = random.uniform(0, total)
        current = 0
        for opt in options_list:
            current += opt['percentage']
            if rand <= current:
                return opt['text']
        return options_list[-1]['text'] if options_list else ""
    
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
            
            # DEBUG: Print all buttons on page first
            try:
                all_buttons = self.driver.find_elements(By.XPATH, "//*[@role='button' or self::button]")
                logger.info(f"=== DEBUG: Found {len(all_buttons)} total button elements ===")
                for i, btn in enumerate(all_buttons):
                    try:
                        btn_text = btn.text.strip()
                        btn_class = btn.get_attribute('class') or ''
                        btn_visible = btn.is_displayed()
                        btn_tag = btn.tag_name
                        logger.info(f"  [{i}] {btn_tag} | visible={btn_visible} | text='{btn_text}' | class='{btn_class}'")
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Debug listing error: {e}")
            
            # Method 1: Find button by text "Gửi" (Vietnamese for Submit) - PRIORITIZE THIS
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//*[@role='button' and contains(., 'Gửi')]")
                logger.info(f"Found submit button by text 'Gửi': '{submit_btn.text}'")
            except Exception as e:
                logger.debug(f"Method 1 (text 'Gửi') error: {e}")
            
            # Method 2: Find button by text "Submit"
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//*[@role='button' and contains(., 'Submit')]")
                    logger.info(f"Found submit button by text 'Submit': '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 2 (text 'Submit') error: {e}")
            
            # Method 3: Find by unique class Y5sE8d (only submit button has this)
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'Y5sE8d')]")
                    logger.info(f"Found submit button by class Y5sE8d: '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 3 (Y5sE8d) error: {e}")
            
            # Method 4: Find by class QvWxOd (submit button specific)
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by class QvWxOd: '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 4 (QvWxOd) error: {e}")
            
            # Method 5: Find by all unique classes together
            if not submit_btn:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e') and contains(@class, 'Y5sE8d') and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by combined classes: '{submit_btn.text}'")
                except Exception as e:
                    logger.debug(f"Method 5 (combined) error: {e}")
            
            # Method 6: Find uArJ5e button that is NOT "Quay lại", NOT "Xóa", NOT empty, NOT "Tiếp"
            if not submit_btn:
                try:
                    uarj5e_divs = self.driver.find_elements(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e')]")
                    logger.info(f"Found {len(uarj5e_divs)} divs with class uArJ5e")
                    for i, div in enumerate(uarj5e_divs):
                        is_displayed = div.is_displayed()
                        div_text = div.text.strip()
                        logger.debug(f"  [{i}] displayed={is_displayed}, text='{div_text}'")
                        # Only accept if: displayed AND has text AND NOT back/clear/next buttons
                        if is_displayed and div_text and div_text not in ['Xóa hết câu trả lời', 'Clear', 'Tiếp', 'Quay lại', 'Next', 'Back']:
                            submit_btn = div
                            logger.info(f"Found submit button (uArJ5e): '{div_text}'")
                            break
                except Exception as e:
                    logger.debug(f"Method 6 (uArJ5e loop) error: {e}")
            
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
                logger.error("❌ Could not find submit button - will NOT submit form")
                # Extended debug info
                try:
                    all_role_buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
                    logger.error(f"All role=button elements ({len(all_role_buttons)}):")
                    for i, btn in enumerate(all_role_buttons):
                        try:
                            logger.error(f"  [{i}] text='{btn.text}' | class='{btn.get_attribute('class')}' | displayed={btn.is_displayed()}")
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Error listing buttons: {e}")
        
        except Exception as e:
            logger.error(f"Error submitting form: {e}", exc_info=True)
    
    def _fill_form_for_thread(self, driver):
        """🆕 Điền form - phiên bản thread-safe (dùng driver được pass vào), hỗ trợ multi-page"""
        logger.info(f"Starting to fill form with {len(self.answers)} answers (thread-safe, multi-page)")
        
        page_number = 1
        form_question_index = 0  # Global index của câu hỏi trong self.questions
        
        while True:
            logger.info(f"\n{'='*60}")
            logger.info(f"FILLING PAGE {page_number} (thread-safe)")
            logger.info(f"{'='*60}")
            
            # Wait for page to load - wait for either Qr7Oae or M7eMe elements
            time.sleep(2)  # Initial wait for page load
            wait_attempts = 0
            max_wait_attempts = 5
            while wait_attempts < max_wait_attempts:
                question_check = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                if len(question_check) > 0:
                    logger.debug(f"Page loaded, found questions with Qr7Oae")
                    break
                question_check = driver.find_elements(By.CLASS_NAME, "M7eMe")
                if len(question_check) > 0:
                    logger.debug(f"Page loaded, found question text with M7eMe")
                    break
                wait_attempts += 1
                if wait_attempts < max_wait_attempts:
                    logger.debug(f"Waiting for questions to load... (attempt {wait_attempts})")
                    time.sleep(1)
            
            # Find all question elements on current page - try multiple selectors for both editor and viewform
            try:
                question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                logger.debug(f"Selector 'Qr7Oae' found {len(question_elements)} questions")
                
                # If no questions found, try alternative selectors for viewform
                if len(question_elements) == 0:
                    logger.debug("Qr7Oae found 0, trying to find by span.M7eMe (question text container)...")
                    # Find span elements with class M7eMe (question text in viewform)
                    question_text_elements = driver.find_elements(By.CLASS_NAME, "M7eMe")
                    logger.debug(f"Found {len(question_text_elements)} span.M7eMe elements")
                    
                    # Get parent containers of these question texts
                    for span_elem in question_text_elements:
                        try:
                            parent = span_elem.find_element(By.XPATH, "ancestor::div[@data-item-id or @role='listitem'][1]")
                            if parent not in question_elements:
                                question_elements.append(parent)
                        except:
                            try:
                                parent = span_elem.find_element(By.XPATH, "ancestor::div[contains(@class, 'mKEK5c') or contains(@class, 'LMRjW')][1]")
                                if parent not in question_elements:
                                    question_elements.append(parent)
                            except:
                                pass
                    
                    logger.debug(f"Found {len(question_elements)} question containers from span.M7eMe parents")
                
                if len(question_elements) == 0:
                    logger.debug("Still found 0, trying data-item-id...")
                    question_elements = driver.find_elements(By.XPATH, "//*[@data-item-id]")
                
                if len(question_elements) == 0:
                    logger.debug("data-item-id found 0, trying div[role='listitem']...")
                    question_elements = driver.find_elements(By.XPATH, "//div[@role='listitem']")
            except:
                question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            
            logger.info(f"Found {len(question_elements)} questions on page {page_number}")
            
            if len(question_elements) == 0:
                logger.warning("No question elements found - might be at end")
                break
            
            # Fill all questions on current page
            for local_idx, question_element in enumerate(question_elements):
                try:
                    idx = form_question_index
                    
                    if idx >= len(self.questions):
                        logger.warning(f"Question {idx} exceeds questions count")
                        form_question_index += 1
                        continue
                    
                    # Skip if not in answers (e.g., page title or section header)
                    if idx not in self.answers:
                        logger.warning(f"Question {idx} not in answers - skipping (probably page title)")
                        form_question_index += 1
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
                finally:
                    form_question_index += 1
            
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
        logger.info(f"✓ Form filling complete")
        logger.info(f"{'='*60}\n")
        
        # 🆕 Gửi form sau khi điền xong
        logger.info("Now submitting the form (thread-safe)...")
        self._submit_form_for_thread(driver)
    
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
            
            # Create WebDriverWait with longer timeout for parallel operations
            wait = WebDriverWait(driver, timeout=15)
            
            # ⏳ Wait for any button to be clickable - sign that page is interactive
            try:
                logger.info("⏳ Waiting for page to be interactive...")
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@role='button']")))
                logger.info("✓ Page is interactive")
            except:
                logger.warning("Timeout waiting for buttons, continuing anyway...")
            
            # Scroll to bottom to ensure submit button is visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # DEBUG: Print all buttons on page first
            try:
                all_buttons = driver.find_elements(By.XPATH, "//*[@role='button' or self::button]")
                logger.info(f"=== DEBUG (thread): Found {len(all_buttons)} total button elements ===")
                for i, btn in enumerate(all_buttons):
                    try:
                        btn_text = btn.text.strip()
                        btn_class = btn.get_attribute('class') or ''
                        btn_visible = btn.is_displayed()
                        btn_tag = btn.tag_name
                        logger.info(f"  [{i}] {btn_tag} | visible={btn_visible} | text='{btn_text}' | class='{btn_class}'")
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Debug listing error: {e}")
            
            # Method 1: Find button by text "Gửi" (Vietnamese for Submit) - PRIORITIZE THIS
            try:
                submit_btn = driver.find_element(By.XPATH, "//*[@role='button' and contains(., 'Gửi')]")
                logger.info(f"Found submit button by text 'Gửi'")
            except:
                pass
            
            # Method 2: Find button by text "Submit"
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//*[@role='button' and contains(., 'Submit')]")
                    logger.info(f"Found submit button by text 'Submit'")
                except:
                    pass
            
            # Method 3: Find by unique class Y5sE8d
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'Y5sE8d')]")
                    logger.info(f"Found submit button by class Y5sE8d")
                except:
                    pass
            
            # Method 4: Find by class QvWxOd
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by class QvWxOd")
                except:
                    pass
            
            # Method 5: Find by combined classes
            if not submit_btn:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e') and contains(@class, 'Y5sE8d') and contains(@class, 'QvWxOd')]")
                    logger.info(f"Found submit button by combined classes")
                except:
                    pass
            
            # Method 6: Find uArJ5e button that is NOT "Quay lại", NOT "Xóa", NOT "Tiếp", etc
            if not submit_btn:
                try:
                    uarj5e_divs = driver.find_elements(By.XPATH, "//div[@role='button' and contains(@class, 'uArJ5e')]")
                    for i, div in enumerate(uarj5e_divs):
                        is_displayed = div.is_displayed()
                        div_text = div.text.strip()
                        # Only accept if displayed AND has text AND NOT navigation buttons
                        if is_displayed and div_text and div_text not in ['Xóa hết câu trả lời', 'Clear', 'Tiếp', 'Quay lại', 'Next', 'Back']:
                            submit_btn = div
                            logger.info(f"Found submit button (uArJ5e): '{div_text}'")
                            break
                except:
                    pass
            
            if submit_btn:
                try:
                    # Try to wait for button to be clickable
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@role='button' and contains(., 'Gửi')] | //*[@role='button' and contains(., 'Submit')]")))
                except:
                    logger.debug("Timeout waiting for button to be clickable, clicking anyway...")
                
                try:
                    # Scroll element into view before clicking
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", submit_btn)
                    logger.info(f"✓ Clicked submit button via JS")
                except:
                    try:
                        submit_btn.click()
                        logger.info(f"✓ Clicked submit button")
                    except Exception as e:
                        logger.warning(f"Failed to click submit: {e}, trying JS again...")
                        driver.execute_script("arguments[0].click();", submit_btn)
                        logger.info(f"✓ Clicked via JS (retry)")
                
                time.sleep(3)
            else:
                logger.error("❌ Could not find submit button - will NOT submit form")
        
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
        """Tạo tab nhập URL - yêu cầu editor link và viewform link"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Bước 1: Lấy Câu Hỏi từ Link Editor")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Info
        info = QLabel("📌 Dùng link EDITOR để tránh vấn đề câu hỏi bắt buộc\n(Tất cả câu hỏi sẽ hiển thị trên 1 trang)")
        info.setFont(QFont("Arial", 10))
        info.setStyleSheet("color: #666; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info)
        
        # ===== EDITOR URL INPUT =====
        layout.addWidget(QLabel("🔗 Link Editor (để lấy câu hỏi):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.google.com/forms/d/YOUR_FORM_ID/edit")
        layout.addWidget(self.url_input)
        
        # Load button
        self.load_btn = QPushButton("🔍 Lấy Tất Cả Câu Hỏi từ Editor")
        self.load_btn.clicked.connect(self.loadFormInfo)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #5e35b1;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7e57c2;
            }
        """)
        layout.addWidget(self.load_btn)
        
        # Progress
        self.load_progress = QTextEdit()
        self.load_progress.setReadOnly(True)
        self.load_progress.setMaximumHeight(200)
        layout.addWidget(self.load_progress)
        
        # Separator
        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel(""))
        
        # ===== VIEWFORM URL INPUT =====
        title2 = QLabel("Bước 2: Nhập Link ViewForm (để gửi responses)")
        title2.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title2)
        
        info2 = QLabel("📌 Gửi link VIEWFORM sau khi hoàn tất bước 1")
        info2.setFont(QFont("Arial", 9))
        info2.setStyleSheet("color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info2)
        
        layout.addWidget(QLabel("🔗 Link ViewForm (để gửi responses):"))
        self.viewform_url_input = QLineEdit()
        self.viewform_url_input.setPlaceholderText("https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform")
        layout.addWidget(self.viewform_url_input)
        
        # Button to confirm viewform URL
        self.confirm_viewform_btn = QPushButton("✅ Xác Nhận Link ViewForm")
        self.confirm_viewform_btn.clicked.connect(self.confirmViewFormUrl)
        self.confirm_viewform_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #66bb6a;
            }
        """)
        layout.addWidget(self.confirm_viewform_btn)
        
        layout.addWidget(QLabel("ℹ️ Sẽ kích hoạt sau khi lấy xong câu hỏi"))
        
        # Add stretch
        layout.addStretch()
        
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
        
        # ✅ ADD CONFIRM BUTTON
        confirm_btn_layout = QHBoxLayout()
        confirm_btn_layout.addStretch()
        self.confirm_answers_btn = QPushButton("✅ Xác Nhận Đáp Án")
        self.confirm_answers_btn.setMinimumWidth(200)
        self.confirm_answers_btn.setMinimumHeight(50)
        self.confirm_answers_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.confirm_answers_btn.clicked.connect(self.onConfirmAnswers)
        confirm_btn_layout.addWidget(self.confirm_answers_btn)
        layout.addLayout(confirm_btn_layout)
        
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
        """Lấy thông tin form từ EDITOR link"""
        editor_url = self.url_input.text().strip()
        
        if not editor_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL Editor")
            return
        
        # Validate link là editor link
        if "/edit" not in editor_url:
            QMessageBox.warning(self, "Lỗi", "❌ Vui lòng gửi link EDITOR (chứa '/edit')\n\nVí dụ: https://docs.google.com/forms/d/FORM_ID/edit")
            return
        
        self.load_btn.setEnabled(False)
        self.load_progress.clear()
        self.load_progress.append("⏳ Đang lấy tất cả câu hỏi từ link editor...\n")
        
        # Extract from editor link (all questions on 1 page)
        self.worker = GoogleFormWorker(editor_url)
        self.worker.progress.connect(self.updateLoadProgress)
        self.worker.finished.connect(self.onFormLoaded)
        self.worker.error.connect(self.onLoadError)
        self.worker.start()
    
    def updateLoadProgress(self, message: str):
        """Cập nhật progress"""
        self.load_progress.append(message)
    
    def onFormLoaded(self, questions: List[Dict]):
        """Khi form được tải thành công từ editor link"""
        self.questions = questions
        self.load_progress.append(f"\n✅ Đã tải {len(questions)} câu hỏi từ editor link!")
        self.load_progress.append("\n" + "="*60)
        self.load_progress.append("📌 Bây giờ hãy nhập link VIEWFORM ở bên dưới")
        self.load_progress.append("="*60)
        
        self.load_btn.setEnabled(True)
        
        # Cập nhật tab questions
        self.questions_list.clear()
        for q in questions:
            # Skip section headers in display
            if q.get('is_page_title', False):
                # Add as separator
                item = QListWidgetItem(f"📌 {q['title']}")
                item.setBackground(QColor("#f3e5f5"))
                self.questions_list.addItem(item)
                continue
            
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
        
        QMessageBox.information(self, "Thành Công", f"✅ Đã tải {len([q for q in questions if not q.get('is_page_title')])} câu hỏi!\n\nHãy nhập link VIEWFORM rồi chuyển sang tab 'Chọn Đáp Án'")
    
    def onLoadError(self, error: str):
        """Khi có lỗi"""
        self.load_progress.append(f"\n❌ {error}")
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi", error)
    
    def confirmViewFormUrl(self):
        """Xác nhận link ViewForm - enable tabs Chọn Đáp Án và Gửi"""
        viewform_url = self.viewform_url_input.text().strip()
        
        if not viewform_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link ViewForm")
            return
        
        if "/viewform" not in viewform_url and "/formResponse" not in viewform_url:
            QMessageBox.warning(self, "Lỗi", "❌ Vui lòng gửi link VIEWFORM hoặc formResponse\n\nVí dụ: https://docs.google.com/forms/d/e/FORM_ID/viewform")
            return
        
        # Store the viewform URL
        self.form_url = viewform_url
        
        # Message thành công
        QMessageBox.information(
            self, 
            "Thành Công", 
            f"✅ Link ViewForm được xác nhận!\n\nBây giờ hãy:\n1. Chuyển sang tab 'Chọn Đáp Án' để chọn câu trả lời\n2. Rồi chuyển sang tab 'Gửi' để submit responses"
        )
        
        logger.info(f"✓ ViewForm URL confirmed: {viewform_url}")
    
    
    def createAnswerInputs(self):
        """Tạo input fields cho đáp án - UI giống Google Form"""
        # Clear previous
        while self.answers_layout.count():
            widget = self.answers_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        self.answer_widgets = {}
        
        # 🆕 Track actual question index (skip page titles)
        actual_q_idx = 0
        
        logger.info(f"[createAnswerInputs] START - Creating UI for {len(self.questions)} questions")
        
        for q in self.questions:
            idx = q['index']
            q_type = q['type']
            title = q['title']
            options = q['options']
            is_page_title = q.get('is_page_title', False)
            
            logger.info(f"[createAnswerInputs] Q{idx}: type={q_type}, is_page_title={is_page_title}, title={title[:40]}")
            
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
            
            # Question title - Special format for page titles
            
            if is_page_title:
                # Format cho tiêu đề trang
                label = QLabel(f"📌 {title}")
                label.setFont(QFont("Arial", 13, QFont.Bold))
                label.setWordWrap(True)
                label.setStyleSheet("color: #5e35b1; font-weight: bold;")
                question_frame.setStyleSheet("""
                    QFrame {
                        background-color: #f3e5f5;
                        border: 2px solid #5e35b1;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 10px 0px;
                    }
                """)
            else:
                # Format cho câu hỏi thường
                label = QLabel(f"{actual_q_idx + 1}. {title}")
                label.setFont(QFont("Arial", 12, QFont.Bold))
                label.setWordWrap(True)
            
            question_layout.addWidget(label)
            
            # Required indicator - không hiển thị cho page titles
            if not is_page_title and q['required']:
                required_label = QLabel("* Bắt buộc")
                required_label.setFont(QFont("Arial", 9))
                required_label.setStyleSheet("color: #d32f2f;")
                question_layout.addWidget(required_label)
            
            question_layout.addSpacing(10)
            
            # Options or input - bỏ qua cho page titles
            if is_page_title:
                # Không thêm options cho tiêu đề trang
                pass
            else:
                # Create input widgets ONLY for non-page-title questions
                if q_type == "multiple_choice":
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
                        
                        self.answer_widgets[actual_q_idx] = ('random', checkbox_list)
                    else:
                        # Normal mode: use radio buttons (single select)
                        group = QButtonGroup()
                        self.answer_widgets[actual_q_idx] = group
                        
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
                    self.answer_widgets[actual_q_idx] = widget
                
                elif q_type == "long_answer":
                    widget = QTextEdit()
                    widget.setPlaceholderText("Nhập câu trả lời của bạn")
                    widget.setMinimumHeight(100)
                    question_layout.addWidget(widget)
                    self.answer_widgets[actual_q_idx] = widget
                
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
                    self.answer_widgets[actual_q_idx] = checkboxes
                
                elif q_type == "dropdown":
                    combo = QComboBox()
                    combo.addItem("-- Chọn --")
                    if options:
                        for opt in options:
                            combo.addItem(opt['text'])
                    combo.setMinimumHeight(40)
                    question_layout.addWidget(combo)
                    self.answer_widgets[actual_q_idx] = combo
                
                elif q_type in ["linear_scale", "multiple_choice_grid"]:
                    # These types have options
                    if options:
                        group = QButtonGroup()
                        self.answer_widgets[actual_q_idx] = group
                        
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
                        self.answer_widgets[actual_q_idx] = widget
                
                else:
                    # For any unknown type, default to text input (safer than error)
                    widget = QLineEdit()
                    widget.setPlaceholderText("Nhập câu trả lời của bạn")
                    widget.setMinimumHeight(40)
                    question_layout.addWidget(widget)
                    self.answer_widgets[actual_q_idx] = widget
            
            question_layout.addStretch()
            
            self.answers_layout.addWidget(question_frame)
            
            # Increment actual_q_idx only for non-page-title questions
            if not is_page_title:
                logger.info(f"[createAnswerInputs] Widget created for Q{idx} with actual_q_idx={actual_q_idx}")
                actual_q_idx += 1
        
        logger.info(f"[createAnswerInputs] DONE - Created {len(self.answer_widgets)} widgets with keys: {list(self.answer_widgets.keys())}")
        self.answers_layout.addStretch()
    
    def onRandomModeToggled(self, state):
        """Xử lý toggle chế độ random"""
        self.random_mode = (state == Qt.Checked)
        logger.info(f"Random mode toggled: {self.random_mode}")
        # Recreate answer inputs when random mode changes
        if self.questions:
            self.createAnswerInputs()
    
    def onConfirmAnswers(self):
        """🆕 Xác nhận và lưu đáp án từ widgets"""
        logger.info("[CONFIRM] User clicked Confirm Answers button")
        
        # Extract answers from widgets
        self.answers = self.getAnswersFromWidgets()
        
        # Count real questions (skip page titles)
        real_questions = sum(1 for q in self.questions if not q.get('is_page_title', False))
        
        if not self.answers:
            QMessageBox.warning(self, "Lỗi", f"Vui lòng chọn ít nhất một đáp án\n\n(Tổng {real_questions} câu hỏi)")
            return
        
        # Show confirmation
        msg = f"✅ Đã lưu {len(self.answers)}/{real_questions} đáp án\n\n"
        for idx, ans in sorted(self.answers.items()):
            ans_preview = str(ans)[:30] if not isinstance(ans, tuple) else f"{ans[0]}(...)"
            msg += f"Q{idx}: {ans_preview}\n"
        
        msg += f"\nBây giờ hãy chuyển sang tab 'Gửi' để submit {self.count_spinbox.value()} responses"
        
        QMessageBox.information(self, "Thành Công", msg)
        logger.info(f"[CONFIRM] Saved {len(self.answers)} answers successfully")
    
    def startSubmission(self):
        """Bắt đầu gửi responses - dùng link ViewForm"""
        if not self.questions:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tải form trước")
            return
        
        # 🆕 Validate viewform URL
        viewform_url = self.viewform_url_input.text().strip()
        if not viewform_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập link ViewForm")
            return
        
        if "/viewform" not in viewform_url:
            QMessageBox.warning(self, "Lỗi", "❌ Vui lòng gửi link VIEWFORM (chứa '/viewform')\n\nVí dụ: https://docs.google.com/forms/d/e/FORM_ID/viewform")
            return
        
        # 🆕 Use viewform URL for submission instead of editor URL
        self.form_url = viewform_url
        
        # 🆕 Check if answers are already confirmed, if not ask user to confirm first
        if not hasattr(self, 'answers') or not self.answers:
            QMessageBox.warning(
                self, 
                "Lỗi", 
                "⚠️ Bạn chưa xác nhận đáp án!\n\nVui lòng:\n1. Chọn đáp án cho các câu hỏi\n2. Click nút '✅ Xác Nhận Đáp Án'\n3. Rồi mới click 'Gửi'"
            )
            return
        
        # 🆕 DEBUG: Log question structure
        total_questions = len(self.questions)
        section_headers = sum(1 for q in self.questions if q.get('is_page_title', False))
        real_questions = total_questions - section_headers
        logger.info(f"[SUBMIT] Question structure: total={total_questions}, section_headers={section_headers}, real_questions={real_questions}")
        for i, q in enumerate(self.questions):
            is_header = q.get('is_page_title', False)
            logger.info(f"  Q{i}: '{q['title'][:40]}' - type={q['type']}, is_page_title={is_header}")
        
        logger.info(f"[SUBMIT] Using confirmed answers: {len(self.answers)} answers")
        for q_idx, ans in self.answers.items():
            ans_str = str(ans)[:50] if not isinstance(ans, tuple) else f"{ans[0]}(...)"
            logger.info(f"  Answer for Q{q_idx}: {ans_str}")
        
        # Warn if not all questions are answered
        if len(self.answers) < real_questions:
            missing = real_questions - len(self.answers)
            reply = QMessageBox.question(
                self, "Cảnh báo",
                f"⚠️ Bạn chỉ trả lời {len(self.answers)}/{real_questions} câu hỏi (thiếu {missing} câu).\n\nCó tiếp tục gửi không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Check number of responses to send
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
        logger.info(f"[SUBMIT] Using ViewForm URL: {self.form_url}")
        self.worker = SubmissionWorker(self.form_url, self.answers, count, self.questions, max_parallel)  # 🆕 Pass max_parallel
        self.worker.progress.connect(self.updateSubmissionLog)
        self.worker.count_progress.connect(self.submission_progress.setValue)
        self.worker.finished.connect(self.onSubmissionFinished)
        self.worker.error.connect(self.onSubmissionError)
        logger.info(f"[SUBMIT] Starting worker thread")
        self.worker.start()
        logger.info(f"[SUBMIT] Worker thread started")
    
    def getAnswersFromWidgets(self) -> Dict:
        """Lấy đáp án từ widgets - hỗ trợ cả chế độ bình thường và random, skip page titles"""
        answers = {}
        
        # 🆕 Build mapping: answer_widgets_idx → question_idx
        # answer_widgets chỉ chứa câu hỏi thực (không page titles)
        # nhưng self.questions có cả page titles
        # Tạo list question index mà không phải page titles
        real_question_indices = [q['index'] for q in self.questions if not q.get('is_page_title', False)]
        
        logger.info(f"[getAnswersFromWidgets] answer_widgets keys: {list(self.answer_widgets.keys())}")
        logger.info(f"[getAnswersFromWidgets] real_question_indices: {real_question_indices}")
        
        for widget_idx, widget in self.answer_widgets.items():
            # widget_idx là index từ createAnswerInputs (chỉ đếm câu hỏi thực)
            # Tìm question index thực từ widget_idx
            if widget_idx < len(real_question_indices):
                actual_question_idx = real_question_indices[widget_idx]
                logger.info(f"[getAnswersFromWidgets] Mapping widget_idx={widget_idx} -> actual_question_idx={actual_question_idx}")
            else:
                logger.warning(f"Widget index {widget_idx} exceeds real questions count")
                continue
            
            logger.info(f"[getAnswersFromWidgets] Widget {widget_idx}: type={type(widget).__name__}, isinstance(QButtonGroup)={isinstance(widget, QButtonGroup)}")
            
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
                            f"Câu {actual_question_idx + 1}: Tổng tỉ lệ phải bằng 100% (hiện tại: {total_percent}%)"
                        )
                        return {}
                    answers[actual_question_idx] = ('random', random_answer)
            
            elif isinstance(widget, QLineEdit):
                if widget.text().strip():
                    answers[actual_question_idx] = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                if widget.toPlainText().strip():
                    answers[actual_question_idx] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                if widget.currentIndex() > 0:
                    answers[actual_question_idx] = widget.currentText()
            elif isinstance(widget, QButtonGroup):
                # Radio button group
                checked_btn = widget.checkedButton()
                if checked_btn:
                    answers[actual_question_idx] = checked_btn.text()
            elif isinstance(widget, list):
                # Checkboxes list
                selected = [text for cb, text in widget if cb.isChecked()]
                if selected:
                    answers[actual_question_idx] = selected
        
        logger.info(f"[ANSWERS] Extracted {len(answers)} answers from {len(self.answer_widgets)} widgets")
        for idx, ans in answers.items():
            logger.info(f"  Q{idx}: {str(ans)[:50]}")
        
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
