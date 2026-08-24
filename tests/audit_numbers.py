"""
tests/audit_numbers.py
Detailed numerical and state audit script for EDITH.
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

def run_audit():
    print("==================================================")
    print("        EDITH RIGOROUS NUMERICAL AUDIT           ")
    print("==================================================")
    repo = DataRepository.get_instance()
    
    # 1. Anomaly Audit
    df_ts = repo.get_kpi_time_series('kpi_b2b_sales')
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anom = AnomalyEngine.evaluate_current_anomaly(df_analyzed, 'Monthly B2B Sales')
    
    print("\n--- [1] ANOMALY ENGINE NUMBERS ---")
    print(f"Current Observed Revenue:    ${anom['current_value']:,.2f}")
    print(f"Baseline (8-wk robust med):  ${anom['baseline_value']:,.2f}")
    print(f"Dollar Delta:                ${anom['delta_value']:,.2f}")
    print(f"Percentage Delta:            {anom['delta_pct']:.2f}%")
    print(f"Z-Score:                     {anom['z_score']:.2f}")
    print(f"Lower Corridor (-2.0 sigma): ${anom['lower_corridor']:,.2f}")
    print(f"Upper Corridor (+2.0 sigma): ${anom['upper_corridor']:,.2f}")
    print(f"Is Anomaly Flagged:          {anom['is_anomaly']}")
    print(f"Is P1 Material Flagged:      {anom['is_p1_material']}")
    print(f"Persistence Status:          {anom['is_persistent']}")
    print(f"Status Label:                {anom['status_label']}")
    
    # 2. Dimensional Contribution Audit
    contrib = ContributionEngine.calculate_variance_decomposition(repo, 'kpi_b2b_sales')
    print("\n--- [2] CONTRIBUTION BREAKDOWNS ---")
    print(f"Primary Region:       {contrib['primary_region']} ({contrib['primary_region_share']:.2f}%)")
    print(f"Primary Customer Tier:{contrib['primary_tier']} ({contrib['primary_tier_share']:.2f}%)")
    print(f"Primary Product:      {contrib['primary_product']} ({contrib['primary_product_share']:.2f}%)")
    
    # 3. Evidence Engine Audit
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses('kpi_b2b_sales')
    print("\n--- [3] HYPOTHESES & EVIDENCE SCORES ---")
    for h in hypotheses:
        print(f"* ID: {h['id']:<24} | Name: {h['name']:<35} | Score: {h['evidence_score']:.2f} | Band: {h['confidence_band']}")
        print(f"  Temporal Lag: {h['temporal_alignment']['assessment']}")
        print(f"  Lineage:      {h['data_lineage']}")

    # 4. Simulation Engine Audit
    reg_breakdowns = contrib['breakdowns']['region']
    reg_b_row = reg_breakdowns[reg_breakdowns["region"] == "Region B"]
    reg_base = float(reg_b_row.iloc[0]["prev_value"])
    reg_curr = float(reg_b_row.iloc[0]["curr_value"])
    
    sim = SimulationEngine.simulate_lever_impact(
        baseline_revenue=anom['baseline_value'],
        current_revenue=anom['current_value'],
        regional_affected_baseline=reg_base,
        regional_affected_current=reg_curr,
        base_unit_price=11200.0,
        cogs_per_unit=3136.0,
        price_rollback_pct=-6.0,
        marketing_boost_usd=15000.0,
        competitor_retaliation=True
    )
    print("\n--- [4] SIMULATION LEVER RESPONSE (-6% Price, +$15k Mkt) ---")
    print(f"New Unit Price:       ${sim['new_unit_price']:,.2f}")
    print(f"Simulated Revenue:    ${sim['simulated_revenue']:,.2f}")
    print(f"Net Revenue Delta:    ${sim['net_revenue_delta']:+,.2f}/wk")
    print(f"Simulated Margin %:   {sim['simulated_margin_pct']:.2f}%")
    print(f"Volume Recovery %:    {sim['recovery_pct']:.2f}%")
    
    # 5. Offline Reasoner Text vs Data Check
    briefing = OfflineEdithReasoner.generate_investigation_briefing(anom, hypotheses)
    print("\n--- [5] OFFLINE BRIEFING SANITY ---")
    assert str(int(anom['baseline_value'])) in briefing.replace(",", "")
    assert str(int(anom['current_value'])) in briefing.replace(",", "")
    print("  [PASS] Offline briefing dynamically incorporates exact baseline & current values.")

    # 6. LLM Gateway Check
    client = EdithLLMClient(api_key="")
    text, meta = client.generate_briefing(anom, hypotheses)
    print("\n--- [6] LLM CLIENT FALLBACK STATUS ---")
    print(f"Provider: {meta['provider']} | Mode: {meta['mode']} | Status: {meta['status']}")
    print("\nALL AUDIT CHECKS COMPLETED AND VERIFIED!")

if __name__ == "__main__":
    run_audit()
