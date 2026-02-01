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
            options.add_argument("--headless=new")  # 🔧 Chrome chạy ẩn
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1200,900")
            
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
                        
                        # Lấy giới hạn max selections nếu là checkbox
                        max_selections = None
                        if q_type == "checkbox":
                            max_selections = self._get_max_selections(parent_container)
                        
                        question_data = {
                            "index": len(self.questions),
                            "title": title,
                            "type": q_type,
                            "options": options_list,
                            "required": self._is_required(elem),
                            "element": elem,
                            "is_page_title": False,
                            "max_selections": max_selections  # 🆕 Giới hạn số đáp án
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
    
    def _get_max_selections(self, question_element) -> int:
        """Lấy giới hạn số lượng đáp án tối đa được chọn (cho checkbox questions)
        
        Google Form có thể giới hạn: 'Chọn tối đa X đáp án' hoặc 'Select at most X'
        Returns: max số lượng, hoặc None nếu không có giới hạn
        """
        try:
            import re
            
            # Lấy toàn bộ text của question để tìm pattern
            full_text = question_element.text or ""
            full_text_lower = full_text.lower()
            
            # =======================================================
            # 🇻🇳 VIETNAMESE PATTERNS
            # =======================================================
            
            # Pattern 1: "tối đa X" - phổ biến nhất
            match = re.search(r'tối đa\s*(\d+)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (VN 'tối đa'): {max_val}")
                return max_val
            
            # Pattern 2: "chọn X đáp án" hoặc "được chọn X"
            match = re.search(r'(?:được\s*)?chọn\s*(\d+)\s*(?:đáp án|câu|ý)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (VN 'chọn X'): {max_val}")
                return max_val
            
            # Pattern 3: "không quá X" hoặc "nhiều nhất X"
            match = re.search(r'(?:không quá|nhiều nhất)\s*(\d+)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (VN 'không quá/nhiều nhất'): {max_val}")
                return max_val
            
            # =======================================================
            # 🇬🇧 ENGLISH PATTERNS
            # =======================================================
            
            # Pattern 4: "at most X" hoặc "maximum X"
            match = re.search(r'(?:at most|maximum|max)\s*(\d+)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (EN 'at most/max'): {max_val}")
                return max_val
            
            # Pattern 5: "select/choose up to X"
            match = re.search(r'(?:select|choose)\s*(?:up to|at most)?\s*(\d+)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (EN 'select/choose X'): {max_val}")
                return max_val
            
            # Pattern 6: "no more than X"
            match = re.search(r'no more than\s*(\d+)', full_text_lower)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (EN 'no more than'): {max_val}")
                return max_val
            
            # Pattern 7: "(0-X)" hoặc "(1-X)" trong ngoặc - range format
            match = re.search(r'\(\s*\d+\s*-\s*(\d+)\s*\)', full_text)
            if match:
                max_val = int(match.group(1))
                logger.info(f"  Found max_selections (range format): {max_val}")
                return max_val
            
            # =======================================================
            # 📋 VALIDATION ERROR MESSAGES (when user exceeds limit)
            # =======================================================
            error_msgs = question_element.find_elements(By.CLASS_NAME, "dEOOab")
            for msg in error_msgs:
                msg_text = msg.text.lower()
                match = re.search(r'(\d+)', msg_text)
                if match and ('tối đa' in msg_text or 'at most' in msg_text or 'maximum' in msg_text):
                    max_val = int(match.group(1))
                    logger.info(f"  Found max_selections from validation error: {max_val}")
                    return max_val
            
            # Không tìm thấy giới hạn → trả về None (không giới hạn)
            return None
            
        except Exception as e:
            logger.debug(f"  _get_max_selections error: {e}")
            return None
    
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
            # Method 0: Check for LINEAR SCALE first (before multiple choice)
            # Linear scale has class 'Ht8Grd' or 'lLfZXe' or radiogroup with numbered options
            try:
                linear_markers = question_element.find_elements(By.CLASS_NAME, "Ht8Grd")
                if linear_markers and len(linear_markers) > 0:
                    logger.debug("  Detected LINEAR SCALE via Ht8Grd class")
                    return "linear_scale"
                
                # Also check for lLfZXe (linear scale row container)
                llfzxe_markers = question_element.find_elements(By.CLASS_NAME, "lLfZXe")
                if llfzxe_markers and len(llfzxe_markers) > 0:
                    logger.debug("  Detected LINEAR SCALE via lLfZXe class")
                    return "linear_scale"
                
                # 🆕 Check for EDITOR link linear scale: look for consecutive numbers pattern
                # In editor, linear scale displays "1\n2\n3\n4\n5" as visible text
                all_text = question_element.text or ""
                
                import re
                
                # Method A: Find pattern like "1\n2\n3\n4\n5" (consecutive numbers with newlines)
                # This is the ACTUAL format in editor view for linear scale
                consecutive_numbers = re.search(r'\n1\n2\n3\n4\n5\n|\n1\n2\n3\n4\n5$|^1\n2\n3\n4\n5\n', all_text)
                if not consecutive_numbers:
                    # Also try pattern with scale labels: "Label1\n1\n2\n3\n4\n5\nLabel2"
                    consecutive_numbers = re.search(r'(?:^|\n)1\n2\n3\n4\n5(?:\n|$)', all_text)
                
                if consecutive_numbers:
                    logger.info(f"  Detected LINEAR SCALE via consecutive numbers pattern 1-5")
                    return "linear_scale"
                
                # Also check for other scale ranges (0-10, 1-10, etc.)
                for scale_range in [(0, 10), (1, 10), (1, 7), (0, 5)]:
                    min_v, max_v = scale_range
                    pattern_nums = '\n'.join(str(i) for i in range(min_v, max_v + 1))
                    if pattern_nums in all_text:
                        logger.info(f"  Detected LINEAR SCALE via consecutive numbers pattern {min_v}-{max_v}")
                        return "linear_scale"
                
                # Check for radiogroup with numbered aria-labels (1, 2, 3, 4, 5...)
                radiogroup = question_element.find_elements(By.XPATH, ".//div[@role='radiogroup']")
                if radiogroup:
                    radios = radiogroup[0].find_elements(By.XPATH, ".//div[@role='radio']")
                    if radios and len(radios) >= 2:
                        # Check if all aria-labels are numbers (linear scale indicator)
                        all_numeric = True
                        for radio in radios[:5]:  # Check first 5
                            aria = radio.get_attribute('aria-label') or ""
                            data_val = radio.get_attribute('data-value') or ""
                            # Check if either is numeric
                            if not (aria.isdigit() or data_val.isdigit()):
                                all_numeric = False
                                break
                        if all_numeric:
                            logger.debug("  Detected LINEAR SCALE via numeric radiogroup")
                            return "linear_scale"
            except Exception as e:
                logger.debug(f"  Linear scale detection error: {e}")
            
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
        
        # 🆕 Strategy 0.5: LINEAR SCALE for EDITOR LINK - CHECK THIS FIRST!
        # In editor, linear scale displays numbers like "1\n2\n3\n4\n5" as visible text
        # This MUST run BEFORE other strategies that might pick up the label inputs
        try:
            all_text = question_element.text or ""
            
            import re
            
            # Method 1: Find pattern like "1\n2\n3\n4\n5" (consecutive numbers with newlines)
            # Check various scale ranges - ORDER MATTERS (most common first)
            for scale_range in [(1, 5), (1, 10), (0, 10), (1, 7), (0, 5)]:
                min_v, max_v = scale_range
                pattern_nums = '\n'.join(str(i) for i in range(min_v, max_v + 1))
                if pattern_nums in all_text:
                    logger.info(f"  ✓ Found LINEAR SCALE pattern {min_v}-{max_v} in text!")
                    # Generate options from min to max
                    for idx, val in enumerate(range(min_v, max_v + 1)):
                        options.append({
                            "index": idx,
                            "text": str(val)
                        })
                    logger.info(f"  ✓ Generated {len(options)} options: {[o['text'] for o in options]}")
                    return options
            
            # Method 2: Try to extract scale labels from input fields aria-labels
            # Editor linear scale has inputs with aria like 'Nhãn không bắt buộc đối với giới hạn tỷ lệ dưới: X'
            scale_inputs = question_element.find_elements(By.XPATH, ".//input[contains(@aria-label, 'giới hạn tỷ lệ')]")
            if scale_inputs and len(scale_inputs) >= 2:
                min_val = None
                max_val = None
                for inp in scale_inputs:
                    aria = inp.get_attribute('aria-label') or ""
                    # Extract number from aria-label like "Nhãn không bắt buộc đối với giới hạn tỷ lệ dưới: 1"
                    match = re.search(r':\s*(\d+)', aria)
                    if match:
                        num = int(match.group(1))
                        if 'dưới' in aria.lower():
                            min_val = num
                        elif 'trên' in aria.lower():
                            max_val = num
                
                if min_val is not None and max_val is not None:
                    logger.info(f"  ✓ Found LINEAR SCALE from aria-labels: {min_val} to {max_val}")
                    for idx, val in enumerate(range(min_val, max_val + 1)):
                        options.append({
                            "index": idx,
                            "text": str(val)
                        })
                    logger.info(f"  ✓ Generated {len(options)} options: {[o['text'] for o in options]}")
                    return options
                    
        except Exception as e:
            logger.debug(f"  Editor linear scale strategy failed: {e}")
        
        # 🆕 Strategy 0: Check for LINEAR SCALE on VIEWFORM (radiogroup with numeric values)
        try:
            radiogroup = question_element.find_elements(By.XPATH, ".//div[@role='radiogroup']")
            if radiogroup:
                radios = radiogroup[0].find_elements(By.XPATH, ".//div[@role='radio']")
                if radios and len(radios) >= 2:
                    # Check if this looks like a linear scale (numeric values)
                    first_aria = radios[0].get_attribute('aria-label') or ""
                    first_data = radios[0].get_attribute('data-value') or ""
                    
                    if first_aria.isdigit() or first_data.isdigit():
                        # This is a linear scale - extract all values
                        logger.debug(f"  Detected LINEAR SCALE options from radiogroup")
                        for idx, radio in enumerate(radios):
                            aria_label = radio.get_attribute('aria-label') or ""
                            data_value = radio.get_attribute('data-value') or ""
                            # Prefer data-value, fallback to aria-label
                            value = data_value if data_value else aria_label
                            if value:
                                options.append({
                                    "index": idx,
                                    "text": value.strip()
                                })
                                logger.debug(f"    Scale option {idx}: '{value}'")
                        
                        if options:
                            # Also try to get scale labels (min/max descriptions)
                            try:
                                # Viewform uses Xb9hP class for scale endpoint labels
                                scale_labels = question_element.find_elements(By.CLASS_NAME, "Xb9hP")
                                if not scale_labels:
                                    scale_labels = question_element.find_elements(By.CLASS_NAME, "OaBhFe")
                                if scale_labels and len(scale_labels) >= 2:
                                    min_label = scale_labels[0].text.strip()
                                    max_label = scale_labels[-1].text.strip()
                                    if min_label or max_label:
                                        logger.info(f"  Scale labels: '{min_label}' to '{max_label}'")
                            except:
                                pass
                            
                            logger.debug(f"  Extracted {len(options)} linear scale options")
                            return options
        except Exception as e:
            logger.debug(f"  Linear scale radiogroup strategy failed: {e}")
        
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
            "linear_scale": "📊 Thang điểm tuyến tính",
            "multiple_choice_grid": "Bảng chọn",
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
        self.max_parallel = max(1, min(max_parallel, 10))  # 🆕 Tăng lên 1-10 tabs
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
        options.add_argument("--headless=new")  # 🔧 Chrome chạy ẩn
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,900")
        # 🔧 Page load strategy để không đợi full load (giữ Chrome bình thường)
        options.page_load_strategy = 'eager'
        
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
        """🆕 Chạy đa luồng: Mở N Chrome cùng lúc, thực hiện task LẦN LƯỢT từng Chrome"""
        
        logger.info(f"=" * 60)
        logger.info(f"_run_parallel STARTED (SEQUENTIAL EXECUTION)")
        logger.info(f"count_int = {count_int}")
        logger.info(f"max_parallel = {self.max_parallel}")
        logger.info(f"=" * 60)
        
        if count_int <= 0:
            logger.error(f"❌ count_int is {count_int} - nothing to do!")
            self.progress.emit(f"❌ Lỗi: số lượng response = {count_int}")
            self.finished.emit()
            return
        
        # 🔥 Install chromedriver trước
        self.progress.emit("⏳ Đang chuẩn bị ChromeDriver...")
        logger.info("Pre-installing ChromeDriver...")
        
        try:
            driver_path = ChromeDriverManager().install()
            logger.info(f"✓ ChromeDriver ready: {driver_path}")
        except Exception as e:
            logger.error(f"Failed to install ChromeDriver: {e}")
            driver_path = None
        
        # 🔧 Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")  # 🔧 Chrome chạy ẩn
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Tính vị trí cửa sổ cho mỗi Chrome
        window_width = 600
        window_height = 500
        cols = min(self.max_parallel, 3)
        
        def get_window_position(idx):
            col = idx % cols
            row = idx // cols
            return col * window_width, row * window_height
        
        # 🔥 BƯỚC 1: Mở TẤT CẢ Chrome instances cùng lúc
        self.progress.emit(f"🚀 Đang mở {self.max_parallel} Chrome...")
        drivers = []
        
        for i in range(self.max_parallel):
            try:
                logger.info(f"[Chrome {i}] Creating...")
                if driver_path:
                    driver = webdriver.Chrome(service=Service(driver_path), options=options)
                else:
                    driver = webdriver.Chrome(options=options)
                
                # Đặt vị trí cửa sổ
                x, y = get_window_position(i)
                try:
                    driver.set_window_position(x, y)
                    driver.set_window_size(window_width, window_height)
                except:
                    pass
                
                driver.implicitly_wait(3)
                driver.set_page_load_timeout(30)
                
                drivers.append(driver)
                logger.info(f"[Chrome {i}] ✓ Ready at ({x}, {y})")
                self.progress.emit(f"✓ Chrome {i + 1}/{self.max_parallel} đã sẵn sàng")
                
                # Delay nhỏ giữa các Chrome để tránh race condition
                if i < self.max_parallel - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"[Chrome {i}] ❌ Failed to create: {e}")
                self.progress.emit(f"⚠️ Chrome {i + 1} lỗi: {e}")
        
        if not drivers:
            self.progress.emit("❌ Không thể mở Chrome nào!")
            self.finished.emit()
            return
        
        logger.info(f"✓ Opened {len(drivers)} Chrome instances")
        self.progress.emit(f"✓ Đã mở {len(drivers)} Chrome, bắt đầu gửi responses...")
        
        # 🔥 BƯỚC 2: Thực hiện tasks LẦN LƯỢT - luân phiên giữa các Chrome
        submitted_count = 0
        current_chrome = 0
        
        for task_idx in range(count_int):
            # Chọn Chrome tiếp theo (round-robin)
            driver = drivers[current_chrome]
            chrome_id = current_chrome
            current_chrome = (current_chrome + 1) % len(drivers)
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Task {task_idx + 1}/{count_int} - Using Chrome {chrome_id}")
            logger.info(f"{'='*50}")
            
            self.progress.emit(f"📮 [Chrome {chrome_id}] Response {task_idx + 1}/{count_int}")
            
            try:
                # Load form URL
                logger.info(f"[Chrome {chrome_id}] Loading form URL...")
                driver.get(self.form_url)
                logger.info(f"[Chrome {chrome_id}] ✓ Page loaded: {driver.title}")
                
                # Wait cho form elements
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='radiogroup'], input, .Qr7Oae, div[data-params], .YKDB3e"))
                    )
                except:
                    pass
                
                time.sleep(1)
                
                # 🔥 FIX: Set self.driver để các hàm helper hoạt động đúng
                self.driver = driver
                
                # Fill form - sử dụng logic đơn luồng
                logger.info(f"[Chrome {chrome_id}] Filling form...")
                self._fill_form_for_thread(driver)
                
                submitted_count += 1
                self.count_progress.emit(submitted_count)
                self.progress.emit(f"✓ [Chrome {chrome_id}] Response {task_idx + 1} OK ({submitted_count}/{count_int})")
                logger.info(f"[Chrome {chrome_id}] ✓ Response {task_idx + 1} done")
                
            except Exception as e:
                import traceback
                logger.error(f"[Chrome {chrome_id}] ❌ Error on task {task_idx + 1}: {e}")
                logger.error(traceback.format_exc())
                self.progress.emit(f"⚠️ [Chrome {chrome_id}] Lỗi response {task_idx + 1}: {str(e)[:50]}")
                
                # Nếu Chrome bị crash, thử tạo lại
                try:
                    driver.quit()
                except:
                    pass
                
                try:
                    logger.info(f"[Chrome {chrome_id}] Recreating...")
                    if driver_path:
                        new_driver = webdriver.Chrome(service=Service(driver_path), options=options)
                    else:
                        new_driver = webdriver.Chrome(options=options)
                    
                    x, y = get_window_position(chrome_id)
                    try:
                        new_driver.set_window_position(x, y)
                        new_driver.set_window_size(window_width, window_height)
                    except:
                        pass
                    
                    new_driver.implicitly_wait(3)
                    new_driver.set_page_load_timeout(30)
                    drivers[chrome_id] = new_driver
                    logger.info(f"[Chrome {chrome_id}] ✓ Recreated successfully")
                except Exception as re:
                    logger.error(f"[Chrome {chrome_id}] Failed to recreate: {re}")
        
        # 🔥 BƯỚC 3: Đóng tất cả Chrome
        logger.info("Closing all Chrome instances...")
        for i, driver in enumerate(drivers):
            try:
                driver.quit()
                logger.info(f"[Chrome {i}] ✓ Closed")
            except Exception as e:
                logger.warning(f"[Chrome {i}] Error closing: {e}")
        
        logger.info(f"✓ Complete! {submitted_count}/{count_int} responses")
        self.progress.emit(f"✅ Hoàn tất! Đã gửi {submitted_count}/{count_int} responses ({len(drivers)} Chrome)")
        self.finished.emit()

    def _get_thread_rng(self):
        """Tạo RNG riêng cho từng thread để random độc lập giữa các luồng."""
        import threading
        import time
        import random

        if not hasattr(self, "_thread_rngs"):
            self._thread_rngs = {}
        tid = threading.get_ident()
        rng = self._thread_rngs.get(tid)
        if rng is None:
            seed = time.time_ns() ^ tid
            rng = random.Random(seed)
            self._thread_rngs[tid] = rng
        return rng

    def _select_by_percentage(self, options_list: List[Dict], rng=None) -> str:
        """Chọn option dựa trên tỉ lệ phần trăm"""
        import random as rand
        rng = rng or rand
        
        # Build a list where each option appears based on its percentage
        weighted_options = []
        for option_data in options_list:
            text = option_data['text']
            percentage = option_data['percentage']
            # Repeat the option based on percentage (100 times total)
            weighted_options.extend([text] * percentage)
        
        # Randomly select one
        selected = rng.choice(weighted_options)
        logger.info(f"Random selection: {selected} (from {len(options_list)} options with percentages)")
        return selected
    
    def _fill_form(self):
        """Điền form - hỗ trợ chế độ bình thường và random, tự động chuyển trang
        
        🆕 MATCH BY TITLE: Thay vì dựa vào index (không đáng tin cậy vì editor và viewform có cấu trúc khác),
        giờ sẽ match câu hỏi theo title để đảm bảo điền đúng câu.
        """
        logger.info(f"Starting to fill form with {len(self.answers)} answers (multi-page support)")
        logger.info(f"🆕 Using TITLE-BASED matching for reliable question mapping")
        
        # Tạo dictionary để lookup nhanh theo title
        # Normalize title để so sánh chính xác hơn
        self._question_title_map = {}
        for idx, q in enumerate(self.questions):
            if q.get('type') != 'section_header':
                title_normalized = self._normalize_title(q['title'])
                self._question_title_map[title_normalized] = {
                    'index': idx,
                    'data': q
                }
                logger.debug(f"  Map: '{title_normalized[:50]}...' -> Q{idx+1}")
        
        page_num = 1
        filled_count = 0
        
        try:
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"FILLING PAGE {page_num}")
                logger.info(f"{'='*60}")
                
                time.sleep(1)
                
                # 🆕 Tìm câu hỏi trên viewform bằng cách tìm question containers có title
                questions_on_page = self._find_viewform_questions()
                logger.info(f"Found {len(questions_on_page)} questions on page {page_num}")
                
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
                
                # 🆕 Điền câu trả lời cho các câu hỏi trên trang này - MATCH BY TITLE
                for page_q_idx, (q_element, q_title_from_viewform) in enumerate(questions_on_page):
                    # Tìm câu hỏi tương ứng trong danh sách đã extract từ editor
                    title_normalized = self._normalize_title(q_title_from_viewform)
                    matched = self._question_title_map.get(title_normalized)
                    
                    if not matched:
                        # Thử tìm với partial match
                        matched = self._find_question_by_partial_title(q_title_from_viewform)
                    
                    if not matched:
                        logger.warning(f"  ⚠️ Q{page_q_idx + 1}: '{q_title_from_viewform[:40]}...' - NOT FOUND in extracted questions")
                        continue
                    
                    question_idx = matched['index']
                    question_data = matched['data']
                    
                    # Skip nếu không có đáp án cho câu này
                    if question_idx not in self.answers:
                        logger.info(f"  Q{question_idx + 1}: Skipped (no answer)")
                        continue
                    
                    try:
                        answer = self.answers[question_idx]
                        q_type = question_data['type']
                        q_title = question_data['title']
                        
                        logger.info(f"  Q{question_idx + 1} ({q_type}): {q_title[:50]}...")
                        logger.info(f"    Answer: {answer}")
                        
                        if q_type == "short_answer" or q_type == "long_answer":
                            self._fill_text_field(q_element, str(answer))
                            logger.info(f"    ✓ Filled text")
                            filled_count += 1
                        
                        elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                            # 🆕 Hỗ trợ cả 'random' và 'random_scale' từ getAnswersFromWidgets
                            if isinstance(answer, tuple) and answer[0] in ['random', 'random_scale']:
                                options_list = answer[1]
                                selected_option = self._select_by_percentage(options_list)
                                logger.info(f"    Random Mode - Selected: {selected_option}")
                                self._select_option(q_element, selected_option)
                            else:
                                self._select_option(q_element, str(answer))
                            logger.info(f"    ✓ Selected option")
                            filled_count += 1
                        
                        elif q_type == "checkbox":
                            # 🆕 Hỗ trợ cả 'random' và 'random_checkbox' từ getAnswersFromWidgets
                            if isinstance(answer, tuple) and answer[0] in ['random', 'random_checkbox']:
                                options_list = answer[1]
                                # Random độc lập - không giới hạn số lượng
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
                            filled_count += 1
                    
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
                    page_num += 1
                else:
                    # Trang cuối cùng - exit loop để gửi form
                    logger.info(f"  ✓ No next button found - last page reached")
                    break
        
        except Exception as e:
            logger.error(f"Error filling form: {e}", exc_info=True)
            raise
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Form filling complete - Filled {filled_count} questions")
        logger.info(f"{'='*60}\n")
        
        # 🆕 Gửi form sau khi điền xong
        logger.info("Now submitting the form...")
        self._submit_form()
    
    def _normalize_title(self, title: str) -> str:
        """Chuẩn hóa title để so sánh - loại bỏ whitespace thừa, normalize unicode"""
        if not title:
            return ""
        import unicodedata
        import re
        # Normalize unicode
        normalized = unicodedata.normalize('NFC', title)
        # Loại bỏ whitespace thừa và newlines
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized.lower()
    
    def _find_question_by_partial_title(self, viewform_title: str):
        """Tìm câu hỏi bằng partial match nếu exact match không tìm thấy"""
        if not viewform_title:
            return None
        
        viewform_title_clean = self._normalize_title(viewform_title)
        
        # Thử match phần đầu của title (có thể viewform có thêm các suffix)
        for title_key, data in self._question_title_map.items():
            # Nếu một cái chứa cái kia thì coi như match
            if viewform_title_clean in title_key or title_key in viewform_title_clean:
                logger.debug(f"  Partial match: '{viewform_title_clean[:30]}' ~ '{title_key[:30]}'")
                return data
        
        # Thử với similarity ratio nếu cần
        try:
            from difflib import SequenceMatcher
            best_match = None
            best_ratio = 0.6  # Ngưỡng tối thiểu
            
            for title_key, data in self._question_title_map.items():
                ratio = SequenceMatcher(None, viewform_title_clean, title_key).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = data
            
            if best_match:
                logger.debug(f"  Fuzzy match ({best_ratio:.2f}): '{viewform_title_clean[:30]}' ~ Q{best_match['index']+1}")
                return best_match
        except:
            pass
        
        return None
    
    def _find_viewform_questions(self):
        """
        🆕 Tìm tất cả câu hỏi trên viewform và trả về list của (element, title) tuples.
        Đây là function mới để detect câu hỏi trên viewform một cách chính xác.
        """
        questions = []
        
        # Method 1: Tìm bằng data-params (chứa entry IDs) - đáng tin cậy nhất
        try:
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div[data-params]")
            logger.debug(f"Method 1 (data-params): Found {len(containers)} containers")
            
            for container in containers:
                try:
                    if not container.is_displayed():
                        continue
                    
                    # Tìm title trong container
                    title = self._extract_question_title_from_viewform(container)
                    if title:
                        questions.append((container, title))
                except:
                    pass
        except Exception as e:
            logger.debug(f"Method 1 failed: {e}")
        
        # Method 2: Nếu chưa tìm được, thử với div[role='listitem']
        if len(questions) == 0:
            try:
                containers = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
                logger.debug(f"Method 2 (role=listitem): Found {len(containers)} containers")
                
                for container in containers:
                    try:
                        if not container.is_displayed():
                            continue
                        
                        title = self._extract_question_title_from_viewform(container)
                        if title:
                            questions.append((container, title))
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Method 2 failed: {e}")
        
        # Method 3: Tìm với Qr7Oae (old selector)
        if len(questions) == 0:
            try:
                containers = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                logger.debug(f"Method 3 (Qr7Oae): Found {len(containers)} containers")
                
                for container in containers:
                    try:
                        if not container.is_displayed():
                            continue
                        
                        title = self._extract_question_title_from_viewform(container)
                        if title:
                            questions.append((container, title))
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Method 3 failed: {e}")
        
        # Method 4: Tìm với M7eMe (question title class) và lấy parent
        if len(questions) == 0:
            try:
                title_elements = self.driver.find_elements(By.CLASS_NAME, "M7eMe")
                logger.debug(f"Method 4 (M7eMe): Found {len(title_elements)} title elements")
                
                seen_containers = set()
                for title_elem in title_elements:
                    try:
                        if not title_elem.is_displayed():
                            continue
                        
                        title = title_elem.text.strip()
                        if not title:
                            continue
                        
                        # Lấy parent container
                        parent = self.driver.execute_script("""
                            let el = arguments[0];
                            for (let i = 0; i < 10; i++) {
                                el = el.parentElement;
                                if (!el) break;
                                if (el.getAttribute('data-params') || el.getAttribute('data-item-id') || 
                                    el.getAttribute('role') === 'listitem') {
                                    return el;
                                }
                            }
                            return arguments[0].parentElement.parentElement.parentElement;
                        """, title_elem)
                        
                        if parent and id(parent) not in seen_containers:
                            seen_containers.add(id(parent))
                            questions.append((parent, title))
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Method 4 failed: {e}")
        
        logger.info(f"Found {len(questions)} questions with titles on viewform")
        for i, (_, title) in enumerate(questions):
            logger.debug(f"  VF-Q{i+1}: {title[:50]}...")
        
        return questions
    
    def _extract_question_title_from_viewform(self, container) -> str:
        """Extract title của câu hỏi từ container trên viewform"""
        try:
            # Try M7eMe first (most common)
            try:
                title_elem = container.find_element(By.CLASS_NAME, "M7eMe")
                title = title_elem.text.strip()
                if title:
                    return title
            except:
                pass
            
            # Try span with question text
            try:
                title_elem = container.find_element(By.CSS_SELECTOR, "span.M7eMe, span.yCMM9e, div.M7eMe")
                title = title_elem.text.strip()
                if title:
                    return title
            except:
                pass
            
            # Try getting any text in the header area
            try:
                header = container.find_element(By.CSS_SELECTOR, "div[role='heading'], .freebirdFormviewerComponentsQuestionBaseHeader")
                title = header.text.strip().split('\n')[0]  # Get first line
                if title:
                    return title
            except:
                pass
            
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")
        
        return ""
    
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
    
    def _select_by_percentage(self, options_list, rng=None):
        """🎯 Chọn một option theo xác suất % độc lập
        
        Mỗi option có target % riêng (VD: 30% = option sẽ xuất hiện trong ~30% responses)
        Random độc lập từng option - nếu không có option nào được chọn, fallback random 1 option
        """
        import random
        rng = rng or random
        
        if not options_list:
            return ""
        
        # Duyệt qua từng option, roll % độc lập
        candidates = []
        for opt in options_list:
            rand_val = rng.randint(1, 100)
            if rand_val <= opt['percentage']:
                candidates.append(opt)
                logger.debug(f"    {opt['text'][:20]}: roll={rand_val} <= {opt['percentage']}% → ✓")
            else:
                logger.debug(f"    {opt['text'][:20]}: roll={rand_val} > {opt['percentage']}% → ✗")
        
        # Nếu có candidates → random chọn 1 trong số đó
        if candidates:
            selected = rng.choice(candidates)
            logger.info(f"  ✅ Selected from {len(candidates)} candidates: {selected['text'][:30]}")
            return selected['text']
        
        # 🔥 FALLBACK: Không có option nào được chọn → random 1 option bất kỳ
        selected = rng.choice(options_list)
        logger.info(f"  ⚠️ No option matched % → Fallback random: {selected['text'][:30]}")
        return selected['text']
    
    def _select_multiple_by_percentage(self, options_list, max_selections=None, rng=None):
        """🎯 TARGET DISTRIBUTION MODE: Chọn nhiều options dựa trên target % độc lập
        
        Mỗi option có target % riêng (VD: 65% = option sẽ xuất hiện trong ~65% responses)
        Random độc lập từng option - KHÔNG giới hạn số lượng được chọn
        
        Args:
            options_list: [{'text': 'A', 'percentage': 65}, {'text': 'B', 'percentage': 25}, ...]
            max_selections: (Không sử dụng - giữ để tương thích)
        
        Returns: List các option_text được chọn
        """
        import random
        rng = rng or random
        
        logger.info(f"  📊 TARGET DISTRIBUTION: {[(o['text'][:20], str(o['percentage']) + '%') for o in options_list]}")
        
        # Random độc lập cho từng option
        selected = []
        for opt in options_list:
            rand_val = rng.randint(1, 100)
            is_selected = rand_val <= opt['percentage']
            if is_selected:
                selected.append(opt['text'])
            logger.debug(f"    {opt['text'][:20]}: roll={rand_val}, target={opt['percentage']}% → {'✓' if is_selected else '✗'}")
        
        # Đảm bảo ít nhất 1 option được chọn
        if not selected and options_list:
            best_option = max(options_list, key=lambda x: x['percentage'])
            selected.append(best_option['text'])
            logger.info(f"    (Fallback: selected highest target option)")
        
        logger.info(f"  ✅ Selected {len(selected)}/{len(options_list)} options: {selected}")
        return selected
    
    def _weighted_random_choice(self, options_list):
        """Chọn 1 option dựa trên weight (percentage)"""
        import random
        total = sum(opt['percentage'] for opt in options_list)
        rand = random.uniform(0, total)
        cumulative = 0
        for opt in options_list:
            cumulative += opt['percentage']
            if rand <= cumulative:
                return opt
        return options_list[-1]
    
    def _weighted_sample_without_replacement(self, population, weights, k):
        """Weighted random sampling WITHOUT replacement
        
        Chọn k items từ population, dựa trên weights, KHÔNG lặp lại.
        Options có weight cao hơn → xác suất được chọn cao hơn.
        
        Args:
            population: List các items cần chọn
            weights: List weights tương ứng (percentage)
            k: Số lượng cần chọn
        
        Returns: List k items được chọn (không trùng lặp)
        """
        import random
        
        if k >= len(population):
            return population[:]
        
        selected = []
        available = list(zip(population, weights))
        
        for _ in range(k):
            # Tính tổng weight còn lại
            total_weight = sum(w for _, w in available)
            
            # Random với weight
            rand = random.uniform(0, total_weight)
            cumulative = 0
            
            for i, (item, weight) in enumerate(available):
                cumulative += weight
                if rand <= cumulative:
                    selected.append(item)
                    available.pop(i)  # Loại bỏ để không chọn lại
                    break
        
        return selected
    
    def _select_option(self, question_element, option_text: str):
        """Chọn option - try multiple methods (bao gồm LINEAR SCALE)"""
        try:
            logger.debug(f"Trying to select: {option_text}")
            
            # 🆕 METHOD 0: LINEAR SCALE - data-value match (PRIORITIZE for numeric options)
            # Linear scale options are numbers like "1", "2", "3", "4", "5"
            if option_text.strip().isdigit():
                logger.debug(f"  Detected numeric option '{option_text}' - trying LINEAR SCALE methods")
                
                # Method 0a: Try div.Od2TWd[data-value='X'] or div[role='radio'][data-value='X']
                for selector in [
                    f"div.Od2TWd[data-value='{option_text}']",
                    f"div[role='radio'][data-value='{option_text}']",
                    f"div[data-value='{option_text}']"
                ]:
                    try:
                        radios = question_element.find_elements(By.CSS_SELECTOR, selector)
                        if radios:
                            radio = radios[0]
                            # Check if not already checked
                            is_checked = radio.get_attribute("aria-checked") == "true"
                            if not is_checked:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                time.sleep(0.3)
                                self.driver.execute_script("arguments[0].click();", radio)
                                logger.info(f"✓ Clicked LINEAR SCALE via {selector}: {option_text}")
                                time.sleep(0.5)
                                return
                            else:
                                logger.debug(f"  Radio {option_text} already checked")
                                return
                    except Exception as e:
                        logger.debug(f"  {selector} failed: {e}")
                
                # Method 0b: Try label.T5pZmf containing Zki2Ve with matching text (for some viewform layouts)
                try:
                    labels = question_element.find_elements(By.CSS_SELECTOR, "label.T5pZmf")
                    for label in labels:
                        try:
                            zki = label.find_element(By.CLASS_NAME, "Zki2Ve")
                            if zki.text.strip() == option_text.strip():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
                                time.sleep(0.3)
                                self.driver.execute_script("arguments[0].click();", label)
                                logger.info(f"✓ Clicked LINEAR SCALE label Zki2Ve='{option_text}'")
                                time.sleep(0.5)
                                return
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"  label.T5pZmf method failed: {e}")
                
                # Method 0c: Find div[role='radio'] with aria-label matching the number
                try:
                    radios = question_element.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                    for radio in radios:
                        aria_label = radio.get_attribute("aria-label") or ""
                        data_value = radio.get_attribute("data-value") or ""
                        if aria_label.strip() == option_text.strip() or data_value.strip() == option_text.strip():
                            is_checked = radio.get_attribute("aria-checked") == "true"
                            if not is_checked:
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                time.sleep(0.3)
                                self.driver.execute_script("arguments[0].click();", radio)
                                logger.info(f"✓ Clicked LINEAR SCALE radio aria-label/data-value='{option_text}'")
                                time.sleep(0.5)
                                return
                            else:
                                logger.debug(f"  Radio {option_text} already checked")
                                return
                except Exception as e:
                    logger.debug(f"  div[role='radio'] aria-label method failed: {e}")
            
            # Method 1: Try via YKDB3e class (for multiple choice)
            # 🔧 FIX: Thêm scroll, normalize text, và JavaScript click
            try:
                options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
                logger.debug(f"  Found {len(options)} YKDB3e options")
                for option in options:
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        label_text = label.text.strip()
                        target_text = option_text.strip()
                        
                        # 🔧 Normalize text: thay thế các ký tự đặc biệt
                        label_normalized = label_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        logger.debug(f"    Comparing: '{label_normalized}' vs '{target_normalized}'")
                        
                        if label_normalized == target_normalized or label_text == target_text:
                            # 🔧 FIX: Scroll vào view trước
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                            time.sleep(0.3)
                            
                            # 🔧 FIX: Thử JavaScript click trước (đáng tin cậy hơn)
                            try:
                                self.driver.execute_script("arguments[0].click();", option)
                                logger.info(f"✓ JS-Clicked option via YKDB3e: {option_text}")
                                time.sleep(0.5)
                                return
                            except:
                                # Fallback to normal click
                                option.click()
                                logger.info(f"✓ Clicked option via YKDB3e: {option_text}")
                                time.sleep(0.5)
                                return
                    except Exception as e:
                        logger.debug(f"    YKDB3e option error: {e}")
                        pass
            except Exception as e:
                logger.debug(f"  YKDB3e method error: {e}")
            
            # 🆕 Method 1b: Try clicking the div[role='radio'] inside docssharedWizToggleLabeledContainer
            try:
                containers = question_element.find_elements(By.CLASS_NAME, "docssharedWizToggleLabeledContainer")
                logger.debug(f"  Found {len(containers)} docssharedWizToggleLabeledContainer")
                for container in containers:
                    try:
                        container_text = container.text.strip().split('\n')[0]  # First line
                        target_text = option_text.strip()
                        
                        # Normalize
                        container_normalized = container_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        if container_normalized == target_normalized or container_text == target_text:
                            # Scroll
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
                            time.sleep(0.3)
                            
                            # Try to find and click the radio div inside
                            try:
                                radio_div = container.find_element(By.CSS_SELECTOR, "div[role='radio']")
                                self.driver.execute_script("arguments[0].click();", radio_div)
                                logger.info(f"✓ Clicked radio inside container: {option_text}")
                                time.sleep(0.5)
                                return
                            except:
                                # Click container itself
                                self.driver.execute_script("arguments[0].click();", container)
                                logger.info(f"✓ Clicked container: {option_text}")
                                time.sleep(0.5)
                                return
                    except:
                        pass
            except Exception as e:
                logger.debug(f"  docssharedWizToggleLabeledContainer method error: {e}")
            
            # 🆕 Method 1c: Find all div[role='radio'] and match by parent text
            try:
                radiogroup = question_element.find_element(By.CSS_SELECTOR, "div[role='radiogroup']")
                radios = radiogroup.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                logger.debug(f"  Found {len(radios)} div[role='radio'] in radiogroup")
                
                for radio in radios:
                    try:
                        # Get parent container text
                        parent = radio.find_element(By.XPATH, "./..")
                        parent_text = parent.text.strip().split('\n')[0] if parent.text else ""
                        
                        # Also check sibling label
                        try:
                            label_sibling = parent.find_element(By.CLASS_NAME, "urLvsc")
                            sibling_text = label_sibling.text.strip()
                        except:
                            sibling_text = ""
                        
                        target_text = option_text.strip()
                        
                        # Normalize
                        parent_normalized = parent_text.replace('–', '-').replace('—', '-')
                        sibling_normalized = sibling_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        if (parent_normalized == target_normalized or 
                            sibling_normalized == target_normalized or
                            parent_text == target_text or 
                            sibling_text == target_text):
                            
                            # Check if not already checked
                            is_checked = radio.get_attribute("aria-checked") == "true"
                            if is_checked:
                                logger.debug(f"    Radio already checked: {option_text}")
                                return
                            
                            # Scroll and click
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                            time.sleep(0.3)
                            self.driver.execute_script("arguments[0].click();", radio)
                            logger.info(f"✓ Clicked div[role='radio'] by parent text: {option_text}")
                            time.sleep(0.5)
                            return
                    except Exception as e:
                        logger.debug(f"    Radio check error: {e}")
            except Exception as e:
                logger.debug(f"  div[role='radiogroup'] method error: {e}")
            
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
            
            # Method 5: Try aria-label match (generic fallback)
            try:
                elements = question_element.find_elements(By.CSS_SELECTOR, f"div[aria-label='{option_text}']")
                if elements:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
                    time.sleep(0.2)
                    self.driver.execute_script("arguments[0].click();", elements[0])
                    logger.info(f"✓ Clicked element with aria-label '{option_text}'")
                    time.sleep(0.5)
                    return
            except:
                pass
            
            # 🆕 Method 6: FALLBACK - Tìm trên TOÀN BỘ PAGE (nếu question_element không chứa đúng)
            # Đặc biệt cho LINEAR SCALE khi question_element không đúng
            if option_text.strip().isdigit():
                logger.info(f"  Trying GLOBAL search for linear scale option '{option_text}'...")
                try:
                    # Tìm trên toàn bộ driver thay vì chỉ trong question_element
                    for selector in [
                        f"div[data-value='{option_text}']",
                        f"div[role='radio'][data-value='{option_text}']",
                        f"div.Od2TWd[data-value='{option_text}']"
                    ]:
                        radios = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if radios:
                            # Tìm radio chưa được check
                            for radio in radios:
                                is_checked = radio.get_attribute("aria-checked") == "true"
                                if not is_checked:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                    time.sleep(0.3)
                                    self.driver.execute_script("arguments[0].click();", radio)
                                    logger.info(f"✓ GLOBAL: Clicked LINEAR SCALE via {selector}: {option_text}")
                                    time.sleep(0.5)
                                    return
                except Exception as e:
                    logger.debug(f"  Global linear scale search failed: {e}")
            
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
        import threading
        tid = threading.get_ident()
        logger.info(f"[FILL-{tid}] ====== STARTING _fill_form_for_thread ======")
        logger.info(f"[FILL-{tid}] self.questions count: {len(self.questions) if hasattr(self, 'questions') and self.questions else 0}")
        logger.info(f"[FILL-{tid}] self.answers count: {len(self.answers) if hasattr(self, 'answers') and self.answers else 0}")
        logger.info(f"[FILL-{tid}] driver: {driver}")
        rng = self._get_thread_rng()
        
        # 🔧 FIX: Tạo thread-local copy của questions và answers để tránh race condition
        tid = threading.get_ident()
        questions_copy = list(self.questions)  # Shallow copy to avoid shared state issues
        answers_copy = dict(self.answers)  # Copy answers dict
        logger.debug(f"[T{tid}] Created thread-local copies: {len(questions_copy)} questions, {len(answers_copy)} answers")
        
        # 🆕 Build ordered list of (answer, q_type) - only real questions, skip page titles
        answers_ordered = []
        for q_idx in sorted(answers_copy.keys()):
            if q_idx < len(questions_copy):
                q = questions_copy[q_idx]
                if not q.get('is_page_title', False):
                    answers_ordered.append({
                        'answer': answers_copy[q_idx],
                        'type': q.get('type', 'unknown'),
                        'title': q.get('title', ''),
                        'max_selections': q.get('max_selections')  # 🆕 Giới hạn tối đa cho checkbox
                    })
        
        logger.info(f"Prepared {len(answers_ordered)} answers to fill (excluding page titles)")
        for i, a in enumerate(answers_ordered):
            logger.debug(f"  [{i}] {a['type']}: {a['title'][:50]}...")
        
        page_number = 1
        global_question_idx = 0  # Index vào answers_ordered
        
        # 🆕 Create WebDriverWait for explicit waits
        wait = WebDriverWait(driver, timeout=10)  # FIX: Tăng từ 6s lên 10s cho đa luồng
        
        while True:
            logger.info(f"\n{'='*60}")
            logger.info(f"FILLING PAGE {page_number} (global_idx={global_question_idx})")
            logger.info(f"Current URL: {driver.current_url}")
            logger.info(f"{'='*60}")
            
            # 🆕 DEBUG: Take screenshot of current state
            try:
                page_title = driver.title
                logger.info(f"Page title: {page_title}")
            except:
                pass
            
            # 🔧 Wait for page to load - thử nhiều selectors (with timeout)
            page_loaded = False
            wait_selectors = [
                (By.CLASS_NAME, "Qr7Oae"),
                (By.CLASS_NAME, "YKDB3e"),  # 🔧 Thêm selector quan trọng
                (By.CSS_SELECTOR, "div[role='radiogroup']"),
                (By.CSS_SELECTOR, "div[data-params]"),
            ]
            
            # Try waiting with short timeout per selector
            for by_type, selector in wait_selectors:
                try:
                    wait_short = WebDriverWait(driver, timeout=1.5)  # faster per selector
                    wait_short.until(EC.presence_of_element_located((by_type, selector)))
                    logger.debug(f"✓ Page loaded - found {selector}")
                    page_loaded = True
                    break
                except:
                    continue
            
            if not page_loaded:
                logger.warning("⚠️ Could not find question elements via selectors - using fallback")
                time.sleep(0.5)  # Tăng từ 0.1s
            else:
                logger.debug("✓ Page loaded successfully")
            
            # 🔧 FIX: Tăng wait time cho DOM ổn định (0.15s -> 1.0s)
            time.sleep(1.0)
            
            # 🆕 Find question elements - try MANY strategies for different viewform versions
            question_elements = []
            
            # Strategy 1: Qr7Oae (classic)
            question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            logger.debug(f"Selector Qr7Oae: {len(question_elements)}")
            
            # Strategy 2: data-params
            if len(question_elements) == 0:
                question_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-params]")
                logger.debug(f"Selector data-params: {len(question_elements)}")
            
            # Strategy 3: freebirdFormviewerComponentsQuestionBaseRoot
            if len(question_elements) == 0:
                question_elements = driver.find_elements(By.CLASS_NAME, "freebirdFormviewerComponentsQuestionBaseRoot")
                logger.debug(f"Selector freebirdFormviewerComponentsQuestionBaseRoot: {len(question_elements)}")
            
            # Strategy 4: Find by radiogroup and get parent
            if len(question_elements) == 0:
                logger.debug("Trying to find questions by radiogroup...")
                radiogroups = driver.find_elements(By.CSS_SELECTOR, "div[role='radiogroup']")
                for rg in radiogroups:
                    try:
                        parent = rg.find_element(By.XPATH, "./ancestor::div[contains(@class, 'Qr7Oae') or @data-params or contains(@class, 'freebirdFormviewerComponentsQuestionBaseRoot')][1]")
                        if parent not in question_elements:
                            question_elements.append(parent)
                    except:
                        question_elements.append(rg)
                logger.debug(f"  Questions from radiogroups: {len(question_elements)}")
            
            # Strategy 5: Just use the whole form body as single question container
            if len(question_elements) == 0:
                logger.debug("Using form body as question container...")
                try:
                    form_body = driver.find_element(By.CSS_SELECTOR, "form, div.freebirdFormviewerViewFormCard, div.RH5hzf")
                    question_elements = [form_body]
                except:
                    pass
            
            logger.info(f"Total question elements found: {len(question_elements)}")
            
            # 🆕 For multi-page forms, we might not have traditional question containers
            # Just proceed to fill answers directly by finding interactive elements
            if len(question_elements) == 0:
                logger.warning("No question containers found - trying direct element search")
                # Create a "fake" question element using the entire page
                try:
                    page_container = driver.find_element(By.TAG_NAME, "body")
                    question_elements = [page_container]
                except:
                    pass
            
            # 🆕 Filter only REAL question elements (có input/radio/checkbox, không phải section header)
            real_questions = []
            for idx, elem in enumerate(question_elements):
                try:
                    # Check if element has input fields (text, radio, checkbox, dropdown)
                    has_input = len(elem.find_elements(By.CSS_SELECTOR, "input, textarea")) > 0
                    has_radio = len(elem.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='radiogroup']")) > 0
                    has_checkbox = len(elem.find_elements(By.CSS_SELECTOR, "div[role='checkbox'], div[role='group']")) > 0
                    has_listbox = len(elem.find_elements(By.CSS_SELECTOR, "div[role='listbox']")) > 0
                    # 🆕 Check for linear scale (has aria-valuemin/max attributes)
                    has_linear_scale = len(elem.find_elements(By.CSS_SELECTOR, "div[aria-valuemin], div[data-value]")) > 0
                    
                    # 🆕 DEBUG: Log all elements for page 2+
                    if page_number >= 2:
                        try:
                            elem_text = elem.text[:80].replace('\n', ' ') if elem.text else "(no text)"
                            logger.info(f"  [{idx}] text='{elem_text}' | input={has_input}, radio={has_radio}, cb={has_checkbox}, linear={has_linear_scale}")
                        except:
                            pass
                    
                    if has_input or has_radio or has_checkbox or has_listbox or has_linear_scale:
                        real_questions.append(elem)
                        logger.debug(f"  ✓ Real question found: input={has_input}, radio={has_radio}, cb={has_checkbox}, listbox={has_listbox}, linear={has_linear_scale}")
                    else:
                        # Check element text to log what we're skipping
                        try:
                            elem_text = elem.text[:50] if elem.text else "(no text)"
                            logger.debug(f"  ✗ Skipping non-question element: {elem_text}")
                        except:
                            pass
                except Exception as e:
                    logger.debug(f"  Error checking element: {e}")
            
            logger.info(f"Filtered to {len(real_questions)} real question elements on page {page_number}")
            
            # 🔧 FIX: Nếu KHÔNG có câu hỏi trên trang này, kiểm tra nút TIẾP ngay lập tức
            if len(real_questions) == 0:
                logger.warning(f"⚠️ NO QUESTIONS found on page {page_number}")
                
                # Tìm nút Tiếp/Next
                next_btn = None
                next_xpaths = [
                    "//span[contains(text(),'Tiếp')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(.,'Tiếp')]",
                    "//span[contains(text(),'Next')]/ancestor::div[@role='button']",
                    "//div[@role='button' and contains(.,'Next')]",
                    "//div[contains(@class,'freebirdFormviewerViewNavigationLeftButtons')]//div[@role='button']",
                ]
                
                for xpath in next_xpaths:
                    try:
                        btns = driver.find_elements(By.XPATH, xpath)
                        for btn in btns:
                            btn_text = (btn.text or "").lower()
                            # Skip submit/back buttons
                            if any(x in btn_text for x in ['gửi', 'submit', 'quay', 'back']):
                                continue
                            if btn.is_displayed():
                                next_btn = btn
                                logger.info(f"  ✓ Found NEXT button: '{btn.text}'")
                                break
                        if next_btn:
                            break
                    except:
                        continue
                
                if next_btn:
                    # Click nút Tiếp để sang trang có câu hỏi
                    logger.info(f"  → Clicking NEXT to go to page {page_number + 1}...")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                        time.sleep(0.3)
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(2.0)  # Wait for page load
                        page_number += 1
                        continue  # 🔥 QUAN TRỌNG: Tiếp tục loop, không fill gì cả!
                    except Exception as e:
                        logger.error(f"  ✗ Error clicking NEXT: {e}")
                else:
                    # Không có nút Tiếp và không có câu hỏi -> có thể đã xong
                    if global_question_idx >= len(answers_ordered):
                        logger.info("  All answers filled - form complete!")
                        break
                    else:
                        logger.warning(f"  ⚠️ No NEXT button and still have {len(answers_ordered) - global_question_idx} answers to fill!")
                        # Thử đợi thêm và retry 1 lần
                        time.sleep(2.0)
                        # Re-find questions sau khi đợi
                        question_elements = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                        if len(question_elements) == 0:
                            question_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-params]")
                        if len(question_elements) == 0:
                            logger.error("  ✗ Still no questions found - breaking loop")
                            break
                        # Re-filter
                        real_questions = []
                        for elem in question_elements:
                            try:
                                has_input = len(elem.find_elements(By.CSS_SELECTOR, "input, textarea, div[role='radio'], div[role='checkbox'], div[role='listbox'], div[data-value]")) > 0
                                if has_input:
                                    real_questions.append(elem)
                            except:
                                pass
                        if len(real_questions) == 0:
                            logger.error("  ✗ No real questions after retry - breaking")
                            break
                        logger.info(f"  ✓ Found {len(real_questions)} questions after retry")
            
            # Fill each question on current page
            for local_idx, question_element in enumerate(real_questions):
                if global_question_idx >= len(answers_ordered):
                    logger.info(f"All answers filled (global_idx={global_question_idx})")
                    break
                
                try:
                    answer_data = answers_ordered[global_question_idx]
                    answer = answer_data['answer']
                    q_type = answer_data['type']
                    title = answer_data['title']

                    # 🔧 Ưu tiên tìm đúng câu hỏi theo title để tránh lệch khi chạy đa luồng
                    try:
                        matched_container = self._find_question_container_by_title_for_thread(driver, title)
                        if matched_container is not None:
                            question_element = matched_container
                    except:
                        pass
                    
                    # 🆕 Log the element we're about to fill
                    try:
                        elem_title = question_element.find_element(By.CLASS_NAME, "M7eMe").text[:50]
                        logger.info(f"Filling Q{global_question_idx + 1} ({q_type}): expected='{title}' | found='{elem_title}'")
                    except:
                        logger.info(f"Filling Q{global_question_idx + 1} ({q_type}): {title}...")
                    
                    logger.info(f"  Answer: {str(answer)[:50]}...")
                    logger.info(f"  Answer type: {type(answer).__name__}")
                    
                    # Check required status for fallback
                    is_required = self._is_required_question_for_thread(question_element)

                    # Fill based on question type
                    if q_type in ["short_answer", "long_answer"]:
                        logger.info(f"  → Calling _fill_text_field_for_thread...")
                        self._fill_text_field_for_thread(driver, question_element, str(answer))
                    
                    elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                        logger.info(f"  → q_type={q_type}, checking if random...")
                        if isinstance(answer, tuple) and answer[0] in ['random', 'random_scale']:
                            logger.info(f"  → Random mode detected: {answer[0]}")
                            logger.info(f"  → Options list: {answer[1]}")
                            selected = self._select_by_percentage(answer[1], rng=rng)
                            logger.info(f"  → Random selected: {selected}")
                            ok = self._select_option_for_thread(driver, question_element, selected)
                            if not ok:
                                ok = self._retry_select_option_with_xpath(driver, question_element, selected)
                            if not ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                        else:
                            logger.info(f"  → Fixed answer mode, selecting: {answer}")
                            
                            # 🔍 DEBUG: Log question_element details
                            try:
                                radios_in_q = question_element.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                                logger.info(f"  → DEBUG: question_element has {len(radios_in_q)} div[role='radio']")
                                for i, r in enumerate(radios_in_q[:5]):
                                    dv = r.get_attribute("data-value") or "none"
                                    logger.info(f"    [{i}] data-value='{dv}'")
                            except Exception as e:
                                logger.warning(f"  → DEBUG: Cannot inspect question_element: {e}")
                            
                            ok = self._select_option_for_thread(driver, question_element, str(answer))
                            if not ok:
                                ok = self._retry_select_option_with_xpath(driver, question_element, str(answer))
                            if not ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                    
                    elif q_type == "checkbox":
                        if isinstance(answer, tuple) and answer[0] == 'random_checkbox':
                            # Random độc lập - không giới hạn số lượng
                            selected_list = self._select_multiple_by_percentage(answer[1], rng=rng)
                            logger.info(f"  Random checkbox selected: {selected_list}")
                            any_ok = False
                            for opt in selected_list:
                                ok = self._select_option_for_thread(driver, question_element, opt)
                                if not ok:
                                    ok = self._retry_select_option_with_xpath(driver, question_element, opt)
                                any_ok = any_ok or ok
                            if not any_ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                        elif isinstance(answer, tuple) and answer[0] == 'random':
                            selected = self._select_by_percentage(answer[1], rng=rng)
                            ok = self._select_option_for_thread(driver, question_element, selected)
                            if not ok:
                                ok = self._retry_select_option_with_xpath(driver, question_element, selected)
                            if not ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                        elif isinstance(answer, list):
                            any_ok = False
                            for opt in answer:
                                ok = self._select_option_for_thread(driver, question_element, str(opt))
                                if not ok:
                                    ok = self._retry_select_option_with_xpath(driver, question_element, str(opt))
                                any_ok = any_ok or ok
                            if not any_ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                        else:
                            ok = self._select_option_for_thread(driver, question_element, str(answer))
                            if not ok:
                                ok = self._retry_select_option_with_xpath(driver, question_element, str(answer))
                            if not ok and is_required:
                                self._select_any_option_for_thread(driver, question_element)
                    
                    global_question_idx += 1
                    
                except Exception as e:
                    logger.error(f"Error filling question {global_question_idx}: {e}", exc_info=True)
                    global_question_idx += 1  # Move to next anyway
            
            # Check for next page button
            logger.info(f"Page {page_number} done - checking for next button...")
            time.sleep(0.2)
            
            # 🆕 More comprehensive next button search
            next_button = None
            next_button_xpaths = [
                # Vietnamese "Tiếp" variants
                "//span[contains(text(),'Tiếp')]/ancestor::div[@role='button']",
                "//span[text()='Tiếp']/ancestor::div[@role='button']",
                "//div[@role='button']//span[contains(text(),'Tiếp')]",
                "//div[@role='button' and contains(.,'Tiếp')]",
                # English "Next" variants
                "//span[contains(text(),'Next')]/ancestor::div[@role='button']",
                "//div[@role='button']//span[contains(text(),'Next')]",
                # Generic button patterns
                "//div[@role='button' and @data-continue='true']",
                "//div[contains(@class,'freebirdFormviewerViewNavigationLeftButtons')]//div[@role='button']",
                "//div[contains(@class,'freebirdFormviewerViewNavigationNoSubmitButton')]//div[@role='button']",
            ]
            
            for xpath in next_button_xpaths:
                try:
                    btns = driver.find_elements(By.XPATH, xpath)
                    for btn in btns:
                        # Skip if it's a submit/send button
                        btn_text = btn.text.lower() if btn.text else ""
                        if 'gửi' in btn_text or 'submit' in btn_text or 'send' in btn_text:
                            continue
                        if btn.is_displayed():
                            next_button = btn
                            logger.info(f"  ✓ Found next button: '{btn.text}' via xpath: {xpath[:50]}...")
                            break
                    if next_button:
                        break
                except:
                    pass
            
            if next_button and next_button.is_displayed():
                try:
                    logger.debug(f"⏭️ Clicking 'Tiếp'/'Next' to go to page {page_number + 1}")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.1)
                    
                    # Robust click
                    from selenium.webdriver.common.action_chains import ActionChains
                    try:
                        driver.execute_script("arguments[0].click();", next_button)
                    except:
                        try:
                            next_button.click()
                        except:
                            ActionChains(driver).move_to_element(next_button).click().perform()
                    
                    # Wait cho page transition - tối ưu (ngắn và theo trạng thái)
                    try:
                        WebDriverWait(driver, 2).until(EC.staleness_of(next_button))
                    except:
                        pass
                    
                    # Wait for new questions (ngắn)
                    try:
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".Qr7Oae, .YKDB3e, div[data-params]"))
                        )
                    except:
                        time.sleep(0.2)
                    
                    page_number += 1
                    logger.debug(f"  ✓ Navigated to page {page_number}")
                        
                except Exception as e:
                    logger.error(f"Error clicking next: {e}")
                    break
            else:
                logger.info("No more 'Tiếp'/'Next' button found - reached last page")
                break
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Form filling complete - filled {global_question_idx} questions")
        logger.info(f"{'='*60}\n")
        
        # 🆕 Gửi form sau khi điền xong
        logger.info("Now submitting the form (thread-safe)...")
        self._submit_form_for_thread(driver)
    
    def _find_question_container_by_title_for_thread(self, driver, title: str):
        """Tìm question container theo title trên viewform (ưu tiên cho đa luồng)."""
        if not title:
            return None
        try:
            target = self._normalize_title(title)
        except Exception:
            target = title.strip().lower()
        if not target:
            return None

        try:
            title_elements = driver.find_elements(By.CLASS_NAME, "M7eMe")
            for elem in title_elements:
                try:
                    if not elem.is_displayed():
                        continue
                    elem_text = elem.text or ""
                    try:
                        elem_norm = self._normalize_title(elem_text)
                    except Exception:
                        elem_norm = elem_text.strip().lower()
                    if not elem_norm:
                        continue
                    if elem_norm == target or target in elem_norm or elem_norm in target:
                        container = elem.find_element(
                            By.XPATH,
                            "./ancestor::div[@data-params or @role='listitem' or contains(@class,'Qr7Oae') or contains(@class,'freebirdFormviewerComponentsQuestionBaseRoot')][1]"
                        )
                        return container
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _is_required_question_for_thread(self, question_element) -> bool:
        """Kiểm tra câu hỏi bắt buộc trên viewform."""
        try:
            if question_element.get_attribute("aria-required") == "true":
                return True
        except:
            pass
        try:
            required_spans = question_element.find_elements(By.CSS_SELECTOR, "span[aria-label='Required'], span[aria-label='Bắt buộc']")
            if required_spans:
                return True
        except:
            pass
        try:
            # Google Forms thường dùng class RVEQke cho dấu * bắt buộc
            if question_element.find_elements(By.CLASS_NAME, "RVEQke"):
                return True
        except:
            pass
        try:
            text = question_element.text or ""
            if "Bắt buộc" in text or "Required" in text:
                return True
        except:
            pass
        return False

    def _select_any_option_for_thread(self, driver, question_element) -> bool:
        """Chọn 1 option bất kỳ để vượt qua câu hỏi bắt buộc nếu không match được."""
        try:
            # Ưu tiên role elements
            for selector in ["div[role='radio']", "div[role='checkbox']", "div[role='option']", ".YKDB3e"]:
                elems = question_element.find_elements(By.CSS_SELECTOR, selector)
                for elem in elems:
                    try:
                        if elem.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            driver.execute_script("arguments[0].click();", elem)
                            return True
                    except:
                        continue
        except:
            pass
        return False

    def _retry_select_option_with_xpath(self, driver, question_element, option_text: str) -> bool:
        """Fallback: dùng XPath theo text để click nhanh trong cùng question container."""
        def _xpath_literal(s: str) -> str:
            if '"' not in s:
                return f'"{s}"'
            if "'" not in s:
                return f"'{s}'"
            parts = s.split('"')
            return "concat(" + ", '\"', ".join([f'"{p}"' for p in parts]) + ")"

        try:
            text_literal = _xpath_literal(option_text.strip())
            xpaths = [
                f".//span[normalize-space(text())={text_literal}]/ancestor::*[@role='radio' or @role='checkbox' or @role='option'][1]",
                f".//div[@role='radio' or @role='checkbox' or @role='option'][.//span[normalize-space(text())={text_literal}]]",
                f".//*[@aria-label={text_literal}]",
            ]
            for xp in xpaths:
                try:
                    elem = question_element.find_element(By.XPATH, xp)
                    if elem:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        driver.execute_script("arguments[0].click();", elem)
                        return True
                except:
                    continue
        except:
            pass
        return False

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
    
    def _select_option_for_thread(self, driver, question_element, option_text: str) -> bool:
        """🆕 Chọn option - thread-safe với NHIỀU phương pháp tìm element + RETRY mechanism (TURBO)"""
        max_retries = 2  # 🚀 TURBO: Giảm từ 3 -> 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return self._select_option_for_thread_internal(driver, question_element, option_text, retry_count)
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to select '{option_text}' after {max_retries} retries: {e}")
                    return False
                # 🚀 TURBO: Giảm exponential backoff
                wait_time = 0.3 * retry_count
                logger.warning(f"Retry {retry_count}/{max_retries} for '{option_text}' after {wait_time}s...")
                time.sleep(wait_time)
        return False
    
    def _select_option_for_thread_internal(self, driver, question_element, option_text: str, retry_num: int = 0) -> bool:
        """Internal method cho _select_option_for_thread với retry support"""
        try:
            logger.debug(f">>> _select_option_for_thread_internal (retry {retry_num}): '{option_text}'")
            
            # 🔧 FIX: Import ActionChains một lần
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.common.exceptions import StaleElementReferenceException
            
            # 🚀 FIX: Focus vào Chrome window trước khi thao tác
            try:
                driver.switch_to.window(driver.current_window_handle)
            except:
                pass
            
            def robust_click(element):
                """🚀 TURBO: Helper function để click với focus window"""
                # 🚀 Focus window trước
                try:
                    driver.switch_to.window(driver.current_window_handle)
                except:
                    pass
                
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.05)  # 🚀 TURBO: Rất ngắn
                except StaleElementReferenceException:
                    logger.warning("Stale element on scroll - will retry")
                    return False
                except:
                    pass
                
                # 🚀 Try focus element first
                try:
                    driver.execute_script("arguments[0].focus();", element)
                except:
                    pass
                
                # Try JS click first (most reliable)
                try:
                    driver.execute_script("arguments[0].click();", element)
                    logger.debug(f"  ✓ JS click success")
                    return True
                except StaleElementReferenceException:
                    logger.warning("Stale element on JS click - will retry")
                    return False
                except Exception as e:
                    logger.debug(f"  JS click failed: {e}")
                
                # Try dispatchEvent click
                try:
                    driver.execute_script("""
                        var evt = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        arguments[0].dispatchEvent(evt);
                    """, element)
                    logger.debug(f"  ✓ dispatchEvent click success")
                    return True
                except Exception as e:
                    logger.debug(f"  dispatchEvent failed: {e}")
                
                # Try native click
                try:
                    element.click()
                    logger.debug(f"  ✓ Native click success")
                    return True
                except StaleElementReferenceException:
                    logger.warning("Stale element on native click - will retry")
                    return False
                except Exception as e:
                    logger.debug(f"  Native click failed: {e}")
                
                # Try ActionChains
                try:
                    ActionChains(driver).move_to_element(element).click().perform()
                    logger.debug(f"  ✓ ActionChains click success")
                    return True
                except StaleElementReferenceException:
                    logger.warning("Stale element on ActionChains - will retry")
                    return False
                except Exception as e:
                    logger.debug(f"  ActionChains failed: {e}")
                
                return False
            
            # ==========================================
            # 🔥 METHOD 0: YKDB3e + urLvsc (QUAN TRỌNG cho Multiple Choice!)
            # ==========================================
            try:
                start_time = time.time()
                options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
                if options:
                    logger.debug(f"Found {len(options)} YKDB3e elements")
                for option in options:
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        label_text = label.text.strip()
                        target_text = option_text.strip()
                        
                        # 🔧 FIX: Normalize text để xử lý ký tự đặc biệt như "–" vs "-"
                        label_normalized = label_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        if label_normalized == target_normalized or label_text == target_text:
                            if robust_click(option):
                                logger.debug(f"✓ Clicked via YKDB3e/urLvsc: '{option_text}'")
                                time.sleep(0.5)  # FIX: Restore to 0.5s for thread safety
                                return True
                    except:
                        pass
                elapsed = time.time() - start_time
                if elapsed > 3:  # FIX: Tăng threshold từ 2s lên 3s
                    logger.debug(f"METHOD 0 took {elapsed:.1f}s")
            except Exception as e:
                logger.debug(f"  YKDB3e method failed: {e}")
            
            # ==========================================
            # 🆕 METHOD 0b: docssharedWizToggleLabeledContainer + div[role='radio']
            # ==========================================
            try:
                containers = question_element.find_elements(By.CLASS_NAME, "docssharedWizToggleLabeledContainer")
                logger.debug(f"Found {len(containers)} docssharedWizToggleLabeledContainer")
                for container in containers:
                    try:
                        container_text = container.text.strip().split('\n')[0]  # First line
                        target_text = option_text.strip()
                        
                        # Normalize
                        container_normalized = container_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        if container_normalized == target_normalized or container_text == target_text:
                            # Try to find and click the radio div inside
                            try:
                                radio_div = container.find_element(By.CSS_SELECTOR, "div[role='radio']")
                                if robust_click(radio_div):
                                    logger.debug(f"✓ Clicked radio inside container: '{option_text}'")
                                    time.sleep(0.5)
                                    return True
                            except:
                                # Click container itself
                                if robust_click(container):
                                    logger.debug(f"✓ Clicked container: '{option_text}'")
                                    time.sleep(0.5)
                                    return True
                    except:
                        pass
            except Exception as e:
                logger.debug(f"  docssharedWizToggleLabeledContainer method failed: {e}")
            
            # ==========================================
            # 🆕 METHOD 0c: Find div[role='radio'] by parent text
            # ==========================================
            try:
                radiogroup = question_element.find_element(By.CSS_SELECTOR, "div[role='radiogroup']")
                radios = radiogroup.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                logger.debug(f"Found {len(radios)} div[role='radio'] in radiogroup")
                
                for radio in radios:
                    try:
                        # Get parent container text
                        parent = radio.find_element(By.XPATH, "./..")
                        parent_text = parent.text.strip().split('\n')[0] if parent.text else ""
                        
                        # Also check sibling label
                        try:
                            label_sibling = parent.find_element(By.CLASS_NAME, "urLvsc")
                            sibling_text = label_sibling.text.strip()
                        except:
                            sibling_text = ""
                        
                        target_text = option_text.strip()
                        
                        # Normalize
                        parent_normalized = parent_text.replace('–', '-').replace('—', '-')
                        sibling_normalized = sibling_text.replace('–', '-').replace('—', '-')
                        target_normalized = target_text.replace('–', '-').replace('—', '-')
                        
                        if (parent_normalized == target_normalized or 
                            sibling_normalized == target_normalized or
                            parent_text == target_text or 
                            sibling_text == target_text):
                            
                            # Check if not already checked
                            is_checked = radio.get_attribute("aria-checked") == "true"
                            if is_checked:
                                logger.debug(f"  Radio already checked: {option_text}")
                                return True
                            
                            if robust_click(radio):
                                logger.debug(f"✓ Clicked div[role='radio'] by parent text: '{option_text}'")
                                time.sleep(0.5)
                                return True
                    except:
                        pass
            except Exception as e:
                logger.debug(f"  div[role='radiogroup'] method failed: {e}")
            
            # ==========================================
            # 🔥 METHOD 1: LINEAR SCALE - data-value match (IMPROVED)
            # ==========================================
            if option_text.strip().isdigit():
                logger.info(f"  → LINEAR SCALE mode for value: {option_text}")
                
                # 🚀 Method 1a: Tìm tất cả radio trong question_element
                try:
                    all_radios = question_element.find_elements(By.CSS_SELECTOR, "div[role='radio']")
                    logger.debug(f"  Found {len(all_radios)} div[role='radio'] in question")
                    
                    for radio in all_radios:
                        try:
                            data_value = radio.get_attribute("data-value")
                            aria_label = radio.get_attribute("aria-label") or ""
                            radio_text = radio.text.strip() if radio.text else ""
                            
                            logger.debug(f"    Radio: data-value={data_value}, aria-label={aria_label}, text={radio_text}")
                            
                            if data_value == option_text.strip() or aria_label == option_text.strip() or radio_text == option_text.strip():
                                is_checked = radio.get_attribute("aria-checked") == "true"
                                if is_checked:
                                    logger.info(f"  ✓ Radio {option_text} already checked")
                                    return True
                                
                                if robust_click(radio):
                                    logger.info(f"  ✓ Clicked LINEAR SCALE radio: data-value={data_value}")
                                    time.sleep(0.2)
                                    return True
                        except Exception as e:
                            logger.debug(f"    Error checking radio: {e}")
                except Exception as e:
                    logger.debug(f"  Method 1a failed: {e}")
                
                # 🚀 Method 1b: Tìm theo CSS selectors cụ thể hơn
                for selector in [
                    f"div[data-value='{option_text}']",
                    f"div[role='radio'][data-value='{option_text}']",
                    f"div.Od2TWd[data-value='{option_text}']",
                    f"label[data-value='{option_text}']",
                ]:
                    try:
                        # Tìm trong question_element trước
                        radios = question_element.find_elements(By.CSS_SELECTOR, selector)
                        logger.debug(f"  Selector '{selector}': found {len(radios)} elements")
                        
                        for radio in radios:
                            try:
                                is_checked = radio.get_attribute("aria-checked") == "true"
                                if not is_checked:
                                    if robust_click(radio):
                                        logger.info(f"  ✓ Clicked LINEAR SCALE via {selector}: '{option_text}'")
                                        time.sleep(0.2)
                                        return True
                                else:
                                    logger.info(f"  ✓ Radio {option_text} already checked")
                                    return True
                            except:
                                continue
                        
                        # Fallback: tìm trên toàn page
                        if not radios:
                            radios = driver.find_elements(By.CSS_SELECTOR, selector)
                            logger.debug(f"  GLOBAL search '{selector}': found {len(radios)} elements")
                            for radio in radios:
                                try:
                                    is_checked = radio.get_attribute("aria-checked") == "true"
                                    if not is_checked:
                                        if robust_click(radio):
                                            logger.info(f"  ✓ Clicked LINEAR SCALE (GLOBAL) via {selector}: '{option_text}'")
                                            time.sleep(0.2)
                                            return True
                                except:
                                    continue
                    except Exception as e:
                        logger.debug(f"  Selector {selector} failed: {e}")
                
                # 🚀 Method 1c: Tìm bằng XPath - aria-label hoặc text content
                try:
                    xpath_patterns = [
                        f"//div[@role='radio' and @data-value='{option_text}']",
                        f"//div[@role='radio' and contains(@aria-label, '{option_text}')]",
                        f"//div[@role='radio']//div[text()='{option_text}']/ancestor::div[@role='radio']",
                        f"//label[contains(@class, 'T5pZmf')]//span[text()='{option_text}']/ancestor::label",
                    ]
                    
                    for xpath in xpath_patterns:
                        try:
                            elements = driver.find_elements(By.XPATH, xpath)
                            logger.debug(f"  XPath '{xpath[:50]}': found {len(elements)} elements")
                            for elem in elements:
                                if robust_click(elem):
                                    logger.info(f"  ✓ Clicked LINEAR SCALE via XPath: '{option_text}'")
                                    time.sleep(0.2)
                                    return True
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"  XPath method failed: {e}")
                
                # Try label.T5pZmf với Zki2Ve
                try:
                    labels = question_element.find_elements(By.CSS_SELECTOR, "label.T5pZmf")
                    logger.debug(f"  label.T5pZmf: found {len(labels)} labels")
                    for label in labels:
                        try:
                            zki = label.find_element(By.CLASS_NAME, "Zki2Ve")
                            if zki.text.strip() == option_text.strip():
                                if robust_click(label):
                                    logger.info(f"  ✓ Clicked LINEAR via Zki2Ve: '{option_text}'")
                                    time.sleep(0.2)
                                    return True
                        except:
                            continue
                except:
                    pass
            
            # ==========================================
            # 🔥 METHOD 2: Radio button by label text
            # ==========================================
            try:
                radios = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if radios:
                    for radio in radios:
                        try:
                            parent = radio.find_element(By.XPATH, "..")
                            labels = parent.find_elements(By.TAG_NAME, "label")
                            for lbl in labels:
                                if lbl.text.strip() == option_text.strip():
                                    if robust_click(radio):
                                        logger.debug(f"✓ Clicked radio input: '{option_text}'")
                                        time.sleep(0.3)
                                        return True
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 🔥 METHOD 3: Checkbox by label text
            # ==========================================
            try:
                checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkboxes:
                    for checkbox in checkboxes:
                        try:
                            parent = checkbox.find_element(By.XPATH, "..")
                            labels = parent.find_elements(By.TAG_NAME, "label")
                            for lbl in labels:
                                if lbl.text.strip() == option_text.strip():
                                    if robust_click(checkbox):
                                        logger.debug(f"✓ Clicked checkbox input: '{option_text}'")
                                        time.sleep(0.3)
                                        return True
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 🔥 METHOD 4: Label với text khớp
            # ==========================================
            try:
                labels = question_element.find_elements(By.CSS_SELECTOR, "label")
                if labels:
                    for label in labels:
                        try:
                            if label.text.strip() == option_text.strip():
                                if robust_click(label):
                                    logger.debug(f"✓ Clicked label: '{option_text}'")
                                    time.sleep(0.3)
                                    return True
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 🔥 METHOD 5: Span text match, click parent (FAST)
            # ==========================================
            try:
                spans = question_element.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    try:
                        if span.text.strip() == option_text.strip():
                            if robust_click(span):
                                logger.debug(f"✓ Clicked span: '{option_text}'")
                                time.sleep(0.3)
                                return True
                            try:
                                parent = span.find_element(By.XPATH, "..")
                                if robust_click(parent):
                                    logger.debug(f"✓ Clicked span parent: '{option_text}'")
                                    time.sleep(0.3)
                                    return True
                            except:
                                pass
                    except:
                        pass
            except:
                pass
            
            # ==========================================
            # 🔥 METHOD 6: div[role='radio'] hoặc div[role='checkbox'] với text
            # ==========================================
            try:
                role_elements = question_element.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox'], div[role='option']")
                if role_elements:
                    for elem in role_elements:
                        try:
                            elem_text = elem.text.strip()
                            aria_label = elem.get_attribute("aria-label") or ""
                            if elem_text == option_text.strip() or aria_label == option_text.strip():
                                is_checked = elem.get_attribute("aria-checked") == "true"
                                if not is_checked:
                                    if robust_click(elem):
                                        logger.debug(f"✓ Clicked role element: '{option_text}'")
                                        time.sleep(0.3)
                                        return True
                                else:
                                    return True  # Already checked
                        except:
                            pass
            except:
                pass
            
            # ==========================================
            # 🔥 METHOD 7: Tìm trên TOÀN BỘ PAGE (fallback cuối cùng) - SHORT VERSION
            # ==========================================
            # Only try global search if all local methods failed
            logger.debug(f"  No local match for '{option_text}' - trying global search...")
            
            try:
                # 7a: YKDB3e trên toàn page
                options = driver.find_elements(By.CLASS_NAME, "YKDB3e")
                for option in options:
                    try:
                        label = option.find_element(By.CLASS_NAME, "urLvsc")
                        if label.text.strip() == option_text.strip():
                            if robust_click(option):
                                logger.debug(f"✓ GLOBAL: Clicked via YKDB3e: '{option_text}'")
                                time.sleep(0.3)
                                return True
                    except:
                        pass
            except:
                pass
            
            # If we get here, log and give up
            logger.warning(f"⚠️ Could NOT select: '{option_text}' - skipping")
            return False
        
        except Exception as e:
            logger.error(f"Error selecting option '{option_text}': {e}")
        return False
    
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
                    time.sleep(0.2)
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
        self.parallel_spinbox.setMaximum(10)  # 🆕 Tăng lên 10 tabs
        self.parallel_spinbox.setValue(3)     # 🆕 Default 3 tabs
        self.parallel_spinbox.setToolTip("1 = Tuần tự (chậm)\n2-5 = Parallel (nhanh)\n6-10 = TURBO (rất nhanh, cần RAM mạnh)")
        self.parallel_spinbox.setMaximumWidth(80)
        parallel_layout.addWidget(self.parallel_spinbox)
        
        parallel_info = QLabel("(1=chậm, 3-5=nhanh, 6-10=turbo)")
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
                    if self.random_mode:
                        # Random mode: checkboxes with percentage inputs
                        checkbox_list = []
                        
                        # Add info label - TARGET DISTRIBUTION
                        info_label = QLabel("📊 TARGET DISTRIBUTION: Mỗi option có tỉ lệ % độc lập (VD: 65% = option này xuất hiện trong ~65% responses)")
                        info_label.setStyleSheet("color: #1976d2; font-style: italic; font-size: 10px; font-weight: bold;")
                        question_layout.addWidget(info_label)
                        
                        for opt in options:
                            row_layout = QHBoxLayout()
                            
                            cb = QCheckBox(opt['text'])
                            cb.setMinimumHeight(35)
                            font = QFont()
                            font.setPointSize(12)
                            cb.setFont(font)
                            cb.setStyleSheet("""
                                QCheckBox {
                                    font-size: 12px;
                                    padding: 6px 5px;
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
                            
                            # Percentage spinbox - Target Distribution
                            percent_label = QLabel("Target:")
                            percent_label.setFont(QFont("Arial", 10))
                            percent_label.setStyleSheet("color: #1976d2; font-weight: bold;")
                            
                            percent_spinbox = QSpinBox()
                            percent_spinbox.setMinimum(0)
                            percent_spinbox.setMaximum(100)
                            percent_spinbox.setValue(0)
                            percent_spinbox.setSuffix("%")
                            percent_spinbox.setMaximumWidth(70)
                            percent_spinbox.setStyleSheet("""
                                QSpinBox {
                                    border: 1px solid #ddd;
                                    border-radius: 4px;
                                    padding: 4px;
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
                        
                        self.answer_widgets[actual_q_idx] = ('random_checkbox', checkbox_list)
                    else:
                        # Normal mode: simple checkboxes
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
                        if self.random_mode:
                            # Random mode: use checkboxes with percentage inputs for weighted random
                            checkbox_list = []
                            
                            # Add info label
                            info_label = QLabel("📊 Tick chọn các giá trị và đặt tỉ lệ % (tổng = 100%)")
                            info_label.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")
                            question_layout.addWidget(info_label)
                            
                            for opt in options:
                                # Create a row with checkbox and percentage spinbox
                                row_layout = QHBoxLayout()
                                
                                cb = QCheckBox(opt['text'])
                                cb.setMinimumHeight(35)
                                font = QFont()
                                font.setPointSize(12)
                                cb.setFont(font)
                                cb.setStyleSheet("""
                                    QCheckBox {
                                        font-size: 12px;
                                        padding: 6px 5px;
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
                                percent_label = QLabel("Tỉ lệ:")
                                percent_label.setFont(QFont("Arial", 10))
                                percent_label.setStyleSheet("color: black;")
                                
                                percent_spinbox = QSpinBox()
                                percent_spinbox.setMinimum(0)
                                percent_spinbox.setMaximum(100)
                                percent_spinbox.setValue(0)
                                percent_spinbox.setSuffix("%")
                                percent_spinbox.setMaximumWidth(70)
                                percent_spinbox.setStyleSheet("""
                                    QSpinBox {
                                        border: 1px solid #ddd;
                                        border-radius: 4px;
                                        padding: 4px;
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
                            
                            self.answer_widgets[actual_q_idx] = ('random_scale', checkbox_list)
                        else:
                            # Normal mode: use radio buttons
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
            
            # Handle random mode for linear scale (weighted random)
            elif isinstance(widget, tuple) and widget[0] == 'random_scale':
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
                    answers[actual_question_idx] = ('random_scale', random_answer)
            
            # Handle random mode for checkbox (multi-select with independent percentages)
            elif isinstance(widget, tuple) and widget[0] == 'random_checkbox':
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
                    # For checkbox, percentages don't need to sum to 100%
                    # Each option is independently selected based on its probability
                    answers[actual_question_idx] = ('random_checkbox', random_answer)
            
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
