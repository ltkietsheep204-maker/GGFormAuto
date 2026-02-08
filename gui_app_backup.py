"""
Google Form Auto Filler - Desktop App (PyQt5) - FIXED VERSION
Ứng dụng desktop để tự động điền Google Forms với xử lý lỗi tốt
"""

import sys
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QTabWidget, QProgressBar, QMessageBox,
    QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

# Setup logging
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
else:
    logger.info("Selenium imported successfully.")


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
                    self.progress.emit(f"✓ Tải câu {idx + 1}: {title[:40]}...")
                    logger.info(f"Question {idx}: {title[:40]} ({q_type})")
                except Exception as e:
                    logger.error(f"Error processing question {idx}: {e}")
                    self.progress.emit(f"⚠️ Lỗi câu {idx}: {str(e)}")
            
            self.finished.emit(self.questions)
            logger.info("Form loaded successfully")
        except Exception as e:
            return "Untitled Question"
    
    def _get_question_type(self, question_element) -> str:
        try:
            radio_buttons = question_element.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                return "multiple_choice"
            
            checkboxes = question_element.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes and len(checkboxes) > 0:
                return "checkbox"
            
            if question_element.find_elements(By.CSS_SELECTOR, "select"):
                return "dropdown"
            
            textareas = question_element.find_elements(By.TAG_NAME, "textarea")
            if textareas:
                return "long_answer"
            
            text_inputs = question_element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if text_inputs:
                return "short_answer"
            
            return "unknown"
        except Exception as e:
            logger.error(f"Error detecting type: {e}")
            return "unknown"
    
    def _get_options(self, question_element) -> List[Dict]:
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
        except Exception as e:
            logger.debug(f"Error getting options: {e}")
        return options
    def _get_options(self, question_element) -> List[Dict]:
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
        except Exception as e:
            logger.debug(f"Error getting options: {e}")
        return options
    count_progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, form_url: str, answers: Dict, count: int, questions: List):
        super().__init__()
        self.form_url = form_url
        self.answers = answers
        self.count = count
        self.questions = questions
        self.driver = None
    
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
                    
                    # Điền form
                    self._fill_form()
                    
                    # Gửi
                    self._submit_form()
                    
                    self.progress.emit(f"✓ Response {i + 1} đã gửi")
                    self.count_progress.emit(i + 1)
                    logger.info(f"Response {i + 1} submitted")
                    
                    if i < self.count - 1:
                        time.sleep(2)
                
                except Exception as e:
                    logger.error(f"Error sending response {i + 1}: {e}")
        except Exception as e:
            logger.error(f"Error initializing driver: {e}")
            
            self.finished.emit()
            logger.info(f"All {self.count} responses submitted")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _fill_form(self):
        """Điền form"""
        for idx, answer in self.answers.items():
            try:
                question_elements = self.driver.find_elements(By.CLASS_NAME, "Qr7Oae")
                if idx >= len(question_elements):
                    continue
                
                question_element = question_elements[idx]
                q_type = self.questions[idx]['type']
                
                if q_type == "short_answer" or q_type == "long_answer":
                    self._fill_text_field(question_element, answer)
                
                elif q_type == "multiple_choice" or q_type == "dropdown":
                    self._select_option(question_element, answer)
                
                elif q_type == "checkbox":
                    if isinstance(answer, list):
                        for option_text in answer:
                            self._select_option(question_element, option_text)
            
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
                    input_field = question_element.find_element(By.XPATH, "//textarea")
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
                    if label.text == option_text:
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
                    self.progress.emit(f"✓ Response {i + 1} đã gửi")
                    
                    if i < self.count - 1:
                        time.sleep(2)
                
                except Exception as e:
                    self.progress.emit(f"⚠️ Lỗi response {i + 1}: {str(e)}")
            
            driver.quit()
            self.finished.emit()
        
        exInfo
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
        self.load_progress.setMaximumHeight(150
        super().__init__()
        self.form_url = ""
        self.questions = []
        self.answers = {}
        self.worker = None
        
        self.initUI()
    
    def initUI(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("🤖 Google Form Auto Filler")
        self.setGeometry(100, 100, 900, 700)
        
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
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
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
        """)
        
        #elf.submit_btn = QPushButton("📤 Bắt Đầu Gửi")
        self.submit_btn.clicked.connect(self.startSubmission)
        layout.addWidget(self.dget(central_widget)
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
        
        # URL input
        layout.addWidget(QLabel("Google Form URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://docs.google.com/forms/d/e/...")
        layout.addWidget(self.url_input)
        
        # Load button
        load_btn = QPushButton("🔍 Lấy Thông Tin Form")
        load_btn.clicked.connect(self.loadFormInfo)
        layout.addWidget(load_btn)
        
        # Progress
        self.load_progress = QLabel("Chưa tải form")
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
        
        title = QLabel("Nhập Đáp Án")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
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
        submit_btn = QPushButton("📤 Bắt Đầu Gửi")
        submit_btn.clicked.connect(self.startSubmission)
        layout.addWidget(submit_btn)
        
        # Progress bar
        self.submission_progress = QProgressBar()
        layout.addWidget(self.submission_progress)
        
        # Log
        self.submission_log = QTextEdit()
        self.submission_log.setReadOnly(True)
        layout.addWidget(self.submission_log)
        btn.setEnabled(False)
        self.load_progress.clear()
        self.load_progress.append("⏳ Đang tải thông tin form...\n")
    
    def loadFormInfo(self):
        """Lấy thông tin form"""
        self.form_url = self.url_input.text().strip()
        
        if not self.form_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL form")
            return
        append
        self.load_progress.setText("⏳ Đang tải...")
        self.load_btn_enabled = False
        
        self.worker = GoogleFormWorker(self.form_url)
        self.worker.progresappend(f"\n✅ Đã tải {len(questions)} câu hỏi thành công!")
        self.load_btn.setEnabled(True)
        
        # Cập nhật tab questions
        self.questions_list.clear()
        for q in questions:
            item_text = f"{q['index'] + 1}. {q['title'][:60]}... ({self._format_type(q['type'])})"
            item = QListWidgetItem(item_text)
            self.questions_list.addItem(item)
        
        # Tạo input fields cho answers
        self.createAnswerInputs()
        
        QMessageBox.information(self, "Thành Công", f"✅ Đã tải {len(questions)} câu hỏi!\n\nChuyển sang tab 'Đáp Án' để điền thông tin
        
        # Cập nhật tab questions
        self.questions_listappend(f"\n❌ {error}")
        self.load_btn.setEnabled(True
        for q in questions:
            item_text = f"{q['index'] + 1}. {q['title'][:50]}... ({self._format_type(q['type'])})"
            item = QListWidgetItem(item_text)
            self.questions_list.addItem(item)
        
        # Tạo input fields cho answers
        self.createAnswerInputs()
        
        QMessageBox.information(self, "Thành Công", f"Đã tải {len(questions)} câu hỏi!")
    widget = self.answers_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        self.answer_widgets = {}
        
        for q in self.questions:
            idx = q['index']
            q_type = q['type']
            title = q['title']
            
            # Label câu hỏi
            label = QLabel(f"Câu {idx + 1}: {title}")
            label.setFont(QFont("Arial", 11, QFont.Bold))
            label.setWordWrap(True
        self.answer_widgets = {}
        
        for q in self.questions:
            idx = q['index']
            q_type = q['type']
            title = q['title']
            
            # Label câu hỏi
            label = QLabel(f"Câu {idx + 1}: {title}")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            self.answers_layout.addWidget(label)
            
            if q_type == "short_answer" or q_type == "long_answer":
                widget = QLineEdit()
                widget.setPlaceholderText("Nhập đáp án...")
                self.answers_layout.addWidget(widget)
                self.answer_widgets[idx] = widget
            
            elif q_type == "multiple_choice" or q_type == "dropdown":
                combo = QComboBox()
                combo.addItem("-- Chọn --")
                for opt in q['options']:
                    combo.addItem(opt['text'])
                self.answers_layout.addWidget(combo)
                self.answer_widgets[idx] = combo
            
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
    
    def _format_type(self, q_type: str) -> str:
        """Format loại câu hỏi"""
        type_map = {
            "multiple_choice": "Chọn một",
            "checkbox": "Chọn nhiều",
            "dropdown": "Dropdown",
            "short_answer": "Trả lời ngắn",
            "long_answer": "Trả lời dài",
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
        
        self.worker = SubmissionWorker(self.form_url, self.answers, count, self.questions)
        self.worker.progress.connect(self.updateSubmissionLog)
        self.worker.count_progress.connect(self.submission_progress.setValue
                self, "Xác nhận",
                f"Bạn sắp gửi {count} responses. Tiếp tục?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.submission_log.clear()
        self.submission_progress.setMaximum(count)
        self.submission_progress.setValue(0)
        
        self.worker = SubmissionWorker(self.form_url, self.answers, count, self.questions)
        self.worker.progress.connect(self.updateSubmissionLog)
        self.worker.finished.connect(self.onSubmissionFinished)
        self.worker.error.connect(self.onSubmissionError)
        self.worker.start()
    
    def getAnswersFromWidgets(self) -> Dict:
        """Lấy đáp án từ widgets"""
        answers = {}
        
        for idx, widget in self.answer_widgets.items():
            if isinstance(widget, QLineEdit):
                answers[idx] = widget.text()
        # Auto scroll to bottom
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
    
    # Set exception hook để catch exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = exception_handler
    
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
        event.accept(
    def updateSubmissionLog(self, message: str):
        """Cập nhật log gửi"""
        self.submission_log.append(message)
    
    def onSubmissionFinished(self):
        """Khi gửi xong"""
        self.submission_log.append("\n✅ Hoàn tất! Đã gửi tất cả responses")
        QMessageBox.information(self, "Thành Công", "Đã gửi tất cả responses!")
    
    def onSubmissionError(self, error: str):
        """Khi có lỗi gửi"""
        self.submission_log.append(f"\n❌ {error}")
        QMessageBox.critical(self, "Lỗi", error)


def main():
    """Hàm main"""
    app = QApplication(sys.argv)
    window = GoogleFormFillerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
