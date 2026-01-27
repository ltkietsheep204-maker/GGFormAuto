"""
Google Form Auto Filler - Desktop App v2 (FIXED)
- Fix: Tốt hơn nhận diện loại câu hỏi
- NEW: Chức năng Random Mode với tỉ lệ tùy chỉnh
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
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QScrollArea, QSlider, QDoubleSpinBox
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
            logger.info(f"Loading form: {self.form_url}")
            
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.form_url)
            time.sleep(3)
            
            question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            self.progress.emit(f"✓ Tìm thấy {len(question_elements)} câu hỏi")
            logger.info(f"Found {len(question_elements)} questions")
            
            for idx, question_element in enumerate(question_elements):
                try:
                    title = self._get_question_text(question_element)
                    q_type = self._get_question_type(question_element)
                    options_list = self._get_options(question_element)
                    
                    question_data = {
                        "index": idx,
                        "title": title,
                        "type": q_type,
                        "options": options_list,
                        "required": self._is_required(question_element),
                        "element": question_element
                    }
                    
                    self.questions.append(question_data)
                    self.progress.emit(f"✓ Tải câu {idx + 1}: {title[:40]}... ({self._format_type(q_type)})")
                    logger.info(f"Question {idx}: {title[:40]} ({q_type})")
                except Exception as e:
                    logger.error(f"Error processing question {idx}: {e}")
                    self.progress.emit(f"⚠️ Lỗi câu {idx}: {str(e)}")
            
            self.finished.emit(self.questions)
            logger.info("Form loaded successfully")
        
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
            "unknown": "❓ Không xác định"
        }
        return type_map.get(q_type, "❓ Unknown")
    
    def _get_question_text(self, question_element) -> str:
        """Lấy text câu hỏi - try multiple selectors"""
        try:
            # Try primary selector
            try:
                title = question_element.find_element(By.CLASS_NAME, "Uc2Deb")
                return title.text.strip()
            except:
                pass
            
            # Try alternative selectors
            try:
                title = question_element.find_element(By.XPATH, ".//div[@role='heading']")
                return title.text.strip()
            except:
                pass
            
            try:
                title = question_element.find_element(By.XPATH, ".//span[@data-tooltip]")
                return title.text.strip()
            except:
                pass
            
            # Fallback
            return "Untitled Question"
        except:
            return "Untitled Question"
    
    def _get_question_type(self, question_element) -> str:
        """Xác định loại câu hỏi - improve detection"""
        try:
            # Check for linear scale (1-5 buttons)
            if question_element.find_elements(By.CLASS_NAME, "Ht8Grd"):
                return "linear_scale"
            
            # Check for multiple choice grid
            if question_element.find_elements(By.CLASS_NAME, "GnICSe"):
                return "multiple_choice_grid"
            
            # Check for radio buttons (multiple choice)
            radio_buttons = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons and len(radio_buttons) > 0:
                return "multiple_choice"
            
            # Check for checkboxes
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes and len(checkboxes) > 0:
                return "checkbox"
            
            # Check for dropdown/select
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            # Check for textarea (long answer)
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            if textareas and len(textareas) > 0:
                return "long_answer"
            
            # Check for text input (short answer)
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if text_inputs and len(text_inputs) > 0:
                return "short_answer"
            
            # Alternative: check for YKDB3e (options container)
            if question_element.find_elements(By.CLASS_NAME, "YKDB3e"):
                if question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                    return "multiple_choice"
                elif question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                    return "checkbox"
            
            logger.debug(f"Could not determine type, returning unknown")
            return "unknown"
        except Exception as e:
            logger.error(f"Error detecting type: {e}")
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
                        "text": label.text.strip()
                    })
                except Exception as e:
                    logger.debug(f"Error getting option {idx}: {e}")
                    pass
        except Exception as e:
            logger.debug(f"Error getting options: {e}")
            pass
        
        return options
    
    def _is_required(self, question_element) -> bool:
        """Kiểm tra câu hỏi có bắt buộc không"""
        try:
            question_element.find_element(By.CLASS_NAME, "geHIc")
            return True
        except:
            return False


class SubmissionWorker(QThread):
    """Worker thread để gửi responses"""
    progress = pyqtSignal(str)
    count_progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, form_url: str, answers: Dict, count: int, questions: List, use_random: bool = False):
        super().__init__()
        self.form_url = form_url
        self.answers = answers
        self.count = count
        self.questions = questions
        self.driver = None
        self.use_random = use_random
    
    def run(self):
        """Chạy gửi responses"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = webdriver.Chrome(options=options)
            
            for i in range(self.count):
                try:
                    self.progress.emit(f"📮 Gửi response {i + 1}/{self.count}...")
                    self.driver.get(self.form_url)
                    time.sleep(2)
                    
                    # Prepare answers for this response
                    current_answers = self._prepare_answers(self.answers)
                    
                    # Điền form
                    self._fill_form(current_answers)
                    
                    # Gửi
                    self._submit_form()
                    
                    self.progress.emit(f"✓ Response {i + 1} đã gửi")
                    self.count_progress.emit(i + 1)
                    logger.info(f"Response {i + 1} submitted")
                    
                    if i < self.count - 1:
                        time.sleep(2)
                
                except Exception as e:
                    logger.error(f"Error submitting response {i + 1}: {e}\n{traceback.format_exc()}")
                    self.progress.emit(f"⚠️ Lỗi response {i + 1}: {str(e)}")
                    self.count_progress.emit(i + 1)
            
            self.finished.emit()
            logger.info(f"All {self.count} responses submitted")
        
        except Exception as e:
            logger.error(f"Worker error: {e}\n{traceback.format_exc()}")
            self.error.emit(f"❌ Lỗi: {str(e)}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _prepare_answers(self, answers: Dict) -> Dict:
        """Prepare answers - handle random selection"""
        if not self.use_random:
            return answers
        
        prepared = {}
        for idx, answer in answers.items():
            if isinstance(answer, dict) and "options" in answer:
                # Random mode: random select từ options
                options = answer["options"]
                weights = answer.get("weights", [1.0] * len(options))
                selected = random.choices(options, weights=weights, k=1)[0]
                prepared[idx] = selected
            else:
                prepared[idx] = answer
        
        return prepared
    
    def _fill_form(self, answers: Dict):
        """Điền form"""
        for idx, answer in answers.items():
            try:
                question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                if idx >= len(question_elements):
                    continue
                
                question_element = question_elements[idx]
                q_type = self.questions[idx]['type']
                
                if q_type == "short_answer" or q_type == "long_answer":
                    self._fill_text_field(question_element, str(answer))
                
                elif q_type in ["multiple_choice", "dropdown", "linear_scale", "multiple_choice_grid"]:
                    self._select_option(question_element, str(answer))
                
                elif q_type == "checkbox":
                    if isinstance(answer, list):
                        for option_text in answer:
                            self._select_option(question_element, str(option_text))
            
            except Exception as e:
                logger.warning(f"Error filling question {idx}: {e}")
    
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
        """Chọn option"""
        try:
            options = question_element.find_elements(By.CLASS_NAME, "YKDB3e")
            
            for option in options:
                try:
                    label = option.find_element(By.CLASS_NAME, "urLvsc")
                    if label.text.strip() == option_text.strip():
                        option.click()
                        time.sleep(0.5)
                        return
                except:
                    pass
        
        except Exception as e:
            logger.warning(f"Error selecting option: {e}")
    
    def _submit_form(self):
        """Gửi form"""
        try:
            submit_btn = None
            try:
                submit_btn = self.driver.find_element(By.CLASS_NAME, "uArJ5e")
            except:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                except:
                    pass
            
            if submit_btn:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                time.sleep(1)
                submit_btn.click()
                time.sleep(2)
        
        except Exception as e:
            logger.warning(f"Error submitting form: {e}")


class RandomAnswerWidget(QWidget):
    """Widget để set random answers với weights"""
    
    def __init__(self, question_idx: int, options: List[Dict]):
        super().__init__()
        self.question_idx = question_idx
        self.options = options
        self.selected_options = {}
        self.weights = {}
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for opt in self.options:
            h_layout = QHBoxLayout()
            
            # Checkbox to select
            cb = QCheckBox(opt['text'][:40])
            cb.stateChanged.connect(lambda state, idx=opt['index']: self._on_check(idx, state))
            h_layout.addWidget(cb)
            
            # Weight slider (0-100%)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(50)
            slider.setMaximumWidth(100)
            h_layout.addWidget(QLabel("Tỉ lệ:"))
            h_layout.addWidget(slider)
            
            # Percentage label
            label = QLabel("50%")
            label.setMaximumWidth(40)
            slider.valueChanged.connect(lambda val, lbl=label, idx=opt['index']: self._on_weight_change(val, lbl, idx))
            h_layout.addWidget(label)
            
            h_layout.addStretch()
            layout.addLayout(h_layout)
        
        layout.addStretch()
    
    def _on_check(self, option_idx: int, state: int):
        if state == Qt.Checked:
            self.selected_options[option_idx] = True
        else:
            self.selected_options.pop(option_idx, None)
    
    def _on_weight_change(self, value: int, label: QLabel, option_idx: int):
        label.setText(f"{value}%")
        self.weights[option_idx] = value
    
    def get_data(self) -> Dict:
        """Get selected options and weights"""
        if not self.selected_options:
            return None
        
        selected_texts = []
        weights = []
        
        for opt in self.options:
            if opt['index'] in self.selected_options:
                selected_texts.append(opt['text'])
                weight = self.weights.get(opt['index'], 50)
                weights.append(weight)
        
        return {
            "options": selected_texts,
            "weights": weights
        }


class GoogleFormFillerApp(QMainWindow):
    """Ứng dụng chính"""
    
    def __init__(self):
        super().__init__()
        self.form_url = ""
        self.questions = []
        self.answers = {}
        self.random_mode = False
        self.worker = None
        
        self.initUI()
    
    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("🤖 Google Form Auto Filler v2")
        self.setGeometry(100, 100, 1100, 800)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
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
            QCheckBox {
                color: #333;
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
        tabs.addTab(tab3, "✏️ Đáp Án")
        
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
        self.load_progress.setMaximumHeight(200)
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
        """Tạo tab nhập đáp án"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Nhập Đáp Án")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title_layout.addWidget(title)
        
        # Random mode checkbox
        self.random_mode_cb = QCheckBox("🎲 Chế độ Ngẫu Nhiên")
        self.random_mode_cb.stateChanged.connect(self._on_random_mode_toggle)
        title_layout.addWidget(self.random_mode_cb)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Info
        self.random_info = QLabel("")
        self.random_info.setFont(QFont("Arial", 9))
        self.random_info.setStyleSheet("color: #666;")
        layout.addWidget(self.random_info)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.answers_container = QWidget()
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
        self.count_spinbox.setValue(5)
        layout.addWidget(self.count_spinbox)
        
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
            if q_type == "unknown":
                type_str = "❓ Unknown"
            else:
                type_map = {
                    "multiple_choice": "Chọn một",
                    "checkbox": "Chọn nhiều",
                    "dropdown": "Dropdown",
                    "short_answer": "Trả lời ngắn",
                    "long_answer": "Trả lời dài",
                    "linear_scale": "Thang điểm",
                    "multiple_choice_grid": "Bảng chọn"
                }
                type_str = type_map.get(q_type, "Unknown")
            
            item_text = f"{q['index'] + 1}. {q['title'][:60]}... ({type_str})"
            item = QListWidgetItem(item_text)
            self.questions_list.addItem(item)
        
        # Tạo input fields cho answers
        self.createAnswerInputs()
        
        QMessageBox.information(self, "Thành Công", f"✅ Đã tải {len(questions)} câu hỏi!\n\nChuyển sang tab 'Đáp Án' để điền thông tin")
    
    def onLoadError(self, error: str):
        """Khi có lỗi"""
        self.load_progress.append(f"\n❌ {error}")
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi", error)
    
    def createAnswerInputs(self):
        """Tạo input fields cho đáp án"""
        # Clear previous
        while self.answers_layout.count():
            widget = self.answers_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        self.answer_widgets = {}
        self.random_widgets = {}
        
        for q in self.questions:
            idx = q['index']
            q_type = q['type']
            title = q['title']
            
            # Label câu hỏi
            label = QLabel(f"Câu {idx + 1}: {title}")
            label.setFont(QFont("Arial", 11, QFont.Bold))
            label.setWordWrap(True)
            self.answers_layout.addWidget(label)
            
            if q_type == "short_answer" or q_type == "long_answer":
                widget = QLineEdit()
                widget.setPlaceholderText("Nhập đáp án...")
                self.answers_layout.addWidget(widget)
                self.answer_widgets[idx] = widget
            
            elif q_type in ["multiple_choice", "dropdown", "linear_scale"]:
                combo = QComboBox()
                combo.addItem("-- Chọn --")
                for opt in q['options']:
                    combo.addItem(opt['text'])
                self.answers_layout.addWidget(combo)
                self.answer_widgets[idx] = combo
                
                # Random widget
                if q['options']:
                    random_widget = RandomAnswerWidget(idx, q['options'])
                    random_widget.setVisible(False)
                    self.answers_layout.addWidget(random_widget)
                    self.random_widgets[idx] = random_widget
            
            elif q_type == "checkbox":
                group_box = QGroupBox()
                group_layout = QVBoxLayout(group_box)
                checkboxes = []
                for opt in q['options']:
                    cb = QCheckBox(opt['text'])
                    checkboxes.append(cb)
                    group_layout.addWidget(cb)
                self.answers_layout.addWidget(group_box)
                self.answer_widgets[idx] = checkboxes
            
            self.answers_layout.addSpacing(10)
        
        self.answers_layout.addStretch()
        self._update_random_mode()
    
    def _on_random_mode_toggle(self, state: int):
        """Toggle random mode"""
        self.random_mode = state == Qt.Checked
        self._update_random_mode()
    
    def _update_random_mode(self):
        """Update UI based on random mode"""
        if self.random_mode:
            self.random_info.setText("💡 Chế độ ngẫu nhiên: Chọn các đáp án mà bạn muốn, tool sẽ random chọn 1 câu trả lời từ danh sách đó")
            # Hide normal widgets, show random widgets
            for idx, widget in self.answer_widgets.items():
                if idx in self.random_widgets:
                    widget.setVisible(False)  # Hide combo
                    self.random_widgets[idx].setVisible(True)
                else:
                    widget.setVisible(True)  # Show text inputs
        else:
            self.random_info.setText("")
            # Show normal widgets, hide random widgets
            for idx, widget in self.answer_widgets.items():
                widget.setVisible(True)
                if idx in self.random_widgets:
                    self.random_widgets[idx].setVisible(False)
    
    def startSubmission(self):
        """Bắt đầu gửi responses"""
        if not self.questions:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tải form trước")
            return
        
        # Lấy đáp án từ widgets
        self.answers = self.getAnswersFromWidgets()
        
        if not self.answers:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ít nhất một câu trả lời")
            return
        
        count = self.count_spinbox.value()
        
        if count > 100:
            reply = QMessageBox.question(
                self, "Xác nhận",
                f"Bạn sắp gửi {count} responses. Tiếp tục?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.submission_log.clear()
        self.submission_progress.setMaximum(count)
        self.submission_progress.setValue(0)
        self.submit_btn.setEnabled(False)
        
        self.worker = SubmissionWorker(self.form_url, self.answers, count, self.questions, self.random_mode)
        self.worker.progress.connect(self.updateSubmissionLog)
        self.worker.count_progress.connect(self.submission_progress.setValue)
        self.worker.finished.connect(self.onSubmissionFinished)
        self.worker.error.connect(self.onSubmissionError)
        self.worker.start()
    
    def getAnswersFromWidgets(self) -> Dict:
        """Lấy đáp án từ widgets"""
        answers = {}
        
        for idx, widget in self.answer_widgets.items():
            if isinstance(widget, QLineEdit):
                if widget.text():
                    answers[idx] = widget.text()
            elif isinstance(widget, QComboBox):
                if self.random_mode and idx in self.random_widgets:
                    # Get from random widget
                    data = self.random_widgets[idx].get_data()
                    if data:
                        answers[idx] = data
                elif widget.currentIndex() > 0:
                    answers[idx] = widget.currentText()
            elif isinstance(widget, list):  # Checkboxes
                selected = [cb.text() for cb in widget if cb.isChecked()]
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
        self.submission_log.append("\n✅ Hoàn tát! Đã gửi tất cả responses")
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
