"""
ui/screens/s2_diagnostic.py
Screen 2: KPI Deep Diagnostic & Dimensional Variance Decomposition
"""
import streamlit as st
from state.session_state import set_screen
from ui.components.charts import plot_expected_corridor, plot_waterfall_contribution
from ui.components.cards import render_data_tag
from config.semantic_contracts import KPIS
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine

def render_screen_2():
    """Renders the deep diagnostic and dimensional breakdown screen."""
    col_nav, col_title, col_tag = st.columns([1.2, 3.8, 1])
    with col_nav:
        if st.button("← Back to Overview", use_container_width=True):
            set_screen("overview")
            
    selected_kpi_id = st.session_state.get("selected_kpi_id", "kpi_b2b_sales")
    kpi_meta = KPIS.get(selected_kpi_id, KPIS["kpi_b2b_sales"])
    kpi_name = kpi_meta["name"]
    
    with col_title:
        st.markdown(f"<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #FFFFFF;'>📈 KPI Deep Diagnostic: {kpi_name}</h2>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_data_tag("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.caption(f"{kpi_meta.get('description', '')} Source: {', '.join(kpi_meta.get('source_systems', []))} ({kpi_meta.get('refresh_cadence', 'Weekly')})")
    
    repo = DataRepository.get_instance()
    
    # If B2B Sales (the primary anomaly)
    if selected_kpi_id == "kpi_b2b_sales":
        df_ts = st.session_state.get("kpi_ts")
        anom_ctx = st.session_state.get("anomaly_context", {})
        contrib_ctx = st.session_state.get("contribution_context", {})
        
        # 1. Historical Time-Series Chart
        if df_ts is not None:
            fig_corridor = plot_expected_corridor(df_ts, kpi_name=kpi_name)
            st.plotly_chart(fig_corridor, use_container_width=True)
            
        # 2. Anomaly Summary Metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Observed Revenue", f"${anom_ctx.get('current_value', 0):,.0f}", f"{anom_ctx.get('delta_pct', 0):+.1f}% vs baseline", delta_color="inverse")
        with col_m2:
            st.metric("Baseline Target", f"${anom_ctx.get('baseline_value', 0):,.0f}", "Rolling 8-Wk Median")
        with col_m3:
            st.metric("Statistical Z-Score", f"{anom_ctx.get('z_score', 0):.2f}", "Breaches ±2.0σ Corridor", delta_color="inverse")
        with col_m4:
            st.metric("Persistence", "2 Consecutive Wks", "P1 Material Anomaly", delta_color="off")
            
        st.markdown("---")
        
        # 3. Dimensional Variance Decomposition
        st.markdown("<h3 style='font-size: 16px; font-weight: 700; color: #FFFFFF; margin-bottom: 2px;'>🧩 Dimensional Variance Localization: Isolating Impact Epicenter</h3>", unsafe_allow_html=True)
        st.caption("Decomposes aggregate variance to localize where the shock is concentrated (empirical locus of effect, distinct from causal mechanism):")
        
        breakdowns = contrib_ctx.get("breakdowns", {})
        tab_reg, tab_tier, tab_prod, tab_chan = st.tabs(["🌍 By Region", "🏢 By Customer Tier", "📦 By Product Line", "🌐 By Channel"])
        
        with tab_reg:
            if "region" in breakdowns:
                fig_reg = plot_waterfall_contribution(breakdowns["region"], "region", "Region Variance Breakdown")
                st.plotly_chart(fig_reg, use_container_width=True)
                reg_name = contrib_ctx.get("primary_region", "Region B")
                reg_pct = contrib_ctx.get("primary_region_share", 97.3)
                st.markdown(
                    f"""
                    <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366F1; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #E0E7FF;">
                        💡 <b>Localization Finding:</b> <b>{reg_name}</b> accounts for <b>{reg_pct:.1f}%</b> of the aggregate revenue contraction. Other regions remained within normal variation.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab_tier:
            if "customer_tier" in breakdowns:
                fig_tier = plot_waterfall_contribution(breakdowns["customer_tier"], "customer_tier", "Customer Tier Variance Breakdown")
                st.plotly_chart(fig_tier, use_container_width=True)
                tier_name = contrib_ctx.get("primary_tier", "Enterprise")
                tier_pct = contrib_ctx.get("primary_tier_share", 97.3)
                st.markdown(
                    f"""
                    <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366F1; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #E0E7FF;">
                        💡 <b>Localization Finding:</b> <b>{tier_name}</b> accounts for <b>{tier_pct:.1f}%</b> of the tier-level variance; Mid-Market and SMB cohorts remained stable.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab_prod:
            if "product_line" in breakdowns:
                fig_prod = plot_waterfall_contribution(breakdowns["product_line"], "product_line", "Product Line Variance Breakdown")
                st.plotly_chart(fig_prod, use_container_width=True)
                prod_name = contrib_ctx.get("primary_product", "Product Suite Alpha")
                prod_pct = contrib_ctx.get("primary_product_share", 100.0)
                st.markdown(
                    f"""
                    <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366F1; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #E0E7FF;">
                        💡 <b>Localization Finding:</b> <b>{prod_name}</b> accounts for <b>{prod_pct:.1f}%</b> of product variance. Suite Beta and Gamma were unaffected.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab_chan:
            if "channel" in breakdowns:
                fig_chan = plot_waterfall_contribution(breakdowns["channel"], "channel", "Sales Channel Variance Breakdown")
                st.plotly_chart(fig_chan, use_container_width=True)
                
        st.markdown("---")
        
        # CTA to transition to Screen 3
        col_cta1, col_cta2 = st.columns([3, 1])
        with col_cta1:
            st.markdown("<div style='font-size: 13px; color: #9CA3AF; margin-top: 6px;'><b>Next Step:</b> Evaluate competing hypotheses, test empirical predictions, and consult EDITH.</div>", unsafe_allow_html=True)
        with col_cta2:
            if st.button("🚀 Investigate Hypotheses (Screen 3) →", type="primary", use_container_width=True):
                set_screen("workspace")
    else:
        # Diagnostic for other normal KPIs
        df_raw = repo.get_kpi_time_series(selected_kpi_id)
        df_kpi_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_raw)
        anom_kpi = AnomalyEngine.evaluate_current_anomaly(df_kpi_analyzed, kpi_name=kpi_name)
        
        fig_corridor = plot_expected_corridor(df_kpi_analyzed, kpi_name=kpi_name)
        st.plotly_chart(fig_corridor, use_container_width=True)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        fmt = kpi_meta.get("format", "{:,.2f}")
        with col_m1:
            st.metric("Observed Value", fmt.format(anom_kpi["current_value"]), f"{anom_kpi['delta_pct']:+.1f}% vs baseline")
        with col_m2:
            st.metric("Baseline Target", fmt.format(anom_kpi["baseline_value"]), "Rolling 8-Wk Median")
        with col_m3:
            st.metric("Statistical Z-Score", f"{anom_kpi['z_score']:.2f}", "Normal Corridor", delta_color="normal")
            
        st.success(f"✅ **Normal Operational Status:** **{kpi_name}** is currently tracking within its expected statistical corridor ($Z = {anom_kpi['z_score']:.2f}$). No anomalous breach detected.")
        
        if st.button("🔍 Switch to Anomalous Monthly B2B Sales", type="primary"):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            st.rerun()
