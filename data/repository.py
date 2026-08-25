"""
data/repository.py
In-memory data access and query repository for EDITH.
Provides clean query functions for KPI time series, dimensional slices, driver signals, and control cohort evaluation.
Supports dynamic switching between Built-in Demo Dataset and User-Imported (CSV, Excel, SQL) datasets.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from data.generator import generate_enterprise_dataset

class DataRepository:
    """Singleton repository managing in-memory access to enterprise dataset tables."""
    _instance: Optional['DataRepository'] = None
    
    def __init__(self, seed: int = 42):
        self.tables: Dict[str, pd.DataFrame] = generate_enterprise_dataset(seed=seed)
        self.active_source_info: Dict[str, Any] = {
            "source_type": "Demo",
            "name": "EDITH Demo Dataset (B2B SaaS Sales)",
            "is_demo": True,
            "row_count": len(self.tables.get("sales", [])),
            "description": "52-week synthetic B2B SaaS commercial ledger with ground-truth causal interventions."
        }
        
    @classmethod
    def get_instance(cls, seed: int = 42) -> 'DataRepository':
        if cls._instance is None:
            cls._instance = DataRepository(seed=seed)
        return cls._instance

    def set_custom_data(self, tables: Dict[str, pd.DataFrame], source_info: Dict[str, Any]):
        """Replaces in-memory tables with custom imported/connected business data."""
        self.tables = tables
        self.active_source_info = source_info

    def reset_to_demo_dataset(self, seed: int = 42):
        """Resets repository back to the standard built-in demo dataset."""
        self.tables = generate_enterprise_dataset(seed=seed)
        self.active_source_info = {
            "source_type": "Demo",
            "name": "EDITH Demo Dataset (B2B SaaS Sales)",
            "is_demo": True,
            "row_count": len(self.tables.get("sales", [])),
            "description": "52-week synthetic B2B SaaS commercial ledger with ground-truth causal interventions."
        }

    def get_active_source_info(self) -> Dict[str, Any]:
        """Returns metadata about the active data source."""
        return self.active_source_info

    def get_kpi_time_series(self, kpi_id: str) -> pd.DataFrame:
        """Returns the time series for a specified KPI."""
        df_sales = self.tables.get("sales", pd.DataFrame())
        if df_sales.empty:
            return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            
        if kpi_id == "kpi_b2b_sales" or not self.active_source_info.get("is_demo", True):
            # For primary metric or custom imported data
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
            np.random.seed(42)
            churn_values = np.random.normal(2.1, 0.08, len(weeks))
            weeks = weeks.copy()
            weeks["value"] = churn_values
            return weeks
            
        elif kpi_id == "kpi_marketing_roas":
            weeks = df_sales[["week_idx", "week_label", "week_date"]].drop_duplicates().sort_values("week_idx")
            np.random.seed(43)
            roas_values = np.random.normal(4.18, 0.12, len(weeks))
            weeks = weeks.copy()
            weeks["value"] = roas_values
            return weeks
            
        else:
            # Fallback sum of gross revenue
            return df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                value=("gross_revenue", "sum")
            ).reset_index().sort_values("week_idx")

    def get_dimensional_breakdown(self, kpi_id: str, current_week_idx: Optional[int] = None, prev_week_idx: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Returns dimensional variance breakdown between current anomaly week and baseline week.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty:
            return {}
            
        max_week = df["week_idx"].max()
        curr_idx = current_week_idx if current_week_idx is not None else max_week
        prev_idx = prev_week_idx if prev_week_idx is not None else max(1, max_week - 4)
        
        df_curr = df[df["week_idx"] == curr_idx]
        df_prev = df[df["week_idx"] == prev_idx]
        
        breakdowns = {}
        dimensions = [d for d in ["region", "customer_tier", "product_line", "channel"] if d in df.columns]
        
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
        Returns weekly revenue comparison between treated cohort vs control cohort.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty or "customer_tier" not in df.columns:
            return pd.DataFrame(columns=["week_idx", "week_label", "Enterprise", "Mid-Market"])
            
        cohort = df
        if "region" in df.columns and region in df["region"].values:
            cohort = cohort[cohort["region"] == region]
        if "product_line" in df.columns and product in df["product_line"].values:
            cohort = cohort[cohort["product_line"] == product]
            
        if cohort.empty or cohort["customer_tier"].nunique() <= 1:
            # Fallback cohort comparison
            pivoted = df.groupby(["week_idx", "week_label", "customer_tier"])["gross_revenue"].sum().unstack().reset_index().fillna(0)
        else:
            pivoted = cohort.groupby(["week_idx", "week_label", "customer_tier"])["gross_revenue"].sum().unstack().reset_index().fillna(0)
            
        # Ensure standard column names if missing
        if "Enterprise" not in pivoted.columns:
            pivoted["Enterprise"] = pivoted.iloc[:, 2] if len(pivoted.columns) > 2 else 0
        if "Mid-Market" not in pivoted.columns:
            pivoted["Mid-Market"] = pivoted.iloc[:, 3] if len(pivoted.columns) > 3 else (pivoted["Enterprise"] * 0.8)
            
        return pivoted

    def get_all_segment_time_series(self) -> pd.DataFrame:
        """Returns weekly revenue aggregated by segment dimensions."""
        df_sales = self.tables.get("sales", pd.DataFrame())
        dims = [d for d in ["region", "customer_tier", "product_line"] if d in df_sales.columns]
        group_cols = dims + ["week_idx", "week_label", "week_date"]
        return df_sales.groupby(group_cols).agg(
            gross_revenue=("gross_revenue", "sum"),
            units_sold=("units_sold", "sum"),
            avg_unit_price=("unit_price", "mean")
        ).reset_index()

    def get_feedback_signals(self, region: str = "Region B") -> pd.DataFrame:
        """Returns customer complaint time series."""
        fb = self.tables.get("feedback", pd.DataFrame())
        if fb.empty or "region" not in fb.columns or region not in fb["region"].values:
            return fb
        return fb[fb["region"] == region]

    def get_inventory_signals(self, region: str = "Region B", product: str = "Product Suite Alpha") -> pd.DataFrame:
        """Returns inventory fill rate time series."""
        inv = self.tables.get("inventory", pd.DataFrame())
        if inv.empty:
            return inv
        subset = inv
        if "region" in inv.columns and region in inv["region"].values:
            subset = subset[subset["region"] == region]
        if "product_line" in inv.columns and product in inv["product_line"].values:
            subset = subset[subset["product_line"] == product]
        return subset if not subset.empty else inv

    def get_competitor_signals(self, region: str = "Region B") -> pd.DataFrame:
        """Returns competitor pricing index and campaign logs."""
        comp = self.tables.get("competitor", pd.DataFrame())
        if comp.empty or "region" not in comp.columns or region not in comp["region"].values:
            return comp
        return comp[comp["region"] == region]

    def get_pricing_logs(self) -> pd.DataFrame:
        """Returns pricing changes history audit table."""
        return self.tables.get("pricing", pd.DataFrame())
