"""
state/session_state.py
Centralized, typed session state management for EDITH in Streamlit.
Ensures seamless state persistence across workflow transitions without page reloads.
"""
import os
import streamlit as st
from typing import Dict, List, Any, Optional

from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine

def init_session_state():
    """Initializes all necessary session state keys on first load."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_screen = "overview" # "overview" | "diagnostic" | "workspace" | "simulation" | "console"
        st.session_state.previous_screen = "overview"
        st.session_state.selected_kpi_id = "kpi_b2b_sales"
        st.session_state.selected_hypothesis_id = "H1_PRICING_PRESSURE"
        st.session_state.chat_history = []
        st.session_state.simulation_levers = {
            "price_rollback_pct": -6.0,
            "marketing_boost_usd": 15000.0,
            "competitor_matching": True
        }
        st.session_state.api_key_input = os.getenv("GEMINI_API_KEY", "").strip()

        
        # Load and cache initial analytics
        repo = DataRepository.get_instance()
        df_ts = repo.get_kpi_time_series(st.session_state.selected_kpi_id)
        df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
        anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, kpi_name="Monthly B2B Sales")
        
        contribution_ctx = ContributionEngine.calculate_variance_decomposition(repo, st.session_state.selected_kpi_id)
        evidence_eng = EvidenceEngine(repo)
        hypotheses = evidence_eng.evaluate_all_hypotheses(st.session_state.selected_kpi_id)
        
        st.session_state.kpi_ts = df_analyzed
        st.session_state.anomaly_context = anomaly_ctx
        st.session_state.contribution_context = contribution_ctx
        st.session_state.hypotheses = hypotheses
        st.session_state.edith_briefing = ""
        st.session_state.llm_metadata = {}

def set_screen(screen_name: str):
    """Sets the active workflow screen and triggers re-render, tracking prior screen."""
    current = st.session_state.get("current_screen", "overview")
    if screen_name == "console" and current != "console":
        st.session_state.previous_screen = current
    elif current != "console" and screen_name != current:
        st.session_state.previous_screen = current
        
    st.session_state.current_screen = screen_name
    st.rerun()

def select_hypothesis(hypo_id: str):
    """Selects an active hypothesis in the investigation workspace."""
    st.session_state.selected_hypothesis_id = hypo_id
