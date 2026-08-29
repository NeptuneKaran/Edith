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
    is_demo = repo.active_source_info.get("is_demo", True)
    sem_model = repo.get_semantic_model()
    
    kpi_name = sem_model.primary_measure_label if (sem_model and sem_model.primary_measure_label) else anom_ctx.get("kpi_name", "Monthly B2B Sales")
    unit_symbol = sem_model.primary_measure_unit if (sem_model and sem_model.primary_measure_unit) else "$"
    
    curr_val = anom_ctx.get("current_value", 1_253_600.0)
    base_val = anom_ctx.get("baseline_value", 1_401_300.0)
    d_val = anom_ctx.get("delta_value", -147_700.0)
    d_pct = anom_ctx.get("delta_pct", -10.54)
    z_sc = anom_ctx.get("z_score", -2.30)
    wk_lbl = anom_ctx.get("current_week_label", "Week 08, 2026")
    
    primary_dim_name = contrib_ctx.get("primary_dimension_name", "Region")
    primary_dim_val = contrib_ctx.get("primary_dimension_val", "Region B")
    primary_dim_share = contrib_ctx.get("primary_dimension_share", 97.3)
    
    reg_name = contrib_ctx.get("primary_region", "Region B")
    reg_pct = contrib_ctx.get("primary_region_share", 97.3)
    tier_name = contrib_ctx.get("primary_tier", "Enterprise")
    prod_name = contrib_ctx.get("primary_product", "Product Suite Alpha")
    
    # Value format helper
    def fmt_val(v: float) -> str:
        if unit_symbol == "$":
            return f"${v:,.0f}"
        elif unit_symbol == "%":
            return f"{v:.1f}%"
        else:
            return f"{v:,.1f} {unit_symbol}".strip()

    # Epistemology & Temporal Mode Evaluation
    is_temporal = repo.active_source_info.get("feature_status", {}).get("is_temporal", True)
    if sem_model and any(kw in sem_model.analysis_grain.lower() for kw in ["snapshot", "cross-sectional", "record", "event"]):
        is_temporal = False
        
    is_anomaly = anom_ctx.get("is_anomaly", True) if is_temporal else False
    
    # =========================================================================
    # 1. PROMINENT ACTIVE INCIDENT HERO BANNER
    # =========================================================================
    if is_temporal:
        border_color = "#FECACA" if is_anomaly else "#BBF7D0"
        bar_color = "#DC2626" if is_anomaly else "#16A34A"
        tag_bg = "#FEE2E2" if is_anomaly else "#DCFCE7"
        tag_color = "#991B1B" if is_anomaly else "#166534"
        tag_label = "ACTIVE DEFICIT ANOMALY" if is_anomaly else "NORMAL OPERATING STATUS"
        badge_text = f"Z = {z_sc:.2f}"
        
        trajectory_html = f'<b>Observed Trajectory:</b> Metric moved by <b>{d_pct:+.1f}% ({fmt_val(d_val)})</b> relative to historical baseline. Multi-dimensional decomposition localizes <b>{primary_dim_share:.1f}% of net variance</b> to segment <b>{primary_dim_val}</b> ({primary_dim_name}).'
        
        box3_title = "Net Delta"
        box3_val = f"{d_pct:+.1f}%"
        box3_color = bar_color
        box4_title = "Primary Concentration"
        box4_val = f"{primary_dim_val}"
    else:
        border_color = "#93C5FD"
        bar_color = "#2563EB"
        tag_bg = "#EFF6FF"
        tag_color = "#1E40AF"
        tag_label = "CROSS-SECTIONAL SNAPSHOT" if (sem_model and "record" not in sem_model.analysis_grain.lower()) else "RECORD-LEVEL EVENT LOG"
        badge_text = f"{repo.active_source_info.get('row_count', len(repo.tables.get('sales', []))):,} Records"
        
        trajectory_html = f'<b>Cross-Sectional Analysis:</b> Evaluating empirical segment distribution, driver associations, and data quality across active records without temporal assumptions. Multi-dimensional breakdown isolates <b>{primary_dim_share:.1f}% of aggregate concentration</b> to segment <b>{primary_dim_val}</b> ({primary_dim_name}).'
        
        box3_title = "Primary Epicenter"
        box3_val = f"{primary_dim_val}"
        box3_color = "#0F172A"
        box4_title = "Concentration Share"
        box4_val = f"{primary_dim_share:.1f}%"
    
    hero_html = (
        f'<div style="background: #FFFFFF; border: 1px solid {border_color}; border-left: 5px solid {bar_color}; border-radius: 10px; padding: 22px 26px; margin-bottom: 24px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
        f'<div style="display: flex; align-items: center; gap: 10px;">'
        f'<span style="background: {tag_bg}; color: {tag_color}; border: 1px solid {border_color}; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px; text-transform: uppercase;">{tag_label}</span>'
        f'<span style="font-size: 16px; font-weight: 800; color: #0F172A;">{kpi_name} {"Evaluation (" + wk_lbl + ")" if is_temporal else "Snapshot & Concentration Profile"}</span>'
        f'</div>'
        f'<span style="background: {bar_color}; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800;">{badge_text}</span>'
        f'</div>'
        f'<div style="font-size: 14px; color: #334155; line-height: 1.6; margin-bottom: 16px;">'
        f'{trajectory_html}'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Observed Value</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; margin-top: 2px;">{fmt_val(curr_val)}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">{"Expected Baseline" if is_temporal else "Metric Measure"}</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: #2563EB; margin-top: 2px;">{fmt_val(base_val) if is_temporal else kpi_name}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">{box3_title}</div>'
        f'<div style="font-size: 20px; font-weight: 800; color: {box3_color}; margin-top: 2px;">{box3_val}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; padding: 12px 14px; border-radius: 6px; border: 1px solid #E2E8F0;">'
        f'<div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">{box4_title}</div>'
        f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 2px;">{box4_val}</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 10px 14px; font-size: 12px; color: #1E40AF; display: flex; align-items: center; justify-content: space-between;">'
        f'<span>🎯 <b>Recommended Next Step:</b> Traverse to Diagnostic stage to isolate dimensional concentrations and examine driver associations.</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Primary CTA Button to Start Investigation
    col_btn, col_empty = st.columns([2.0, 3.0])
    with col_btn:
        if st.button("🚀 Start Deep Diagnostic (Diagnose) →", key="btn_start_investigation_hero", type="primary", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            set_screen("diagnostic")
            st.rerun()
            
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    
    # =========================================================================
    # 2. PORTFOLIO KPI HEALTH SUMMARY CARDS
    # =========================================================================
    st.markdown("<h3 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 12px;'>📊 Monitored KPI & Data Telemetry Status</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    if is_demo:
        # Standard B2B SaaS Demo 4-Card Summary
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
    else:
        # Dynamic Custom Dataset 4-Card Summary
        quality_rep = repo.get_data_quality_report()
        correlations = repo.get_driver_correlations().get("correlations", {})
        top_drv_name = list(correlations.keys())[0] if correlations else "No Drivers"
        top_drv_r = correlations[top_drv_name]["pearson_r"] if correlations else 0.0
        
        with col1:
            render_kpi_card(
                title=f"{kpi_name}",
                value_str=fmt_val(curr_val),
                delta_str=f"{d_pct:+.1f}%",
                status="P1 Anomaly" if is_anomaly else "Normal",
                is_anomaly=is_anomaly
            )
            if st.button("🔍 View Diagnostic →", key="btn_diag_custom_kpi", type="primary", use_container_width=True):
                st.session_state.selected_kpi_id = "kpi_b2b_sales"
                set_screen("diagnostic")
                st.rerun()
                
        with col2:
            render_kpi_card(
                title=f"Top Concentration",
                value_str=str(primary_dim_val),
                delta_str=f"{primary_dim_share:.1f}% Share",
                status=str(primary_dim_name),
                is_anomaly=False
            )
            if st.button("Slices & Waterfall", key="btn_diag_custom_dim", use_container_width=True):
                st.session_state.selected_kpi_id = "kpi_b2b_sales"
                set_screen("diagnostic")
                st.rerun()
                
        with col3:
            render_kpi_card(
                title=f"Top Driver Correlation",
                value_str=f"r = {top_drv_r:+.2f}" if correlations else "N/A",
                delta_str=top_drv_name.replace("_", " ").title() if correlations else "None",
                status="Active Driver" if correlations else "Unmapped",
                is_anomaly=False
            )
            if st.button("Driver Associations", key="btn_diag_custom_drv", use_container_width=True):
                set_screen("workspace")
                st.rerun()
                
        with col4:
            render_kpi_card(
                title="Data Quality Score",
                value_str=f"{quality_rep.get('data_quality_score', 100.0):.1f}%",
                delta_str=f"{quality_rep.get('total_rows', 0):,} Rows",
                status="High Integrity" if quality_rep.get('data_quality_score', 100.0) >= 90.0 else "Audit Needed",
                is_anomaly=False
            )
            if st.button("Data Sources", key="btn_ret_sources_card", use_container_width=True):
                set_screen("sources")
                st.rerun()

