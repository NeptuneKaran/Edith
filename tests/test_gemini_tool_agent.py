"""
tests/test_gemini_tool_agent.py
Unit tests for the Gemini tool-calling conversational agent loop, Render environment key loading,
free-form scenario calculations, and safe error masking.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.llm_client import EdithLLMClient, _sanitize_log_message
from ai.tools import AVAILABLE_TOOLS, execute_tool_call
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.evidence_engine import EvidenceEngine

def test_gemini_tool_agent_suite():
    print("==================================================")
    print("   RUNNING GEMINI TOOL-CALLING AGENT SUITE        ")
    print("==================================================")
    
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(analyzed, kpi_name="Monthly B2B Sales")
    
    evidence_eng = EvidenceEngine(repo)
    hyps = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    top_h = hyps[0]
    
    # 1. Test Render Environment Key Resolution
    print("\n--- [1] RENDER ENVIRONMENT KEY RESOLUTION ---")
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyRenderRuntimeSecretKey12345"}):
        with patch("google.genai.Client") as MockGenAI:
            MockGenAI.return_value = MagicMock()
            client_render = EdithLLMClient(api_key="")
            assert client_render.api_key == "AIzaSyRenderRuntimeSecretKey12345"
            assert client_render.client is not None
    print("  [PASS] Render environment variable GEMINI_API_KEY is honored when passed empty string.")

    # 2. Test Free-Form Scenario Query (e.g. -8% Price Adjustment)
    print("\n--- [2] FREE-FORM SCENARIO QUESTION EVALUATION ---")
    client_offline = EdithLLMClient(api_key="")
    scenario_query = "what will be the effect if I do an -8 percent price adjustment instead of -6"
    resp_scen, meta_scen = client_offline.answer_question(scenario_query, anomaly_ctx, top_h, hyps)
    
    # Must contain scenario-specific figures, not generic hypothesis finding
    assert "-8.0%" in resp_scen or "-8%" in resp_scen
    assert "$1,278,985" in resp_scen or "1,278,98" in resp_scen or "recovery" in resp_scen.lower()
    assert "Investigation Finding for" not in resp_scen, "Scenario query should NOT return generic investigation finding!"
    print("  [PASS] Free-form scenario query (-8% adjustment) returns direct scenario calculations.")

    # 3. Multi-turn Tool Calling Roundtrip (Mock)
    print("\n--- [3] MULTI-TURN TOOL CALLING ROUNDTRIP (MOCK) ---")
    with patch("google.genai.Client") as MockGenAI:
        mock_instance = MagicMock()
        MockGenAI.return_value = mock_instance
        
        from google.genai import types
        # Turn 1: Model requests tool call
        mock_fc = types.FunctionCall(name="get_simulation_results", args={"price_rollback_pct": -8.0, "marketing_boost_usd": 15000.0})
        
        resp_turn1 = MagicMock()
        resp_turn1.function_calls = [mock_fc]
        resp_turn1.text = None
        resp_turn1.candidates = []

        
        # Turn 2: Model receives tool result and produces synthesized text
        resp_turn2 = MagicMock()
        resp_turn2.function_calls = None
        resp_turn2.text = "With an -8% price adjustment and $15k marketing boost, simulated revenue reaches $1,278,985/wk, recovering 17.2% of lost volume."
        
        mock_instance.models.generate_content.side_effect = [resp_turn1, resp_turn2]
        
        client_live = EdithLLMClient(api_key="mock_test_key_12345")
        client_live.client = mock_instance
        
        ans, meta = client_live.answer_question(scenario_query, anomaly_ctx, top_h, hyps)
        assert "$1,278,985" in ans or "17.2%" in ans
        assert "get_simulation_results" in meta.get("tools_called", [])
        assert "Live Gemini Agent" in meta["mode"]
        print("  [PASS] Multi-turn tool calling loop successfully executed tool and returned Gemini synthesis.")

    # 4. Safe Logging / Redaction Check
    print("\n--- [4] SAFE LOGGING / SECRET REDACTION ---")
    raw_error = "API key AIzaSyTestKeySecret12345 failed with 403 Forbidden"
    sanitized = _sanitize_log_message(raw_error, "AIzaSyTestKeySecret12345")
    assert "AIzaSyTestKeySecret12345" not in sanitized
    assert "[REDACTED" in sanitized
    print("  [PASS] Sensitive API keys are redacted from error logs.")

    # 5. Honest Offline Mode Communication
    print("\n--- [5] HONEST OFFLINE BOUNDARY REPORTING ---")
    client_off = EdithLLMClient(api_key="")
    assert client_off.client is None
    briefing, meta_off = client_off.generate_briefing(anomaly_ctx, hyps)
    assert meta_off["status"] == "Active (Offline Mode)"
    assert "Zero-Key" in meta_off["mode"] or "Offline" in meta_off["mode"]
    print("  [PASS] Zero-key mode transparently identifies itself as deterministic offline mode.")

    print("\n==================================================")
    print("    ALL GEMINI AGENT TESTS PASSED (100%)!         ")
    print("==================================================")

if __name__ == "__main__":
    test_gemini_tool_agent_suite()
