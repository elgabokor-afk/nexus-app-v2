import sys
import os
import subprocess

print("==================================================")
print("   NEXUS AI: ML ENVIRONMENT DIAGNOSTIC")
print("==================================================")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Current Directory: {os.getcwd()}")
print("==================================================")

libraries = ['joblib', 'xgboost', 'sklearn', 'numpy', 'pandas']
green = '\033[92m'
red = '\033[91m'
reset = '\033[0m'

all_good = True

for lib in libraries:
    try:
        __import__(lib)
        print(f"[{green}OK{reset}] {lib} is installed.")
    except ImportError as e:
        print(f"[{red}FAIL{reset}] {lib} is MISSING! ({e})")
        all_good = False

print("==================================================")
if all_good:
    print(f"{green}>>> ALL SYSTEMS GO. AI ENGINE READY.{reset}")
    sys.exit(0)
else:
    print(f"{red}>>> CRITICAL MISSING LIBRARIES DETECTED.{reset}")
    print("    Attempting Auto-Repair...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "joblib", "xgboost", "scikit-learn", "numpy", "pandas"])
        print(f"{green}>>> REPAIR COMPLETE. PLEASE RESTART BRAIN.{reset}")
    except Exception as e:
        print(f"{red}>>> AUTO-REPAIR FAILED: {e}{reset}")
    sys.exit(1)
