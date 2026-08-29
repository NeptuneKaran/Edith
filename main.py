"""
main.py - EDITH (Executive Decision Intelligence & Tactical Hypothesis)
Production FastAPI Application & REST API Gateway

Provides high-performance, asynchronous REST endpoints for generic data ingestion,
automated profiling, semantic modeling, diagnostic decomposition, observational evidence,
and grounded conversational intelligence.
"""
import os
import io
import sqlite3
import tempfile
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, HTTPException, Body

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Core EDITH Analytics and AI Modules
from data.repository import DataRepository
from data.source_manager import (
    DataProfiler,
    SemanticDataModel,
    AnalysisFeasibilityChecker,
    ColumnMapper
)
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine

from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine
from ai.llm_client import EdithLLMClient
from ai.offline_reasoner import OfflineEdithReasoner
from config.personas import get_personas, get_persona, DEFAULT_PERSONA
from core.access_control import (
    scope_overview,
    scope_diagnostic,
    scope_workspace,
    scope_simulation,
    get_access_log,
    log_access
)



# ==============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ==============================================================================
app = FastAPI(
    title="EDITH Decision Intelligence Platform",
    description="Generic Business Dataset Ingestion, Empirical Root-Cause Diagnostic & Decision Assistant",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _to_json_safe(obj: Any) -> Any:
    """Recursively converts numpy/pandas types and non-serializable objects to native Python primitives."""
    if isinstance(obj, pd.DataFrame):
        return _to_json_safe(obj.fillna("").to_dict(orient="records"))
    elif isinstance(obj, pd.Series):
        return _to_json_safe(obj.to_dict())
    elif isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif obj is None:
        return None
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass
    return obj



# In-memory storage for raw uploaded file before semantic ingestion
_UPLOAD_CACHE: Dict[str, Any] = {}
_ACTIVE_SIM_LEVERS: Dict[str, Any] = {
    "price_rollback_pct": 6.0,
    "promo_fund_k": 15.0,
    "churn_mitigation": True
}



# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================
class SemanticModelRequest(BaseModel):
    dataset_name: str = "Uploaded Custom Dataset"
    analysis_grain: str = "Time Series (Weekly / Monthly / Daily)"
    primary_measure: str
    primary_measure_label: Optional[str] = None
    primary_measure_unit: Optional[str] = None
    aggregation_type: str = "sum"
    distinct_entity_column: Optional[str] = None
    date_column: Optional[str] = None
    dimension_columns: List[str] = Field(default_factory=list)
    driver_columns: List[str] = Field(default_factory=list)
    identifier_columns: List[str] = Field(default_factory=list)
    drop_invalid_rows: bool = True


class SimulationLeversRequest(BaseModel):
    price_rollback_pct: float = 6.0
    promo_fund_k: float = 15.0
    churn_mitigation: bool = True
    persona: Optional[str] = None


class ChatQueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    selected_hypothesis_id: Optional[str] = None
    simulation_levers: Optional[Dict[str, Any]] = None
    persona: Optional[str] = None


# ==============================================================================
# DATA INGESTION & CONFIGURATION ENDPOINTS
# ==============================================================================

@app.post("/api/data/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accepts CSV, Excel, or SQLite files.
    Inspects and profiles all columns, returning type guesses, null rates, cardinality, and sample rows.
    """
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        if ext in [".csv", ".txt"]:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(io.BytesIO(content))
        elif ext in [".sqlite", ".db"]:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            if not tables:
                conn.close()
                os.remove(tmp_path)
                raise HTTPException(status_code=400, detail="No readable user tables found in SQLite database.")
            
            table_name = tables[0][0]
            df = pd.read_sql_query(f"SELECT * FROM `{table_name}`", conn)
            conn.close()
            os.remove(tmp_path)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Please upload CSV (.csv), Excel (.xlsx/.xls), or SQLite (.db/.sqlite)."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file '{filename}': {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains zero rows of data.")

    # Cache raw dataframe in session memory
    _UPLOAD_CACHE["raw_df"] = df
    _UPLOAD_CACHE["filename"] = filename

    # Compute comprehensive profile
    profiles = DataProfiler.profile_dataframe(df)
    valid_numerics = DataProfiler.get_valid_numeric_columns(df)
    valid_dates = DataProfiler.get_valid_date_columns(df)

    # Safe JSON preview
    preview_df = df.head(15).copy()
    for col in preview_df.columns:
        if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
            preview_df[col] = preview_df[col].astype(str)
    preview = preview_df.fillna("").to_dict(orient="records")

    return {
        "success": True,
        "filename": filename,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "profiles": profiles,
        "valid_numeric_columns": valid_numerics,
        "valid_date_columns": valid_dates,
        "preview": preview
    }


@app.post("/api/data/profile")
async def get_data_profile():
    """Returns profile for currently uploaded raw dataframe."""
    df = _UPLOAD_CACHE.get("raw_df")
    if df is None:
        raise HTTPException(status_code=400, detail="No dataset has been uploaded yet.")
    
    profiles = DataProfiler.profile_dataframe(df)
    valid_numerics = DataProfiler.get_valid_numeric_columns(df)
    valid_dates = DataProfiler.get_valid_date_columns(df)
    
    return {
        "success": True,
        "filename": _UPLOAD_CACHE.get("filename", "custom_data"),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "profiles": profiles,
        "valid_numeric_columns": valid_numerics,
        "valid_date_columns": valid_dates
    }


@app.post("/api/data/configure")
async def configure_dataset(req: SemanticModelRequest):
    """
    Validates user semantic configuration, maps columns, checks feasibility,
    and sets the custom dataset into the active DataRepository.
    """
    df_raw = _UPLOAD_CACHE.get("raw_df")
    if df_raw is None:
        raise HTTPException(status_code=400, detail="No uploaded dataset found. Please upload a file first.")

    model = SemanticDataModel(
        dataset_name=req.dataset_name,
        analysis_grain=req.analysis_grain,
        primary_measure=req.primary_measure,
        primary_measure_label=req.primary_measure_label or req.primary_measure,
        primary_measure_unit=req.primary_measure_unit or "Units",
        aggregation_type=req.aggregation_type,
        distinct_entity_column=req.distinct_entity_column,
        date_column=req.date_column if req.date_column and req.date_column != "None (Snapshot)" else None,
        dimension_columns=req.dimension_columns,
        driver_columns=req.driver_columns,
        identifier_columns=req.identifier_columns,
        is_demo=False
    )

    try:
        tables, feat_status, warnings = ColumnMapper.transform_generic_dataset(
            df_raw, model, drop_invalid_rows=req.drop_invalid_rows
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data transformation error: {str(e)}")

    # Update active repository state
    repo = DataRepository.get_instance()
    source_info = {
        "name": req.dataset_name,
        "is_demo": False,
        "row_count": len(tables["sales"]),
        "columns": list(df_raw.columns),
        "feature_status": feat_status,
        "analysis_grain": req.analysis_grain,
        "primary_measure_label": model.primary_measure_label,
        "primary_measure_unit": model.primary_measure_unit
    }
    repo.set_custom_data(tables, source_info, model)

    # Evaluate feasibility across all 8 capabilities
    feasibility = AnalysisFeasibilityChecker.evaluate_feasibility(df_raw, model)

    return _to_json_safe({
        "success": True,
        "message": f"Successfully ingested '{req.dataset_name}' ({len(tables['sales']):,} records).",
        "source_info": source_info,
        "feasibility": feasibility,
        "warnings": warnings
    })



@app.post("/api/data/reset-demo")
async def reset_demo_dataset():
    """Resets the repository to the built-in B2B SaaS Benchmark dataset."""
    repo = DataRepository.get_instance()
    repo.reset_to_demo_dataset()
    _UPLOAD_CACHE.clear()
    return {
        "success": True,
        "message": "Reset to built-in B2B SaaS Benchmark dataset.",
        "source_info": repo.active_source_info
    }


@app.get("/api/data/source")
async def get_active_source():
    """Returns metadata for the currently active data source."""
    repo = DataRepository.get_instance()
    info = repo.active_source_info.copy()
    info["has_uploaded_cache"] = ("raw_df" in _UPLOAD_CACHE)
    if repo.semantic_model:
        info["semantic_model"] = {
            "dataset_name": repo.semantic_model.dataset_name,
            "analysis_grain": repo.semantic_model.analysis_grain,
            "primary_measure": repo.semantic_model.primary_measure,
            "primary_measure_label": repo.semantic_model.primary_measure_label,
            "primary_measure_unit": repo.semantic_model.primary_measure_unit,
            "aggregation_type": repo.semantic_model.aggregation_type,
            "distinct_entity_column": repo.semantic_model.distinct_entity_column,
            "date_column": repo.semantic_model.date_column,
            "dimension_columns": repo.semantic_model.dimension_columns,
            "driver_columns": repo.semantic_model.driver_columns
        }
    return info


# ==============================================================================
@app.get("/api/personas")
async def list_personas():
    """Returns available enterprise personas with metadata and permission profiles."""
    return _to_json_safe(get_personas())

@app.get("/api/access-log")
async def get_access_audit_log(limit: int = 50):
    """Returns recent role-based access control and scoping audit events."""
    return _to_json_safe({
        "total_logged": len(get_access_log(200)),
        "events": get_access_log(limit)
    })


# ANALYTICAL DASHBOARD ENDPOINTS
# ==============================================================================

@app.get("/api/overview")
async def get_overview(persona: Optional[str] = None):
    """
    Returns executive overview metrics:
    - Primary KPI cards (Observed, Baseline, Delta, Status)
    - Time-series trajectory / corridor points (temporal) or snapshot banner (non-temporal)
    - Primary concentration share
    - Top driver correlation association
    - Overall data health score
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    is_temporal = repo.active_source_info.get("feature_status", {}).get("is_temporal", True)
    grain = repo.active_source_info.get("analysis_grain", "Time Series")
    
    label = repo.active_source_info.get("primary_measure_label", "Gross Revenue" if is_demo else "Primary Measure")
    unit = repo.active_source_info.get("primary_measure_unit", "$" if is_demo else "Units")
    
    # 1. KPI Time Series
    ts = repo.get_kpi_time_series()
    anom_ctx = AnomalyEngine.evaluate_current_anomaly(ts, kpi_name=label)
    
    # Format time series points for chart
    ts_points = []
    if not ts.empty and is_temporal:
        corridor_df = AnomalyEngine.calculate_baseline_and_corridor(ts)
        for _, r in corridor_df.iterrows():

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

    # 2. Dimensional Concentration
    breakdowns = repo.get_dimensional_breakdown()
    top_conc = None
    if breakdowns:
        best_dim = list(breakdowns.keys())[0]
        best_df = breakdowns[best_dim]
        if not best_df.empty:
            top_row = best_df.iloc[0]
            top_conc = {
                "dimension": best_dim.replace("_", " ").title(),
                "segment": str(top_row[best_dim]),
                "share_pct": float(top_row.get("contribution_pct", 0.0)),
                "value": float(top_row.get("curr_value", 0.0))
            }

    # 3. Top Driver Correlation
    driver_data = repo.get_driver_correlations().get("correlations", {})
    top_driver = None
    if driver_data:
        sorted_drvs = sorted(
            driver_data.items(),
            key=lambda x: abs(x[1].get("pearson_r", 0.0)),
            reverse=True
        )
        if sorted_drvs:
            drv_name, drv_stats = sorted_drvs[0]
            top_driver = {
                "name": drv_name.replace("_", " ").title(),
                "pearson_r": float(drv_stats.get("pearson_r", 0.0)),
                "spearman_r": float(drv_stats.get("spearman_r", 0.0)),
                "strength": str(drv_stats.get("strength", "Moderate")),
                "direction": str(drv_stats.get("direction", "Positive"))
            }

    # 4. Data Quality
    dq = repo.get_data_quality_report()

    res_payload = {
        "dataset_name": repo.active_source_info.get("name", "EDITH Benchmark"),
        "is_demo": is_demo,
        "is_temporal": is_temporal,
        "analysis_grain": grain,
        "primary_measure_label": label,
        "primary_measure_unit": unit,
        "kpi_metrics": {
            "current_value": float(anom_ctx.get("current_value", 0.0)),
            "baseline_value": float(anom_ctx.get("baseline_value", 0.0)),
            "delta_value": float(anom_ctx.get("delta_value", 0.0)),
            "delta_pct": float(anom_ctx.get("delta_pct", 0.0)),
            "z_score": float(anom_ctx.get("z_score", 0.0)),
            "is_anomaly": bool(anom_ctx.get("is_anomaly", False)),
            "status_label": str(anom_ctx.get("status_label", "Healthy Baseline"))
        },
        "time_series": ts_points,
        "primary_concentration": top_conc,
        "top_driver": top_driver,
        "data_quality_score": float(dq.get("data_quality_score", 100.0)),
        "total_records": int(repo.active_source_info.get("row_count", len(ts)))
    }
    if persona:
        res_payload = scope_overview(res_payload, persona, repo)
    return _to_json_safe(res_payload)


@app.get("/api/diagnostic")
async def get_diagnostic(persona: Optional[str] = None):
    """
    Returns deep diagnostic decomposition:
    - Time-series corridor data (temporal) OR distribution & outlier profile (non-temporal)
    - Multi-dimensional breakdowns
    - Driver correlation matrix
    - Data quality health audit table
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    is_temporal = repo.active_source_info.get("feature_status", {}).get("is_temporal", True)
    
    label = repo.active_source_info.get("primary_measure_label", "Gross Revenue" if is_demo else "Primary Measure")
    unit = repo.active_source_info.get("primary_measure_unit", "$" if is_demo else "Units")
    
    # 1. Dimensional breakdowns
    raw_breakdowns = repo.get_dimensional_breakdown()
    breakdowns = {}
    for dim, b_df in raw_breakdowns.items():
        if not b_df.empty:
            breakdowns[dim] = b_df.fillna(0).to_dict(orient="records")

    # 2. Driver correlations
    drv_corrs = repo.get_driver_correlations().get("correlations", {})
    correlations_list = []
    for drv_col, stats in drv_corrs.items():
        correlations_list.append({
            "column": drv_col,
            "label": drv_col.replace("_", " ").title(),
            "pearson_r": float(stats.get("pearson_r", 0.0)),
            "spearman_r": float(stats.get("spearman_r", 0.0)),
            "direction": stats.get("direction", "Neutral"),
            "strength": stats.get("strength", "Low"),
            "sample_size": int(stats.get("sample_size", 0))
        })

    # 3. Distribution & Outliers (for snapshot / non-temporal data)
    dist_stats = repo.get_distribution_statistics()

    # 4. Data Quality Report
    dq_report = repo.get_data_quality_report()

    # 5. Variance Decomposition
    decomp = ContributionEngine.calculate_variance_decomposition(repo)

    res_payload = {
        "is_demo": is_demo,
        "is_temporal": is_temporal,
        "primary_measure_label": label,
        "primary_measure_unit": unit,
        "breakdowns": breakdowns,
        "driver_correlations": correlations_list,
        "distribution_stats": dist_stats,
        "data_quality_report": dq_report,
        "variance_decomposition": decomp
    }
    if persona:
        res_payload = scope_diagnostic(res_payload, persona)
    return _to_json_safe(res_payload)


@app.get("/api/workspace")
async def get_investigation_workspace(persona: Optional[str] = None):
    """
    Returns investigation findings:
    - For Built-in Demo: 8 full Causal Hypotheses with DiD, mathematical decomposition, DAG roles, and rank.
    - For Custom Datasets: Observational Findings clearly labeled as empirical associations and patterns.
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    ev_engine = EvidenceEngine(repo)
    findings = ev_engine.evaluate_all_hypotheses()
    
    decomp = ContributionEngine.calculate_variance_decomposition(repo)
    
    res_payload = {
        "is_demo": is_demo,
        "findings": findings,
        "variance_decomposition": decomp,
        "disclaimer": "" if is_demo else "Observational Integrity Notice: For custom uploaded datasets, results represent empirical concentrations, statistical associations, and distribution patterns—not confirmed causal hypotheses."
    }
    if persona:
        res_payload = scope_workspace(res_payload, persona)
    return _to_json_safe(res_payload)



@app.get("/api/simulation")
async def get_simulation(persona: Optional[str] = None):
    """
    Returns simulation state.
    Available strictly for the built-in B2B SaaS benchmark.
    Returns explicit 'unavailable' notice for custom datasets.
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    if not is_demo:
        return {
            "available": False,
            "reason": "Counterfactual policy simulation is currently restricted to calibrated econometric models (e.g., the built-in B2B SaaS benchmark). Custom uploaded datasets require structural elasticity parameterization.",
            "levers": {},
            "trajectory": []
        }
    
    # Built-in demo simulation
    res = SimulationEngine.simulate_lever_impact(
        price_rollback_pct=-abs(_ACTIVE_SIM_LEVERS["price_rollback_pct"]),
        marketing_boost_usd=_ACTIVE_SIM_LEVERS["promo_fund_k"] * 1000.0,
        competitor_retaliation=_ACTIVE_SIM_LEVERS["churn_mitigation"]
    )
    traj_df = res.get("trajectory_df", pd.DataFrame())
    trajectory = []
    for _, r in traj_df.iterrows():
        trajectory.append({
            "week_label": str(r["projection_week"]),
            "baseline_target": float(r["Baseline Target"]),
            "do_nothing_revenue": float(r["Do-Nothing Outlook"]),
            "simulated_revenue": float(r["Simulated Scenario"])
        })
    summary = {
        "new_unit_price": float(res.get("new_unit_price", 0.0)),
        "simulated_revenue": float(res.get("simulated_revenue", 0.0)),
        "simulated_margin_pct": float(res.get("simulated_margin_pct", 0.0)),
        "recovery_pct": float(res.get("recovery_pct", 0.0)),
        "net_revenue_delta": float(res.get("net_revenue_delta", 0.0))
    }
    
    res_payload = {
        "available": True,
        "levers": _ACTIVE_SIM_LEVERS,
        "trajectory": trajectory,
        "summary": summary
    }
    if persona:
        res_payload = scope_simulation(res_payload, persona)
    return _to_json_safe(res_payload)


@app.post("/api/simulation")
async def update_simulation(req: SimulationLeversRequest):
    """Updates simulation levers (demo only)."""
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    if not is_demo:
        raise HTTPException(
            status_code=400,
            detail="Counterfactual simulation is only supported on calibrated structural models (Demo dataset)."
        )
    
    _ACTIVE_SIM_LEVERS["price_rollback_pct"] = req.price_rollback_pct
    _ACTIVE_SIM_LEVERS["promo_fund_k"] = req.promo_fund_k
    _ACTIVE_SIM_LEVERS["churn_mitigation"] = req.churn_mitigation
    
    res = SimulationEngine.simulate_lever_impact(
        price_rollback_pct=-abs(req.price_rollback_pct),
        marketing_boost_usd=req.promo_fund_k * 1000.0,
        competitor_retaliation=req.churn_mitigation
    )
    traj_df = res.get("trajectory_df", pd.DataFrame())
    trajectory = []
    for _, r in traj_df.iterrows():
        trajectory.append({
            "week_label": str(r["projection_week"]),
            "baseline_target": float(r["Baseline Target"]),
            "do_nothing_revenue": float(r["Do-Nothing Outlook"]),
            "simulated_revenue": float(r["Simulated Scenario"])
        })
    summary = {
        "new_unit_price": float(res.get("new_unit_price", 0.0)),
        "simulated_revenue": float(res.get("simulated_revenue", 0.0)),
        "simulated_margin_pct": float(res.get("simulated_margin_pct", 0.0)),
        "recovery_pct": float(res.get("recovery_pct", 0.0)),
        "net_revenue_delta": float(res.get("net_revenue_delta", 0.0))
    }
    
    res_payload = {
        "success": True,
        "available": True,
        "levers": _ACTIVE_SIM_LEVERS,
        "trajectory": trajectory,
        "summary": summary
    }
    if req.persona:
        res_payload = scope_simulation(res_payload, req.persona, is_update=True, requested_levers=dict(req))
    return _to_json_safe(res_payload)



@app.post("/api/chat")
async def chat_with_edith(req: ChatQueryRequest):
    """
    Conversational assistant turn grounded in verified data.
    Uses Gemini API if key is present, otherwise falls back to 100% deterministic OfflineEdithReasoner.
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    label = repo.active_source_info.get("primary_measure_label", "Gross Revenue" if is_demo else "Primary Measure")
    
    ts = repo.get_kpi_time_series()
    anom_ctx = AnomalyEngine.evaluate_current_anomaly(ts, kpi_name=label)
    
    ev_engine = EvidenceEngine(repo)
    all_hypotheses = ev_engine.evaluate_all_hypotheses()
    
    # Resolve selected hypothesis
    selected_h = all_hypotheses[0] if all_hypotheses else {}
    if req.selected_hypothesis_id:
        for h in all_hypotheses:
            if h.get("id") == req.selected_hypothesis_id:
                selected_h = h
                break

    # Initialize Gemini client / Offline reasoner
    try:
        client = EdithLLMClient()
        answer_text, meta = client.answer_question(
            query=req.query,
            anomaly_context=anom_ctx,
            selected_hypothesis=selected_h,
            hypotheses=all_hypotheses,
            chat_history=req.chat_history or [],
            simulation_levers=req.simulation_levers or _ACTIVE_SIM_LEVERS,
            persona=req.persona
        )
    except Exception as e:
        print(f"[Chat API Exception] Falling back to reasoner: {e}")
        answer_text = OfflineEdithReasoner.answer_conversational_query(
            query=req.query,
            anomaly_context=anom_ctx,
            selected_hypothesis=selected_h,
            all_hypotheses=all_hypotheses,
            chat_history=req.chat_history or [],
            simulation_levers=req.simulation_levers or _ACTIVE_SIM_LEVERS
        )
        meta = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "status": "Active (Fallback on Error)",
            "intent": "general_inquiry",
            "error_detail": str(e)
        }

    return {
        "answer": answer_text,
        "intent": meta.get("intent", "evidence_retrieval"),
        "citations": meta.get("citations", []),
        "metadata": meta,
        "is_demo": is_demo
    }



class SetApiKeyRequest(BaseModel):
    api_key: str = Field(..., description="Google Gemini API Key")


@app.get("/api/briefing")
async def get_executive_briefing(persona: Optional[str] = None):
    """
    Generates persona-specific standing Executive Briefing report artifact.
    Works 100% offline with zero API key requirement.
    """
    p_id = persona or DEFAULT_PERSONA
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    label = repo.active_source_info.get("primary_measure_label", "Gross Revenue" if is_demo else "Primary Measure")
    
    ts = repo.get_kpi_time_series(region="Region B" if p_id == "regional_lead" else None)
    anom_ctx = AnomalyEngine.evaluate_current_anomaly(ts, kpi_name=label)
    
    ev_engine = EvidenceEngine(repo)
    all_hypotheses = ev_engine.evaluate_all_hypotheses()
    
    client = EdithLLMClient()
    briefing = client.generate_executive_briefing(
        persona=p_id,
        anomaly_context=anom_ctx,
        hypotheses=all_hypotheses,
        simulation_levers=_ACTIVE_SIM_LEVERS
    )
    
    log_access(
        persona=p_id,
        endpoint="/api/briefing",
        granted_sections=["executive_briefing_narrative", "recommended_actions_matrix", "primary_root_cause"],
        restricted_sections=["competitor_telemetry", "cross_region_lineage"] if p_id == "regional_lead" else []
    )
    
    return _to_json_safe(briefing)


@app.get("/api/ai/status")
async def get_ai_status():
    """Returns real-time AI engine status (Live Gemini Agent vs. Offline Reasoner)."""
    client = EdithLLMClient()
    has_key = bool(client.api_key and client.client)
    return {
        "has_api_key": has_key,
        "provider": "Google Gemini" if has_key else "Deterministic Analytical Engine",
        "model": client.primary_model if has_key else "OfflineEdithReasoner v2.0",
        "mode": f"Live Gemini Agent ({client.primary_model})" if has_key else "Deterministic Offline Mode (Zero-Key)",
        "badge_text": f"Live Gemini AI ({client.primary_model})" if has_key else "Deterministic Offline Mode",
        "is_live": has_key
    }


@app.post("/api/ai/key")
async def set_api_key(req: SetApiKeyRequest):
    """
    Dynamically sets and verifies the Gemini API key in process memory.
    Allows instant activation of Live Gemini AI directly from the UI without container redeployments.
    """
    clean_key = req.api_key.strip().strip("'").strip('"')
    if not clean_key:
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        return {
            "success": True,
            "message": "Switched back to Deterministic Offline Mode.",
            "is_live": False
        }
    
    try:
        from google import genai
        # Initialize and test key
        test_client = genai.Client(api_key=clean_key)
        
        # Test lightweight generation probe
        try:
            test_client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Ping"
            )
        except Exception:
            pass  # Even if probe throttles, save key
            
        os.environ["GEMINI_API_KEY"] = clean_key
        return {
            "success": True,
            "message": "Google Gemini API Key verified and activated successfully!",
            "is_live": True,
            "model": "gemini-2.0-flash",
            "provider": "Google Gemini"
        }
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "not valid" in err_msg.lower():
            raise HTTPException(status_code=400, detail="The provided Google Gemini API key is invalid. Please check your key from Google AI Studio.")
        
        os.environ["GEMINI_API_KEY"] = clean_key
        return {
            "success": True,
            "message": "API Key saved successfully.",
            "is_live": True,
            "model": "gemini-2.0-flash",
            "provider": "Google Gemini"
        }




# ==============================================================================
# STATIC FILES & SPA SERVING
# ==============================================================================

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_spa():
    """Serves the single-page application dashboard."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse(
        content={"message": "EDITH FastAPI API Server is running. frontend/index.html not found."},
        status_code=200
    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8501))
    print(f"🚀 Starting EDITH Decision Intelligence FastAPI Server on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
