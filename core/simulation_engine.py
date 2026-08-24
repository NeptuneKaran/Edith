"""
core/simulation_engine.py
Quantitative What-If Scenario Simulation Engine for EDITH.
Simulates counterfactual KPI outcomes from controllable business lever adjustments on the affected cohort.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from config.settings import SIMULATION_ASSUMPTIONS

class SimulationEngine:
    """Calculates counterfactual recovery trajectories and financial trade-offs."""
    
    @staticmethod
    def simulate_lever_impact(
        baseline_revenue: float = 1_401_300.0,
        current_revenue: float = 1_253_600.0,
        regional_affected_baseline: float = 380_000.0,
        regional_affected_current: float = 232_300.0,
        base_unit_price: float = 11_200.0,
        cogs_per_unit: float = 3_136.0,
        price_rollback_pct: float = -6.0,       # e.g. -6% price rollback on Enterprise Alpha
        marketing_boost_usd: float = 15_000.0,  # e.g. $15,000 targeted promo
        competitor_retaliation: bool = True
    ) -> Dict[str, Any]:
        """
        Computes the quantitative outcome of business lever adjustments on the affected cohort.
        Combines parametric elasticity response with unaffected territory stability.
        """
        # Assumptions (explicitly cited)
        elasticity_p = SIMULATION_ASSUMPTIONS.price_elasticity_enterprise # -1.65
        beta_m = SIMULATION_ASSUMPTIONS.marketing_response_coeff         # 0.25
        base_m_budget = 30_000.0                                         # Base regional promo allocation
        
        # Volume response from price rollback (e.g. -6% rollback yields +9.9% volume)
        volume_delta_from_price = abs(elasticity_p) * (abs(price_rollback_pct) / 100.0) if price_rollback_pct < 0 else (elasticity_p * (price_rollback_pct / 100.0))
        
        # Volume response from marketing boost
        marketing_growth_ratio = (marketing_boost_usd / base_m_budget)
        volume_delta_from_mkt = beta_m * np.log1p(max(0, marketing_growth_ratio))
        
        # Retention / competitive factor
        comp_multiplier = 0.92 if competitor_retaliation else 1.0
        
        # Combined unit volume multiplier on the affected cohort
        net_volume_multiplier = (1.0 + volume_delta_from_price + volume_delta_from_mkt) * comp_multiplier
        
        # Starting units in affected cohort
        current_regional_units = regional_affected_current / base_unit_price
        new_unit_price = base_unit_price * (1.0 + price_rollback_pct / 100.0)
        simulated_regional_units = max(0.0, current_regional_units * net_volume_multiplier)
        
        simulated_regional_revenue = simulated_regional_units * new_unit_price
        unaffected_revenue = max(0.0, current_revenue - regional_affected_current)
        simulated_total_revenue = unaffected_revenue + simulated_regional_revenue
        
        # Financial margins
        simulated_cogs = (simulated_regional_units * cogs_per_unit) + (unaffected_revenue * 0.28) + marketing_boost_usd
        simulated_margin_pct = ((simulated_total_revenue - simulated_cogs) / simulated_total_revenue * 100.0) if simulated_total_revenue > 0 else 0.0
        
        # Recovery % of the lost revenue
        lost_revenue = max(1.0, baseline_revenue - current_revenue)
        recovered_revenue = max(0.0, simulated_total_revenue - current_revenue)
        recovery_pct = min(100.0, (recovered_revenue / lost_revenue) * 100.0)
        
        # Generate 8-week projected trajectory
        weeks_proj = [f"+W{i+1}" for i in range(8)]
        # S-curve adoption over 8 weeks
        s_curve = 1.0 / (1.0 + np.exp(-1.2 * (np.arange(8) - 3)))
        
        do_nothing_series = [current_revenue for _ in range(8)]
        baseline_series = [baseline_revenue for _ in range(8)]
        simulated_series = [current_revenue + (simulated_total_revenue - current_revenue) * s for s in s_curve]
        
        trajectory_df = pd.DataFrame({
            "projection_week": weeks_proj,
            "Baseline Target": baseline_series,
            "Do-Nothing Outlook": do_nothing_series,
            "Simulated Scenario": simulated_series
        })
        
        return {
            "new_unit_price": new_unit_price,
            "simulated_revenue": simulated_total_revenue,
            "simulated_margin_pct": simulated_margin_pct,
            "recovery_pct": recovery_pct,
            "net_revenue_delta": simulated_total_revenue - current_revenue,
            "assumptions_used": {
                "price_elasticity": elasticity_p,
                "marketing_coefficient": beta_m,
                "lead_time_weeks": SIMULATION_ASSUMPTIONS.recovery_lag_weeks
            },
            "trajectory_df": trajectory_df
        }
