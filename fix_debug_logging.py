#!/usr/bin/env python3
"""Script to fix gui_app_v3.py - add debug logging to worker thread"""

import re

def fix_file():
    with open('gui_app_v3.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the loop section
    old_text = '''                # 🔥 Loop lấy và xử lý tasks
                while True:
                    # Lấy task tiếp theo (thread-safe)
                    with lock:
                        if current_task[0] >= count_int:
                            break
                        task_idx = current_task[0]
                        current_task[0] += 1'''
    
    new_text = '''                # 🔥 Loop lấy và xử lý tasks
                logger.info(f"[T{thread_id}] Starting loop: current_task={current_task[0]}, count_int={count_int}")
                
                while True:
                    # Lấy task tiếp theo (thread-safe)
                    with lock:
                        if current_task[0] >= count_int:
                            logger.info(f"[T{thread_id}] No more tasks, exiting")
                            break
                        task_idx = current_task[0]
                        current_task[0] += 1
                        logger.info(f"[T{thread_id}] Got task {task_idx + 1}/{count_int}")'''
    
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open('gui_app_v3.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ File updated - added debug logging to worker thread loop")
        return True
    else:
        print("✗ Pattern not found")
        # Show what's there
        idx = content.find("# 🔥 Loop")
        if idx > 0:
            print(f"Content at that position ({idx}):")
            print(content[idx:idx+400])
        return False

if __name__ == "__main__":
    fix_file()
