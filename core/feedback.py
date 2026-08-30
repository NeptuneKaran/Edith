"""Feedback & learning-loop: hypothesis confirmation/override and action ratings."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

_FEEDBACK_LOG: List[Dict[str, Any]] = []
_MAX_ENTRIES = 200
_FEEDBACK_ID_COUNTER = 0

def submit_hypothesis_feedback(
    hypothesis_id: str,
    action: str,  # "confirmed" or "overridden"
    reason: str = "",
    persona_id: str = "executive"
) -> Dict[str, Any]:
    global _FEEDBACK_ID_COUNTER
    _FEEDBACK_ID_COUNTER += 1
    entry = {
        "id": _FEEDBACK_ID_COUNTER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "hypothesis_feedback",
        "hypothesis_id": hypothesis_id,
        "action": action,
        "reason": reason,
        "persona_id": persona_id
    }
    _FEEDBACK_LOG.insert(0, entry)
    if len(_FEEDBACK_LOG) > _MAX_ENTRIES:
        _FEEDBACK_LOG.pop()
    return entry

def submit_action_rating(
    action_id: str,
    rating: str,  # "helpful" or "not_helpful"
    persona_id: str = "executive"
) -> Dict[str, Any]:
    global _FEEDBACK_ID_COUNTER
    _FEEDBACK_ID_COUNTER += 1
    entry = {
        "id": _FEEDBACK_ID_COUNTER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "action_rating",
        "action_id": action_id,
        "rating": rating,
        "persona_id": persona_id
    }
    _FEEDBACK_LOG.insert(0, entry)
    if len(_FEEDBACK_LOG) > _MAX_ENTRIES:
        _FEEDBACK_LOG.pop()
    return entry

def get_feedback_log(limit: int = 50) -> List[Dict[str, Any]]:
    return _FEEDBACK_LOG[:limit]

def get_hypothesis_annotations(hypothesis_id: str) -> Dict[str, Any]:
    relevant = [e for e in _FEEDBACK_LOG if e.get("hypothesis_id") == hypothesis_id]
    confirmations = [e for e in relevant if e["action"] == "confirmed"]
    overrides = [e for e in relevant if e["action"] == "overridden"]
    return {
        "hypothesis_id": hypothesis_id,
        "confirmation_count": len(confirmations),
        "override_count": len(overrides),
        "overrides": [{"persona": o["persona_id"], "reason": o["reason"], "timestamp": o["timestamp"]} for o in overrides],
        "last_confirmed_by": confirmations[0]["persona_id"] if confirmations else None,
        "last_confirmed_at": confirmations[0]["timestamp"] if confirmations else None
    }

def annotate_hypotheses(hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enriches hypothesis list with feedback annotations without altering scores."""
    for h in hypotheses:
        hid = h.get("id", "")
        ann = get_hypothesis_annotations(hid)
        h["feedback_annotations"] = ann
    return hypotheses

def clear_feedback():
    global _FEEDBACK_LOG, _FEEDBACK_ID_COUNTER
    _FEEDBACK_LOG.clear()
    _FEEDBACK_ID_COUNTER = 0
