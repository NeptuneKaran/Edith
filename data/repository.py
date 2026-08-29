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
        self.semantic_model: Optional[Any] = None
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

    def set_custom_data(self, tables: Dict[str, pd.DataFrame], source_info: Dict[str, Any], semantic_model: Optional[Any] = None):
        """Replaces in-memory tables with custom imported/connected business data."""
        self.tables = tables
        self.active_source_info = source_info
        self.semantic_model = semantic_model

    def reset_to_demo_dataset(self, seed: int = 42):
        """Resets repository back to the standard built-in demo dataset."""
        self.tables = generate_enterprise_dataset(seed=seed)
        self.semantic_model = None
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

    def get_semantic_model(self) -> Optional[Any]:
        """Returns the active SemanticDataModel if configured."""
        return self.semantic_model

    def get_kpi_time_series(self, kpi_id: str = "kpi_b2b_sales", region: Optional[str] = None) -> pd.DataFrame:
        """Returns the time series for a specified KPI or user-configured primary measure, optionally filtered by region."""
        df_sales = self.tables.get("sales", pd.DataFrame())
        if df_sales.empty:
            return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            
        if region and "region" in df_sales.columns:
            df_sales = df_sales[df_sales["region"] == region]
            if df_sales.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            
        if kpi_id == "kpi_b2b_sales" or not self.active_source_info.get("is_demo", True):
            # Check aggregation type if custom semantic model is active
            agg_type = "sum"
            if self.semantic_model and hasattr(self.semantic_model, "aggregation_type"):
                agg_type = self.semantic_model.aggregation_type.lower()
            elif self.active_source_info.get("feature_status", {}).get("aggregation_type"):
                agg_type = self.active_source_info["feature_status"]["aggregation_type"].lower()
                
            if "distinct" in agg_type:
                target_col = self.semantic_model.distinct_entity_column if (self.semantic_model and self.semantic_model.distinct_entity_column and self.semantic_model.distinct_entity_column in df_sales.columns) else "gross_revenue"
                ts = df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                    value=(target_col, "nunique")
                ).reset_index().sort_values("week_idx")
                return ts
                
            agg_func = "sum"
            if "mean" in agg_type or "avg" in agg_type or "average" in agg_type:
                agg_func = "mean"
            elif "count" in agg_type:
                agg_func = "count"
            elif "min" in agg_type:
                agg_func = "min"
            elif "max" in agg_type:
                agg_func = "max"
                
            ts = df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                value=("gross_revenue", agg_func)
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
            return df_sales.groupby(["week_idx", "week_label", "week_date"]).agg(
                value=("gross_revenue", "sum")
            ).reset_index().sort_values("week_idx")

    def get_dimensional_breakdown(self, kpi_id: str = "kpi_b2b_sales", current_week_idx: Optional[int] = None, prev_week_idx: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Returns dimensional variance breakdown across all governed/mapped dimensions.
        Works seamlessly for both time-series datasets and snapshot cross-sections.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty:
            return {}
            
        # Determine active dimensions list
        dimensions = []
        if self.semantic_model and self.semantic_model.dimension_columns:
            dimensions = [d for d in self.semantic_model.dimension_columns if d in df.columns]
        elif self.active_source_info.get("feature_status", {}).get("mapped_dimensions"):
            dimensions = [d for d in self.active_source_info["feature_status"]["mapped_dimensions"] if d in df.columns]
            
        if not dimensions:
            dimensions = [d for d in ["region", "customer_tier", "product_line", "channel"] if d in df.columns]
            
        # Determine primary measure column
        val_col = "gross_revenue" if "gross_revenue" in df.columns else (df.select_dtypes(include=[np.number]).columns[0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else "")
        if not val_col:
            return {}
            
        is_temporal = self.active_source_info.get("feature_status", {}).get("is_temporal", True)
        if self.semantic_model and any(kw in self.semantic_model.analysis_grain.lower() for kw in ["snapshot", "cross-sectional", "record", "event"]):
            is_temporal = False

        max_week = df["week_idx"].max() if "week_idx" in df.columns else 1
        min_week = df["week_idx"].min() if "week_idx" in df.columns else 1
        
        breakdowns = {}
        
        agg_type = "sum"
        if self.semantic_model and hasattr(self.semantic_model, "aggregation_type"):
            agg_type = self.semantic_model.aggregation_type.lower()

        # If temporal variation exists (multiple weeks)
        if is_temporal and max_week > min_week:
            curr_idx = current_week_idx if current_week_idx is not None else max_week
            prev_idx = prev_week_idx if prev_week_idx is not None else max(min_week, max_week - 4)
            
            df_curr = df[df["week_idx"] == curr_idx]
            df_prev = df[df["week_idx"] == prev_idx]
            
            for dim in dimensions:
                if "distinct" in agg_type:
                    target_col = self.semantic_model.distinct_entity_column if (self.semantic_model and self.semantic_model.distinct_entity_column and self.semantic_model.distinct_entity_column in df.columns) else val_col
                    curr_agg = df_curr.groupby(dim)[target_col].nunique().reset_index(name="curr_value")
                    prev_agg = df_prev.groupby(dim)[target_col].nunique().reset_index(name="prev_value")
                elif "mean" in agg_type or "avg" in agg_type:
                    curr_agg = df_curr.groupby(dim)[val_col].mean().reset_index(name="curr_value")
                    prev_agg = df_prev.groupby(dim)[val_col].mean().reset_index(name="prev_value")
                else:
                    curr_agg = df_curr.groupby(dim)[val_col].sum().reset_index(name="curr_value")
                    prev_agg = df_prev.groupby(dim)[val_col].sum().reset_index(name="prev_value")
                    
                merged = pd.merge(prev_agg, curr_agg, on=dim, how="outer").fillna(0)
                merged["delta_value"] = merged["curr_value"] - merged["prev_value"]
                total_drop = merged["delta_value"].sum()
                merged["contribution_pct"] = (merged["delta_value"] / total_drop * 100.0) if total_drop != 0 else (100.0 / max(1, len(merged)))
                merged = merged.sort_values("delta_value", ascending=True)
                breakdowns[dim] = merged

        else:
            # Snapshot / Non-temporal mode: Aggregate categories based on configured aggregation type
            agg_type = "sum"
            if self.semantic_model and hasattr(self.semantic_model, "aggregation_type"):
                agg_type = self.semantic_model.aggregation_type.lower()
                
            for dim in dimensions:
                if "distinct" in agg_type:
                    target_col = self.semantic_model.distinct_entity_column if (self.semantic_model and self.semantic_model.distinct_entity_column and self.semantic_model.distinct_entity_column in df.columns) else val_col
                    agg = df.groupby(dim)[target_col].nunique().reset_index()
                    agg.columns = [dim, "curr_value"]
                    overall_total = float(df[target_col].nunique())
                    agg["prev_value"] = overall_total / max(1, len(agg))
                    agg["delta_value"] = agg["curr_value"] - agg["prev_value"]
                    agg["contribution_pct"] = (agg["curr_value"] / max(1.0, overall_total) * 100.0) if overall_total > 0 else 0.0
                elif "mean" in agg_type or "avg" in agg_type:
                    agg = df.groupby(dim)[val_col].agg(["mean", "count"]).reset_index()
                    agg.columns = [dim, "curr_value", "record_count"]
                    overall_mean = float(df[val_col].mean())
                    agg["prev_value"] = overall_mean
                    agg["delta_value"] = agg["curr_value"] - overall_mean
                    sum_abs_diff = (agg["curr_value"] - overall_mean).abs().sum()
                    agg["contribution_pct"] = ((agg["curr_value"] - overall_mean).abs() / max(1e-6, sum_abs_diff) * 100.0) if sum_abs_diff > 0 else (100.0 / len(agg))
                else:
                    agg = df.groupby(dim)[val_col].agg(["sum", "mean", "count"]).reset_index()
                    agg.columns = [dim, "curr_value", "mean_value", "record_count"]
                    overall_sum = float(agg["curr_value"].sum())
                    agg["prev_value"] = overall_sum / max(1, len(agg))
                    agg["delta_value"] = agg["curr_value"] - agg["prev_value"]
                    agg["contribution_pct"] = (agg["curr_value"] / overall_sum * 100.0) if overall_sum != 0 else 0.0
                    
                agg = agg.sort_values("curr_value", ascending=False).reset_index(drop=True)
                breakdowns[dim] = agg
                
        return breakdowns


    def get_driver_correlations(self) -> Dict[str, Any]:
        """
        Calculates empirical correlation matrix and pairwise associations
        between primary measure and all configured numeric drivers.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty:
            return {"correlations": {}, "summary": "No data available."}
            
        val_col = "gross_revenue"
        drivers = []
        if self.semantic_model and self.semantic_model.driver_columns:
            drivers = [d for d in self.semantic_model.driver_columns if d in df.columns]
        elif self.active_source_info.get("feature_status", {}).get("mapped_drivers"):
            drivers = [d for d in self.active_source_info["feature_status"]["mapped_drivers"] if d in df.columns]
            
        if not drivers:
            drivers = [d for d in ["unit_price", "units_sold", "spend", "clicks", "defects", "downtime_minutes", "resolution_hours"] if d in df.columns]
            
        if not drivers or val_col not in df.columns:
            return {"correlations": {}, "summary": "No numeric explanatory drivers configured."}
            
        correlations = {}
        for drv in drivers:
            try:
                valid = df[[val_col, drv]].dropna()
                if len(valid) >= 3 and valid[val_col].std() > 0 and valid[drv].std() > 0:
                    r_pearson = float(valid[val_col].corr(valid[drv]))
                    r_spearman = float(valid[val_col].rank().corr(valid[drv].rank()))
                    if np.isnan(r_pearson):
                        r_pearson = 0.0
                    if np.isnan(r_spearman):
                        r_spearman = 0.0

                    
                    strength = "negligible"
                    abs_r = abs(r_pearson)
                    if abs_r >= 0.7:
                        strength = "strong"
                    elif abs_r >= 0.4:
                        strength = "moderate"
                    elif abs_r >= 0.2:
                        strength = "weak"
                        
                    direction = "positive" if r_pearson > 0 else "negative"
                    
                    correlations[drv] = {
                        "driver": drv,
                        "pearson_r": round(r_pearson, 3),
                        "spearman_r": round(r_spearman, 3),
                        "strength": strength,
                        "direction": direction,
                        "interpretation": f"Observed {strength} {direction} association with primary measure (r = {r_pearson:+.2f}). Note: association indicates an empirical pattern, not proven causation."
                    }
            except Exception:
                continue
                
        return {
            "correlations": correlations,
            "drivers_evaluated": list(correlations.keys()),
            "total_drivers": len(correlations)
        }

    def get_distribution_statistics(self) -> Dict[str, Any]:
        """
        Calculates comprehensive parametric and non-parametric distribution statistics,
        percentiles, IQR corridor boundaries, and empirical outlier records for the primary measure.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty or "gross_revenue" not in df.columns:
            return {}
            
        series = df["gross_revenue"].dropna()
        if series.empty:
            return {}
            
        mean_val = float(series.mean())
        std_val = float(series.std()) if len(series) > 1 else 0.0
        median_val = float(series.median())
        q25 = float(series.quantile(0.25))
        q75 = float(series.quantile(0.75))
        iqr = max(q75 - q25, 1e-6)
        
        # Outlier boundaries
        lower_iqr = q25 - 1.5 * iqr
        upper_iqr = q75 + 1.5 * iqr
        outliers_iqr = df[(df["gross_revenue"] < lower_iqr) | (df["gross_revenue"] > upper_iqr)]
        
        skewness = float(series.skew()) if len(series) > 2 else 0.0
        
        return {
            "count": len(series),
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "median": round(median_val, 2),
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "iqr": round(iqr, 2),
            "skewness": round(skewness, 2),
            "lower_iqr_threshold": round(lower_iqr, 2),
            "upper_iqr_threshold": round(upper_iqr, 2),
            "outlier_count": len(outliers_iqr),
            "outlier_pct": round(len(outliers_iqr) / max(1, len(series)) * 100.0, 1),
            "p10": round(float(series.quantile(0.10)), 2),
            "p50": round(median_val, 2),
            "p90": round(float(series.quantile(0.90)), 2),
            "p99": round(float(series.quantile(0.99)), 2)
        }

    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        Generates complete data quality, schema integrity, and missingness audit report.
        """
        df_raw = self.tables.get("raw", self.tables.get("sales", pd.DataFrame()))
        if df_raw.empty:
            return {"status": "Empty Dataset"}
            
        n_rows = len(df_raw)
        n_cols = len(df_raw.columns)
        n_dupes = int(df_raw.duplicated().sum())
        
        col_audit = {}
        for c in df_raw.columns:
            s = df_raw[c]
            null_cnt = int(s.isnull().sum())
            col_audit[str(c)] = {
                "dtype": str(s.dtype),
                "null_count": null_cnt,
                "null_pct": round(null_cnt / max(1, n_rows) * 100.0, 1),
                "unique_count": int(s.nunique())
            }
            
        overall_null_cells = int(df_raw.isnull().sum().sum())
        total_cells = max(1, n_rows * n_cols)
        quality_score = max(0.0, 100.0 - (overall_null_cells / total_cells * 100.0) - (n_dupes / max(1, n_rows) * 50.0))
        
        return {
            "total_rows": n_rows,
            "total_columns": n_cols,
            "duplicate_rows": n_dupes,
            "overall_null_cells": overall_null_cells,
            "overall_completeness_pct": round(100.0 - (overall_null_cells / total_cells * 100.0), 1),
            "data_quality_score": round(quality_score, 1),
            "columns": col_audit
        }

    def get_cohort_comparison(self, region: str = "Region B", product: str = "Product Suite Alpha") -> pd.DataFrame:
        """
        Returns weekly comparison between primary cohorts across dimensions.
        """
        df = self.tables.get("sales", pd.DataFrame())
        if df.empty:
            return pd.DataFrame(columns=["week_idx", "week_label", "Cohort A", "Cohort B"])
            
        dim_col = "customer_tier" if "customer_tier" in df.columns else (self.semantic_model.dimension_columns[0] if (self.semantic_model and self.semantic_model.dimension_columns) else df.columns[0])
        val_col = "gross_revenue"
        
        if dim_col in df.columns and df[dim_col].nunique() > 1:
            pivoted = df.groupby(["week_idx", "week_label", dim_col])[val_col].sum().unstack().reset_index().fillna(0)
            return pivoted
        else:
            ts = df.groupby(["week_idx", "week_label"])[val_col].sum().reset_index()
            ts["Cohort A"] = ts[val_col]
            return ts

    def get_all_segment_time_series(self) -> pd.DataFrame:
        """Returns weekly metric aggregated by segment dimensions."""
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

