#!/bin/bash
cd /Users/2apple_mgn_63_ram16/Desktop/GGform
python3 gui_app_v3.py > /tmp/app_output.txt 2>&1 &
sleep 25
kill $! 2>/dev/null || true
cat /tmp/app_output.txt
