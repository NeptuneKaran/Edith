"""
config/settings.py
Global configurations, weights, thresholds, and model assumptions for EDITH.
"""
from dataclasses import dataclass
from typing import Dict, Any
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass(frozen=True)
class EvidenceWeights:
    """
    Configurable weights for the deterministic composite Root-Cause & Evidence Score formula (0-100 & 0-1 scales).
    Base Score = w_temp * S_temp + w_mag * S_mag + w_dir * S_dir + w_hist * S_hist + w_dep * S_dep + w_contrib * S_contrib
    Final Score = clamp(Base Score - w_counter * P_counter - w_conf * P_conf) * Q
    """
    temporal_weight: float = 0.20             # w_T: Temporal precedence & lead-time window
    magnitude_weight: float = 0.15            # w_M: Normalized deviation & effect size
    directional_weight: float = 0.15          # w_D: Domain directional compatibility
    historical_lag_weight: float = 0.20       # w_H: Lagged cross-correlation over historical window
    dependency_weight: float = 0.15           # w_G: Upstream vs Downstream metric DAG structure
    contribution_weight: float = 0.15         # w_C: Mathematical decomposition share
    
    # Penalties
    counter_evidence_penalty_weight: float = 0.50 # w_K: Direct counter-evidence / falsification penalty
    confounder_penalty_weight: float = 0.20       # w_CF: Confounding / overlapping event penalty
    pre_trend_penalty_weight: float = 0.20        # w_PT: Control group pre-trend violation penalty
    
    # Backward compatibility aliases
    prediction_weight: float = 0.30
    did_effect_weight: float = 0.25
    corroboration_weight: float = 0.25
    contradiction_penalty_weight: float = 0.50
    effect_weight: float = 0.25
    contradiction_weight: float = 0.50

@dataclass(frozen=True)
class AnomalyThresholds:
    """Configurable thresholds for anomaly detection and materiality filters."""
    z_score_threshold: float = 2.0          # Statistical standard deviation corridor multiplier (±2σ)
    materiality_pct_threshold: float = 5.0  # Minimum % deviation to be deemed material
    materiality_dollar_threshold: float = 50_000.0  # Minimum absolute dollar impact
    persistence_cycles: int = 2             # Minimum consecutive weeks breach must persist

@dataclass(frozen=True)
class SimulationAssumptions:
    """Model assumptions used in the what-if simulation workbench (clearly distinguished from data)."""
    price_elasticity_enterprise: float = -1.65  # % volume change per 1% price increase for Enterprise tier
    price_elasticity_midmarket: float = -1.10   # % volume change for Mid-Market
    marketing_response_coeff: float = 0.25      # Volume boost coefficient from targeted marketing spend
    competitor_reaction_factor: float = 0.85    # Market share retention damper under competitor active promo
    recovery_lag_weeks: int = 2                 # Lead time (weeks) before policy adjustments reflect in sales

# Central instances
EVIDENCE_WEIGHTS = EvidenceWeights()
ANOMALY_THRESHOLDS = AnomalyThresholds()
SIMULATION_ASSUMPTIONS = SimulationAssumptions()

# Confidence Classification
def classify_cause_confidence(score_100: float, role: str = "UPSTREAM_DIRECT", is_testable: bool = True) -> str:
    """Classifies candidate drivers into calibrated, intellectually honest confidence tiers."""
    if not is_testable:
        return "NOT TESTABLE (MISSING TELEMETRY)"
    if role == "DOWNSTREAM_EFFECT":
        return "DOWNSTREAM EFFECT"
    if score_100 >= 75.0:
        return "HIGH-CONFIDENCE DRIVER"
    elif score_100 >= 50.0:
        return "POSSIBLE DRIVER"
    elif score_100 >= 25.0:
        return "CORRELATED SIGNAL"
    elif score_100 > 0.0:
        return "WEAK / INSUFFICIENT EVIDENCE"
    else:
        return "REFUTED BY DATA"

# Standard Evidence Strength Bands (0.0 to 1.0 scale)
def get_confidence_band(score: float, is_testable: bool = True, role: str = "UPSTREAM_DIRECT") -> str:
    """Returns the standardized, explainable evidence strength band."""
    if not is_testable:
        return "Not Testable (Missing Telemetry)"
    if role == "DOWNSTREAM_EFFECT":
        return "Downstream Effect"
    if score >= 0.80:
        return "Strong Evidence"
    elif score >= 0.50:
        return "Moderate Evidence"
    elif score >= 0.25:
        return "Weak Evidence"
    elif score > 0.0:
        return "Insufficient Evidence"
    else:
        return "Refuted by Data"

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
FALLBACK_GEMINI_MODEL = "gemini-1.5-flash"

