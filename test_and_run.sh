#!/bin/bash
cd /Users/2apple_mgn_63_ram16/Desktop/GGform
echo "=== Running Final Test ==="
python3 final_test.py 2>&1
echo ""
echo "=== Running GUI App ==="
python3 gui_app_v3.py 2>&1 &
APP_PID=$!
sleep 25
kill $APP_PID 2>/dev/null || true
echo "Done!"
