"""
data/repository.py
In-memory data access and query repository for EDITH.
Provides clean query functions for KPI time series, dimensional slices, driver signals, and control cohort evaluation.
Supports dynamic switching between 3 Calibrated Built-in Benchmarks and User-Imported (CSV, Excel, SQL) datasets.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from data.generator import generate_enterprise_dataset, generate_subscription_dataset, generate_retail_dataset

class DataRepository:
    """Singleton repository managing in-memory access to enterprise dataset tables."""
    _instance: Optional['DataRepository'] = None
    
    def __init__(self, seed: int = 42):
        self.active_benchmark_id: str = "b2b_saas_pricing"
        self.tables: Dict[str, pd.DataFrame] = generate_enterprise_dataset(seed=seed)
        self.semantic_model: Optional[Any] = None
        self.active_source_info: Dict[str, Any] = {
            "source_type": "Demo",
            "benchmark_id": "b2b_saas_pricing",
            "name": "EDITH Demo (B2B SaaS Commercial Ledger Benchmark)",
            "is_demo": True,
            "row_count": len(self.tables.get("sales", [])),
            "analysis_grain": "Weekly Series",
            "primary_measure_label": "Gross Revenue",
            "primary_measure_unit": "$",
            "description": "52-week B2B SaaS commercial ledger calibrated with pricing elasticity and competitor promotion shocks."
        }
        
    @classmethod
    def get_instance(cls, seed: int = 42) -> 'DataRepository':
        if cls._instance is None:
            cls._instance = DataRepository(seed=seed)
        return cls._instance

    def switch_benchmark(self, benchmark_id: str, seed: int = 42):
        """Switches active dataset to one of the 3 calibrated structural benchmarks."""
        self.semantic_model = None
        self.active_benchmark_id = benchmark_id
        
        if benchmark_id == "saas_churn_roas":
            self.tables = generate_subscription_dataset(seed=seed)
            self.active_source_info = {
                "source_type": "Demo",
                "benchmark_id": "saas_churn_roas",
                "name": "EDITH Demo (Subscription Growth & Retention Benchmark)",
                "is_demo": True,
                "row_count": len(self.tables.get("subscriptions_weekly", [])),
                "analysis_grain": "Multi-Cadence (Weekly / Daily / Monthly / Free-text)",
                "primary_measure_label": "Customer Churn Rate",
                "primary_measure_unit": "%",
                "description": "Multi-cadence subscription dataset featuring self-serve onboarding friction, marketing channel budget reallocation confounder, and sparse-history AI Beta tier."
            }
        elif benchmark_id == "retail_fulfillment":
            self.tables = generate_retail_dataset(seed=seed)
            self.active_source_info = {
                "source_type": "Demo",
                "benchmark_id": "retail_fulfillment",
                "name": "EDITH Demo (Regional Retail Demand & Fulfillment Benchmark)",
                "is_demo": True,
                "row_count": len(self.tables.get("store_sales_weekly", [])),
                "analysis_grain": "Multi-Cadence (Weekly / Daily / Event / Free-text)",
                "primary_measure_label": "Weekly Store Revenue",
                "primary_measure_unit": "$",
                "description": "Retail commercial dataset with competing near-tied hypotheses: supplier container freight customs delay vs extreme regional blizzard foot-traffic contraction."
            }
        elif benchmark_id == "manufacturing_quality":
            import os
            import pandas as pd
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'benchmark_datasets', 'manufacturing_quality')
            
            df_prod = pd.read_csv(os.path.join(base_dir, "production_output_daily.csv"))
            df_cal = pd.read_csv(os.path.join(base_dir, "machine_calibration_logs.csv"))
            df_mat = pd.read_csv(os.path.join(base_dir, "supplier_material_certs_weekly.csv"))
            df_roster = pd.read_csv(os.path.join(base_dir, "shift_roster_monthly.csv"))
            df_qc = pd.read_csv(os.path.join(base_dir, "qc_inspector_notes.csv"))
            df_maint = pd.read_csv(os.path.join(base_dir, "maintenance_tickets.csv"))
            
            self.tables = {
                "production_output_daily": df_prod,
                "machine_calibration_logs": df_cal,
                "supplier_material_certs_weekly": df_mat,
                "shift_roster_monthly": df_roster,
                "qc_inspector_notes": df_qc,
                "maintenance_tickets": df_maint,
                "sales": df_prod
            }
            
            self.active_source_info = {
                "source_type": "Calibrated Structural Benchmark",
                "name": "Manufacturing Quality & Supply Chain",
                "is_demo": True,
                "row_count": len(df_prod),
                "primary_measure_label": "First-Pass Yield (%)",
                "primary_measure_unit": "%",
                "analysis_grain": "Multi-Cadence (Daily / Weekly-Fiscal / Monthly / Event)",
                "benchmark_id": "manufacturing_quality",
                "feature_status": {
                    "is_temporal": True,
                    "has_multi_cadence": True,
                    "has_unstructured": True,
                    "has_fiscal_calendar": True,
                    "aggregation_type": "mean"
                }
            }
        else:
            self.active_benchmark_id = "b2b_saas_pricing"
            self.tables = generate_enterprise_dataset(seed=seed)
            self.active_source_info = {
                "source_type": "Demo",
                "benchmark_id": "b2b_saas_pricing",
                "name": "EDITH Demo (B2B SaaS Commercial Ledger Benchmark)",
                "is_demo": True,
                "row_count": len(self.tables.get("sales", [])),
                "analysis_grain": "Weekly Series",
                "primary_measure_label": "Gross Revenue",
                "primary_measure_unit": "$",
                "description": "52-week B2B SaaS commercial ledger calibrated with pricing elasticity and competitor promotion shocks."
            }

    def set_custom_data(self, tables: Dict[str, pd.DataFrame], source_info: Dict[str, Any], semantic_model: Optional[Any] = None):
        """Replaces in-memory tables with custom imported/connected business data."""
        self.tables = tables
        self.active_source_info = source_info
        self.semantic_model = semantic_model
        self.active_benchmark_id = "custom"

    def reset_to_demo(self, seed: int = 42):
        return self.reset_to_demo_dataset(seed=seed)

    def reset_to_demo_dataset(self, seed: int = 42):
        """Resets repository back to the standard built-in demo dataset (Benchmark 1)."""
        self.switch_benchmark("b2b_saas_pricing", seed=seed)

    def get_active_source_info(self) -> Dict[str, Any]:
        """Returns metadata about the active data source."""
        return self.active_source_info

    def get_semantic_model(self) -> Optional[Any]:
        """Returns the active SemanticDataModel if configured."""
        return self.semantic_model

    def get_unstructured_records(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all unstructured free-text records across active tables."""
        unstructured_keys = ["cs_call_notes", "exit_survey_comments", "supplier_emails", "customer_reviews", "feedback_notes"]
        records = []
        target_keys = [table_name] if (table_name and table_name in self.tables) else [k for k in unstructured_keys if k in self.tables]
        
        for k in target_keys:
            df = self.tables.get(k, pd.DataFrame())
            if not df.empty:
                for row in df.to_dict(orient="records"):
                    row["_source_table"] = k
                    records.append(row)
        return records

    def get_kpi_time_series(self, kpi_id: str = "kpi_b2b_sales", region: Optional[str] = None) -> pd.DataFrame:
        """Returns the time series for a specified KPI or user-configured primary measure, optionally filtered by region."""
        # 1. Custom or Generic Dataset
        if not self.active_source_info.get("is_demo", True):
            df_sales = self.tables.get("sales", pd.DataFrame())
            if df_sales.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            if region and "region" in df_sales.columns:
                df_sales = df_sales[df_sales["region"] == region]
                
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

        # 2. Benchmark 2: saas_churn_roas
        if self.active_benchmark_id == "saas_churn_roas":
            df_sub = self.tables.get("subscriptions_weekly", pd.DataFrame())
            if df_sub.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            if region and "region" in df_sub.columns:
                df_sub = df_sub[df_sub["region"] == region]
                
            if kpi_id == "kpi_marketing_roas":
                df_mkt = self.tables.get("marketing_spend_daily", pd.DataFrame())
                if not df_mkt.empty:
                    if region and "region" in df_mkt.columns:
                        df_mkt = df_mkt[df_mkt["region"] == region]
                    ts = df_mkt.groupby("week_idx").agg(
                        spend=("spend_usd", "sum"),
                        conv=("conversions", "sum")
                    ).reset_index()
                    ts["value"] = np.round((ts["conv"] * 120.0) / np.maximum(ts["spend"], 1.0), 2)
                    ts["week_label"] = [f"2025-W{i:02d}" if i <= 44 else f"2026-W{i-44:02d}" for i in ts["week_idx"]]
                    ts["week_date"] = "2026-02-22"
                    return ts[["week_idx", "week_label", "week_date", "value"]].sort_values("week_idx")
            
            if kpi_id == "kpi_customer_churn":
                ts = df_sub.groupby(["week_idx", "week_label", "week_date"]).agg(
                    cancellations=("cancellations", "sum"),
                    active=("active_subscriptions", "sum")
                ).reset_index().sort_values("week_idx")
                ts["value"] = np.round((ts["cancellations"] / np.maximum(ts["active"], 1.0)) * 100.0, 2)
                return ts[["week_idx", "week_label", "week_date", "value"]]
            else:
                ts = df_sub.groupby(["week_idx", "week_label", "week_date"]).agg(
                    value=("mrr", "sum")
                ).reset_index().sort_values("week_idx")
                return ts

        # 3. Benchmark 3: retail_fulfillment
        elif self.active_benchmark_id == "retail_fulfillment":
            df_store = self.tables.get("store_sales_weekly", pd.DataFrame())
            if df_store.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            if region and "region" in df_store.columns:
                df_store = df_store[df_store["region"] == region]
                
            if kpi_id == "kpi_stockout_rate":
                df_inv = self.tables.get("inventory_daily", pd.DataFrame())
                if not df_inv.empty:
                    if region and "region" in df_inv.columns:
                        df_inv = df_inv[df_inv["region"] == region]
                    ts = df_inv.groupby("week_idx").agg(
                        stockout_rate=("stockout_flag", "mean")
                    ).reset_index()
                    ts["value"] = np.round(ts["stockout_rate"] * 100.0, 1)
                    ts["week_label"] = [f"2025-W{i:02d}" if i <= 44 else f"2026-W{i-44:02d}" for i in ts["week_idx"]]
                    ts["week_date"] = "2026-02-22"
                    return ts[["week_idx", "week_label", "week_date", "value"]].sort_values("week_idx")
                    
            ts = df_store.groupby(["week_idx", "week_label", "week_date"]).agg(
                value=("sales_usd", "sum")
            ).reset_index().sort_values("week_idx")
            return ts

        # 4. Benchmark 4: manufacturing_quality
        elif self.active_benchmark_id == "manufacturing_quality":
            df_prod = self.tables.get("production_output_daily", pd.DataFrame())
            if df_prod.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            if region and "plant" in df_prod.columns:
                df_prod = df_prod[df_prod["plant"] == region]
            
            # Aggregate weekly yield
            df_prod_copy = df_prod.copy()
            sorted_weeks = sorted(df_prod_copy["iso_week"].unique())
            week_map = {w: i for i, w in enumerate(sorted_weeks)}
            df_prod_copy["week_idx"] = df_prod_copy["iso_week"].map(week_map)
            df_prod_copy["week_label"] = df_prod_copy["iso_week"]
            
            ts = df_prod_copy.groupby(["week_idx", "week_label"]).agg(
                units_p=("units_produced", "sum"),
                units_qc=("units_passed_qc", "sum"),
                week_date=("date", "max")
            ).reset_index().sort_values("week_idx")
            ts["value"] = (ts["units_qc"] / np.maximum(ts["units_p"], 1.0)) * 100.0
            return ts[["week_idx", "week_label", "week_date", "value"]]

        # 5. Benchmark 1: b2b_saas_pricing
        df_sales = self.tables.get("sales", pd.DataFrame())
        if df_sales.empty:
            return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            
        if region and "region" in df_sales.columns:
            df_sales = df_sales[df_sales["region"] == region]
            if df_sales.empty:
                return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])
            
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
            
        return pd.DataFrame(columns=["week_idx", "week_label", "week_date", "value"])

    def get_all_segment_time_series(self) -> pd.DataFrame:
        """Returns the full dimensional segment time series dataframe."""
        if self.active_benchmark_id == "saas_churn_roas":
            return self.tables.get("subscriptions_weekly", pd.DataFrame())
        elif self.active_benchmark_id == "retail_fulfillment":
            return self.tables.get("store_sales_weekly", pd.DataFrame())
        elif self.active_benchmark_id == "manufacturing_quality":
            df = self.tables.get("production_output_daily", pd.DataFrame()).copy()
            if not df.empty and "week_idx" not in df.columns:
                sorted_weeks = sorted(df["iso_week"].unique())
                week_map = {w: i for i, w in enumerate(sorted_weeks)}
                df["week_idx"] = df["iso_week"].map(week_map)
                df["week_label"] = df["iso_week"]
                df["week_date"] = df["date"]
            return df
        return self.tables.get("sales", pd.DataFrame())

    def get_pricing_logs(self) -> pd.DataFrame:
        return self.tables.get("pricing", pd.DataFrame())

    def get_competitor_signals(self) -> pd.DataFrame:
        return self.tables.get("competitor", pd.DataFrame())

    def get_inventory_signals(self) -> pd.DataFrame:
        return self.tables.get("inventory", self.tables.get("inventory_daily", pd.DataFrame()))

    def get_feedback_signals(self) -> pd.DataFrame:
        return self.tables.get("feedback", self.tables.get("support_tickets_monthly", pd.DataFrame()))

    def get_sparse_segments(self) -> List[Dict[str, Any]]:
        """Identifies segments with sparse historical recordings (< 8 periods)."""
        df = self.get_all_segment_time_series()
        if df.empty or "week_idx" not in df.columns:
            return []
            
        dim_cols = [c for c in ["product_tier", "product_line", "customer_tier", "region"] if c in df.columns]
        if not dim_cols:
            return []
            
        sparse = []
        for name, group in df.groupby(dim_cols):
            periods = group["week_idx"].nunique()
            if periods < 8:
                segment_label = " | ".join([f"{dim_cols[i]}: {name[i]}" for i in range(len(dim_cols))]) if isinstance(name, tuple) else f"{dim_cols[0]}: {name}"
                sparse.append({
                    "segment": segment_label,
                    "recorded_periods": periods,
                    "min_required_periods": 8,
                    "status": "INSUFFICIENT_HISTORY",
                    "reason": "Segment launched recently; statistical expected corridor disabled to avoid false confidence."
                })
        return sparse

    def get_cohort_comparison(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Calculates cohort performance between baseline (W01-W48) and current anomaly (W51)."""
        df_sales = self.get_all_segment_time_series()
        if df_sales.empty:
            return {"baseline_mean": 0.0, "current_val": 0.0, "delta_pct": 0.0, "treated_segment": "N/A", "control_segment": "N/A"}
            
        reg_target = region or "Region B"
        if self.active_benchmark_id == "retail_fulfillment":
            reg_target = region or "Region North"
            
        reg_df = df_sales[df_sales["region"] == reg_target] if "region" in df_sales.columns else df_sales
        base_df = reg_df[reg_df["week_idx"] <= 48] if "week_idx" in reg_df.columns else reg_df
        curr_df = reg_df[reg_df["week_idx"] == 51] if "week_idx" in reg_df.columns else reg_df
        
        target_col = "gross_revenue" if "gross_revenue" in reg_df.columns else ("mrr" if "mrr" in reg_df.columns else ("sales_usd" if "sales_usd" in reg_df.columns else reg_df.select_dtypes(include=[np.number]).columns[0]))
        base_mean = float(base_df[target_col].sum() / 48.0) if len(base_df) > 0 else 0.0
        curr_val = float(curr_df[target_col].sum()) if len(curr_df) > 0 else 0.0
        delta_pct = ((curr_val - base_mean) / max(1.0, base_mean)) * 100.0
        
        return {
            "baseline_mean": base_mean,
            "current_val": curr_val,
            "delta_pct": delta_pct,
            "region": reg_target,
            "treated_segment": f"{reg_target} Treated Slice",
            "control_segment": "Unexposed Control Slice"
        }

    def get_dimensional_breakdown(self, kpi_id: str = "kpi_b2b_sales", region: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Decomposes the variance across all categorical dimensions.
        Returns a Dict[str, pd.DataFrame] mapping each dimension column to its slice performance table.
        """
        df_sales = self.get_all_segment_time_series()
        if df_sales.empty:
            return {}
            
        if region and "region" in df_sales.columns:
            df_sales = df_sales[df_sales["region"] == region]
            
        target_col = "yield_pct" if "yield_pct" in df_sales.columns else ("gross_revenue" if "gross_revenue" in df_sales.columns else ("mrr" if "mrr" in df_sales.columns else ("sales_usd" if "sales_usd" in df_sales.columns else df_sales.select_dtypes(include=[np.number]).columns[0])))
        
        # Check aggregation type
        is_distinct = False
        distinct_col = None
        if self.semantic_model:
            agg_type = getattr(self.semantic_model, "aggregation_type", "sum").lower()
            if "distinct" in agg_type:
                is_distinct = True
                distinct_col = getattr(self.semantic_model, "distinct_entity_column", None) or target_col
        elif self.active_source_info.get("feature_status", {}).get("aggregation_type"):
            if "distinct" in self.active_source_info["feature_status"]["aggregation_type"].lower():
                is_distinct = True
                distinct_col = target_col

        # Check if metric is a percentage / rate (e.g. yield_pct, margin, churn_rate)
        is_rate_metric = ("yield" in target_col.lower() or "rate" in target_col.lower() or "pct" in target_col.lower() or "margin" in target_col.lower() or self.active_source_info.get("primary_measure_unit") == "%" or (self.semantic_model and getattr(self.semantic_model, "aggregation_type", "") == "mean"))

        # Identify categorical dimensions
        dim_candidates = []
        if self.semantic_model and hasattr(self.semantic_model, "dimension_columns") and self.semantic_model.dimension_columns:
            dim_candidates = [c for c in self.semantic_model.dimension_columns if c in df_sales.columns]
        if not dim_candidates:
            dim_candidates = [c for c in ["region", "customer_tier", "product_line", "product_tier", "store_category", "department", "cost_center", "location", "office_location", "plant", "line_id", "shift", "channel"] if c in df_sales.columns]
        if not dim_candidates:
            dim_candidates = df_sales.select_dtypes(include=["object", "category"]).columns.tolist()
            
        w_max = df_sales["week_idx"].max() if "week_idx" in df_sales.columns else 1
        is_snapshot = ("week_idx" not in df_sales.columns or df_sales["week_idx"].nunique() <= 1 or str(df_sales.get("week_label", pd.Series([""])).iloc[0]) in ["Snapshot", "Record-Level"])
        
        breakdowns = {}
        for dim in dim_candidates:
            if is_distinct and distinct_col and distinct_col in df_sales.columns:
                grouped = df_sales.groupby(dim)[distinct_col].nunique().reset_index()
                grouped.rename(columns={distinct_col: "current_value"}, inplace=True)
                grouped["curr_value"] = grouped["current_value"]
                grouped["baseline_value"] = grouped["current_value"]
                grouped["base_value"] = grouped["current_value"]
                grouped["delta_value"] = 0.0
                grouped["delta_pct"] = 0.0
                total_val = grouped["current_value"].sum()
                grouped["contribution_pct"] = (grouped["current_value"] / max(1.0, total_val)) * 100.0
                grouped["impact_share_pct"] = grouped["contribution_pct"]
                grouped = grouped.sort_values("current_value", ascending=False)
                breakdowns[dim] = grouped
            elif is_snapshot:
                if is_rate_metric:
                    grouped = df_sales.groupby(dim)[target_col].mean().reset_index()
                else:
                    grouped = df_sales.groupby(dim)[target_col].sum().reset_index()
                total_val = grouped[target_col].sum()
                grouped["baseline_value"] = grouped[target_col]
                grouped["base_value"] = grouped[target_col]
                grouped["current_value"] = grouped[target_col]
                grouped["curr_value"] = grouped[target_col]
                grouped["delta_value"] = 0.0
                grouped["delta_pct"] = 0.0
                grouped["contribution_pct"] = (grouped[target_col] / max(1.0, total_val)) * 100.0
                grouped["impact_share_pct"] = grouped["contribution_pct"]
                grouped = grouped.sort_values(target_col, ascending=False)
                breakdowns[dim] = grouped
            else:
                curr_slice = df_sales[df_sales["week_idx"] == w_max]
                base_slice = df_sales[df_sales["week_idx"] <= 48] if w_max >= 48 else df_sales[df_sales["week_idx"] < w_max]
                
                n_base_weeks = 48.0 if w_max >= 48 else max(1.0, float(w_max - 1))
                if is_rate_metric:
                    curr_grp = curr_slice.groupby(dim)[target_col].mean()
                    base_grp = base_slice.groupby(dim)[target_col].mean()
                else:
                    curr_grp = curr_slice.groupby(dim)[target_col].sum()
                    base_grp = base_slice.groupby(dim)[target_col].sum() / n_base_weeks
                
                all_keys = list(set(curr_grp.index).union(set(base_grp.index)))
                rows = []
                total_delta = 0.0
                for k in all_keys:
                    c_v = float(curr_grp.get(k, 0.0))
                    b_v = float(base_grp.get(k, 0.0))
                    d_v = c_v - b_v
                    total_delta += d_v
                    rows.append({
                        dim: k,
                        "current_value": c_v,
                        "curr_value": c_v,
                        "baseline_value": b_v,
                        "base_value": b_v,
                        "delta_value": d_v,
                        "delta_pct": ((c_v - b_v) / max(1.0, b_v)) * 100.0
                    })
                    
                df_dim = pd.DataFrame(rows)
                if not df_dim.empty:
                    total_neg = sum(r["delta_value"] for r in rows if r["delta_value"] < 0)
                    if total_neg < 0:
                        df_dim["contribution_pct"] = df_dim["delta_value"].apply(lambda d: round((d / total_neg) * 100.0, 1) if d < 0 else 0.0)
                    else:
                        df_dim["contribution_pct"] = (df_dim["delta_value"] / (total_delta if abs(total_delta) > 0 else 1.0)) * 100.0
                    df_dim["impact_share_pct"] = df_dim["contribution_pct"]
                    df_dim = df_dim.sort_values("delta_value", key=abs, ascending=False)
                breakdowns[dim] = df_dim
                
        return breakdowns

    def get_driver_correlations(self) -> Dict[str, Any]:
        """Calculates driver correlations across active tables."""
        df_sales = self.get_all_segment_time_series()
        if df_sales.empty:
            return {"correlations": {}}
            
        numeric_cols = df_sales.select_dtypes(include=[np.number]).columns.tolist()
        target_col = "gross_revenue" if "gross_revenue" in numeric_cols else ("mrr" if "mrr" in numeric_cols else ("sales_usd" if "sales_usd" in numeric_cols else numeric_cols[0]))
        
        driver_cols = []
        if self.semantic_model and hasattr(self.semantic_model, "driver_columns") and self.semantic_model.driver_columns:
            driver_cols = [c for c in self.semantic_model.driver_columns if c in df_sales.columns]
        if not driver_cols:
            driver_cols = [c for c in numeric_cols if c not in [target_col, "week_idx", "cogs", "gross_margin"]]
            
        corrs = {}
        for col in driver_cols:
            v1 = df_sales[col].dropna().values
            v2 = df_sales[target_col].dropna().values
            min_len = min(len(v1), len(v2))
            v1 = v1[:min_len]
            v2 = v2[:min_len]
            if min_len > 2 and np.std(v1) > 0 and np.std(v2) > 0:
                p_r = float(np.corrcoef(v1, v2)[0, 1])
                r1 = pd.Series(v1).rank().values
                r2 = pd.Series(v2).rank().values
                s_r = float(np.corrcoef(r1, r2)[0, 1]) if (len(r1) > 2 and np.std(r1) > 0 and np.std(r2) > 0) else 0.0
                p_clean = round(0.0 if np.isnan(p_r) else p_r, 3)
                s_clean = round(0.0 if np.isnan(s_r) else s_r, 3)
                corrs[col] = {
                    "pearson_r": p_clean,
                    "spearman_r": s_clean,
                    "spearman_rs": s_clean,
                    "direction": "Positive" if p_clean > 0.1 else ("Negative" if p_clean < -0.1 else "Neutral"),
                    "strength": "Strong" if abs(p_clean) > 0.6 else ("Moderate" if abs(p_clean) > 0.3 else "Weak"),
                    "sample_size": min_len
                }
        return {"correlations": corrs}

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Returns comprehensive data quality metrics across all tables in repository."""
        df_primary = self.get_all_segment_time_series()
        total_rows = len(df_primary)
        null_counts = df_primary.isnull().sum().to_dict()
        null_pcts = {k: round((v / max(1, total_rows)) * 100.0, 2) for k, v in null_counts.items()}
        duplicates = int(df_primary.duplicated().sum())
        
        return {
            "data_quality_score": 100.0 if sum(null_counts.values()) == 0 and duplicates == 0 else 94.5,
            "total_rows": total_rows,
            "null_rows": int(sum(null_counts.values())),
            "duplicate_rows": duplicates,
            "duplicate_pct": round((duplicates / max(1, total_rows)) * 100.0, 2),
            "column_null_percentages": null_pcts
        }

    def get_distribution_statistics(self) -> Dict[str, Any]:
        """Calculates distribution quantiles and outliers for primary measure."""
        df = self.get_all_segment_time_series()
        if df.empty:
            return {"count": 0, "mean": 0.0, "std": 0.0, "iqr": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "median": 0.0, "outlier_count": 0}
        target_col = "gross_revenue" if "gross_revenue" in df.columns else ("mrr" if "mrr" in df.columns else ("sales_usd" if "sales_usd" in df.columns else df.select_dtypes(include=[np.number]).columns[0]))
        vals = df[target_col].dropna().values
        
        q25, q50, q75 = np.percentile(vals, [25, 50, 75])
        iqr = q75 - q25
        outliers = vals[(vals < (q25 - 1.5 * iqr)) | (vals > (q75 + 1.5 * iqr))]
        
        return {
            "count": len(vals),
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "iqr": float(iqr),
            "p25": float(q25),
            "p50": float(q50),
            "p75": float(q75),
            "median": float(q50),
            "percentiles": {
                "P25": float(q25),
                "P50_median": float(q50),
                "P75": float(q75)
            },
            "outlier_count": len(outliers),
            "outlier_pct": round((len(outliers) / max(1, len(vals))) * 100.0, 2)
        }
