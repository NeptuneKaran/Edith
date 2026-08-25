"""
core/contribution_engine.py
Deterministic Variance Localization & Impact Concentration Engine for EDITH.
Calculates exact variance contribution shares across hierarchical dimensions (Region, Customer Tier, Product, Channel).
NOTE: This engine localizes WHERE variance is concentrated (empirical locus of effect).
It does NOT establish or claim causal mechanism, which is evaluated separately by the Evidence Engine.
"""
import pandas as pd
from typing import Dict, Any, List
from data.repository import DataRepository

class ContributionEngine:
    """Localizes dimensional variance concentrations across aggregate KPI movements."""
    
    @staticmethod
    def calculate_variance_decomposition(repo: DataRepository, kpi_id: str = "kpi_b2b_sales") -> Dict[str, Any]:
        """
        Decomposes the variance between current anomaly week (52) and pre-shock baseline (48)
        across all governed dimensions. Returns exact data-derived variance concentration shares.
        """
        breakdowns = repo.get_dimensional_breakdown(kpi_id, current_week_idx=52, prev_week_idx=48)
        
        # Identify the primary driving slice across dimensions
        primary_region = breakdowns["region"].iloc[0] # Largest drop
        primary_tier = breakdowns["customer_tier"].iloc[0]
        primary_product = breakdowns["product_line"].iloc[0]
        primary_channel = breakdowns["channel"].iloc[0]
        
        # Summary path (Concentration Trail)
        top_epicenter_path = [
            {
                "dimension": "Region",
                "segment": str(primary_region["region"]),
                "contribution_pct": float(primary_region["contribution_pct"]),
                "delta_value": float(primary_region["delta_value"]),
                "interpretation": f"Region {primary_region['region']} accounts for {float(primary_region['contribution_pct']):.1f}% of aggregate net variance."
            },
            {
                "dimension": "Customer Tier",
                "segment": str(primary_tier["customer_tier"]),
                "contribution_pct": float(primary_tier["contribution_pct"]),
                "delta_value": float(primary_tier["delta_value"]),
                "interpretation": f"Customer Tier {primary_tier['customer_tier']} accounts for {float(primary_tier['contribution_pct']):.1f}% of aggregate net variance."
            },
            {
                "dimension": "Product Line",
                "segment": str(primary_product["product_line"]),
                "contribution_pct": float(primary_product["contribution_pct"]),
                "delta_value": float(primary_product["delta_value"]),
                "interpretation": f"Product Line {primary_product['product_line']} accounts for {float(primary_product['contribution_pct']):.1f}% of aggregate net variance."
            },
            {
                "dimension": "Channel",
                "segment": str(primary_channel["channel"]),
                "contribution_pct": float(primary_channel["contribution_pct"]),
                "delta_value": float(primary_channel["delta_value"]),
                "interpretation": f"Channel {primary_channel['channel']} accounts for {float(primary_channel['contribution_pct']):.1f}% of aggregate net variance."
            }
        ]
        
        return {
            "breakdowns": breakdowns,
            "top_epicenter_path": top_epicenter_path,
            "primary_region": str(primary_region["region"]),
            "primary_region_share": float(primary_region["contribution_pct"]),
            "primary_tier": str(primary_tier["customer_tier"]),
            "primary_tier_share": float(primary_tier["contribution_pct"]),
            "primary_product": str(primary_product["product_line"]),
            "primary_product_share": float(primary_product["contribution_pct"]),
            "localization_note": "Impact Concentration localizes the empirical segment where the anomaly is concentrated. It does not establish causal origin."
        }
