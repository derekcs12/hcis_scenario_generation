import subprocess

# 定義要執行的 Python 檔案
scripts = [
    "./config_generator_4way.py",
    "./config_generator_straight.py",
    "./config_generator_straight_at4way.py"
]

# 依次執行每個 Python 檔案
for script in scripts:
    command = ["python", script]
    subprocess.run(command)