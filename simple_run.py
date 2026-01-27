#!/usr/bin/env python3
"""
Simple test - chỉ chạy GUI app và ghi log
"""
import subprocess
import sys
import os

os.chdir('/Users/2apple_mgn_63_ram16/Desktop/GGform')

print("=" * 60)
print("Starting GUI App v3...")
print("=" * 60)

# Run the app và pipe output
proc = subprocess.Popen(
    [sys.executable, 'gui_app_v3.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1  # Line buffered
)

# Read output với timeout
import select
import time

start_time = time.time()
timeout = 35  # 35 second timeout
output_lines = []

try:
    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            print("\n[TIMEOUT] Killing process...")
            proc.terminate()
            break
        
        # Read available output
        if proc.poll() is not None:
            # Process ended
            remaining = proc.stdout.read()
            if remaining:
                output_lines.append(remaining)
            break
        
        # Read one line with short timeout
        try:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            output_lines.append(line)
            # Print in real-time
            print(line, end='', flush=True)
        except:
            time.sleep(0.1)
            
except KeyboardInterrupt:
    print("\n[INTERRUPTED]")
    proc.terminate()

proc.wait()
print("\n" + "=" * 60)
print("Done!")
