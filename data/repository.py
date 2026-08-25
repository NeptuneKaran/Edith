"""
data/repository.py
In-memory data access and query repository for EDITH.
Provides clean query functions for KPI time series, dimensional slices, driver signals, and control cohort evaluation.
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from data.generator import generate_enterprise_dataset

class DataRepository:
    """Singleton repository managing in-memory access to enterprise dataset tables."""
    _instance: Optional['DataRepository'] = None
    
    def __init__(self, seed: int = 42):
        self.tables: Dict[str, pd.DataFrame] = generate_enterprise_dataset(seed=seed)
        
    @classmethod
    def get_instance(cls, seed: int = 42) -> 'DataRepository':
        if cls._instance is None:
            cls._instance = DataRepository(seed=seed)
        return cls._instance

    def get_kpi_time_series(self, kpi_id: str) -> pd.DataFrame:
        """Returns the 52-week aggregate time series for a specified KPI."""
        df_sales = self.tables["sales"]
        
        if kpi_id == "kpi_b2b_sales":
            ts = df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                value=("gross_revenue", "sum")
            ).reset_index().sort_values("week_idx")
            return ts
        
        elif kpi_id == "kpi_gross_margin":
            ts = df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                rev=("gross_revenue", "sum"),
                margin=("gross_margin", "sum")
            ).reset_index().sort_values("week_idx")
            ts["value"] = (ts["margin"] / ts["rev"]) * 100.0
            return ts[["week_idx", "week_label", "week_date", "value"]]
            
        elif kpi_id == "kpi_customer_churn":
            weeks = df_sales[["week_idx", "week_label", "week_date"]].drop_duplicates().sort_values("week_idx")
            import numpy as np
            np.random.seed(42)
            churn_values = np.random.normal(2.1, 0.08, len(weeks))
            weeks = weeks.copy()
            weeks["value"] = churn_values
            return weeks
            
        elif kpi_id == "kpi_marketing_roas":
            weeks = df_sales[["week_idx", "week_label", "week_date"]].drop_duplicates().sort_values("week_idx")
            import numpy as np
            np.random.seed(43)
            roas_values = np.random.normal(4.18, 0.12, len(weeks))
            weeks = weeks.copy()
            weeks["value"] = roas_values
            return weeks
            
        else:
            raise ValueError(f"Unknown KPI: {kpi_id}")

    def get_dimensional_breakdown(self, kpi_id: str, current_week_idx: int = 52, prev_week_idx: int = 48) -> Dict[str, pd.DataFrame]:
        """
        Returns the dimensional variance breakdown between current anomaly week (52)
        and pre-shock baseline week (48) across Region, Customer Tier, Product Line, and Channel.
        """
        df = self.tables["sales"]
        df_curr = df[df["week_idx"] == current_week_idx]
        df_prev = df[df["week_idx"] == prev_week_idx]
        
        breakdowns = {}
        dimensions = ["region", "customer_tier", "product_line", "channel"]
        
        for dim in dimensions:
            curr_agg = df_curr.groupby(dim)["gross_revenue"].sum().reset_index(name="curr_value")
            prev_agg = df_prev.groupby(dim)["gross_revenue"].sum().reset_index(name="prev_value")
            merged = pd.merge(prev_agg, curr_agg, on=dim, how="outer").fillna(0)
            merged["delta_value"] = merged["curr_value"] - merged["prev_value"]
            total_drop = merged["delta_value"].sum()
            merged["contribution_pct"] = (merged["delta_value"] / total_drop * 100.0) if total_drop != 0 else 0.0
            merged = merged.sort_values("delta_value", ascending=True) # Largest drops first
            breakdowns[dim] = merged
            
        return breakdowns

    def get_cohort_comparison(self, region: str = "Region B", product: str = "Product Suite Alpha") -> pd.DataFrame:
        """
        Returns weekly revenue comparison between treated cohort (Enterprise) vs control cohort (Mid-Market).
        """
        df = self.tables["sales"]
        cohort = df[(df["region"] == region) & (df["product_line"] == product)]
        pivoted = cohort.groupby(["week_idx", "week_label", "customer_tier"])["gross_revenue"].sum().unstack().reset_index()
        return pivoted

    def get_all_segment_time_series(self) -> pd.DataFrame:
        """Returns 52-week weekly revenue aggregated by (region, customer_tier, product_line, week_idx)."""
        df_sales = self.tables["sales"]
        return df_sales.groupby(["region", "customer_tier", "product_line", "week_idx", "week_label", "week_date"]).agg(
            gross_revenue=("gross_revenue", "sum"),
            units_sold=("units_sold", "sum"),
            avg_unit_price=("unit_price", "mean")
        ).reset_index()

    def get_feedback_signals(self, region: str = "Region B") -> pd.DataFrame:
        """Returns customer complaint time series."""
        return self.tables["feedback"][self.tables["feedback"]["region"] == region]

    def get_inventory_signals(self, region: str = "Region B", product: str = "Product Suite Alpha") -> pd.DataFrame:
        """Returns inventory fill rate time series."""
        inv = self.tables["inventory"]
        return inv[(inv["region"] == region) & (inv["product_line"] == product)]

    def get_competitor_signals(self, region: str = "Region B") -> pd.DataFrame:
        """Returns competitor pricing index and campaign logs."""
        comp = self.tables["competitor"]
        return comp[comp["region"] == region]

    def get_pricing_logs(self) -> pd.DataFrame:
        """Returns the pricing changes history audit table."""
        return self.tables["pricing"]
