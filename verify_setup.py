import sys
import os
import importlib.util

def check_import(module_name):
    try:
        if importlib.util.find_spec(module_name) is None:
            print(f"[FAIL] {module_name}: Not found")
            return False
        else:
            print(f"[OK] {module_name}")
            return True
    except ImportError as e:
        print(f"[FAIL] {module_name}: {e}")
        return False

print(f"Python Version: {sys.version}")

print("\nVerifying dependencies...")
deps = ["faster_whisper", "sounddevice", "numpy", "ollama", "rich", "av", "ctranslate2"]
all_deps_ok = True
for dep in deps:
    if not check_import(dep):
        all_deps_ok = False

print("\nVerifying project structure...")
files = [
    "src/audio_capture.py",
    "src/transcriber.py",
    "src/llm_engine.py",
    "src/ui.py",
    "src/utils.py",
    "main.py"
]

all_files_ok = True
for f in files:
    if os.path.exists(f):
        print(f"[OK] {f}")
    else:
        print(f"[FAIL] {f}")
        all_files_ok = False

if all_deps_ok and all_files_ok:
    print("\nSUCCESS: All checks passed.")
else:
    print("\nFAILURE: Some checks failed.")
