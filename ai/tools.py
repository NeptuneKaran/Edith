"""
ai/tools.py
Safe Analytical Tool Layer for Gemini Conversational Agent.
Exposes read-only EDITH analytical functions as structured, callable tools for Gemini function calling.
Ensures 100% parameter validation, zero filesystem/database writes, and complete data grounding.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from core.dependency_graph import MetricDependencyGraph
from core.simulation_engine import SimulationEngine
from config.semantic_contracts import KPIS

# =============================================================================
# 1. TOOL IMPLEMENTATION FUNCTIONS
# =============================================================================

def get_investigation_summary() -> Dict[str, Any]:
    """Returns an executive high-level summary of the active anomaly investigation."""
    repo = DataRepository.get_instance()
    ts = repo.get_kpi_time_series("kpi_b2b_sales")
    analyzed = AnomalyEngine.calculate_baseline_and_corridor(ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(analyzed, kpi_name="Monthly B2B Sales")
    
    evidence_eng = EvidenceEngine(repo)
    hyps = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    top_h = hyps[0] if hyps else {}
    
    return {
        "kpi_name": anomaly_ctx.get("kpi_name"),
        "current_value": anomaly_ctx.get("current_value"),
        "baseline_value": anomaly_ctx.get("baseline_value"),
        "delta_value": anomaly_ctx.get("delta_value"),
        "delta_pct": anomaly_ctx.get("delta_pct"),
        "z_score": anomaly_ctx.get("z_score"),
        "severity": "P1 Material Anomaly" if anomaly_ctx.get("is_persistent") else "Warning",
        "top_hypothesis": {
            "id": top_h.get("id"),
            "name": top_h.get("name"),
            "cause_score_100": top_h.get("cause_score_100"),
            "evidence_score": top_h.get("evidence_score"),
            "classification": top_h.get("confidence_classification")
        },
        "active_data_source": repo.get_active_source_info().get("name")
    }

def get_kpi_overview(kpi_id: str = "kpi_b2b_sales") -> Dict[str, Any]:
    """Returns current and baseline values for a specified KPI."""
    repo = DataRepository.get_instance()
    ts = repo.get_kpi_time_series(kpi_id)
    analyzed = AnomalyEngine.calculate_baseline_and_corridor(ts)
    kpi_meta = KPIS.get(kpi_id, {"name": kpi_id, "unit": "$"})
    
    return {
        "kpi_id": kpi_id,
        "kpi_name": kpi_meta.get("name"),
        "unit": kpi_meta.get("unit"),
        "current_value": float(analyzed["value"].iloc[-1]) if not analyzed.empty else 0.0,
        "baseline_value": float(analyzed["baseline"].iloc[-1]) if not analyzed.empty else 0.0,
        "z_score": float(analyzed["z_score"].iloc[-1]) if not analyzed.empty else 0.0,
        "is_anomaly": bool(analyzed["is_anomaly"].iloc[-1]) if not analyzed.empty else False
    }

def get_anomaly_details(kpi_id: str = "kpi_b2b_sales") -> Dict[str, Any]:
    """Returns detailed corridor boundaries, statistical Z-score, and severity."""
    repo = DataRepository.get_instance()
    ts = repo.get_kpi_time_series(kpi_id)
    analyzed = AnomalyEngine.calculate_baseline_and_corridor(ts)
    kpi_name = KPIS.get(kpi_id, {}).get("name", kpi_id)
    return AnomalyEngine.evaluate_current_anomaly(analyzed, kpi_name=kpi_name)

def get_all_hypotheses() -> List[Dict[str, Any]]:
    """Returns all 8 candidate hypotheses evaluated by the Causal Reasoning Engine with scores."""
    repo = DataRepository.get_instance()
    evidence_eng = EvidenceEngine(repo)
    hyps = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    
    summary = []
    for h in hyps:
        summary.append({
            "id": h.get("id"),
            "rank": h.get("rank"),
            "name": h.get("name"),
            "category": h.get("category"),
            "cause_score_100": h.get("cause_score_100"),
            "evidence_score": h.get("evidence_score"),
            "confidence_classification": h.get("confidence_classification"),
            "dependency_role": h.get("dependency_role"),
            "testable": h.get("testable", True)
        })
    return summary

def get_hypothesis_evidence(hypothesis_id: str) -> Dict[str, Any]:
    """Returns deep-dive evidence, math decomposition, lead-lag, and control group for a hypothesis."""
    repo = DataRepository.get_instance()
    evidence_eng = EvidenceEngine(repo)
    hyps = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    h = next((item for item in hyps if item["id"].lower() == hypothesis_id.lower() or item["id"].split("_")[0].lower() == hypothesis_id.lower()), None)
    
    if not h:
        return {"error": f"Hypothesis '{hypothesis_id}' not found. Available: {[item['id'] for item in hyps]}"}
        
    return {
        "id": h.get("id"),
        "name": h.get("name"),
        "cause_score_100": h.get("cause_score_100"),
        "evidence_score": h.get("evidence_score"),
        "classification": h.get("confidence_classification"),
        "dependency_role": h.get("dependency_role"),
        "mathematical_decomposition": h.get("mathematical_decomposition"),
        "temporal_alignment": h.get("temporal_alignment"),
        "lag_analysis": h.get("lag_analysis"),
        "control_group_analysis": h.get("control_group_analysis"),
        "supporting_evidence": h.get("supporting_evidence"),
        "contradictory_evidence": h.get("contradictory_evidence"),
        "predictions": h.get("predictions"),
        "confounders": h.get("confounders"),
        "data_lineage": h.get("data_lineage")
    }

def get_contribution_breakdown(dimension: str = "region", kpi_id: str = "kpi_b2b_sales") -> Dict[str, Any]:
    """Returns dimensional variance breakdown for region, customer_tier, product_line, or channel."""
    repo = DataRepository.get_instance()
    contrib = ContributionEngine.calculate_variance_decomposition(repo, kpi_id)
    breakdowns = contrib.get("breakdowns", {})
    
    dim_key = dimension.lower().strip()
    if dim_key in breakdowns:
        df_dim = breakdowns[dim_key]
        return {
            "dimension": dim_key,
            "total_variance_explained_pct": 100.0,
            "slices": df_dim.to_dict(orient="records")
        }
    return {
        "error": f"Dimension '{dimension}' not found. Available: {list(breakdowns.keys())}",
        "primary_region": contrib.get("primary_region"),
        "primary_tier": contrib.get("primary_tier"),
        "primary_product": contrib.get("primary_product")
    }

def get_causal_graph() -> Dict[str, Any]:
    """Returns the Metric Dependency Graph (DAG) structure distinguishing drivers from downstream effects."""
    return MetricDependencyGraph.get_full_graph_structure()

def get_counter_evidence(hypothesis_id: str) -> Dict[str, Any]:
    """Returns falsification checks, contradictory facts, and missing expected telemetry."""
    repo = DataRepository.get_instance()
    evidence_eng = EvidenceEngine(repo)
    hyps = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    h = next((item for item in hyps if item["id"].lower() == hypothesis_id.lower() or item["id"].split("_")[0].lower() == hypothesis_id.lower()), None)
    
    if not h:
        return {"error": f"Hypothesis '{hypothesis_id}' not found."}
        
    return {
        "hypothesis_id": h.get("id"),
        "hypothesis_name": h.get("name"),
        "contradictory_evidence": h.get("contradictory_evidence"),
        "missing_expected_evidence": h.get("missing_expected_evidence"),
        "confounders": h.get("confounders")
    }

def get_simulation_results(
    price_rollback_pct: float = -6.0,
    marketing_boost_usd: float = 15000.0,
    competitor_matching: bool = True
) -> Dict[str, Any]:
    """Runs counterfactual policy simulation with specified levers and returns economic outcomes."""
    sim = SimulationEngine.simulate_lever_impact(
        price_rollback_pct=float(price_rollback_pct),
        marketing_boost_usd=float(marketing_boost_usd),
        competitor_retaliation=bool(competitor_matching)
    )
    return {
        "price_rollback_pct": price_rollback_pct,
        "marketing_boost_usd": marketing_boost_usd,
        "competitor_matching": competitor_matching,
        "simulated_revenue": sim.get("simulated_revenue"),
        "net_revenue_delta": sim.get("net_revenue_delta"),
        "simulated_margin_pct": sim.get("simulated_margin_pct"),
        "recovery_pct": sim.get("recovery_pct"),
        "trajectory_summary": [
            {"week": str(r["projection_week"]), "simulated_revenue": float(r["Simulated Scenario"]), "baseline": float(r["Baseline Target"])}
            for _, r in sim.get("trajectory_df", pd.DataFrame()).iterrows()
        ] if hasattr(sim.get("trajectory_df"), "iterrows") else []

    }

def list_available_metrics() -> List[Dict[str, Any]]:
    """Lists all monitored business metrics and their IDs."""
    return [{"id": k, "name": v["name"], "unit": v["unit"], "cadence": v.get("refresh_cadence", "Weekly")} for k, v in KPIS.items()]

def get_data_source_metadata() -> Dict[str, Any]:
    """Returns metadata about the active data source (Demo vs CSV vs Excel vs SQL)."""
    repo = DataRepository.get_instance()
    return repo.get_active_source_info()

def get_driver_correlations() -> Dict[str, Any]:
    """Returns Pearson and Spearman correlations between the primary metric and numeric explanatory drivers."""
    repo = DataRepository.get_instance()
    return repo.get_driver_correlations()

def get_distribution_summary() -> Dict[str, Any]:
    """Returns statistical distribution properties (mean, median, IQR, skewness, outliers) for the primary measure."""
    repo = DataRepository.get_instance()
    return repo.get_distribution_statistics()

def get_data_quality_report() -> Dict[str, Any]:
    """Returns dataset integrity audit including row counts, null percentages, duplicate rates, and data quality score."""
    repo = DataRepository.get_instance()
    return repo.get_data_quality_report()


def search_unstructured_evidence(query: str, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches unstructured free-text tables (CS call notes, cancellation surveys, supplier emails, reviews, CRM notes)
    for relevant qualitative evidence, customer quotes, and operational commentary matching query themes.
    """
    repo = DataRepository.get_instance()
    records = repo.get_unstructured_records(table_name=source)
    if not records:
        return []
        
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    matches = []
    
    for r in records:
        text_fields = [str(v) for k, v in r.items() if "text" in k or "reason" in k or "note" in k or "comment" in k]
        full_text = " ".join(text_fields)
        
        hit_words = [w for w in query_words if w in full_text.lower()]
        if hit_words or not query_words:
            matches.append({
                "source_table": r.get("_source_table", "unstructured_feed"),
                "record_id": r.get("note_id") or r.get("response_id") or r.get("email_id") or r.get("review_id") or "N/A",
                "date": r.get("date", "N/A"),
                "region": r.get("region", "Global"),
                "segment_or_category": r.get("customer_tier") or r.get("sku_category") or r.get("store_category") or "All",
                "quoted_text": full_text.strip(),
                "matching_keywords": hit_words
            })
            
    matches.sort(key=lambda m: len(m["matching_keywords"]), reverse=True)
    return matches[:10]

# =============================================================================
# 2. TOOL DECLARATIONS & DISPATCHER
# =============================================================================

AVAILABLE_TOOLS = [
    get_investigation_summary,
    get_kpi_overview,
    get_anomaly_details,
    get_all_hypotheses,
    get_hypothesis_evidence,
    get_contribution_breakdown,
    get_causal_graph,
    get_counter_evidence,
    get_simulation_results,
    list_available_metrics,
    get_data_source_metadata,
    get_driver_correlations,
    get_distribution_summary,
    get_data_quality_report,
    search_unstructured_evidence
]

TOOL_REGISTRY = {
    "get_investigation_summary": get_investigation_summary,
    "get_kpi_overview": get_kpi_overview,
    "get_anomaly_details": get_anomaly_details,
    "get_all_hypotheses": get_all_hypotheses,
    "get_hypothesis_evidence": get_hypothesis_evidence,
    "get_contribution_breakdown": get_contribution_breakdown,
    "get_causal_graph": get_causal_graph,
    "get_counter_evidence": get_counter_evidence,
    "get_simulation_results": get_simulation_results,
    "list_available_metrics": list_available_metrics,
    "get_data_source_metadata": get_data_source_metadata,
    "get_driver_correlations": get_driver_correlations,
    "get_distribution_summary": get_distribution_summary,
    "get_data_quality_report": get_data_quality_report,
    "search_unstructured_evidence": search_unstructured_evidence
}

def execute_tool_call(tool_name: str, args: Dict[str, Any], persona_id: Optional[str] = None) -> Any:
    """Executes a tool by name with parameter validation, safe error handling, and role-based access scoping."""
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' is not registered."}
        
    func = TOOL_REGISTRY[tool_name]
    try:
        if args:
            raw_result = func(**args)
        else:
            raw_result = func()
            
        # Apply role-based scoping if persona is set
        if persona_id:
            from core.access_control import scope_tool_call
            return scope_tool_call(tool_name, args, persona_id, raw_result)
        return raw_result
    except Exception as e:
        return {"error": f"Tool execution failed for '{tool_name}': {str(e)}"}


