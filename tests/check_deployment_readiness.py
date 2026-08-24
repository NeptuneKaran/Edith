"""
tests/check_deployment_readiness.py
Inspects the repository for deployment blockers, hardcoded paths, secrets, and compatibility issues.
"""
import os
import sys
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check():
    print("=== CHECKING FOR SECRETS, WINDOWS PATHS, AND HARDCODED ADDRESSES ===")
    patterns = {
        "Windows Absolute Path": r'[c-zC-Z]:\\[^ \n]+',
        "Hardcoded localhost/port": r'http://localhost:\d+',
        "Raw API Key": r'(?:AIzaSy[0-9A-Za-z-_]{33}|sk-[0-9A-Za-z-_]{30,})'
    }
    
    found_issues = 0
    for root, dirs, files in os.walk('.'):
        if '.git' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.toml', '.yaml', '.yml', '.md', '.txt', '.json')):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    for label, pat in patterns.items():
                        matches = re.finditer(pat, content)
                        for m in matches:
                            # skip if it is in README / documentation examples or comments explaining local running
                            line_num = content[:m.start()].count('\n') + 1
                            matched_text = m.group(0)
                            print(f"[{label}] {p}:{line_num} -> {matched_text}")
                            found_issues += 1
                            
    if found_issues == 0:
        print("[PASS] Zero hardcoded secrets, absolute paths, or local addresses found in source files!")
    else:
        print(f"Total occurrences found: {found_issues}")

if __name__ == "__main__":
    check()
