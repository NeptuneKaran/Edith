"""
core/dependency_graph.py
Metric Dependency Graph & Mathematical Decomposition Engine for EDITH.

Models relationships between metrics (upstream drivers, mathematical components, external factors, downstream effects),
provides graph traversal, and executes exact mathematical identities.
"""
from typing import Dict, List, Any, Optional, Tuple
from config.semantic_contracts import METRIC_DEFINITIONS

class MetricDependencyGraph:
    """Directed acyclic dependency graph modeling enterprise metric propagation."""
    
    @staticmethod
    def get_metric(metric_id: str) -> Optional[Dict[str, Any]]:
        """Returns the definition for a governed metric node."""
        return METRIC_DEFINITIONS.get(metric_id)

    @staticmethod
    def get_upstream_drivers(target_id: str = "gross_revenue") -> List[str]:
        """Returns all upstream driver metric IDs for a target metric."""
        metric = METRIC_DEFINITIONS.get(target_id)
        if metric:
            return metric.get("upstream_drivers", [])
        return []

    @staticmethod
    def get_downstream_effects(target_id: str = "gross_revenue") -> List[str]:
        """Returns all downstream metric IDs impacted by changes to the target metric."""
        metric = METRIC_DEFINITIONS.get(target_id)
        if metric:
            return metric.get("downstream_effects", [])
        return []

    @staticmethod
    def is_downstream_effect(candidate_id: str, target_id: str = "gross_revenue") -> bool:
        """
        Determines whether a candidate metric is a downstream consequence of the target metric
        rather than an upstream causal driver.
        """
        downstream = MetricDependencyGraph.get_downstream_effects(target_id)
        if candidate_id in downstream:
            return True
        cand = METRIC_DEFINITIONS.get(candidate_id)
        if cand and cand.get("role") == "DOWNSTREAM_EFFECT":
            return True
        return False

    @staticmethod
    def get_expected_direction(target_id: str, driver_id: str) -> str:
        """
        Returns the theoretical domain direction ('+' or '-') for how driver movements impact the target.
        '+' means driver up -> target up, driver down -> target down.
        '-' means driver up -> target down (e.g. price increase reducing demand volume).
        """
        target = METRIC_DEFINITIONS.get(target_id)
        if target and "expected_direction" in target:
            return target["expected_direction"].get(driver_id, "+")
        return "+"

    @staticmethod
    def decompose_revenue(
        pre_units: float,
        post_units: float,
        pre_price: float,
        post_price: float
    ) -> Dict[str, Any]:
        """
        Executes exact mathematical revenue decomposition:
        Delta Revenue = (post_units * post_price) - (pre_units * pre_price)
        Volume Effect = (post_units - pre_units) * pre_price
        Price Effect = post_units * (post_price - pre_price)
        Identity: Delta Revenue = Volume Effect + Price Effect
        """
        pre_rev = pre_units * pre_price
        post_rev = post_units * post_price
        delta_rev = post_rev - pre_rev
        
        delta_units = post_units - pre_units
        delta_price = post_price - pre_price
        
        volume_effect = delta_units * pre_price
        price_effect = post_units * delta_price
        
        if delta_rev != 0:
            volume_share_pct = (volume_effect / delta_rev) * 100.0
            price_share_pct = (price_effect / delta_rev) * 100.0
        else:
            volume_share_pct = 0.0
            price_share_pct = 0.0
            
        interpretation = (
            f"Volume contraction ({delta_units:+,.0f} units) explains {abs(volume_share_pct):.1f}% of the gross revenue decline, "
            f"partially cushioned by +${price_effect:,.0f} from the +{(delta_price/pre_price)*100:.1f}% unit price increase on retained contracts."
        )
        
        return {
            "formula": "Revenue = Units Sold * Unit Price",
            "pre_revenue": float(pre_rev),
            "post_revenue": float(post_rev),
            "delta_revenue": float(delta_rev),
            "pre_units": float(pre_units),
            "post_units": float(post_units),
            "delta_units": float(delta_units),
            "pre_price": float(pre_price),
            "post_price": float(post_price),
            "delta_price": float(delta_price),
            "volume_effect_usd": float(volume_effect),
            "volume_share_pct": round(float(volume_share_pct), 1),
            "price_effect_usd": float(price_effect),
            "price_share_pct": round(float(price_share_pct), 1),
            "exact_reconciliation_error": round(float(abs(delta_rev - (volume_effect + price_effect))), 4),
            "interpretation": interpretation
        }
