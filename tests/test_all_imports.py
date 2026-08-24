"""
tests/test_all_imports.py
Verifies that every single module in the project can be imported without errors,
without requiring external credentials, and with full dependency resolution.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_imports():
    print("=== TESTING ALL REPOSITORY IMPORTS ===")
    modules_to_test = [
        "config.settings",
        "config.semantic_contracts",
        "data.generator",
        "data.repository",
        "core.baseline_engine",
        "core.contribution_engine",
        "core.evidence_engine",
        "core.simulation_engine",
        "ai.prompts",
        "ai.offline_reasoner",
        "ai.llm_client",
        "state.session_state",
        "ui.components.cards",
        "ui.components.charts",
        "ui.components.chat_pane",
        "ui.screens.s1_overview",
        "ui.screens.s2_diagnostic",
        "ui.screens.s3_workspace",
        "ui.screens.s4_simulation",
    ]
    
    passed = 0
    for mod in modules_to_test:
        try:
            __import__(mod)
            print(f"  [PASS] {mod}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {mod}: {e}")
            raise
            
    print(f"\n[PASS] All {passed}/{len(modules_to_test)} modules imported successfully with zero errors!")

if __name__ == "__main__":
    test_imports()
