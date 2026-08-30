"""
core/simulation_engine.py
Quantitative What-If Scenario Simulation Engine for EDITH.
Simulates counterfactual KPI outcomes from controllable business lever adjustments across all 3 calibrated benchmarks:
1. b2b_saas_pricing (Price rollback, regional co-op fund, VIP retention guard)
2. saas_churn_roas (Onboarding wizard rollback, marketing channel rebalance, targeted retention outreach)
3. retail_fulfillment (Expedited air freight, temporary substitute SKUs, omnichannel warehouse routing)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from config.settings import SIMULATION_ASSUMPTIONS
from data.repository import DataRepository

class SimulationEngine:
    """Calculates counterfactual recovery trajectories and financial trade-offs."""
    
    @staticmethod
    def simulate_lever_impact(
        price_rollback_pct: float = -6.0,
        promo_fund_k: Optional[float] = None,
        churn_mitigation: Optional[bool] = None,
        marketing_boost_usd: Optional[float] = None,
        competitor_retaliation: Optional[bool] = None,
        benchmark_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes the quantitative outcome of business lever adjustments tailored to the active benchmark.
        """
        repo = DataRepository.get_instance()
        active_bm = benchmark_id or repo.active_benchmark_id
        
        # Normalize parameters
        p_fund = promo_fund_k if promo_fund_k is not None else ((marketing_boost_usd / 1000.0) if marketing_boost_usd is not None else 15.0)
        c_mit = churn_mitigation if churn_mitigation is not None else (competitor_retaliation if competitor_retaliation is not None else True)
        
        if active_bm == "saas_churn_roas":
            return SimulationEngine._simulate_subscription_growth(price_rollback_pct, p_fund, c_mit)
        elif active_bm == "retail_fulfillment":
            return SimulationEngine._simulate_retail_fulfillment(price_rollback_pct, p_fund, c_mit)
        elif active_bm == "manufacturing_quality":
            return SimulationEngine._simulate_manufacturing_quality(price_rollback_pct, p_fund, c_mit)
        return SimulationEngine._simulate_b2b_pricing(price_rollback_pct, p_fund, c_mit)

    @staticmethod
    def _simulate_b2b_pricing(
        price_rollback_pct: float = -6.0,
        promo_fund_k: float = 15.0,
        churn_mitigation: bool = True
    ) -> Dict[str, Any]:
        """Simulation model for Benchmark 1: B2B SaaS Sales."""
        baseline_revenue = 1_401_300.0
        current_revenue = 1_253_600.0
        regional_affected_baseline = 380_000.0
        regional_affected_current = 232_300.0
        base_unit_price = 11_200.0
        cogs_per_unit = 3_136.0
        marketing_boost_usd = promo_fund_k * 1000.0

        # Calculate unit deficit and recovered units
        baseline_units = regional_affected_baseline / 10_000.0 # 38.0 units
        current_units = regional_affected_current / base_unit_price # 20.74 units
        unit_deficit = baseline_units - current_units # 17.26 lost units
        
        # Lever response efficiencies
        rollback_eff = min(1.0, abs(price_rollback_pct) / 12.0) # 0 to 1
        mkt_eff = min(1.0, promo_fund_k / 30.0)
        csm_eff = 0.15 if churn_mitigation else 0.0
        
        recovery_factor = (rollback_eff * 0.58) + (mkt_eff * 0.27) + csm_eff
        recovered_units = unit_deficit * recovery_factor
        simulated_regional_units = min(baseline_units, current_units + recovered_units)
        
        new_unit_price = base_unit_price * (1.0 + price_rollback_pct / 100.0)
        simulated_regional_revenue = simulated_regional_units * new_unit_price
        unaffected_revenue = max(0.0, current_revenue - regional_affected_current)
        simulated_total_revenue = unaffected_revenue + simulated_regional_revenue
        
        simulated_cogs = (simulated_regional_units * cogs_per_unit) + (unaffected_revenue * 0.28) + marketing_boost_usd
        simulated_margin_pct = ((simulated_total_revenue - simulated_cogs) / simulated_total_revenue * 100.0) if simulated_total_revenue > 0 else 0.0
        
        lost_revenue = max(1.0, baseline_revenue - current_revenue)
        recovered_revenue = max(0.0, simulated_total_revenue - current_revenue)
        recovery_pct = min(100.0, (recovered_revenue / lost_revenue) * 100.0)
        
        weeks_proj = [f"+W{i+1}" for i in range(8)]
        s_curve = 1.0 / (1.0 + np.exp(-1.2 * (np.arange(8) - 3)))
        
        trajectory_df = pd.DataFrame({
            "projection_week": weeks_proj,
            "Baseline Target": [baseline_revenue for _ in range(8)],
            "Do-Nothing Outlook": [current_revenue for _ in range(8)],
            "Simulated Scenario": [current_revenue + (simulated_total_revenue - current_revenue) * s for s in s_curve]
        })
        
        return {
            "benchmark_id": "b2b_saas_pricing",
            "metric_label": "Gross Revenue ($)",
            "new_unit_price": new_unit_price,
            "simulated_revenue": simulated_total_revenue,
            "simulated_margin_pct": round(simulated_margin_pct, 1),
            "recovery_pct": round(recovery_pct, 1),
            "net_revenue_delta": simulated_total_revenue - current_revenue,
            "levers_applied": {
                "price_rollback_pct": price_rollback_pct,
                "promo_fund_k": promo_fund_k,
                "churn_mitigation": churn_mitigation
            },
            "trajectory_df": trajectory_df
        }

    @staticmethod
    def _simulate_subscription_growth(
        onboarding_rollback_pct: float = -6.0,
        marketing_realloc_k: float = 15.0,
        csm_outreach: bool = True
    ) -> Dict[str, Any]:
        """Simulation model for Benchmark 2: Subscription Growth & Retention."""
        baseline_mrr = 420_000.0
        current_mrr = 342_000.0
        
        # Levers:
        # onboarding_rollback: rolling back confusing wizard (maps to price_rollback_pct slider)
        # marketing_realloc_k: restoring Search acquisition budget
        # csm_outreach: proactive onboarding outreach
        rollback_eff = min(1.0, abs(onboarding_rollback_pct) / 10.0) # 0 to 1
        mkt_eff = min(1.0, marketing_realloc_k / 30.0)
        csm_eff = 0.25 if csm_outreach else 0.0
        
        total_recovery_strength = (rollback_eff * 0.55) + (mkt_eff * 0.25) + csm_eff
        simulated_mrr = current_mrr + (baseline_mrr - current_mrr) * total_recovery_strength
        recovery_pct = min(100.0, total_recovery_strength * 100.0)
        
        simulated_churn_rate = 8.6 - (8.6 - 2.1) * total_recovery_strength
        
        weeks_proj = [f"+W{i+1}" for i in range(8)]
        s_curve = 1.0 / (1.0 + np.exp(-1.4 * (np.arange(8) - 2.5)))
        
        trajectory_df = pd.DataFrame({
            "projection_week": weeks_proj,
            "Baseline Target": [baseline_mrr for _ in range(8)],
            "Do-Nothing Outlook": [current_mrr for _ in range(8)],
            "Simulated Scenario": [current_mrr + (simulated_mrr - current_mrr) * s for s in s_curve]
        })
        
        return {
            "benchmark_id": "saas_churn_roas",
            "metric_label": "Monthly Recurring Revenue ($)",
            "simulated_revenue": simulated_mrr,
            "simulated_churn_rate": round(simulated_churn_rate, 2),
            "simulated_margin_pct": 74.5,
            "recovery_pct": round(recovery_pct, 1),
            "net_revenue_delta": simulated_mrr - current_mrr,
            "levers_applied": {
                "onboarding_rollback_pct": onboarding_rollback_pct,
                "marketing_realloc_k": marketing_realloc_k,
                "csm_outreach": csm_outreach
            },
            "trajectory_df": trajectory_df
        }

    @staticmethod
    def _simulate_retail_fulfillment(
        substitute_sku_pct: float = -6.0,
        expedite_freight_k: float = 15.0,
        omnichannel_routing: bool = True
    ) -> Dict[str, Any]:
        """Simulation model for Benchmark 3: Regional Retail Demand & Fulfillment."""
        baseline_sales = 210_000.0
        current_sales = 118_000.0
        
        freight_eff = min(1.0, expedite_freight_k / 25.0) * 0.45
        sub_sku_eff = min(1.0, abs(substitute_sku_pct) / 10.0) * 0.35
        omni_eff = 0.20 if omnichannel_routing else 0.0
        
        total_strength = freight_eff + sub_sku_eff + omni_eff
        simulated_sales = current_sales + (baseline_sales - current_sales) * total_strength
        recovery_pct = min(100.0, total_strength * 100.0)
        
        simulated_stockout_rate = max(2.0, 48.0 - (48.0 - 2.0) * total_strength)
        
        weeks_proj = [f"+W{i+1}" for i in range(8)]
        s_curve = 1.0 / (1.0 + np.exp(-1.1 * (np.arange(8) - 3)))
        
        trajectory_df = pd.DataFrame({
            "projection_week": weeks_proj,
            "Baseline Target": [baseline_sales for _ in range(8)],
            "Do-Nothing Outlook": [current_sales for _ in range(8)],
            "Simulated Scenario": [current_sales + (simulated_sales - current_sales) * s for s in s_curve]
        })
        
        return {
            "benchmark_id": "retail_fulfillment",
            "metric_label": "Weekly Store Revenue ($)",
            "simulated_revenue": simulated_sales,
            "simulated_stockout_rate": round(simulated_stockout_rate, 1),
            "simulated_margin_pct": 38.2,
            "recovery_pct": round(recovery_pct, 1),
            "net_revenue_delta": simulated_sales - current_sales,
            "levers_applied": {
                "substitute_sku_pct": substitute_sku_pct,
                "expedite_freight_k": expedite_freight_k,
                "omnichannel_routing": omnichannel_routing
            },
            "trajectory_df": trajectory_df
        }

    @staticmethod
    def _simulate_manufacturing_quality(
        recalibration_coverage_pct: float = -6.0,
        reject_batch_cost_k: float = 15.0,
        add_qc_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """Simulation model for Benchmark 4: Manufacturing Quality & Supply Chain."""
        baseline_yield = 96.2
        current_yield = 78.4
        
        recal_eff = min(1.0, abs(recalibration_coverage_pct) / 10.0) * 0.60
        batch_eff = min(1.0, reject_batch_cost_k / 25.0) * 0.20
        qc_eff = 0.20 if add_qc_checkpoint else 0.0
        
        total_strength = recal_eff + batch_eff + qc_eff
        simulated_yield = current_yield + (baseline_yield - current_yield) * total_strength
        recovery_pct = min(100.0, total_strength * 100.0)
        
        # Scrap cost reduction
        baseline_scrap_cost = 0.0  # No scrap at baseline
        current_scrap_cost = 45000.0  # $45k/week from maintenance tickets
        simulated_scrap_cost = max(0.0, current_scrap_cost * (1.0 - total_strength))
        
        weeks_proj = [f"+W{i+1}" for i in range(8)]
        s_curve = 1.0 / (1.0 + np.exp(-1.3 * (np.arange(8) - 2.5)))
        
        trajectory_df = pd.DataFrame({
            "projection_week": weeks_proj,
            "Baseline Target": [baseline_yield for _ in range(8)],
            "Do-Nothing Outlook": [current_yield for _ in range(8)],
            "Simulated Scenario": [current_yield + (simulated_yield - current_yield) * s for s in s_curve]
        })
        
        return {
            "benchmark_id": "manufacturing_quality",
            "metric_label": "First-Pass Yield (%)",
            "simulated_revenue": simulated_yield,  # Using yield as the primary metric
            "simulated_yield_pct": round(simulated_yield, 1),
            "simulated_scrap_cost": round(simulated_scrap_cost, 0),
            "simulated_margin_pct": round(88.0 + (total_strength * 4.0), 1),  # Manufacturing margin improves with yield
            "recovery_pct": round(recovery_pct, 1),
            "net_revenue_delta": round(simulated_yield - current_yield, 1),
            "levers_applied": {
                "recalibration_coverage_pct": recalibration_coverage_pct,
                "reject_batch_cost_k": reject_batch_cost_k,
                "add_qc_checkpoint": add_qc_checkpoint
            },
            "trajectory_df": trajectory_df
        }
