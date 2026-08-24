"""
tests/test_analytics.py
Automated verification tests for EDITH's deterministic analytical engines.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from data.generator import generate_enterprise_dataset
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine

def test_data_generation():
    """Verify that synthetic tables are generated with consistent shapes and keys."""
    tables = generate_enterprise_dataset(seed=42)
    assert "sales" in tables
    assert "pricing" in tables
    assert "competitor" in tables
    assert "inventory" in tables
    assert "feedback" in tables
    
    df_sales = tables["sales"]
    assert len(df_sales) > 0
    assert df_sales["gross_revenue"].min() >= 0
    print("  [PASS] test_data_generation")

def test_baseline_and_corridor():
    """Verify that expected corridor (±2σ) contains historical normal points and flags anomaly."""
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    
    assert "baseline" in df_analyzed.columns
    assert "upper_corridor" in df_analyzed.columns
    assert "lower_corridor" in df_analyzed.columns
    assert "z_score" in df_analyzed.columns
    assert "is_anomaly" in df_analyzed.columns
    
    # Verify bounds are valid: lower <= baseline <= upper
    for _, row in df_analyzed.iterrows():
        assert row["lower_corridor"] <= row["baseline"] <= row["upper_corridor"]
        
    # Verify current point is flagged as anomaly
    curr_anom = AnomalyEngine.evaluate_current_anomaly(df_analyzed, "Monthly B2B Sales")
    assert curr_anom["is_anomaly"] is True
    assert curr_anom["is_p1_material"] is True
    assert curr_anom["z_score"] < -2.0
    print("  [PASS] test_baseline_and_corridor")

def test_dimensional_contribution():
    """Verify dimensional variance decomposition sums properly and identifies Region B."""
    repo = DataRepository.get_instance()
    contrib = ContributionEngine.calculate_variance_decomposition(repo, "kpi_b2b_sales")
    
    breakdowns = contrib["breakdowns"]
    assert "region" in breakdowns
    assert "customer_tier" in breakdowns
    assert "product_line" in breakdowns
    
    # Region B should be the primary driving region
    assert contrib["primary_region"] == "Region B"
    assert contrib["primary_region_share"] > 50.0 # Region B accounts for >50% of the drop
    
    # Enterprise should be the primary driving customer tier
    assert contrib["primary_tier"] == "Enterprise"
    assert contrib["primary_tier_share"] > 50.0
    print("  [PASS] test_dimensional_contribution")

def test_evidence_scoring():
    """Verify that Evidence Scores are bounded in [0, 1] and rank hypotheses correctly."""
    repo = DataRepository.get_instance()
    engine = EvidenceEngine(repo)
    hypotheses = engine.evaluate_all_hypotheses("kpi_b2b_sales")
    
    assert len(hypotheses) == 4
    
    # Check score bounds
    for h in hypotheses:
        score = h["evidence_score"]
        assert 0.0 <= score <= 1.0, f"Score for {h['name']} out of bounds: {score}"
        assert len(h["supporting_evidence"]) > 0
        assert len(h["contradictory_evidence"]) > 0
        assert "data_lineage" in h
        
    # Verify expected ranking: Pricing > Competitor > Demand > Inventory
    h_map = {h["id"]: h["evidence_score"] for h in hypotheses}
    assert h_map["H1_PRICING_PRESSURE"] > h_map["H2_COMPETITOR_CAMPAIGN"]
    assert h_map["H2_COMPETITOR_CAMPAIGN"] > h_map["H4_DEMAND_CONTRACTION"]
    assert h_map["H4_DEMAND_CONTRACTION"] > h_map["H3_INVENTORY_CONSTRAINT"]
    assert h_map["H3_INVENTORY_CONSTRAINT"] < 0.25 # Refuted by 99% stock fill rate
    print("  [PASS] test_evidence_scoring")

def test_simulation_engine():
    """Verify simulation responds monotonically to price and marketing lever changes."""
    sim_base = SimulationEngine.simulate_lever_impact(price_rollback_pct=0.0, marketing_boost_usd=0.0)
    sim_rolled_back = SimulationEngine.simulate_lever_impact(price_rollback_pct=-6.0, marketing_boost_usd=15000.0)
    
    # Rolling back price should increase unit volume and revenue recovery
    assert sim_rolled_back["recovery_pct"] > sim_base["recovery_pct"]
    assert sim_rolled_back["simulated_revenue"] > sim_base["simulated_revenue"]
    assert len(sim_rolled_back["trajectory_df"]) == 8
    print("  [PASS] test_simulation_engine")

if __name__ == "__main__":
    print("Running Analytics Engine Unit Tests...")
    test_data_generation()
    test_baseline_and_corridor()
    test_dimensional_contribution()
    test_evidence_scoring()
    test_simulation_engine()
    print("ALL ANALYTICS UNIT TESTS PASSED SUCCESSFULLY!")
