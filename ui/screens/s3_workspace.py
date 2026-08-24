"""
ui/screens/s3_workspace.py
Screen 3: Dual-Pane Investigation Workspace
Left: Deterministic Analytical Canvas | Right: Edith Conversational Console
"""
import streamlit as st
from state.session_state import set_screen, select_hypothesis
from ui.components.cards import render_evidence_score_badge, render_data_tag
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
        st.markdown("<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #FFFFFF;'>🔬 Investigation Workspace: Multi-Hypothesis & Evidence Engine</h2>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_data_tag("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.caption("Transparent auditability between deterministic empirical evidence (Left Canvas) and cognitive AI synthesis (Right Console).")
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    
    hypotheses = st.session_state.get("hypotheses", [])
    anomaly_ctx = st.session_state.get("anomaly_context", {})
    selected_hypo_id = st.session_state.get("selected_hypothesis_id", "H1_PRICING_PRESSURE")
    
    # Get active hypothesis object
    active_h = next((h for h in hypotheses if h["id"] == selected_hypo_id), hypotheses[0])
    
    col_left, col_right = st.columns([1.15, 1.0], gap="large")
    
    # =========================================================================
    # LEFT PANE: DETERMINISTIC ANALYTICAL EVIDENCE CANVAS
    # =========================================================================
    with col_left:
        st.markdown("<h3 style='margin:0; padding:0; font-size: 17px; font-weight: 700; color: #FFFFFF;'>📊 Deterministic Analytical Evidence Canvas</h3>", unsafe_allow_html=True)
        st.caption("Competing candidate hypotheses evaluated against empirical telemetry:")
        
        # 1. Hypothesis Selection Cards
        for h in hypotheses:
            is_active = (h["id"] == selected_hypo_id)
            score = h["evidence_score"]
            
            # Prefix badge icon
            if score >= 0.75:
                icon = "🟢"
            elif score >= 0.40:
                icon = "🟡"
            elif score > 0.0:
                icon = "⚪"
            else:
                icon = "🔴"
                
            btn_label = f"{icon} {h['name']} (Score: {score:.2f})"
            
            col_b1, col_b2 = st.columns([2.8, 1.2])
            with col_b1:
                if st.button(btn_label, key=f"sel_{h['id']}", type="primary" if is_active else "secondary", use_container_width=True):
                    select_hypothesis(h["id"])
                    st.rerun()
            with col_b2:
                render_evidence_score_badge(score, label="Evidence Strength")
                
        st.markdown("---")
        
        # 2. Selected Hypothesis Deep-Dive
        st.markdown(f"<h4 style='font-size: 15px; font-weight: 700; color: #FFFFFF;'>🔍 Deep-Dive: {active_h['name']}</h4>", unsafe_allow_html=True)
        
        # Temporal Alignment Card
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
        
        # Supporting Evidence Ledger
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #10B981; text-transform: uppercase; margin-bottom: 4px;'>✅ Supporting Evidence Ledger</div>", unsafe_allow_html=True)
        for supp in active_h.get("supporting_evidence", []):
            st.markdown(f"<div style='font-size: 12px; color: #D1D5DB; margin-bottom: 4px; padding-left: 6px; border-left: 2px solid #10B981;'>{supp}</div>", unsafe_allow_html=True)
            
        # Contradictory Evidence Ledger
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #EF4444; text-transform: uppercase; margin: 10px 0 4px 0;'>⚠️ Contradictory Facts / Penalties</div>", unsafe_allow_html=True)
        for contra in active_h.get("contradictory_evidence", []):
            st.markdown(f"<div style='font-size: 12px; color: #D1D5DB; margin-bottom: 4px; padding-left: 6px; border-left: 2px solid #EF4444;'>{contra}</div>", unsafe_allow_html=True)
            
        # Difference-in-Differences Cohort Comparison (for Pricing / Competitor)
        if active_h["id"] in ["H1_PRICING_PRESSURE", "H2_COMPETITOR_CAMPAIGN"]:
            repo = DataRepository.get_instance()
            df_cohort = repo.get_cohort_comparison(region="Region B", product="Product Suite Alpha")
            fig_did = plot_did_cohort(df_cohort)
            st.plotly_chart(fig_did, use_container_width=True)
            
        # Data Lineage
        st.markdown(
            f"""
            <div style="font-size: 11px; color: #6B7280; margin: 8px 0;">
                📦 <b>Data Lineage:</b> {active_h.get('data_lineage')}
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
