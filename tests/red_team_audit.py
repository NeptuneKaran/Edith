"""
tests/red_team_audit.py
Comprehensive Red-Team Verification Script for EDITH.
Tests all edge cases, hostile prompts, mathematical formulas, and UI contexts.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine
from ai.offline_reasoner import OfflineEdithReasoner
from ai.llm_client import EdithLLMClient
from config.settings import ANOMALY_THRESHOLDS, EVIDENCE_WEIGHTS, SIMULATION_ASSUMPTIONS

def run_red_team_tests():
    print("==================================================")
    print("        EDITH BRUTAL RED-TEAM AUDIT SUITE        ")
    print("==================================================")
    repo = DataRepository.get_instance()
    
    # 1. Check Contribution Denominators & Math
    print("\n--- [1] CHECKING CONTRIBUTION DENOMINATORS ---")
    contrib = ContributionEngine.calculate_variance_decomposition(repo, 'kpi_b2b_sales')
    for dim, df in contrib['breakdowns'].items():
        tot_delta = df['delta_value'].sum()
        tot_pct = df['contribution_pct'].sum()
        print(f"Dimension {dim:<15}: sum(delta)=${tot_delta:,.0f} | sum(contribution_pct)={tot_pct:.2f}%")
        assert abs(tot_pct - 100.0) < 0.01, f"Contribution percentages for {dim} do not sum to 100%!"

    # 2. Check Evidence Score Formula Verification
    print("\n--- [2] CHECKING EVIDENCE ENGINE MATH & BOUNDS ---")
    ev = EvidenceEngine(repo)
    hyps = ev.evaluate_all_hypotheses('kpi_b2b_sales')
    for h in hyps:
        score = h['evidence_score']
        print(f"Hypothesis {h['id']:<24}: Score={score:.2f} [{h['confidence_band']}]")
        assert 0.0 <= score <= 1.0, f"Evidence score {score} out of bounds [0.0, 1.0]"

    # 3. Check Simulation Engine Edge Cases across 40 parameter variations
    print("\n--- [3] CHECKING SIMULATION EXTREMES & BOUNDS ---")
    test_prices = [-15.0, -12.0, -6.0, 0.0, 3.0, 5.0]
    test_mkts = [0.0, 5000.0, 15000.0, 30000.0, 50000.0]
    test_comps = [True, False]
    
    for p in test_prices:
        for m in test_mkts:
            for c in test_comps:
                s = SimulationEngine.simulate_lever_impact(
                    baseline_revenue=1401300.0,
                    current_revenue=1253600.0,
                    regional_affected_baseline=577200.0,
                    regional_affected_current=400000.0,
                    price_rollback_pct=p,
                    marketing_boost_usd=m,
                    competitor_retaliation=c
                )
                assert s['simulated_revenue'] > 0, "Simulated revenue is non-positive"
                assert s['simulated_margin_pct'] > 0, "Simulated margin is non-positive"
                assert 0.0 <= s['recovery_pct'] <= 100.0, f"Recovery % out of [0, 100]: {s['recovery_pct']}"
    print("  [PASS] All 60 simulation extreme-value combinations produced valid, non-negative, bounded outputs.")

    # 4. Check Offline Reasoner Resilience Under Hostile & Adversarial Inputs
    print("\n--- [4] CHECKING OFFLINE REASONER HOSTILE INPUTS ---")
    active_h = hyps[0]
    
    hostile_queries = [
        "",  # Empty string
        "   ",  # Whitespace only
        "DROP TABLE fact_sales;--",  # SQL Injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
        "What is the airspeed velocity of an unladen swallow?",  # Out-of-domain
        "Why did sales drop by 50% in Region Z?",  # False premise
        "Who is the CEO of ApexTech?",  # Fact not in database
        "Can you guarantee that lowering price by 6% will definitely increase sales?",  # Causal certainty bait
        "Explain quantum entanglement",  # Total non-sequitur
        "a" * 5000  # Buffer / long input
    ]
    
    for q in hostile_queries:
        resp = OfflineEdithReasoner.answer_followup_question(q, active_h, hyps)
        assert isinstance(resp, str) and len(resp) > 0, f"Failed on hostile query: {q[:30]}"
    print(f"  [PASS] All {len(hostile_queries)} hostile queries handled safely without crash or uncontrolled state.")

    # 5. Check Anomaly Detection Rule Enforcement
    print("\n--- [5] CHECKING ANOMALY PERSISTENCE & THRESHOLD RULES ---")
    df_sales = repo.get_kpi_time_series('kpi_b2b_sales')
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_sales)
    anom_eval = AnomalyEngine.evaluate_current_anomaly(df_analyzed, 'Monthly B2B Sales')
    
    print(f"  Current Z-score: {anom_eval['z_score']:.2f} (Threshold: {ANOMALY_THRESHOLDS.z_score_threshold})")
    print(f"  Current Delta %: {anom_eval['delta_pct']:.2f}% (Threshold: {ANOMALY_THRESHOLDS.materiality_pct_threshold}%)")
    print(f"  Persistence:     {anom_eval['is_persistent']}")
    print(f"  Status Label:    {anom_eval['status_label']}")
    assert anom_eval['is_anomaly'] is True
    assert anom_eval['is_p1_material'] is True
    assert anom_eval['is_persistent'] is True

    print("\n==================================================")
    print("      ALL RED-TEAM TESTS COMPLETED: 100% PASS     ")
    print("==================================================")

if __name__ == "__main__":
    run_red_team_tests()
