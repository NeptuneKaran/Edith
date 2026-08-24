"""
core/contribution_engine.py
Deterministic Dimensional Variance Decomposition Engine for EDITH.
Calculates exact variance contribution shares across hierarchical dimensions (Region, Customer Tier, Product, Channel).
"""
import pandas as pd
from typing import Dict, Any, List
from data.repository import DataRepository

class ContributionEngine:
    """Calculates dimensional contribution of segments to an aggregate KPI variance."""
    
    @staticmethod
    def calculate_variance_decomposition(repo: DataRepository, kpi_id: str = "kpi_b2b_sales") -> Dict[str, Any]:
        """
        Decomposes the variance between current anomaly week (52) and pre-shock baseline (48)
        across all governed dimensions. Returns exact data-derived contribution percentages.
        """
        breakdowns = repo.get_dimensional_breakdown(kpi_id, current_week_idx=52, prev_week_idx=48)
        
        # Identify the primary driving slice across dimensions
        primary_region = breakdowns["region"].iloc[0] # Largest drop
        primary_tier = breakdowns["customer_tier"].iloc[0]
        primary_product = breakdowns["product_line"].iloc[0]
        primary_channel = breakdowns["channel"].iloc[0]
        
        # Summary path
        top_epicenter_path = [
            {"dimension": "Region", "segment": str(primary_region["region"]), "contribution_pct": float(primary_region["contribution_pct"]), "delta_value": float(primary_region["delta_value"])},
            {"dimension": "Customer Tier", "segment": str(primary_tier["customer_tier"]), "contribution_pct": float(primary_tier["contribution_pct"]), "delta_value": float(primary_tier["delta_value"])},
            {"dimension": "Product Line", "segment": str(primary_product["product_line"]), "contribution_pct": float(primary_product["contribution_pct"]), "delta_value": float(primary_product["delta_value"])},
            {"dimension": "Channel", "segment": str(primary_channel["channel"]), "contribution_pct": float(primary_channel["contribution_pct"]), "delta_value": float(primary_channel["delta_value"])}
        ]
        
        return {
            "breakdowns": breakdowns,
            "top_epicenter_path": top_epicenter_path,
            "primary_region": str(primary_region["region"]),
            "primary_region_share": float(primary_region["contribution_pct"]),
            "primary_tier": str(primary_tier["customer_tier"]),
            "primary_tier_share": float(primary_tier["contribution_pct"]),
            "primary_product": str(primary_product["product_line"]),
            "primary_product_share": float(primary_product["contribution_pct"])
        }
