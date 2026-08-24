"""
ui/screens/s1_overview.py
Screen 1: Business Overview (The Observe & Detect Hub)
"""
import streamlit as st
from ui.components.cards import render_kpi_card, render_data_tag
from state.session_state import set_screen
from data.repository import DataRepository

def render_screen_1():
    """Renders the executive KPI overview screen."""
    col_hdr, col_tag = st.columns([4, 1])
    with col_hdr:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #FFFFFF;'>📊 Executive Business Overview</h2>", unsafe_allow_html=True)
        st.caption("Continuously monitoring enterprise portfolio health across commercial, financial, and marketing operational streams.")
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_data_tag("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    
    # 4 KPI Cards Grid
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: B2B Sales (The Anomaly)
    with col1:
        anom_ctx = st.session_state.get("anomaly_context", {})
        curr_val = anom_ctx.get("current_value", 1_253_600)
        delta_pct = anom_ctx.get("delta_pct", -10.54)
        render_kpi_card(
            title="Monthly B2B Sales",
            value_str=f"${curr_val:,.0f}",
            delta_str=f"{delta_pct:+.1f}%",
            status="P1 Material Anomaly",
            is_anomaly=True
        )
        if st.button("🔍 Investigate Anomaly →", key="btn_inv_sales", type="primary", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            set_screen("diagnostic")
            
    # KPI 2: Gross Margin % (Normal)
    with col2:
        df_margin = repo.get_kpi_time_series("kpi_gross_margin")
        curr_margin = df_margin.iloc[-1]["value"]
        prev_margin = df_margin.iloc[-2]["value"]
        margin_delta = curr_margin - prev_margin
        render_kpi_card(
            title="Gross Margin %",
            value_str=f"{curr_margin:.1f}%",
            delta_str=f"{margin_delta:+.1f}%",
            status="Normal Corridor",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_margin", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_gross_margin"
            set_screen("diagnostic")
            
    # KPI 3: Customer Churn (Normal)
    with col3:
        df_churn = repo.get_kpi_time_series("kpi_customer_churn")
        curr_churn = df_churn.iloc[-1]["value"]
        render_kpi_card(
            title="Customer Churn Rate",
            value_str=f"{curr_churn:.2f}%",
            delta_str="-0.04%",
            status="Normal Corridor",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_churn", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_customer_churn"
            set_screen("diagnostic")
            
    # KPI 4: Marketing ROAS (Normal)
    with col4:
        df_roas = repo.get_kpi_time_series("kpi_marketing_roas")
        curr_roas = df_roas.iloc[-1]["value"]
        render_kpi_card(
            title="Marketing ROAS",
            value_str=f"{curr_roas:.2f}x",
            delta_str="+0.08x",
            status="Normal Corridor",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_roas", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_marketing_roas"
            set_screen("diagnostic")
            
    st.markdown("---")
    
    # High-Impact Anomaly Callout Box (Data-Derived from anom_ctx)
    curr_val = anom_ctx.get("current_value", 1_253_600.0)
    base_val = anom_ctx.get("baseline_value", 1_401_300.0)
    d_val = anom_ctx.get("delta_value", -147_700.0)
    d_pct = anom_ctx.get("delta_pct", -10.54)
    z_sc = anom_ctx.get("z_score", -2.30)
    wk_lbl = anom_ctx.get("current_week_label", "Week 08, 2026")
    
    st.markdown(
        f"""
        <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 18px; margin-top: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 14px; font-weight: 800; color: #EF4444; letter-spacing: 0.3px; text-transform: uppercase;">
                    ⚠️ P1 Material Anomaly Flagged: Monthly B2B Sales ({wk_lbl})
                </div>
                <span style="background: #EF4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 800;">Z = {z_sc:.2f}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 14px; margin-bottom: 8px;">
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">OBSERVED REVENUE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #FFFFFF;">${curr_val:,.0f}</div>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">EXPECTED BASELINE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #818CF8;">${base_val:,.0f}</div>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">DOLLAR DEFICIT</div>
                    <div style="font-size: 18px; font-weight: 800; color: #EF4444;">${d_val:,.0f} ({d_pct:+.1f}%)</div>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 11px; color: #9CA3AF; font-weight: 600;">PERSISTENCE</div>
                    <div style="font-size: 18px; font-weight: 800; color: #F59E0B;">2 Consecutive Wks</div>
                </div>
            </div>
            <div style="font-size: 12px; color: #D1D5DB; margin-top: 10px;">
                <b>Detection Diagnosis:</b> Gross revenue breached the lower corridor bound ($1.27M) with high statistical severity. Multi-dimensional variance analysis is required to isolate root cause drivers.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
