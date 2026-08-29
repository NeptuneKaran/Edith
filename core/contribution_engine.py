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
        Decomposes the variance across all governed dimensions. Returns exact data-derived variance concentration shares.
        """
        breakdowns = repo.get_dimensional_breakdown(kpi_id)
        if not breakdowns:
            return {
                "breakdowns": {},
                "top_epicenter_path": [],
                "primary_region": "All",
                "primary_region_share": 100.0,
                "primary_tier": "All",
                "primary_tier_share": 100.0,
                "primary_product": "All",
                "primary_product_share": 100.0,
                "localization_note": "No categorical dimensions mapped for variance decomposition."
            }
            
        top_epicenter_path = []
        primary_dim_name = ""
        primary_dim_val = "All"
        primary_dim_share = 100.0
        
        for dim_name, df_dim in breakdowns.items():
            if df_dim.empty:
                continue
            # Largest contributor is at the top
            top_row = df_dim.iloc[0]
            seg_val = str(top_row[dim_name])
            contrib_pct = float(top_row.get("contribution_pct", 0.0))
            delta_val = float(top_row.get("delta_value", 0.0))
            
            top_epicenter_path.append({
                "dimension": dim_name.replace("_", " ").title(),
                "segment": seg_val,
                "contribution_pct": contrib_pct,
                "delta_value": delta_val,
                "interpretation": f"{dim_name.replace('_', ' ').title()} '{seg_val}' accounts for {contrib_pct:.1f}% of aggregate net variance."
            })
            
            if not primary_dim_name:
                primary_dim_name = dim_name
                primary_dim_val = seg_val
                primary_dim_share = contrib_pct

        # Backward compatibility aliases for B2B demo views
        reg_df = breakdowns.get("region")
        primary_region = str(reg_df.iloc[0]["region"]) if (reg_df is not None and not reg_df.empty and "region" in reg_df.columns) else primary_dim_val
        primary_region_share = float(reg_df.iloc[0]["contribution_pct"]) if (reg_df is not None and not reg_df.empty and "contribution_pct" in reg_df.columns) else primary_dim_share

        tier_df = breakdowns.get("customer_tier")
        primary_tier = str(tier_df.iloc[0]["customer_tier"]) if (tier_df is not None and not tier_df.empty and "customer_tier" in tier_df.columns) else "General"
        primary_tier_share = float(tier_df.iloc[0]["contribution_pct"]) if (tier_df is not None and not tier_df.empty and "contribution_pct" in tier_df.columns) else 100.0

        prod_df = breakdowns.get("product_line")
        primary_product = str(prod_df.iloc[0]["product_line"]) if (prod_df is not None and not prod_df.empty and "product_line" in prod_df.columns) else "Primary"
        primary_product_share = float(prod_df.iloc[0]["contribution_pct"]) if (prod_df is not None and not prod_df.empty and "contribution_pct" in prod_df.columns) else 100.0

        return {
            "breakdowns": breakdowns,
            "top_epicenter_path": top_epicenter_path,
            "primary_dimension_name": primary_dim_name,
            "primary_dimension_val": primary_dim_val,
            "primary_dimension_share": primary_dim_share,
            "primary_region": primary_region,
            "primary_region_share": primary_region_share,
            "primary_tier": primary_tier,
            "primary_tier_share": primary_tier_share,
            "primary_product": primary_product,
            "primary_product_share": primary_product_share,
            "localization_note": "Impact Concentration localizes the empirical segment where the variance is concentrated. It indicates an observed locus of effect, not proven causation."
        }

