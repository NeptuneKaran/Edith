"""
core/access_control.py
Centralized Role-Based Access Control (RBAC), Data Scoping & Audit Logging for EDITH.
Enforces genuine role-based data security and narrative depth tailored to active personas:
- executive: Company-wide figures, condensed narrative depth, no data restrictions.
- regional_lead: Region B operational scope, genuine security restrictions on company-wide totals,
                 competitor intelligence, cross-region control groups, and pricing levers.
- analyst: Unrestricted full mathematical/statistical depth and lineage.
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import copy

from config.personas import get_persona, DEFAULT_PERSONA
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine

# In-memory audit log store (stores up to 200 events)
_ACCESS_LOG: List[Dict[str, Any]] = []
_LOG_ID_COUNTER: int = 1

def log_access(
    persona: str,
    endpoint: str,
    granted_sections: List[str],
    restricted_sections: List[str],
    action: str = "READ",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Records a persona-scoped access event in the in-memory audit trail."""
    global _LOG_ID_COUNTER, _ACCESS_LOG
    
    timestamp = datetime.now(timezone.utc).isoformat()
    status = "RESTRICTED_APPLIED" if restricted_sections else "GRANTED"
    
    entry = {
        "id": _LOG_ID_COUNTER,
        "timestamp": timestamp,
        "persona": persona or DEFAULT_PERSONA,
        "endpoint": endpoint,
        "action": action,
        "status": status,
        "granted_sections": granted_sections,
        "restricted_sections": restricted_sections,
        "details": details or {}
    }
    
    _LOG_ID_COUNTER += 1
    _ACCESS_LOG.insert(0, entry)
    if len(_ACCESS_LOG) > 200:
        _ACCESS_LOG.pop()
        
    return entry

def get_access_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns recent entries from the access audit log."""
    return _ACCESS_LOG[:limit]

def clear_access_log():
    """Clears the access log (useful for testing)."""
    global _ACCESS_LOG, _LOG_ID_COUNTER
    _ACCESS_LOG.clear()
    _LOG_ID_COUNTER = 1

def get_restricted_placeholder(reason: str = "Requires Executive or Analyst access") -> Dict[str, Any]:
    """Generates a standardized restricted data placeholder."""
    return {
        "restricted": True,
        "reason": reason,
        "status": "ACCESS_DENIED_ROLE_RESTRICTION"
    }

# ==============================================================================
# SCOPING HANDLERS
# ==============================================================================

def scope_overview(payload: Dict[str, Any], persona_id: Optional[str], repo: DataRepository) -> Dict[str, Any]:
    """
    Applies persona scoping to /api/overview.
    - None / Unscoped: Returns payload 100% unmodified for backward compatibility.
    - executive / analyst: Returns company-wide figures with persona metadata.
    - regional_lead: Recomputes KPI metrics for Region B, replaces company-wide totals with restricted placeholder.
    """
    if persona_id is None:
        return payload
        
    p_meta = get_persona(persona_id)
    persona = p_meta["id"]
    scoped = copy.deepcopy(payload)
    
    if persona == "regional_lead":
        # Compute Region B specific metrics
        is_demo = repo.active_source_info.get("is_demo", True)
        if is_demo:
            ts_region = repo.get_kpi_time_series(region="Region B")
            if not ts_region.empty:
                corridor_region = AnomalyEngine.calculate_baseline_and_corridor(ts_region)
                anom_region = AnomalyEngine.evaluate_current_anomaly(corridor_region, kpi_name="Region B Revenue")
                
                # Format Region B points for chart
                ts_points = []
                for _, r in corridor_region.iterrows():
                    ts_points.append({
                        "week_idx": int(r.get("week_idx", 0)),
                        "week_label": str(r.get("week_label", f"W{int(r.get('week_idx', 0)):02d}")),
                        "week_date": str(r.get("week_date", "")),
                        "value": float(r.get("value", 0.0)),
                        "baseline": float(r.get("baseline", r.get("value", 0.0))),
                        "lower_bound": float(r.get("lower_bound", r.get("value", 0.0))),
                        "upper_bound": float(r.get("upper_bound", r.get("value", 0.0))),
                        "is_breach": bool(r.get("is_breach", False))
                    })
                
                scoped["kpi_metrics"] = {
                    "current_value": float(anom_region.get("current_value", 420000.0)),
                    "baseline_value": float(anom_region.get("baseline_value", 602200.0)),
                    "delta_value": float(anom_region.get("delta_value", -182200.0)),
                    "delta_pct": float(anom_region.get("delta_pct", -30.3)),
                    "z_score": float(anom_region.get("z_score", -2.85)),
                    "is_anomaly": bool(anom_region.get("is_anomaly", True)),
                    "status_label": "Region B Deficit Incident"
                }
                scoped["time_series"] = ts_points
                scoped["primary_measure_label"] = "Region B Enterprise Revenue"
                
        # Company-wide total is marked restricted
        scoped["company_wide_summary"] = get_restricted_placeholder("Requires Executive or Analyst access")
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "role_title": p_meta["role_title"],
            "depth": p_meta["depth"],
            "scope": "Region B Operational Scope",
            "is_restricted": True
        }
        
        log_access(
            persona=persona,
            endpoint="/api/overview",
            granted_sections=["region_b_kpi_metrics", "region_b_time_series", "regional_concentration"],
            restricted_sections=["company_wide_aggregates", "cross_region_totals"]
        )
        return scoped
        
    else: # executive or analyst
        scoped["company_wide_summary"] = {
            "restricted": False,
            "status": "ACCESS_GRANTED",
            "current_value": scoped.get("kpi_metrics", {}).get("current_value")
        }
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "role_title": p_meta["role_title"],
            "depth": p_meta["depth"],
            "scope": "Company-wide Scope",
            "is_restricted": False
        }
        log_access(
            persona=persona,
            endpoint="/api/overview",
            granted_sections=["company_wide_kpi_metrics", "company_wide_time_series", "all_concentrations", "data_quality"],
            restricted_sections=[]
        )
        return scoped


def scope_diagnostic(payload: Dict[str, Any], persona_id: Optional[str]) -> Dict[str, Any]:
    """
    Applies persona scoping to /api/diagnostic.
    - None / Unscoped: Returns payload unmodified.
    - executive / analyst: Full breakdown.
    - regional_lead: Region breakdown table displays Region B in full; non-Region B rows are replaced with restricted notices.
    """
    if persona_id is None:
        return payload
        
    p_meta = get_persona(persona_id)
    persona = p_meta["id"]
    scoped = copy.deepcopy(payload)
    
    if persona == "regional_lead":
        breakdowns = scoped.get("breakdowns", {})
        if "region" in breakdowns and isinstance(breakdowns["region"], list):
            for row in breakdowns["region"]:
                reg_name = str(row.get("region", "")).strip()
                if reg_name != "Region B":
                    row["curr_value"] = None
                    row["prev_value"] = None
                    row["delta_value"] = None
                    row["contribution_pct"] = None
                    row["restricted"] = True
                    row["reason"] = "Requires Executive or Analyst access"
                else:
                    row["restricted"] = False
                    
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "scope": "Region B Operational Scope",
            "is_restricted": True
        }
        
        log_access(
            persona=persona,
            endpoint="/api/diagnostic",
            granted_sections=["region_b_slice", "driver_correlations", "distribution_stats"],
            restricted_sections=["cross_region_breakdown_rows"]
        )
        return scoped
        
    else:
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "scope": "Company-wide Scope",
            "is_restricted": False
        }
        log_access(
            persona=persona,
            endpoint="/api/diagnostic",
            granted_sections=["all_regional_breakdowns", "tier_breakdowns", "product_breakdowns", "driver_correlations"],
            restricted_sections=[]
        )
        return scoped


def scope_workspace(payload: Dict[str, Any], persona_id: Optional[str]) -> Dict[str, Any]:
    """
    Applies persona scoping to /api/workspace.
    - None / Unscoped: Returns payload unmodified.
    - executive: Condensed/high-level hypothesis highlights.
    - analyst: Full unconstrained evidence ledger and lineage.
    - regional_lead: Restricts competitor intelligence signals and cross-region control-group comparisons.
    """
    if persona_id is None:
        return payload
        
    p_meta = get_persona(persona_id)
    persona = p_meta["id"]
    scoped = copy.deepcopy(payload)
    
    if persona == "regional_lead":
        findings = scoped.get("findings", [])
        for f in findings:
            # Mask competitor intelligence bullets in supporting/contradictory evidence
            if "supporting_evidence" in f and isinstance(f["supporting_evidence"], list):
                sanitized_ev = []
                for ev in f["supporting_evidence"]:
                    ev_lower = ev.lower()
                    if "apextech" in ev_lower or "competitor" in ev_lower or "15% discount" in ev_lower:
                        sanitized_ev.append("[RESTRICTED: Requires Executive or Analyst access] Detailed competitor pricing campaign intelligence is withheld for Regional Lead.")
                    elif "cross-region" in ev_lower or "region a" in ev_lower or "region c" in ev_lower:
                        sanitized_ev.append("[RESTRICTED: Requires Executive or Analyst access] Cross-region comparative control telemetry is withheld for Regional Lead.")
                    else:
                        sanitized_ev.append(ev)
                f["supporting_evidence"] = sanitized_ev
                
            # If hypothesis is specifically competitor campaign, restrict deep telemetry
            if f.get("id") == "H2_COMPETITOR_CAMPAIGN":
                f["competitor_telemetry"] = get_restricted_placeholder("Competitor discount index and campaign logs require Executive or Analyst access.")
                
            # Restrict cross-region control group analysis
            if "control_group_analysis" in f and f["control_group_analysis"]:
                f["control_group_analysis"] = get_restricted_placeholder("Cross-region control group comparative analysis requires Executive or Analyst access.")
                
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "scope": "Region B Operational Scope",
            "is_restricted": True
        }
        
        log_access(
            persona=persona,
            endpoint="/api/workspace",
            granted_sections=["hypotheses_ranking", "pricing_elasticity_evidence", "operational_lead_lag"],
            restricted_sections=["competitor_campaign_intelligence", "cross_region_control_cohorts"]
        )
        return scoped
        
    elif persona == "executive":
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "depth": "condensed",
            "scope": "Company-wide Scope",
            "is_restricted": False
        }
        log_access(
            persona=persona,
            endpoint="/api/workspace",
            granted_sections=["condensed_hypotheses", "top_root_cause_evidence", "executive_decision_ledger"],
            restricted_sections=[]
        )
        return scoped
        
    else: # analyst
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "depth": "full",
            "scope": "Company-wide Scope",
            "is_restricted": False
        }
        log_access(
            persona=persona,
            endpoint="/api/workspace",
            granted_sections=["full_hypothesis_ledger", "did_divergence_metrics", "all_control_cohorts", "data_lineage"],
            restricted_sections=[]
        )
        return scoped


def scope_simulation(
    payload: Dict[str, Any],
    persona_id: Optional[str],
    is_update: bool = False,
    requested_levers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Applies persona scoping to /api/simulation.
    - None / Unscoped: Returns payload unmodified.
    - executive / analyst: Full lever controls.
    - regional_lead: Price Rollback lever is locked/restricted ("Requires Executive persona"),
                     Co-Op Fund and VIP Retention remain fully accessible.
    """
    if persona_id is None:
        return payload
        
    p_meta = get_persona(persona_id)
    persona = p_meta["id"]
    scoped = copy.deepcopy(payload)
    
    if persona == "regional_lead":
        scoped["levers_access"] = {
            "price_rollback": {
                "allowed": False,
                "restricted": True,
                "reason": "Requires Executive persona (Pricing adjustments require CRO authorization)"
            },
            "promo_fund": {
                "allowed": True,
                "restricted": False,
                "reason": "Authorized for Regional Sales Lead"
            },
            "churn_mitigation": {
                "allowed": True,
                "restricted": False,
                "reason": "Authorized for Regional Sales Lead"
            }
        }
        
        # Lock price rollback to 0.0 in returned state for regional lead
        if "levers" in scoped and isinstance(scoped["levers"], dict):
            scoped["levers"]["price_rollback_pct"] = 0.0
            
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "scope": "Region B Operational Scope",
            "is_restricted": True
        }
        
        log_access(
            persona=persona,
            endpoint="/api/simulation",
            action="UPDATE" if is_update else "READ",
            granted_sections=["regional_co_op_fund_lever", "vip_retention_guard_lever", "scenario_trajectory"],
            restricted_sections=["pricing_rollback_lever"]
        )
        return scoped
        
    else: # executive or analyst
        scoped["levers_access"] = {
            "price_rollback": {"allowed": True, "restricted": False},
            "promo_fund": {"allowed": True, "restricted": False},
            "churn_mitigation": {"allowed": True, "restricted": False}
        }
        scoped["persona_context"] = {
            "persona_id": persona,
            "name": p_meta["name"],
            "scope": "Company-wide Scope",
            "is_restricted": False
        }
        log_access(
            persona=persona,
            endpoint="/api/simulation",
            action="UPDATE" if is_update else "READ",
            granted_sections=["price_rollback_lever", "regional_co_op_fund_lever", "vip_retention_guard_lever", "scenario_trajectory"],
            restricted_sections=[]
        )
        return scoped


def scope_tool_call(tool_name: str, args: Dict[str, Any], persona_id: Optional[str], result: Any) -> Any:
    """
    Applies security filters to tool calls executed during AI chat turns.
    """
    if persona_id is None:
        return result
        
    p_meta = get_persona(persona_id)
    persona = p_meta["id"]
    
    if persona == "regional_lead":
        # If tool attempts to fetch competitor signals directly
        if "competitor" in tool_name.lower():
            log_access(
                persona=persona,
                endpoint=f"tool:{tool_name}",
                action="TOOL_CALL_RESTRICTED",
                granted_sections=[],
                restricted_sections=["competitor_intelligence"]
            )
            return get_restricted_placeholder("Competitor intelligence is restricted for Regional Sales Lead role. Requires Executive or Analyst access.")
            
        # If tool is get_contribution_breakdown and asking for region
        if tool_name == "get_contribution_breakdown" and args.get("dimension", "").lower() == "region":
            if isinstance(result, dict) and "slices" in result:
                for sl in result["slices"]:
                    if sl.get("region") != "Region B":
                        sl["curr_value"] = "[RESTRICTED]"
                        sl["contribution_pct"] = "[RESTRICTED]"
                log_access(
                    persona=persona,
                    endpoint=f"tool:{tool_name}",
                    action="TOOL_CALL_SCOPED",
                    granted_sections=["region_b_slice"],
                    restricted_sections=["cross_region_slices"]
                )
                return result
                
    return result
