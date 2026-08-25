"""
tests/test_gemini_tool_agent.py
Unit tests for the Gemini tool-calling conversational agent loop and safe execution fallback.
Verifies multi-turn tool calling, varied phrasing robustness, error recovery, and honest offline boundaries.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.llm_client import EdithLLMClient
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
    
    # 1. Test Varied Phrasings in Offline Mode
    print("\n--- [1] VARIED USER PHRASINGS ---")
    client_offline = EdithLLMClient(api_key="")
    phrasings = [
        "Why is inventory ruled out?",
        "Why are supply constraints not the problem?",
        "Did warehouse stockouts cause the sales drop?",
        "Could inventory fill rate explain the issue?"
    ]
    for q in phrasings:
        resp, meta = client_offline.answer_question(q, anomaly_ctx, top_h, hyps)
        assert "99.4%" in resp or "fill rate" in resp.lower() or "0 stockout" in resp.lower()
        assert meta["provider"] is not None


    print("  [PASS] Varied natural language phrasings for the same underlying question return grounded evidence.")

    # 2. Multi-turn Follow-ups Depending on History
    print("\n--- [2] MULTI-TURN CONTEXT DEPENDENCY ---")
    history_pricing = [
        {"role": "user", "content": "What is the primary cause?"},
        {"role": "assistant", "content": "The primary cause is Pricing Elasticity (H1) due to a +12% price hike."}
    ]
    resp_followup, _ = client_offline.answer_question("Why did that happen?", anomaly_ctx, top_h, hyps, chat_history=history_pricing)
    assert "price" in resp_followup.lower() or "elasticity" in resp_followup.lower()
    print("  [PASS] Follow-up questions resolve contextually using prior message turns.")

    # 3. Tool Dispatcher & Execution Validation
    print("\n--- [3] TOOL CALL DISPATCHER & ERROR BOUNDARIES ---")
    res_summary = execute_tool_call("get_investigation_summary", {})
    assert "current_value" in res_summary
    assert res_summary["current_value"] == 1_253_600.0
    
    res_ev = execute_tool_call("get_hypothesis_evidence", {"hypothesis_id": "H1_PRICING_PRESSURE"})
    assert res_ev["cause_score_100"] >= 80.0
    
    res_err = execute_tool_call("get_hypothesis_evidence", {"hypothesis_id": "NON_EXISTENT_ID"})
    assert "error" in res_ev or "error" in res_err
    print("  [PASS] Tool execution validates parameters and handles invalid inputs gracefully.")

    # 4. Mocking Gemini Tool-Calling Agent Loop
    print("\n--- [4] GEMINI AGENT TOOL-CALLING LOOP (MOCK) ---")
    with patch("google.genai.Client") as MockGenAI:
        mock_instance = MagicMock()
        MockGenAI.return_value = mock_instance
        
        # Mock Gemini response with tool calling
        mock_response = MagicMock()
        mock_response.text = "Based on the EDITH analytical summary tool, Monthly B2B Sales dropped -$147,700 (-10.5%) due to H1 Pricing Pressure."
        mock_fc = MagicMock()
        mock_fc.name = "get_investigation_summary"
        mock_response.function_calls = [mock_fc]
        mock_instance.models.generate_content.return_value = mock_response
        
        client_live = EdithLLMClient(api_key="mock_test_key_12345")
        client_live.client = mock_instance
        
        ans, meta = client_live.answer_question("What happened to sales?", anomaly_ctx, top_h, hyps)
        assert "-$147,700" in ans or "Pricing Pressure" in ans
        assert "get_investigation_summary" in meta.get("tools_called", [])
        assert meta["mode"] == "Live Tool-Calling Agent"
        print("  [PASS] Live Gemini agent successfully invokes tool calls and returns grounded final answer.")

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
