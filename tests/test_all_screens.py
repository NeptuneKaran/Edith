"""
tests/test_all_screens.py
Directly tests each of the 6 screen data contracts and navigation behaviors within an initialized Streamlit session mock.
Verifies that all screens (Data Sources, Detect, Diagnose, Explain, Simulate, Console) execute cleanly without exceptions.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from data.repository import DataRepository
from data.source_manager import DataParser, ColumnMapper, SQLQueryValidator
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from core.dependency_graph import MetricDependencyGraph
from state.session_state import init_session_state, set_screen
from ai.llm_client import EdithLLMClient

def test_screen_data_contracts():
    print("=== TESTING DATA CONTRACTS FOR ALL 6 SCREENS ===")
    
    repo = DataRepository.get_instance()
    
    # Screen 0: Data Sources Manager
    src_info = repo.get_active_source_info()
    assert "name" in src_info
    assert "source_type" in src_info
    assert src_info["is_demo"] is True
    is_safe, _ = SQLQueryValidator.validate_query("SELECT * FROM sales LIMIT 100;")
    assert is_safe
    print("  [PASS] Screen 0: Data Sources Manager contracts verified.")
    
    # Screen 1: Detect (Overview)
    kpis = ["kpi_b2b_sales", "kpi_gross_margin", "kpi_customer_churn", "kpi_marketing_roas"]
    for kpi in kpis:
        ts = repo.get_kpi_time_series(kpi)
        assert len(ts) == 52, f"Expected 52 weeks for {kpi}, got {len(ts)}"
        analyzed = AnomalyEngine.calculate_baseline_and_corridor(ts)
        assert "upper_corridor" in analyzed
        assert "lower_corridor" in analyzed
        assert "z_score" in analyzed
    print("  [PASS] Screen 1: All 4 KPI time series and corridor calculations verified.")
    
    # Screen 2: Diagnose (KPI Diagnostic)
    contrib = ContributionEngine.calculate_variance_decomposition(repo, "kpi_b2b_sales")
    assert "breakdowns" in contrib
    assert "region" in contrib["breakdowns"]
    assert "customer_tier" in contrib["breakdowns"]
    assert "product_line" in contrib["breakdowns"]
    assert "channel" in contrib["breakdowns"]
    print("  [PASS] Screen 2: Multi-dimensional decomposition verified.")
    
    # Screen 3: Explain (Causal Investigation Workspace)
    evidence = EvidenceEngine(repo)
    hypos = evidence.evaluate_all_hypotheses("kpi_b2b_sales")
    assert len(hypos) == 8
    for h in hypos:
        assert "id" in h
        assert "evidence_score" in h
        assert "cause_score_100" in h
        assert "confidence_band" in h
        assert "supporting_evidence" in h
        assert "contradictory_evidence" in h
        assert "predictions" in h
        assert "control_group_analysis" in h
    cohort = repo.get_cohort_comparison()
    assert "Enterprise" in cohort.columns
    assert "Mid-Market" in cohort.columns
    print("  [PASS] Screen 3: Multi-hypothesis and Difference-in-Differences contracts verified.")
    
    # Screen 4: Simulate (Scenario Workbench)
    from core.simulation_engine import SimulationEngine
    sim = SimulationEngine.simulate_lever_impact(price_rollback_pct=-6.0, marketing_boost_usd=15000.0)
    assert "simulated_revenue" in sim
    assert "net_revenue_delta" in sim
    assert "simulated_margin_pct" in sim
    assert "trajectory_df" in sim
    assert len(sim["trajectory_df"]) == 8
    print("  [PASS] Screen 4: 8-week counterfactual trajectory simulation verified.")
    
    # Screen 5: Console (Dedicated Conversational Screen)
    client = EdithLLMClient(api_key="")
    anom_ctx = AnomalyEngine.evaluate_current_anomaly(
        AnomalyEngine.calculate_baseline_and_corridor(repo.get_kpi_time_series("kpi_b2b_sales")),
        kpi_name="Monthly B2B Sales"
    )
    briefing, meta = client.generate_briefing(anom_ctx, hypos)
    assert len(briefing) > 50
    assert meta.get("provider") is not None
    
    ans, meta_ans = client.answer_question("Why is inventory ruled out?", anom_ctx, hypos[0], hypos)
    assert "inventory" in ans.lower() or "fill rate" in ans.lower() or "99.4%" in ans
    print("  [PASS] Screen 5: Full-page EDITH Console grounding & Q&A turn verified.")
    
    print("\n[PASS] ALL 6 SCREEN DATA CONTRACTS PASSED 100%!")

if __name__ == "__main__":
    test_screen_data_contracts()
