"""
ui/screens/s3_workspace.py
Screen 3: Focused Causal Investigation Workspace (Explain Stage)
Full-width, high-clarity analytical canvas evaluating competing causal hypotheses.
"""
import streamlit as st
from state.session_state import set_screen, select_hypothesis
from ui.components.cards import (
    render_cause_score_card,
    render_evidence_score_badge,
    render_mathematical_decomposition_card,
    render_investigation_chain_card,
    render_prediction_card,
    render_control_group_summary,
    render_confounders_summary,
    render_epistemology_chip
)
from ui.components.charts import plot_did_cohort
from data.repository import DataRepository

def render_screen_3():
    """Renders the focused full-width causal investigation workspace."""
    col_nav, col_title, col_tag = st.columns([1.3, 3.7, 1.2])
    with col_nav:
        if st.button("← Back to Diagnose (Diagnostic)", key="btn_ws_back_s3", use_container_width=True):
            set_screen("diagnostic")
            st.rerun()
            
    repo = DataRepository.get_instance()
    is_demo = repo.active_source_info.get("is_demo", True)
    
    with col_title:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #0F172A;'>🔬 Stage 3: Investigation Workspace</h2>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_epistemology_chip("DATA-DERIVED" if is_demo else "OBSERVATIONAL")
        st.markdown("</div>", unsafe_allow_html=True)
        
    if is_demo:
        st.caption("Deterministic multi-dimensional evaluation of 8 competing hypotheses across temporal precedence, magnitude, directional consistency, lag correlations, metric DAG hierarchy, and mathematical decomposition.")
    else:
        st.caption("Empirical pattern isolation: evaluating dimensional concentrations, driver associations, and distribution properties with epistemological integrity (associations, not unearned causal claims).")
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    hypotheses = st.session_state.get("hypotheses", [])
    selected_hypo_id = st.session_state.get("selected_hypothesis_id", hypotheses[0]["id"] if hypotheses else "")
    
    # Get active hypothesis object
    active_h = next((h for h in hypotheses if h["id"] == selected_hypo_id), hypotheses[0] if hypotheses else {})
    
    # =========================================================================
    # 1. CANDIDATE HYPOTHESIS / PATTERN SELECTION STRIP
    # =========================================================================
    section_title = "Candidate Root-Cause Hypotheses (Ranked by Multi-Dimensional Evidence)" if is_demo else "Empirical Investigation Findings (Ranked by Impact & Association Strength)"
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 16px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.4px;">
                {section_title}
            </div>
        """,
        unsafe_allow_html=True
    )

    
    # 8 Hypotheses in 2 rows of 4 columns
    for row_idx in range(0, len(hypotheses), 4):
        cols = st.columns(4)
        for col_idx, h in enumerate(hypotheses[row_idx:row_idx+4]):
            with cols[col_idx]:
                is_active = (h["id"] == selected_hypo_id)
                score_100 = h.get("cause_score_100", 0.0)
                is_testable = h.get("testable", True)
                rank = h.get("rank", 1)
                role = h.get("dependency_role", "UPSTREAM_DIRECT")
                
                if not is_testable:
                    icon = "⚪"
                    score_str = "N/A"
                elif role == "DOWNSTREAM_EFFECT":
                    icon = "🔵"
                    score_str = f"{score_100:.1f}"
                elif score_100 >= 75.0:
                    icon = "🟢"
                    score_str = f"{score_100:.1f}"
                elif score_100 >= 50.0:
                    icon = "🟡"
                    score_str = f"{score_100:.1f}"
                else:
                    icon = "🔴"
                    score_str = f"{score_100:.1f}"
                    
                btn_label = f"#{rank} {icon} {h['name']} ({score_str})"
                if st.button(btn_label, key=f"sel_h_{h['id']}", type="primary" if is_active else "secondary", use_container_width=True):
                    select_hypothesis(h["id"])
                    st.rerun()
                    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # 2. ACTIVE HYPOTHESIS DEEP-DIVE DOSSIER
    # =========================================================================
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <span style="font-size: 11px; font-weight: 800; color: #2563EB; letter-spacing: 0.5px; text-transform: uppercase;">ACTIVE HYPOTHESIS EVALUATION</span>
                    <h3 style="margin: 2px 0 0 0; font-size: 18px; font-weight: 800; color: #0F172A;">#{active_h.get('rank', 1)} {active_h.get('name', 'Hypothesis')}</h3>
                </div>
            </div>
        """,
        unsafe_allow_html=True
    )
    
    # Multi-Dimensional Cause Score Breakdown Card
    render_cause_score_card(active_h)
    
    # 5 Structured Investigation Tabs
    tab_chain, tab_math, tab_lag, tab_ledgers, tab_proof = st.tabs([
        "🧪 Causal Chain & DAG",
        "📐 Math & Control",
        "⏱️ Lags & Predictions",
        "⚖️ Evidence Ledgers",
        "🧠 Proof & Confounders"
    ])
    
    with tab_chain:
        chain = active_h.get("investigation_chain", [])
        if chain:
            render_investigation_chain_card(chain)
        else:
            st.info(f"DAG Role: {active_h.get('dependency_role')} &bull; Category: {active_h.get('category')}")
            
        dir_cons = active_h.get("directional_consistency", {})
        if dir_cons:
            st.markdown(
                f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 6px; padding: 10px 14px; margin-top: 8px;">
                    <span style="font-size: 12px; font-weight: 700; color: #166534;">📐 Directional Consistency:</span>
                    <span style="font-size: 12px; color: #1E293B;"> {dir_cons.get('status')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    with tab_math:
        math_decomp = active_h.get("mathematical_decomposition")
        if math_decomp:
            render_mathematical_decomposition_card(math_decomp)
            
        ctrl_data = active_h.get("control_group_analysis", {})
        render_control_group_summary(ctrl_data)
        
        if active_h["id"] in ["H1_PRICING_PRESSURE", "H2_COMPETITOR_CAMPAIGN"]:
            repo = DataRepository.get_instance()
            df_cohort = repo.get_cohort_comparison(region="Region B", product="Product Suite Alpha")
            fig_did = plot_did_cohort(df_cohort)
            st.plotly_chart(fig_did, use_container_width=True)
            
    with tab_lag:
        temp = active_h.get("temporal_alignment", {})
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #4F46E5; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px;">
                <div style="font-size: 11px; font-weight: 700; color: #4F46E5; text-transform: uppercase;">⏱️ Temporal Precedence Signal (τ Lead-Time)</div>
                <div style="font-size: 13px; font-weight: 700; color: #0F172A; margin-top: 2px;">Shock Event: {temp.get('shock_event')} ({temp.get('shock_date')})</div>
                <div style="font-size: 12px; color: #475569; margin-top: 2px;">{temp.get('assessment')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        lag = active_h.get("lag_analysis", {})
        if lag:
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #6366F1; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px;">
                    <div style="font-size: 11px; font-weight: 700; color: #4F46E5; text-transform: uppercase;">📈 Historical Lagged Cross-Correlation (Weeks 1-48)</div>
                    <div style="font-size: 13px; color: #1E293B; margin-top: 4px;">
                        • <b>Best Lead-Lag:</b> Lag {lag.get('best_lag', 0)} weeks (Strength |r| = <b>{lag.get('lag_strength', 0.0):.3f}</b>, Direction: <code>{lag.get('lag_direction')}</code>)
                    </div>
                    <div style="font-size: 11px; color: #64748B; margin-top: 2px;">
                        • Profile (L0..L4): <code>{lag.get('lag_correlations')}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        preds = active_h.get("predictions", [])
        if preds:
            st.caption("Empirical prediction verification:")
            for p in preds:
                render_prediction_card(p)

    with tab_ledgers:
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #166534; text-transform: uppercase; margin-bottom: 4px;'>✅ Supporting Evidence Ledger</div>", unsafe_allow_html=True)
        for supp in active_h.get("supporting_evidence", []):
            st.markdown(f"<div style='background: #F0FDF4; font-size: 12px; color: #1E293B; margin-bottom: 4px; padding: 6px 10px; border-left: 3px solid #16A34A; border-radius: 0 4px 4px 0;'>{supp}</div>", unsafe_allow_html=True)
            
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #991B1B; text-transform: uppercase; margin: 12px 0 4px 0;'>⚠️ Contradictory Facts / Negative Penalties</div>", unsafe_allow_html=True)
        for contra in active_h.get("contradictory_evidence", []):
            st.markdown(f"<div style='background: #FEF2F2; font-size: 12px; color: #1E293B; margin-bottom: 4px; padding: 6px 10px; border-left: 3px solid #DC2626; border-radius: 0 4px 4px 0;'>{contra}</div>", unsafe_allow_html=True)
            
        missing = active_h.get("missing_expected_evidence", [])
        if missing:
            st.markdown("<div style='font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; margin: 12px 0 4px 0;'>🔍 Missing Expected Signals</div>", unsafe_allow_html=True)
            for m in missing:
                st.markdown(f"<div style='background: #F8FAFC; font-size: 12px; color: #475569; margin-bottom: 4px; padding: 6px 10px; border-left: 3px solid #94A3B8; border-radius: 0 4px 4px 0;'>{m}</div>", unsafe_allow_html=True)

    with tab_proof:
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #92400E; text-transform: uppercase; margin-bottom: 6px;'>🌪️ Confounding Factor Analysis</div>", unsafe_allow_html=True)
        render_confounders_summary(active_h.get("confounders", []))
        
        reasoning_chain = active_h.get("reasoning_chain", [])
        if reasoning_chain:
            st.markdown("<div style='font-size: 12px; font-weight: 700; color: #4338CA; text-transform: uppercase; margin: 14px 0 6px 0;'>🏆 Structured Causal Proof (Why This Hypothesis Ranked #1)</div>", unsafe_allow_html=True)
            for step in reasoning_chain:
                st.markdown(
                    f"""
                    <div style="background: #EEF2FF; border-left: 3px solid #4F46E5; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 6px 6px 0;">
                        <span style="font-size: 12px; font-weight: 700; color: #3730A3;">{step.get('step')}</span>: 
                        <span style="font-size: 12px; color: #1E293B;">{step.get('finding')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    st.markdown(
        f"""
        <div style="font-size: 11px; color: #64748B; margin-top: 14px;">
            📦 <b>Data Lineage:</b> {active_h.get('data_lineage', 'ERP Sales Ledger')}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # =========================================================================
    # 3. AI CONSULTATION CALLOUT & SIMULATION ACTION
    # =========================================================================
    col_ask, col_sim = st.columns([1.2, 1.2])
    with col_ask:
        if st.button("💬 Open EDITH Console (Ask Questions) →", key="btn_open_console_from_ws", use_container_width=True):
            set_screen("console")
            st.rerun()
    with col_sim:
        if st.button("🛠️ Proceed to Scenario Simulation (Simulate) →", key="btn_to_sim_s3", type="primary", use_container_width=True):
            set_screen("simulation")
            st.rerun()
