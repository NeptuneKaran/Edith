"""
core/baseline_engine.py
Deterministic Baseline & Anomaly Detection Engine for EDITH.
Calculates rolling robust baselines, dynamic ±2σ expected corridors, Z-scores, and materiality filters.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from config.settings import ANOMALY_THRESHOLDS

class AnomalyEngine:
    """Calculates statistical baselines and detects material anomalies on KPI time series."""
    
    @staticmethod
    def calculate_baseline_and_corridor(df: pd.DataFrame, window: int = 8, z_multiplier: float = 2.0) -> pd.DataFrame:
        """
        Computes rolling robust median baseline and dynamic ±k*sigma expected corridor using IQR scaling.
        Ensures expected corridor is purely data-derived and statistically valid.
        """
        df = df.copy().sort_values("week_idx")
        values = df["value"].values
        n = len(values)
        
        baselines = np.zeros(n)
        upper_bounds = np.zeros(n)
        lower_bounds = np.zeros(n)
        z_scores = np.zeros(n)
        is_anomaly = np.zeros(n, dtype=bool)
        
        for i in range(n):
            if i < window:
                # Early history: use expanding window
                history = values[:max(1, i+1)]
            else:
                # Rolling previous window (excluding current point to prevent leakage)
                history = values[i - window : i]
                
            median_val = float(np.median(history))
            q75, q25 = np.percentile(history, [75, 25])
            iqr = max(q75 - q25, 1e-6)
            # Robust sigma estimator: 1.349 * IQR for normal distribution
            robust_sigma = max(iqr / 1.349, float(np.std(history)), 1.0)
            
            baselines[i] = median_val
            upper_bounds[i] = median_val + z_multiplier * robust_sigma
            lower_bounds[i] = median_val - z_multiplier * robust_sigma
            
            curr_val = values[i]
            z_scores[i] = (curr_val - median_val) / robust_sigma
            
            # Anomaly condition: outside corridor
            if curr_val < lower_bounds[i] or curr_val > upper_bounds[i]:
                is_anomaly[i] = True
                
        df["baseline"] = baselines
        df["upper_corridor"] = upper_bounds
        df["lower_corridor"] = lower_bounds
        df["z_score"] = z_scores
        df["is_anomaly"] = is_anomaly
        
        return df

    @staticmethod
    def evaluate_current_anomaly(df_analyzed: pd.DataFrame, kpi_name: str = "B2B Sales") -> Dict[str, Any]:
        """
        Evaluates whether the most recent data point constitutes a Material P1 Anomaly
        against statistical significance, materiality threshold, and temporal persistence.
        """
        if df_analyzed.empty:
            return {
                "kpi_name": kpi_name,
                "current_value": 0.0,
                "baseline_value": 0.0,
                "delta_value": 0.0,
                "delta_pct": 0.0,
                "z_score": 0.0,
                "upper_corridor": 0.0,
                "lower_corridor": 0.0,
                "is_anomaly": False,
                "is_p1_material": False,
                "is_persistent": False,
                "is_temporal": False,
                "status_label": "No Data",
                "current_week_label": "N/A",
                "current_week_date": "N/A"
            }
            
        is_snapshot = len(df_analyzed) <= 1 or str(df_analyzed["week_label"].iloc[0]) in ["Snapshot", "Record-Level"] or df_analyzed["week_idx"].nunique() <= 1
        if is_snapshot:
            curr = df_analyzed.iloc[-1]
            curr_val = float(curr["value"])
            return {
                "kpi_name": kpi_name,
                "current_value": curr_val,
                "baseline_value": curr_val,
                "delta_value": 0.0,
                "delta_pct": 0.0,
                "z_score": 0.0,
                "upper_corridor": curr_val,
                "lower_corridor": curr_val,
                "is_anomaly": False,
                "is_p1_material": False,
                "is_persistent": False,
                "is_temporal": False,
                "status_label": "Cross-Sectional Snapshot",
                "current_week_label": str(curr.get("week_label", "Snapshot")),
                "current_week_date": str(curr.get("week_date", "Snapshot"))
            }

        if "baseline" not in df_analyzed.columns:
            df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_analyzed)

        curr = df_analyzed.iloc[-1]
        prev = df_analyzed.iloc[-2] if len(df_analyzed) > 1 else curr
        
        curr_val = float(curr["value"])
        baseline_val = float(curr.get("baseline", curr_val))

        delta_val = curr_val - baseline_val
        delta_pct = (delta_val / baseline_val * 100.0) if baseline_val != 0 else 0.0
        z_score = float(curr["z_score"])
        
        # Check persistence (did anomaly occur in previous period as well?)
        is_persistent = bool(curr["is_anomaly"] and prev["is_anomaly"])
        
        # Tri-partite Materiality Evaluation:
        is_stat_sig = abs(z_score) >= ANOMALY_THRESHOLDS.z_score_threshold
        is_material_pct = abs(delta_pct) >= ANOMALY_THRESHOLDS.materiality_pct_threshold
        is_material_dollar = abs(delta_val) >= ANOMALY_THRESHOLDS.materiality_dollar_threshold
        
        is_p1_anomaly = is_stat_sig and (is_material_pct or is_material_dollar)
        
        status_label = "Normal"
        if is_p1_anomaly:
            status_label = "P1 Material Anomaly" if is_persistent else "Material Anomaly (Watchlist)"
        elif is_stat_sig:
            status_label = "Statistical Outlier"
            
        return {
            "kpi_name": kpi_name,
            "current_value": curr_val,
            "baseline_value": baseline_val,
            "delta_value": delta_val,
            "delta_pct": delta_pct,
            "z_score": z_score,
            "upper_corridor": float(curr["upper_corridor"]),
            "lower_corridor": float(curr["lower_corridor"]),
            "is_anomaly": bool(curr["is_anomaly"]),
            "is_p1_material": is_p1_anomaly,
            "is_persistent": is_persistent,
            "status_label": status_label,
            "current_week_label": str(curr["week_label"]),
            "current_week_date": str(curr["week_date"])
        }
