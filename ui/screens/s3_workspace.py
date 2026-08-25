"""
ui/screens/s3_workspace.py
Screen 3: Dual-Pane Investigation Workspace
Left: Deterministic Analytical Canvas | Right: Edith Conversational Console
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
from ui.components.chat_pane import render_edith_console
from data.repository import DataRepository

def render_screen_3():
    """Renders the dual-pane investigation workspace."""
    col_nav, col_title, col_tag = st.columns([1.2, 3.8, 1])
    with col_nav:
        if st.button("← Back to Diagnostic", use_container_width=True):
            set_screen("diagnostic")
            
    with col_title:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #FFFFFF;'>🔬 Investigation Workspace: Multi-Hypothesis & Causal Engine</h2>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_epistemology_chip("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.caption("Transparent auditability between deterministic empirical evidence (Left Canvas) and cognitive AI synthesis (Right Console).")
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    
    hypotheses = st.session_state.get("hypotheses", [])
    anomaly_ctx = st.session_state.get("anomaly_context", {})
    selected_hypo_id = st.session_state.get("selected_hypothesis_id", "H1_PRICING_PRESSURE")
    
    # Get active hypothesis object
    active_h = next((h for h in hypotheses if h["id"] == selected_hypo_id), hypotheses[0] if hypotheses else {})
    
    col_left, col_right = st.columns([1.2, 1.0], gap="large")
    
    # =========================================================================
    # LEFT PANE: DETERMINISTIC ANALYTICAL EVIDENCE CANVAS
    # =========================================================================
    with col_left:
        st.markdown("<h3 style='margin:0; padding:0; font-size: 17px; font-weight: 700; color: #FFFFFF;'>📊 Deterministic Root-Cause Evidence Canvas</h3>", unsafe_allow_html=True)
        st.caption("Candidate drivers ranked by multi-dimensional cause evidence (temporal, magnitude, directional, lag, dependency, decomposition):")
        
        # 1. Hypothesis Selection Cards
        for h in hypotheses:
            is_active = (h["id"] == selected_hypo_id)
            score_100 = h.get("cause_score_100", 0.0)
            is_testable = h.get("testable", True)
            rank = h.get("rank", 1)
            role = h.get("dependency_role", "UPSTREAM_DIRECT")
            
            # Prefix badge icon
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
            
            col_b1, col_b2 = st.columns([2.7, 1.3])
            with col_b1:
                if st.button(btn_label, key=f"sel_{h['id']}", type="primary" if is_active else "secondary", use_container_width=True):
                    select_hypothesis(h["id"])
                    st.rerun()
            with col_b2:
                render_evidence_score_badge(h.get("evidence_score", 0.0), label="Evidence Index", is_testable=is_testable)
                
        st.markdown("---")
        
        # 2. Selected Hypothesis Deep-Dive
        st.markdown(f"<h4 style='font-size: 15px; font-weight: 700; color: #FFFFFF;'>🔍 Deep-Dive: #{active_h.get('rank', 1)} {active_h.get('name', 'Hypothesis')}</h4>", unsafe_allow_html=True)
        
        # Cause Score & Component Card
        render_cause_score_card(active_h)
        
        # Investigation Detail Tabs
        tab_chain, tab_math, tab_lag, tab_ledgers, tab_reason = st.tabs([
            "🧪 Causal Chain & DAG",
            "📐 Math & Control",
            "⏱️ Lags & Predictions",
            "⚖️ Evidence Ledgers",
            "🧠 Proof & Confounders"
        ])
        
        with tab_chain:
            # Investigation Chain
            chain = active_h.get("investigation_chain", [])
            if chain:
                render_investigation_chain_card(chain)
            else:
                st.info(f"DAG Role: {active_h.get('dependency_role')} | Category: {active_h.get('category')}")
                
            # Directional Consistency
            dir_cons = active_h.get("directional_consistency", {})
            if dir_cons:
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 8px 12px; margin-top: 8px;">
                        <span style="font-size: 11px; font-weight: 700; color: #34D399;">📐 Directional Consistency:</span>
                        <span style="font-size: 11px; color: #D1D5DB;"> {dir_cons.get('status')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab_math:
            # Mathematical Decomposition
            math_decomp = active_h.get("mathematical_decomposition")
            if math_decomp:
                render_mathematical_decomposition_card(math_decomp)
                
            # Control Group Summary
            ctrl_data = active_h.get("control_group_analysis", {})
            render_control_group_summary(ctrl_data)
            
            # Plot Difference-in-Differences cohort if applicable
            if active_h["id"] in ["H1_PRICING_PRESSURE", "H2_COMPETITOR_CAMPAIGN"]:
                repo = DataRepository.get_instance()
                df_cohort = repo.get_cohort_comparison(region="Region B", product="Product Suite Alpha")
                fig_did = plot_did_cohort(df_cohort)
                st.plotly_chart(fig_did, use_container_width=True)
                
        with tab_lag:
            # Temporal Precedence Card
            temp = active_h.get("temporal_alignment", {})
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 10px 14px; margin-bottom: 10px;">
                    <div style="font-size: 11px; font-weight: 700; color: #818CF8; text-transform: uppercase;">⏱️ Temporal Precedence Signal (τ Lead-Time)</div>
                    <div style="font-size: 13px; font-weight: 600; color: #FFFFFF; margin-top: 2px;">Shock Event: {temp.get('shock_event')} ({temp.get('shock_date')})</div>
                    <div style="font-size: 12px; color: #9CA3AF; margin-top: 2px;">{temp.get('assessment')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Historical Lag Analysis
            lag = active_h.get("lag_analysis", {})
            if lag:
                st.markdown(
                    f"""
                    <div style="background: rgba(129, 140, 248, 0.04); border: 1px solid rgba(129, 140, 248, 0.2); border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
                        <div style="font-size: 11px; font-weight: 700; color: #A5B4FC; text-transform: uppercase;">📈 Historical Lagged Cross-Correlation (Weeks 1-48)</div>
                        <div style="font-size: 12px; color: #D1D5DB; margin-top: 4px;">
                            • <b>Best Lead-Lag:</b> Lag {lag.get('best_lag', 0)} weeks (Strength |r| = <b>{lag.get('lag_strength', 0.0):.3f}</b>, Direction: <code>{lag.get('lag_direction')}</code>)
                        </div>
                        <div style="font-size: 11px; color: #9CA3AF; margin-top: 2px;">
                            • Profile (L0..L4): <code>{lag.get('lag_correlations')}</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # Tested Predictions
            preds = active_h.get("predictions", [])
            if preds:
                st.caption("Empirical prediction verification:")
                for p in preds:
                    render_prediction_card(p)
            else:
                st.caption("No explicit predictions defined for this hypothesis.")

        with tab_ledgers:
            # Supporting Evidence Ledger
            st.markdown("<div style='font-size: 12px; font-weight: 700; color: #10B981; text-transform: uppercase; margin-bottom: 4px;'>✅ Supporting Evidence Ledger</div>", unsafe_allow_html=True)
            for supp in active_h.get("supporting_evidence", []):
                st.markdown(f"<div style='font-size: 12px; color: #D1D5DB; margin-bottom: 4px; padding-left: 6px; border-left: 2px solid #10B981;'>{supp}</div>", unsafe_allow_html=True)
                
            # Contradictory Evidence Ledger
            st.markdown("<div style='font-size: 12px; font-weight: 700; color: #EF4444; text-transform: uppercase; margin: 10px 0 4px 0;'>⚠️ Contradictory Facts / Negative Penalties</div>", unsafe_allow_html=True)
            for contra in active_h.get("contradictory_evidence", []):
                st.markdown(f"<div style='font-size: 12px; color: #D1D5DB; margin-bottom: 4px; padding-left: 6px; border-left: 2px solid #EF4444;'>{contra}</div>", unsafe_allow_html=True)
                
            # Missing Signals Ledger
            missing = active_h.get("missing_expected_evidence", [])
            if missing:
                st.markdown("<div style='font-size: 12px; font-weight: 700; color: #9CA3AF; text-transform: uppercase; margin: 10px 0 4px 0;'>🔍 Missing Expected Signals</div>", unsafe_allow_html=True)
                for m in missing:
                    st.markdown(f"<div style='font-size: 12px; color: #9CA3AF; margin-bottom: 4px; padding-left: 6px; border-left: 2px solid #6B7280;'>{m}</div>", unsafe_allow_html=True)

        with tab_reason:
            # Confounders
            st.markdown("<div style='font-size: 12px; font-weight: 700; color: #F59E0B; text-transform: uppercase; margin-bottom: 6px;'>🌪️ Confounding Factor Analysis</div>", unsafe_allow_html=True)
            render_confounders_summary(active_h.get("confounders", []))
            
            # Winner reasoning chain (if available)
            reasoning_chain = active_h.get("reasoning_chain", [])
            if reasoning_chain:
                st.markdown("<div style='font-size: 12px; font-weight: 700; color: #818CF8; text-transform: uppercase; margin: 12px 0 6px 0;'>🏆 Why This Hypothesis Ranked #1 (Structured Proof)</div>", unsafe_allow_html=True)
                for step in reasoning_chain:
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.02); border-left: 2px solid #818CF8; padding: 4px 8px; margin-bottom: 4px; border-radius: 0 4px 4px 0;">
                            <span style="font-size: 11px; font-weight: 700; color: #A5B4FC;">{step.get('step')}</span>: 
                            <span style="font-size: 11px; color: #D1D5DB;">{step.get('finding')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
        # Data Lineage
        st.markdown(
            f"""
            <div style="font-size: 11px; color: #6B7280; margin: 12px 0 8px 0;">
                📦 <b>Data Lineage:</b> {active_h.get('data_lineage', 'ERP Sales Ledger')}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        if st.button("🛠️ Simulate Action Impact (Screen 4) →", type="primary", use_container_width=True):
            set_screen("simulation")

    # =========================================================================
    # RIGHT PANE: EDITH CONVERSATIONAL REASONING CONSOLE
    # =========================================================================
    with col_right:
        render_edith_console(anomaly_ctx, hypotheses, active_h)
