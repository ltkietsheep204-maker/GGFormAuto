#!/usr/bin/env python3
import subprocess
import sys
import time

print("Starting debug script...")
proc = subprocess.Popen(
    [sys.executable, 'debug_selectors.py'],
    cwd='/Users/2apple_mgn_63_ram16/Desktop/GGform',
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

try:
    output, _ = proc.communicate(timeout=40)
    print(output)
except subprocess.TimeoutExpired:
    print("Script timed out, killing...")
    proc.kill()
    try:
        output, _ = proc.communicate(timeout=5)
        if output:
            print(output)
    except:
        pass
    print("\nTimeout exceeded!")
    sys.exit(1)

sys.exit(proc.returncode)
