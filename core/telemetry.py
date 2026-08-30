"""Runtime telemetry: latency, model calls, token usage, and cost tracking."""
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Documented cost assumptions (Gemini 2.0 Flash as of 2026)
GEMINI_FLASH_INPUT_COST_PER_1K = 0.000075
GEMINI_FLASH_OUTPUT_COST_PER_1K = 0.0003

_TELEMETRY_LOG: List[Dict[str, Any]] = []
_MAX_ENTRIES = 500

def record_event(
    endpoint: str,
    provider: str,  # "Google Gemini", "Deterministic Offline", "Deterministic Engine"
    latency_ms: float,
    model_calls: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    estimated_cost_usd: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Records a single telemetry event."""
    if estimated_cost_usd is None:
        if provider == "Deterministic Offline" or provider == "Deterministic Engine":
            estimated_cost_usd = 0.0
        else:
            estimated_cost_usd = (
                (prompt_tokens / 1000.0) * GEMINI_FLASH_INPUT_COST_PER_1K +
                (completion_tokens / 1000.0) * GEMINI_FLASH_OUTPUT_COST_PER_1K
            )
    
    entry = {
        "id": len(_TELEMETRY_LOG) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "provider": provider,
        "latency_ms": round(latency_ms, 1),
        "model_calls": model_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "details": details or {}
    }
    _TELEMETRY_LOG.insert(0, entry)
    if len(_TELEMETRY_LOG) > _MAX_ENTRIES:
        _TELEMETRY_LOG.pop()
    return entry

def get_telemetry(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns recent telemetry entries (newest first)."""
    return _TELEMETRY_LOG[:limit]

def get_rollup() -> Dict[str, Any]:
    """Returns aggregate telemetry statistics."""
    if not _TELEMETRY_LOG:
        return {
            "total_events": 0, "avg_latency_ms": 0.0,
            "total_estimated_cost_usd": 0.0,
            "total_model_calls": 0, "total_tokens": 0,
            "live_call_count": 0, "offline_call_count": 0,
            "engine_call_count": 0, "live_vs_offline_ratio": "N/A"
        }
    
    total = len(_TELEMETRY_LOG)
    avg_lat = sum(e["latency_ms"] for e in _TELEMETRY_LOG) / total
    total_cost = sum(e["estimated_cost_usd"] for e in _TELEMETRY_LOG)
    total_mc = sum(e["model_calls"] for e in _TELEMETRY_LOG)
    total_tok = sum(e["total_tokens"] for e in _TELEMETRY_LOG)
    live = sum(1 for e in _TELEMETRY_LOG if e["provider"] == "Google Gemini")
    offline = sum(1 for e in _TELEMETRY_LOG if e["provider"] == "Deterministic Offline")
    engine = sum(1 for e in _TELEMETRY_LOG if e["provider"] == "Deterministic Engine")
    
    return {
        "total_events": total,
        "avg_latency_ms": round(avg_lat, 1),
        "total_estimated_cost_usd": round(total_cost, 6),
        "total_model_calls": total_mc,
        "total_tokens": total_tok,
        "live_call_count": live,
        "offline_call_count": offline,
        "engine_call_count": engine,
        "live_vs_offline_ratio": f"{live}:{offline}" if (live + offline) > 0 else "N/A"
    }

def clear_telemetry():
    """Clears all telemetry entries."""
    global _TELEMETRY_LOG
    _TELEMETRY_LOG.clear()
