import subprocess

# 定義要執行的 Python 檔案
scripts = [
    "./script/config_generator_4way.py",
    "./script/config_generator_straight.py",
    "./script/config_generator_straight_at4way.py"
]

# 依次執行每個 Python 檔案
for script in scripts:
    command = ["python", script]
    subprocess.run(command)
    
# 01FL-TR_02BL-TR_10_metrics