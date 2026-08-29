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
        "Windows Absolute Path": r'[c-zC-Z]:\\(?:Users|Program|Windows|temp|tmp|\w+[\\])',
        "Hardcoded localhost/port": r'http://localhost:\d+',
        "Raw API Key": r'(?:AIzaSy[0-9A-Za-z-_]{33}|sk-[0-9A-Za-z-_]{30,})'
    }
    
    found_issues = 0
    for root, dirs, files in os.walk('.'):
        if '.git' in root or '__pycache__' in root or '.pytest_cache' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.toml', '.yaml', '.yml', '.md', '.txt', '.json')):
                p = os.path.join(root, f)
                # Skip documentation files and test fixtures designed to test dummy invalid keys
                if f in ['README.md', 'HOW_IT_WORKS.md', 'EDITH_TESTING_GUIDE.md', 'check_deployment_readiness.py', 'test_deployment_simulation.py']:
                    continue

                with open(p, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    for label, pat in patterns.items():
                        matches = re.finditer(pat, content)
                        for m in matches:
                            line_num = content[:m.start()].count('\n') + 1
                            matched_text = m.group(0)
                            print(f"[{label}] {p}:{line_num} -> {matched_text}")
                            found_issues += 1
                            
    if found_issues == 0:
        print("[PASS] Zero hardcoded secrets, absolute paths, or local addresses found in source files!")
    else:
        print(f"Total occurrences found: {found_issues}")
        assert found_issues == 0, "Deployment blocker detected!"

if __name__ == "__main__":
    check()
