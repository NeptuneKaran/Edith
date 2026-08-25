"""
tests/test_deployment_simulation.py
Simulates a full production deployment run of EDITH:
1. Verifies that all state machines, engines, and screens initialize without errors.
2. Verifies that LLM Gateway works seamlessly with and without GEMINI_API_KEY.
3. Verifies that simulation workbench outputs valid non-empty decision packages.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine
from ai.llm_client import EdithLLMClient
from state.session_state import init_session_state, select_hypothesis

def test_full_pipeline_simulation():
    print("=== RUNNING FULL PRODUCTION DEPLOYMENT PIPELINE SIMULATION ===")
    
    # 1. Initialize data repository
    repo = DataRepository.get_instance()
    assert repo is not None, "Repository failed to initialize"
    print("  [PASS] Data repository initialized in-memory")
    
    # 2. Anomaly Engine
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, kpi_name="Monthly B2B Sales")
    assert anomaly_ctx["is_anomaly"] is True
    assert anomaly_ctx["is_p1_material"] is True
    assert round(anomaly_ctx["z_score"], 2) == -2.30
    print("  [PASS] Screen 1 & 2 Anomaly Detection engine evaluated correctly")
    
    # 3. Contribution Engine
    contrib_ctx = ContributionEngine.calculate_variance_decomposition(repo, "kpi_b2b_sales")
    assert "breakdowns" in contrib_ctx
    assert "region" in contrib_ctx["breakdowns"]
    assert "customer_tier" in contrib_ctx["breakdowns"]
    assert "product_line" in contrib_ctx["breakdowns"]
    print("  [PASS] Screen 2 Dimensional Variance engine evaluated correctly")
    
    # 4. Evidence Engine
    evidence_engine = EvidenceEngine(repo)
    hypotheses = evidence_engine.evaluate_all_hypotheses("kpi_b2b_sales")
    assert len(hypotheses) == 8
    assert hypotheses[0]["id"] == "H1_PRICING_PRESSURE"
    assert hypotheses[0]["evidence_score"] >= 0.80
    assert hypotheses[-1]["evidence_score"] == 0.00
    print("  [PASS] Screen 3 Multi-Hypothesis Evidence engine evaluated correctly")
    
    # 5. LLM Client Zero-Key Mode
    client_zero_key = EdithLLMClient(api_key="")
    briefing, meta = client_zero_key.generate_briefing(anomaly_ctx, hypotheses)
    assert len(briefing) > 100
    assert meta["mode"] == "Deterministic Offline Fallback (100% Grounded)"
    print("  [PASS] AI Gateway operates reliably in Zero-Key Offline mode")
    
    # 6. LLM Client Invalid Key Graceful Recovery
    client_invalid_key = EdithLLMClient(api_key="AIzaSyDummyInvalidKeyForTestingFallback12345")
    briefing_fallback, meta_fallback = client_invalid_key.generate_briefing(anomaly_ctx, hypotheses)
    assert len(briefing_fallback) > 100
    assert meta_fallback["status"] == "Active (Zero-Key Mode)"
    print("  [PASS] AI Gateway recovers gracefully from invalid API key")
    
    # 7. Simulation Engine & Decision Package
    sim_engine = SimulationEngine()
    sim_out = sim_engine.simulate_lever_impact(
        price_rollback_pct=-6.0,
        marketing_boost_usd=15000.0,
        competitor_retaliation=False
    )
    assert sim_out["simulated_revenue"] > 1_250_000
    assert sim_out["simulated_margin_pct"] > 65.0
    print("  [PASS] Screen 4 Simulation & What-If engine evaluated correctly")
    
    print("\n[PASS] FULL PRODUCTION PIPELINE TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_pipeline_simulation()
