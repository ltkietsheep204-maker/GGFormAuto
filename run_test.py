import subprocess
import sys

result = subprocess.run(
    [sys.executable, "test_textbox.py"],
    cwd="/Users/2apple_mgn_63_ram16/Desktop/GGform",
    capture_output=True,
    text=True,
    timeout=25
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
