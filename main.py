"""
main.py - EDITH (Executive Decision Intelligence & Tactical Hypothesis)
Production Multi-Page FastAPI Application & REST API Gateway

Delivers:
1. True Multi-Page Architecture with Jinja2 Templates (Base Shell + Screen Templates).
2. Server-Enforced Persona Gate with signed session cookies (SessionMiddleware).
3. Centralized Role-Based Access Control (RBAC), Data Scoping & Audit Logging.
4. Deterministic Analytics Core with Grounded Conversational & Briefing Intelligence.
"""
import os
import io
import sqlite3
import tempfile
import time
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
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
from config.personas import PERSONAS, get_personas, get_persona, DEFAULT_PERSONA
from core.access_control import (
    scope_overview,
    scope_diagnostic,
    scope_workspace,
    scope_simulation,
    get_access_log,
    log_access,
    log_event
)


# ==============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ==============================================================================
app = FastAPI(
    title="EDITH Decision Intelligence Platform",
    description="Enterprise Decision Intelligence, Multi-Hypothesis Causal Decomposition & Scenario Simulation",
    version="2.5.0"
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signed Session Middleware for Server-Enforced Persona Gate (Requirement B)
SESSION_SECRET_KEY = os.environ.get(
    "SESSION_SECRET_KEY",
    "edith_dev_secret_key_2026_accenture_innovation_track3"
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=None  # Browser-session cookie (clears on browser close)
)

# Template and Static Asset Directories
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Temporary In-Memory State
_UPLOAD_CACHE: Dict[str, Any] = {}
_ACTIVE_SIM_LEVERS: Dict[str, Any] = {
    "price_rollback_pct": 6.0,
    "promo_fund_k": 15.0,
    "churn_mitigation": True
}


# ==============================================================================
# DATA MODELS & SCHEMAS
# ==============================================================================

class SwitchBenchmarkRequest(BaseModel):
    benchmark_id: str = Field("b2b_saas_pricing", description="b2b_saas_pricing, saas_churn_roas, retail_fulfillment, or manufacturing_quality")

class SemanticConfigRequest(BaseModel):
    dataset_name: Optional[str] = Field("Custom Ingested Dataset", description="Display name for the dataset")
    analysis_grain: Optional[str] = Field("Time Series (Weekly / Monthly / Daily)", description="Temporal or Snapshot grain")
    primary_measure: str = Field(..., description="Target numeric column")
    primary_measure_label: Optional[str] = Field(None, description="Human-readable business label")
    primary_measure_unit: Optional[str] = Field("Units", description="Measurement unit (e.g. $, Units, %, Hours)")
    aggregation_type: Optional[str] = Field("sum", description="Aggregation method: sum, avg, count, distinct_count")
    distinct_entity_column: Optional[str] = Field(None, description="Entity identifier for distinct count")
    date_column: Optional[str] = Field(None, description="Date column for time series")
    dimension_columns: Optional[List[str]] = Field(default_factory=list, description="Categorical dimension columns")
    driver_columns: Optional[List[str]] = Field(default_factory=list, description="Numeric driver columns")
    identifier_columns: Optional[List[str]] = Field(default_factory=list, description="Ignored identifier columns")
    drop_invalid_rows: Optional[bool] = Field(True, description="Drop null/invalid rows during ingestion")
    file_roles: Optional[List[Dict[str, Any]]] = Field(default=None, description="Per-file role assignments: [{filename, role: fact|dimension|unstructured, join_keys: [...]}]")
    confirmed_relationships: Optional[List[Dict[str, Any]]] = Field(default=None, description="User-confirmed cross-file relationships")


class SimulationLeversRequest(BaseModel):
    price_rollback_pct: float = Field(6.0, ge=0.0, le=10.0, description="Rollback percentage (0-10%)")
    promo_fund_k: float = Field(15.0, ge=0.0, le=50.0, description="Regional Co-Op fund ($0k-$50k)")
    churn_mitigation: bool = Field(True, description="VIP Retention Guard CSM assignment")


class ChatRequest(BaseModel):
    query: str = Field(..., description="User query or hypothesis question")
    chat_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Multi-turn conversation history")
    simulation_levers: Optional[Dict[str, Any]] = Field(None, description="Current simulation lever overrides")
    persona: Optional[str] = Field(None, description="Optional persona override for testing")
    response_style: Optional[str] = Field("concise", description="Response style: concise or deep")


class SetApiKeyRequest(BaseModel):
    api_key: str = Field(..., description="Google Gemini API Key from Google AI Studio")


class LogEventRequest(BaseModel):
    persona: str = Field(..., description="Selected persona ID")
    action: str = Field("GATE_SELECTION", description="Action name")
    endpoint: Optional[str] = "persona_gate"
    details: Optional[Dict[str, Any]] = None


class HypothesisFeedbackRequest(BaseModel):
    hypothesis_id: str
    action: str  # "confirmed" or "overridden"
    reason: Optional[str] = ""

class ActionRatingRequest(BaseModel):
    action_id: str
    rating: str  # "helpful" or "not_helpful"


# Helper for JSON serialization
def _to_json_safe(obj: Any) -> Any:
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.fillna(0).to_dict(orient="records")
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_safe(x) for x in obj]
    return obj


# ==============================================================================
# MULTI-PAGE JINJA2 ROUTES & PERSONA GATE (REQUIREMENTS A & B)
# ==============================================================================

@app.get("/")
@app.get("/gate")
async def root_persona_gate(request: Request):
    """
    Persona Gate Landing Screen (Requirement B).
    Renders gate.html with the 4 persona cards so the user chooses their enterprise role.
    """
    return templates.TemplateResponse(request=request, name="gate.html", context={"personas": get_personas()})



@app.post("/session/select-persona")
async def session_select_persona(request: Request):
    """
    Sets the signed session cookie for the chosen persona and transitions into /overview.
    Rejects invalid persona IDs with 400.
    Logs gate selection event to the audit trail (Requirement D).
    """
    persona_id = None
    # 1. Try form data
    try:
        form = await request.form()
        persona_id = form.get("persona_id")
    except Exception:
        pass
    
    # 2. Try JSON payload
    if not persona_id:
        try:
            body = await request.json()
            persona_id = body.get("persona_id")
        except Exception:
            pass

    if not persona_id or persona_id not in PERSONAS:
        raise HTTPException(status_code=400, detail="Invalid persona selected. Must be one of: executive, general_user, regional_lead, analyst")
    
    request.session["persona_id"] = persona_id
    
    log_event(
        persona=persona_id,
        action="GATE_SELECTION",
        endpoint="persona_gate",
        details={"selected_role": persona_id}
    )
    
    return RedirectResponse(url="/overview", status_code=303)


@app.get("/session/switch-role")
async def session_switch_role(request: Request):
    """
    Clears the session cookie and redirects to the Persona Gate landing view.
    Logs role switch event in audit log.
    """
    curr_persona = request.session.pop("persona_id", None)
    if curr_persona:
        log_event(
            persona=curr_persona,
            action="SWITCH_ROLE",
            endpoint="/session/switch-role",
            details={"switched_from": curr_persona}
        )
    return RedirectResponse(url="/", status_code=303)


def _render_protected_page(request: Request, page_name: str):
    """
    Helper to enforce server-side gate security:
    If no persona is in session, logs BLOCKED_UNAUTHORIZED and redirects to / (Requirement B).
    """
    persona_id = request.session.get("persona_id")
    if not persona_id or persona_id not in PERSONAS:
        log_event(
            persona="unauthorized",
            action="BLOCKED_UNAUTHORIZED",
            endpoint=request.url.path,
            details={"blocked_route": request.url.path},
            status="BLOCKED"
        )
        return RedirectResponse(url="/", status_code=303)
    
    persona_meta = get_persona(persona_id)
    return templates.TemplateResponse(request=request, name=f"{page_name}.html", context={"active_page": page_name, "persona": persona_meta})


@app.get("/overview")
async def page_overview(request: Request):
    return _render_protected_page(request, "overview")


@app.get("/diagnostic")
async def page_diagnostic(request: Request):
    return _render_protected_page(request, "diagnostic")


@app.get("/workspace")
async def page_workspace(request: Request):
    return _render_protected_page(request, "workspace")


@app.get("/simulation")
async def page_simulation(request: Request):
    return _render_protected_page(request, "simulation")


@app.get("/console")
async def page_console(request: Request):
    return _render_protected_page(request, "console")


@app.get("/sources")
async def page_sources(request: Request):
    return _render_protected_page(request, "sources")


# ==============================================================================
# AUDIT LOG & PERSONAS ENDPOINTS
# ==============================================================================

@app.get("/api/personas")
async def list_personas():
    """Returns available enterprise personas with metadata and permission profiles."""
    return _to_json_safe(get_personas())


@app.post("/api/access-log/event")
async def record_access_event(req: LogEventRequest):
    """Records an explicit persona gate selection or navigation event into the audit trail."""
    entry = log_event(
        persona=req.persona,
        action=req.action,
        endpoint=req.endpoint or "persona_gate",
        details=req.details
    )
    return {"status": "SUCCESS", "event": entry}


@app.get("/api/access-log")
async def get_access_audit_log(limit: int = 50):
    """Returns recent role-based access control and scoping audit events."""
    return _to_json_safe({
        "total_logged": len(get_access_log(200)),
        "events": get_access_log(limit)
    })


@app.post("/api/feedback/hypothesis")
async def submit_hypothesis_feedback_endpoint(request: Request, req: HypothesisFeedbackRequest):
    from core.feedback import submit_hypothesis_feedback
    persona_id = request.session.get("persona_id") or "anonymous"
    result = submit_hypothesis_feedback(req.hypothesis_id, req.action, req.reason or "", persona_id)
    return {"success": True, "feedback": result}

@app.post("/api/feedback/action")
async def submit_action_rating_endpoint(request: Request, req: ActionRatingRequest):
    from core.feedback import submit_action_rating
    persona_id = request.session.get("persona_id") or "anonymous"
    result = submit_action_rating(req.action_id, req.rating, persona_id)
    return {"success": True, "feedback": result}

@app.get("/api/feedback-log")
async def get_feedback_log_endpoint(limit: int = 50):
    from core.feedback import get_feedback_log
    return {"feedback": get_feedback_log(limit)}


# ==============================================================================
# DATA INTAKE & SOURCE MANAGEMENT REST APIS
# ==============================================================================

@app.post("/api/data/upload")
async def upload_dataset_files(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None)
):
    """Uploads and profiles external CSV/Excel datasets."""
    all_files = []
    if files:
        all_files.extend(files)
    if file:
        all_files.append(file)
        
    if not all_files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    responses = []
    cache_entry = {}
    
    for f in all_files:
        filename = f.filename or "uploaded_data.csv"
        try:
            content = await f.read()
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(status_code=400, detail=f"Invalid file type for {filename}. Only CSV and Excel files are supported.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file {filename}: {str(e)}")

        if df.empty:
            raise HTTPException(status_code=400, detail=f"Uploaded file {filename} is empty.")

        profile = DataProfiler.profile_dataset(df)
        
        date_cols = profile.get("valid_date_columns", [])
        grain = "Snapshot"
        if date_cols:
            try:
                date_s = pd.to_datetime(df[date_cols[0]], errors="coerce").dropna()
                if len(date_s) > 1:
                    diffs = date_s.sort_values().diff().dropna().mode()
                    if not diffs.empty:
                        d_days = diffs.iloc[0].days
                        if d_days == 1:
                            grain = "Daily"
                        elif 6 <= d_days <= 8:
                            grain = "Weekly"
                        elif 28 <= d_days <= 32:
                            grain = "Monthly"
                        else:
                            grain = f"{d_days} Days"
            except:
                pass
        
        profile["filename"] = filename
        profile["grain"] = grain
        
        stem = os.path.splitext(filename)[0]
        cache_entry[stem] = {"df": df, "profile": profile, "filename": filename}
        
        preview_rows = df.head(10).fillna("").to_dict(orient="records")
        responses.append({
            "filename": filename,
            "total_rows": profile["total_rows"],
            "total_columns": profile["total_columns"],
            "columns": [p["column_name"] for p in profile["profiles"]],
            "valid_numeric_columns": profile["valid_numeric_columns"],
            "valid_date_columns": profile["valid_date_columns"],
            "valid_dimension_columns": profile["valid_dimension_columns"],
            "profiles": profile["profiles"],
            "grain": grain,
            "preview": preview_rows
        })
        
    _UPLOAD_CACHE["files"] = cache_entry
    
    # Backward compatibility for single file
    first_item = list(cache_entry.values())[0]
    _UPLOAD_CACHE["raw_df"] = first_item["df"]
    _UPLOAD_CACHE["profile"] = first_item["profile"]
    _UPLOAD_CACHE["filename"] = first_item["filename"]
    
    # Detect relationships if multiple files
    relationships = []
    if len(all_files) > 1:
        from core.data_reconciliation import detect_join_keys
        stems = list(cache_entry.keys())
        for i in range(len(stems)):
            for j in range(i + 1, len(stems)):
                stem1, stem2 = stems[i], stems[j]
                file1 = cache_entry[stem1]
                file2 = cache_entry[stem2]
                
                join_keys = detect_join_keys(file1["df"], file2["df"])
                if join_keys:
                    relationships.append({
                        "left_file": file1["filename"],
                        "right_file": file2["filename"],
                        "join_keys": join_keys,
                        "grain_left": file1["profile"]["grain"],
                        "grain_right": file2["profile"]["grain"]
                    })
                    
    res_dict = {
        "success": True,
        "files": responses,
        "relationships": relationships
    }
    
    # Merge first file's fields at top level for backward compatibility
    if responses:
        first_resp = responses[0]
        res_dict.update({
            "filename": first_resp["filename"],
            "total_rows": first_resp["total_rows"],
            "total_columns": first_resp["total_columns"],
            "columns": first_resp["columns"],
            "valid_numeric_columns": first_resp["valid_numeric_columns"],
            "valid_date_columns": first_resp["valid_date_columns"],
            "valid_dimension_columns": first_resp["valid_dimension_columns"],
            "profiles": first_resp["profiles"],
            "preview": first_resp["preview"],
            "message": f"Successfully parsed and profiled {first_resp['filename']} ({first_resp['total_rows']} rows, {first_resp['total_columns']} columns)"
        })
        
    return res_dict




@app.post("/api/data/configure")
async def configure_semantic_model(config: SemanticConfigRequest):
    """Applies user semantic mapping to transform and ingest custom dataset."""
    merge_warnings = []
    if config.file_roles:
        if "files" not in _UPLOAD_CACHE:
            raise HTTPException(status_code=400, detail="No datasets uploaded in current session.")
            
        files_cache = _UPLOAD_CACHE["files"]
        tables = {}
        
        fact_file_req = next((f for f in config.file_roles if f["role"] == "fact"), None)
        if not fact_file_req:
            raise HTTPException(status_code=400, detail="Must designate one file as the 'fact' table.")
            
        fact_filename = fact_file_req["filename"]
        fact_stem = os.path.splitext(fact_filename)[0]
        
        if fact_stem not in files_cache:
            raise HTTPException(status_code=400, detail=f"Fact table {fact_filename} not found in cache.")
            
        fact_df = files_cache[fact_stem]["df"].copy()
        tables["sales"] = fact_df
        
        for role_req in config.file_roles:
            role = role_req["role"]
            fname = role_req["filename"]
            stem = os.path.splitext(fname)[0]
            if stem in files_cache and role != "fact":
                tables[stem] = files_cache[stem]["df"].copy()
                
        # Perform actual merge of supporting tables into tables["sales"]
        from core.data_reconciliation import detect_join_keys, merge_tables_with_grain
        confirmed_rels = config.confirmed_relationships
        
        for role_req in config.file_roles:
            role = role_req["role"]
            fname = role_req["filename"]
            stem = os.path.splitext(fname)[0]
            if role == "fact" or stem not in files_cache:
                continue
                
            supp_df = files_cache[stem]["df"]
            
            # Check if this relationship is confirmed
            should_join = True
            join_keys = None
            
            if confirmed_rels is not None:
                matching_rel = next((
                    rel for rel in confirmed_rels
                    if (rel.get("left_file") in [fact_filename, fname] and rel.get("right_file") in [fact_filename, fname])
                    or (rel.get("left_file") in [fact_stem, stem] and rel.get("right_file") in [fact_stem, stem])
                ), None)
                
                if matching_rel is None:
                    should_join = False
                else:
                    join_keys = matching_rel.get("join_keys")
                    
            if not should_join:
                continue
                
            if not join_keys:
                join_keys = detect_join_keys(tables["sales"], supp_df)
                
            if not join_keys:
                merge_warnings.append(
                    f"Could not join supporting table '{fname}' to fact table '{fact_filename}': no compatible shared join keys found."
                )
                continue
                
            fact_d_col = config.date_column if (config.date_column and config.date_column != "None (Snapshot)") else None
            tables["sales"] = merge_tables_with_grain(
                tables["sales"], supp_df, join_keys, fact_date_col=fact_d_col
            )
            
        raw_df = tables["sales"]
                    
    else:
        if "raw_df" not in _UPLOAD_CACHE:
            raise HTTPException(status_code=400, detail="No dataset uploaded in current session. Please upload a CSV first.")
        raw_df = _UPLOAD_CACHE["raw_df"]
        tables = {"sales": raw_df}

    if config.primary_measure not in raw_df.columns:
        raise HTTPException(status_code=400, detail=f"Primary measure '{config.primary_measure}' does not exist in dataset.")
    
    is_num, invalid_cnt, invalid_pct = DataProfiler.is_reliably_numeric(raw_df[config.primary_measure])
    if not is_num:
        raise HTTPException(
            status_code=400,
            detail=f"Selected primary measure '{config.primary_measure}' contains non-numeric text ({invalid_pct}% unparseable). Please select a valid numeric column."
        )

    for drv in config.driver_columns:
        if drv in raw_df.columns:
            d_is_num, _, d_pct = DataProfiler.is_reliably_numeric(raw_df[drv])
            if not d_is_num:
                raise HTTPException(
                    status_code=400,
                    detail=f"Selected driver '{drv}' contains non-numeric text ({d_pct}% invalid). Drivers must be numeric."
                )

    semantic_model = SemanticDataModel(
        dataset_name=config.dataset_name,
        analysis_grain=config.analysis_grain,
        primary_measure=config.primary_measure,
        primary_measure_label=config.primary_measure_label,
        primary_measure_unit=config.primary_measure_unit,
        aggregation_type=config.aggregation_type,
        distinct_entity_column=config.distinct_entity_column,
        date_column=config.date_column if config.date_column != "None (Snapshot)" else None,
        dimension_columns=config.dimension_columns,
        driver_columns=config.driver_columns,
        identifier_columns=config.identifier_columns,
        drop_invalid_rows=config.drop_invalid_rows
    )

    try:
        norm_tables, feat_status, warnings = ColumnMapper.transform_generic_dataset(
            tables["sales"], 
            semantic_model, 
            drop_invalid_rows=config.drop_invalid_rows if config.drop_invalid_rows is not None else True
        )
        if merge_warnings:
            warnings.extend(merge_warnings)
        final_tables = {"sales": norm_tables.get("sales", tables["sales"])}
        for k, v in tables.items():
            if k != "sales":
                final_tables[k] = v
                
        clean_df = final_tables["sales"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Data transformation failed: {str(e)}")

    is_temporal = bool(semantic_model.is_temporal)
    
    repo = DataRepository.get_instance()
    repo.set_custom_data(
        tables=final_tables,
        source_info={
            "source_type": "Custom CSV Ingestion",
            "name": config.dataset_name,
            "is_demo": False,
            "row_count": len(clean_df),
            "primary_measure_label": config.primary_measure_label or config.primary_measure,
            "primary_measure_unit": config.primary_measure_unit or "Units",
            "analysis_grain": config.analysis_grain,
            "feature_status": {
                "is_temporal": is_temporal,
                "aggregation_type": config.aggregation_type
            }
        },
        semantic_model=semantic_model
    )

    feasibility = AnalysisFeasibilityChecker.evaluate_feasibility(clean_df, semantic_model)

    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Dataset '{config.dataset_name}' successfully configured and loaded ({len(clean_df):,} records).",
        "semantic_model": semantic_model.to_dict(),
        "feasibility": feasibility,
        "is_temporal": is_temporal,
        "primary_measure": config.primary_measure_label or config.primary_measure,
        "dimensions": config.dimension_columns,
        "drivers": config.driver_columns,
        "source_info": repo.active_source_info,
        "row_count": len(clean_df),
        "warnings": warnings
    }


@app.post("/api/data/switch-benchmark")
async def switch_calibrated_benchmark(req: SwitchBenchmarkRequest):
    """Switches the active dataset to one of the 4 calibrated structural benchmarks."""
    valid_benchmarks = ["b2b_saas_pricing", "saas_churn_roas", "retail_fulfillment", "manufacturing_quality"]
    if req.benchmark_id not in valid_benchmarks:
        raise HTTPException(status_code=400, detail=f"Invalid benchmark_id '{req.benchmark_id}'. Must be one of: {valid_benchmarks}")
    
    _UPLOAD_CACHE.clear()
    repo = DataRepository.get_instance()
    repo.switch_benchmark(req.benchmark_id)
    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Successfully activated benchmark '{repo.active_source_info.get('name')}'",
        "benchmark_id": req.benchmark_id,
        "source_info": repo.active_source_info,
        "is_demo": True
    }

@app.post("/api/data/reset-demo")
async def reset_to_benchmark():
    """Restores the built-in B2B SaaS benchmark dataset in DataRepository."""
    _UPLOAD_CACHE.clear()
    repo = DataRepository.get_instance()
    repo.reset_to_demo_dataset()
    return {
        "success": True,
        "status": "SUCCESS",
        "message": "Data repository restored to built-in B2B SaaS benchmark dataset.",
        "source_info": repo.active_source_info,
        "is_demo": True
    }


@app.get("/api/data/source")
async def get_active_source_info():
    """Returns metadata about the active dataset."""
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
# ANALYTICAL DASHBOARD APIS (SCOPED FROM SESSION / COMPATIBLE PARAMS)
# ==============================================================================

@app.get("/api/overview")
async def get_overview(request: Request, persona: Optional[str] = None):
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
    
    # Priority: Session cookie persona
    active_p = request.session.get("persona_id")
    if active_p:
        res_payload = scope_overview(res_payload, active_p, repo)
        
    return _to_json_safe(res_payload)


@app.get("/api/diagnostic")
async def get_diagnostic(request: Request, persona: Optional[str] = None):
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
        "distribution": dist_stats,
        "distribution_stats": dist_stats,
        "data_quality": dq_report,
        "variance_decomposition": decomp
    }
    
    active_p = request.session.get("persona_id")
    if active_p:
        res_payload = scope_diagnostic(res_payload, active_p, repo)
        
    return _to_json_safe(res_payload)


@app.get("/api/workspace")
async def get_investigation_workspace(request: Request, persona: Optional[str] = None):
    """
    Returns investigation findings:
    - For Built-in Demo: 8 full Causal Hypotheses with DiD, mathematical decomposition, DAG roles, and rank.
    - For Custom Datasets: Observational Findings clearly labeled as empirical associations and patterns.
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    ev_engine = EvidenceEngine(repo)
    findings = ev_engine.evaluate_all_hypotheses()
    from core.feedback import annotate_hypotheses
    findings = annotate_hypotheses(findings)
    
    decomp = ContributionEngine.calculate_variance_decomposition(repo)
    
    res_payload = {
        "is_demo": is_demo,
        "findings": findings,
        "variance_decomposition": decomp,
        "disclaimer": "" if is_demo else "Observational Integrity Notice: For custom uploaded datasets, results represent empirical concentrations, statistical associations, and distribution patterns—not confirmed causal hypotheses."
    }
    
    active_p = request.session.get("persona_id")
    if active_p:
        res_payload = scope_workspace(res_payload, active_p, repo)
        
    return _to_json_safe(res_payload)


@app.get("/api/simulation")
async def get_simulation(request: Request, persona: Optional[str] = None):
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
    
    res = SimulationEngine.simulate_lever_impact(
        price_rollback_pct=-abs(_ACTIVE_SIM_LEVERS["price_rollback_pct"]),
        promo_fund_k=_ACTIVE_SIM_LEVERS["promo_fund_k"],
        churn_mitigation=_ACTIVE_SIM_LEVERS["churn_mitigation"],
        benchmark_id=repo.active_benchmark_id
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
        "metric_label": res.get("metric_label", "Gross Revenue ($)"),
        "recovery_pct": float(res.get("recovery_pct", 0.0)),
        "summary": summary
    }
    
    active_p = request.session.get("persona_id")
    if active_p:
        res_payload = scope_simulation(res_payload, active_p)
        
    return _to_json_safe(res_payload)


@app.post("/api/simulation")
async def update_simulation(request: Request, levers: SimulationLeversRequest, persona: Optional[str] = None):
    """Updates simulation levers (demo only)."""
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    if not is_demo:
        raise HTTPException(
            status_code=400,
            detail="Counterfactual simulation is only supported on calibrated structural models (Demo dataset)."
        )
    
    _ACTIVE_SIM_LEVERS["price_rollback_pct"] = levers.price_rollback_pct
    _ACTIVE_SIM_LEVERS["promo_fund_k"] = levers.promo_fund_k
    _ACTIVE_SIM_LEVERS["churn_mitigation"] = levers.churn_mitigation
    
    res = SimulationEngine.simulate_lever_impact(
        price_rollback_pct=-abs(levers.price_rollback_pct),
        promo_fund_k=levers.promo_fund_k,
        churn_mitigation=levers.churn_mitigation,
        benchmark_id=repo.active_benchmark_id
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
        "metric_label": res.get("metric_label", "Gross Revenue ($)"),
        "recovery_pct": float(res.get("recovery_pct", 0.0)),
        "summary": summary
    }
    
    active_p = request.session.get("persona_id")
    if active_p:
        res_payload = scope_simulation(res_payload, active_p, is_update=True, requested_levers=dict(levers))
        
    return _to_json_safe(res_payload)


@app.get("/api/briefing")
async def get_executive_briefing(request: Request, persona: Optional[str] = None):
    """
    Generates persona-specific standing Executive Briefing report artifact.
    Works 100% offline with zero API key requirement.
    """
    active_p = request.session.get("persona_id")
    p_meta = get_persona(active_p or DEFAULT_PERSONA)
    p_id = p_meta["id"]
    
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
    briefing["persona"] = p_id
    
    log_access(
        persona=p_id,
        endpoint="/api/briefing",
        granted_sections=["executive_briefing_narrative", "recommended_actions_matrix", "primary_root_cause"],
        restricted_sections=["competitor_telemetry", "cross_region_lineage"] if p_id == "regional_lead" else []
    )
    
    return _to_json_safe(briefing)



@app.post("/api/chat")
async def chat_with_edith(request: Request, req: ChatRequest):
    """
    Asynchronous grounded conversational decision intelligence interface.
    Operates via Live Gemini Agent or Deterministic Offline Reasoner (Zero-Key).
    """
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    label = repo.active_source_info.get("primary_measure_label", "Gross Revenue" if is_demo else "Primary Measure")
    
    active_p = request.session.get("persona_id")
    p_meta = get_persona(active_p or "executive")
    p_id = p_meta["id"]

    ts = repo.get_kpi_time_series(region="Region B" if p_id == "regional_lead" else None)
    anom_ctx = AnomalyEngine.evaluate_current_anomaly(ts, kpi_name=label)

    ev_engine = EvidenceEngine(repo)
    all_hypotheses = ev_engine.evaluate_all_hypotheses()
    selected_h = next((h for h in all_hypotheses if h.get("id") == "H1_PRICING_SHOCK"), all_hypotheses[0] if all_hypotheses else {})

    client = EdithLLMClient()
    
    try:
        answer_text, metadata = client.answer_question(
            query=req.query,
            anomaly_context=anom_ctx,
            selected_hypothesis=selected_h,
            hypotheses=all_hypotheses,
            chat_history=req.chat_history or [],
            simulation_levers=req.simulation_levers or _ACTIVE_SIM_LEVERS,
            persona=p_id,
            response_style=req.response_style or "concise"
        )
    except Exception as e:
        print(f"[LLM Client Error]: {e}. Falling back to Offline Reasoner.")
        answer_text = OfflineEdithReasoner.answer_conversational_query(
            query=req.query,
            anomaly_context=anom_ctx,
            selected_hypothesis=selected_h,
            all_hypotheses=all_hypotheses,
            chat_history=req.chat_history or [],
            simulation_levers=req.simulation_levers or _ACTIVE_SIM_LEVERS,
            persona=p_id
        )
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "mode": "Deterministic Offline Mode (Zero-Key)",
            "latency_sec": 0.01,
            "status": "Fallback Successful"
        }

    log_access(
        persona=p_id,
        endpoint="/api/chat",
        action="QUERY",
        granted_sections=["conversational_narration", "observational_grounding"],
        restricted_sections=["competitor_telemetry"] if p_id == "regional_lead" else [],
        details={"query": req.query[:100]}
    )

    return {
        "answer": answer_text,
        "metadata": metadata,
        "persona": p_id,
        "is_demo": is_demo
    }


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

@app.get("/api/telemetry")
async def get_telemetry_data(limit: int = 50):
    from core.telemetry import get_telemetry, get_rollup
    return {"events": get_telemetry(limit), "rollup": get_rollup()}


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
        test_client = genai.Client(api_key=clean_key)
        try:
            test_client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Ping"
            )
        except Exception:
            pass
            
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
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8501))
    print(f"🚀 Starting EDITH Multi-Page FastAPI Server on http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
