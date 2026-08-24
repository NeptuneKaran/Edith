"""
tests/test_llm_fallback.py
Verification tests for EDITH's Offline Reasoner and LLM Client grounding.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.offline_reasoner import OfflineEdithReasoner
from ai.llm_client import EdithLLMClient
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.evidence_engine import EvidenceEngine

def test_offline_reasoner_briefing():
    """Verify that offline reasoner generates an executive briefing referencing verified data facts."""
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, "Monthly B2B Sales")
    
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    
    briefing = OfflineEdithReasoner.generate_investigation_briefing(anomaly_ctx, hypotheses)
    
    assert "Monthly B2B Sales" in briefing
    assert "Region B" in briefing
    assert "Enterprise" in briefing
    assert "Pricing Elasticity" in briefing
    assert "99.4%" in briefing or "Inventory" in briefing
    print("  [PASS] test_offline_reasoner_briefing")

def test_offline_reasoner_qa():
    """Verify that offline reasoner accurately answers specific drill-down questions."""
    repo = DataRepository.get_instance()
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    selected_h = hypotheses[0]
    
    # Test inventory question
    ans_inv = OfflineEdithReasoner.answer_followup_question("Why is inventory ruled out?", selected_h, hypotheses)
    assert "Warehouse Logistics Fact" in ans_inv or "99.4%" in ans_inv
    assert "0 stockout days" in ans_inv
    
    # Test competitor question
    ans_comp = OfflineEdithReasoner.answer_followup_question("Why is competitor action secondary?", selected_h, hypotheses)
    assert "Week 06" in ans_comp or "Week 07" in ans_comp or "Temporal Sequence" in ans_comp
    print("  [PASS] test_offline_reasoner_qa")

def test_llm_client_fallback_mode():
    """Verify that EdithLLMClient gracefully falls back to deterministic reasoner when no key is set."""
    client = EdithLLMClient(api_key="")
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, "Monthly B2B Sales")
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    
    text, meta = client.generate_briefing(anomaly_ctx, hypotheses)
    assert len(text) > 50
    assert meta["mode"] == "Deterministic Offline Fallback (100% Grounded)"
    assert meta["status"] == "Active (Zero-Key Mode)"
    print("  [PASS] test_llm_client_fallback_mode")

if __name__ == "__main__":
    print("Running LLM Fallback & Grounding Tests...")
    test_offline_reasoner_briefing()
    test_offline_reasoner_qa()
    test_llm_client_fallback_mode()
    print("ALL LLM FALLBACK & GROUNDING TESTS PASSED SUCCESSFULLY!")
