import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def auto_fill_google_form(form_url, response_count=1):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless")  # Bỏ để xem Chrome chạy
    options.add_argument("--disable-gpu")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        for i in range(int(response_count)):
            driver.get(form_url)
            time.sleep(3)
            # Tìm các câu hỏi (ví dụ: class Qr7Oae)
            questions = driver.find_elements(By.CLASS_NAME, "Qr7Oae")
            for q in questions:
                # Ví dụ: chọn radio đầu tiên nếu có
                radios = q.find_elements(By.XPATH, ".//div[@role='radio']")
                if radios:
                    radios[0].click()
                    continue
                # Nếu là text input
                textinputs = q.find_elements(By.XPATH, ".//input[@type='text']")
                if textinputs:
                    textinputs[0].send_keys("Test")
                    continue
            # Gửi form
            submit_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'Gửi')]")
            if submit_btns:
                submit_btns[0].click()
            time.sleep(2)
        return True, f"Đã gửi {response_count} response thành công!"
    except Exception as e:
        return False, str(e)
    finally:
        if driver:
            driver.quit()
