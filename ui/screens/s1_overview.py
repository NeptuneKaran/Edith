"""
ui/screens/s1_overview.py
Screen 1: Executive Command Center & Portfolio Health Overview (Detect Stage)
Clean, editorial Light Theme design with prominent incident hero and high-contrast metrics.
"""
import streamlit as st
from ui.components.cards import render_kpi_card, render_epistemology_chip
from state.session_state import set_screen
from data.repository import DataRepository

def render_screen_1():
    """Renders the Executive Command Center overview screen."""
    col_hdr, col_tag = st.columns([4, 1.2])
    with col_hdr:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #0F172A;'>🏛️ Executive Command Center</h2>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 13px; color: #64748B; margin-top: 2px;'>Continuous portfolio telemetry scan across commercial, financial, and retention streams &bull; <b>Fiscal Q1 2026 (Week 08)</b></div>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_epistemology_chip("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    anom_ctx = st.session_state.get("anomaly_context", {})
    contrib_ctx = st.session_state.get("contribution_context", {})
    
    curr_val = anom_ctx.get("current_value", 1_253_600.0)
    base_val = anom_ctx.get("baseline_value", 1_401_300.0)
    d_val = anom_ctx.get("delta_value", -147_700.0)
    d_pct = anom_ctx.get("delta_pct", -10.54)
    z_sc = anom_ctx.get("z_score", -2.30)
    wk_lbl = anom_ctx.get("current_week_label", "Week 08, 2026")
    
    reg_name = contrib_ctx.get("primary_region", "Region B")
    reg_pct = contrib_ctx.get("primary_region_share", 97.3)
    tier_name = contrib_ctx.get("primary_tier", "Enterprise")
    prod_name = contrib_ctx.get("primary_product", "Product Suite Alpha")
    
    # =========================================================================
    # 1. PROMINENT ACTIVE INCIDENT HERO BANNER
    # =========================================================================
    hero_html = (
        f'<div style="background: #FFFFFF; border: 1px solid #FECACA; border-left: 5px solid #DC2626; border-radius: 10px; padding: 22px 26px; margin-bottom: 24px; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.06);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
        f'<div style="display: flex; align-items: center; gap: 10px;">'
        f'<span style="background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; text-transform: uppercase;">CRITICAL ACTIVE INCIDENT</span>'
        f'<span style="font-size: 16px; font-weight: 800; color: #0F172A;">Monthly B2B Sales Corridor Breach ({wk_lbl})</span>'
        f'</div>'
        f'<span style="background: #DC2626; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800;">Z = {z_sc:.2f} (Breach &gt; 2.0σ)</span>'
        f'</div>'
        f'<div style="font-size: 14px; color: #334155; line-height: 1.6; margin-bottom: 16px;">'
        f'<b>Business Impact:</b> Gross revenue fell by <b>-${abs(d_val):,.0f} ({d_pct:+.1f}%)</b> below expected baseline over the last 2 consecutive weeks, breaching the lower threshold boundary ($1.27M). Multi-dimensional decomposition localizes <b>{reg_pct:.1f}% of the aggregate deficit</b> specifically to <b>{reg_name} {tier_name} contracts on {prod_name}</b>.'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Observed Revenue</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-top: 2px;">${curr_val:,.0f}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Expected Baseline</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: #2563EB; margin-top: 2px;">${base_val:,.0f}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Revenue Deficit</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: #DC2626; margin-top: 2px;">${d_val:,.0f} ({d_pct:+.1f}%)</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Primary Epicenter</div>'
        f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{reg_name} {tier_name}</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #1E40AF; display: flex; align-items: center; justify-content: space-between;">'
        f'<span>🎯 <b>Recommended Next Step:</b> Run deep diagnostic to isolate localized variance, then traverse metric dependency DAG to evaluate pricing elasticity vs competitor promotions.</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Primary CTA Button to Start Investigation
    col_btn, col_empty = st.columns([2.0, 3.0])
    with col_btn:
        if st.button("🚀 Start Causal Investigation (Diagnose) →", key="btn_start_investigation_hero", type="primary", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            set_screen("diagnostic")
            st.rerun()
            
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    
    # =========================================================================
    # 2. PORTFOLIO KPI HEALTH SUMMARY CARDS
    # =========================================================================
    st.markdown("<h3 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>📊 Monitored Portfolio KPI Status</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: B2B Sales (The Primary Anomaly)
    with col1:
        render_kpi_card(
            title="Monthly B2B Sales",
            value_str=f"${curr_val:,.0f}",
            delta_str=f"{d_pct:+.1f}%",
            status="P1 Anomaly",
            is_anomaly=True
        )
        if st.button("🔍 Diagnose Sales →", key="btn_inv_sales_card", type="primary", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            set_screen("diagnostic")
            st.rerun()
            
    # KPI 2: Gross Margin % (Normal)
    df_margin = repo.get_kpi_time_series("kpi_gross_margin")
    curr_margin = df_margin.iloc[-1]["value"]
    with col2:
        render_kpi_card(
            title="Gross Margin %",
            value_str=f"{curr_margin:.1f}%",
            delta_str="+0.2%",
            status="Normal",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_margin_card", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_gross_margin"
            set_screen("diagnostic")
            st.rerun()
            
    # KPI 3: Customer Churn Rate (Normal)
    df_churn = repo.get_kpi_time_series("kpi_customer_churn")
    curr_churn = df_churn.iloc[-1]["value"]
    with col3:
        render_kpi_card(
            title="Churn Rate",
            value_str=f"{curr_churn:.2f}%",
            delta_str="-0.04%",
            status="Normal",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_churn_card", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_customer_churn"
            set_screen("diagnostic")
            st.rerun()
            
    # KPI 4: Marketing ROAS (Normal)
    df_roas = repo.get_kpi_time_series("kpi_marketing_roas")
    curr_roas = df_roas.iloc[-1]["value"]
    with col4:
        render_kpi_card(
            title="Marketing ROAS",
            value_str=f"{curr_roas:.2f}x",
            delta_str="+0.08x",
            status="Normal",
            is_anomaly=False
        )
        if st.button("View Diagnostic", key="btn_diag_roas_card", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_marketing_roas"
            set_screen("diagnostic")
            st.rerun()
