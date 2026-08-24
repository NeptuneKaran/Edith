"""
config/settings.py
Global configurations, weights, thresholds, and model assumptions for EDITH.
"""
from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass(frozen=True)
class EvidenceWeights:
    """Configurable weights for the deterministic composite Evidence Score formula."""
    temporal_weight: float = 0.25       # w_T: Temporal precedence & lag consistency
    effect_weight: float = 0.35         # w_E: Effect size / Difference-in-Differences vs control
    corroboration_weight: float = 0.40  # w_C: Independent supporting data signals
    contradiction_weight: float = 0.45  # w_D: Penalty weight for conflicting data observations

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

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
FALLBACK_GEMINI_MODEL = "gemini-1.5-flash"
