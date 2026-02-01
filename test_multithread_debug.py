#!/usr/bin/env python3
"""
Debug script để test xem Chrome driver có hoạt động đúng trong đa luồng không
"""

import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Test URL - dùng Google để test đơn giản
TEST_URL = "https://www.google.com"

def test_single_driver():
    """Test một driver đơn lẻ"""
    print("=" * 50)
    print("TEST 1: Single driver")
    print("=" * 50)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=800,600")
    
    driver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    
    try:
        print(f"1. Driver created, session_id: {driver.session_id}")
        
        driver.get(TEST_URL)
        print(f"2. Navigated to: {driver.current_url}")
        
        # Try to find search box
        time.sleep(1)
        search_box = driver.find_element(By.NAME, "q")
        print(f"3. Found search box: {search_box}")
        
        search_box.send_keys("Hello World")
        print(f"4. Typed text into search box")
        
        time.sleep(2)
        print(f"5. Current URL: {driver.current_url}")
        
        print("✓ Single driver test PASSED!")
        
    except Exception as e:
        print(f"✗ Single driver test FAILED: {e}")
    finally:
        driver.quit()
        print("Driver closed")

def test_multithread_drivers():
    """Test nhiều drivers chạy song song"""
    print("\n" + "=" * 50)
    print("TEST 2: Multi-thread drivers (2 threads)")
    print("=" * 50)
    
    driver_path = ChromeDriverManager().install()
    results = []
    lock = threading.Lock()
    
    def worker(thread_id):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--window-size=600,500")
            
            driver = webdriver.Chrome(service=Service(driver_path), options=options)
            
            # Position window
            x = thread_id * 620
            y = 0
            driver.set_window_position(x, y)
            
            print(f"[T{thread_id}] Driver created, session: {driver.session_id[:20]}...")
            print(f"[T{thread_id}] Window position: ({x}, {y})")
            
            # Navigate
            driver.get(TEST_URL)
            print(f"[T{thread_id}] Navigated to: {driver.current_url}")
            
            # Wait for page load
            time.sleep(1)
            
            # Try to interact
            try:
                search_box = driver.find_element(By.NAME, "q")
                search_box.send_keys(f"Thread {thread_id} test")
                print(f"[T{thread_id}] ✓ Typed text successfully!")
                
                with lock:
                    results.append(f"T{thread_id}: SUCCESS")
            except Exception as e:
                print(f"[T{thread_id}] ✗ Failed to interact: {e}")
                with lock:
                    results.append(f"T{thread_id}: FAILED - {e}")
            
            time.sleep(3)
            driver.quit()
            print(f"[T{thread_id}] Driver closed")
            
        except Exception as e:
            print(f"[T{thread_id}] ✗ Thread error: {e}")
            with lock:
                results.append(f"T{thread_id}: ERROR - {e}")
    
    # Create and start threads
    threads = []
    for i in range(2):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
    
    print("Starting all threads...")
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    print("\n" + "-" * 30)
    print("RESULTS:")
    for r in results:
        print(f"  {r}")
    
    if all("SUCCESS" in r for r in results):
        print("✓ Multi-thread test PASSED!")
    else:
        print("✗ Multi-thread test FAILED!")

if __name__ == "__main__":
    print("\n🔍 CHROME DRIVER DEBUG TEST\n")
    
    test_single_driver()
    test_multithread_drivers()
    
    print("\n✅ All tests completed!")
