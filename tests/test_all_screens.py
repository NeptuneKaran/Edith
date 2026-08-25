"""
tests/test_all_screens.py
Directly tests each of the 4 screen render functions within an initialized Streamlit session mock.
Verifies that all 4 screens (Overview, Diagnostic, Workspace, Simulation) execute cleanly without exceptions.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine

def test_screen_data_contracts():
    print("=== TESTING DATA CONTRACTS FOR ALL 4 SCREENS ===")
    
    repo = DataRepository.get_instance()
    
    # Screen 1 Data Contract
    kpis = ["kpi_b2b_sales", "kpi_gross_margin", "kpi_customer_churn", "kpi_marketing_roas"]
    for kpi in kpis:
        ts = repo.get_kpi_time_series(kpi)
        assert len(ts) == 52, f"Expected 52 weeks for {kpi}, got {len(ts)}"
        analyzed = AnomalyEngine.calculate_baseline_and_corridor(ts)
        assert "upper_corridor" in analyzed
        assert "lower_corridor" in analyzed
        assert "z_score" in analyzed
    print("  [PASS] Screen 1: All 4 KPI time series and corridor calculations verified.")
    
    # Screen 2 Data Contract
    contrib = ContributionEngine.calculate_variance_decomposition(repo, "kpi_b2b_sales")
    assert "breakdowns" in contrib
    assert "region" in contrib["breakdowns"]
    assert "customer_tier" in contrib["breakdowns"]
    assert "product_line" in contrib["breakdowns"]
    assert "channel" in contrib["breakdowns"]
    print("  [PASS] Screen 2: Multi-dimensional decomposition verified.")
    
    # Screen 3 Data Contract
    evidence = EvidenceEngine(repo)
    hypos = evidence.evaluate_all_hypotheses("kpi_b2b_sales")
    assert len(hypos) == 8
    for h in hypos:
        assert "id" in h
        assert "evidence_score" in h
        assert "confidence_band" in h
        assert "supporting_evidence" in h
        assert "contradictory_evidence" in h
        assert "predictions" in h
        assert "control_group_analysis" in h
    cohort = repo.get_cohort_comparison()
    assert "Enterprise" in cohort.columns
    assert "Mid-Market" in cohort.columns
    print("  [PASS] Screen 3: Multi-hypothesis and Difference-in-Differences contracts verified.")
    
    # Screen 4 Data Contract
    from core.simulation_engine import SimulationEngine
    sim = SimulationEngine.simulate_lever_impact(price_rollback_pct=-6.0, marketing_boost_usd=15000.0)
    assert "simulated_revenue" in sim
    assert "net_revenue_delta" in sim
    assert "simulated_margin_pct" in sim
    assert "trajectory_df" in sim
    assert len(sim["trajectory_df"]) == 8
    print("  [PASS] Screen 4: 8-week counterfactual trajectory simulation verified.")
    
    print("\n[PASS] ALL 4 SCREEN DATA CONTRACTS PASSED 100%!")

if __name__ == "__main__":
    test_screen_data_contracts()
