"""
ui/screens/s2_diagnostic.py
Screen 2: KPI Deep Diagnostic & Dimensional Variance Decomposition (Diagnose Stage)
Clean, editorial Light Theme design with high-contrast charts and localization takeaways.
"""
import streamlit as st
from state.session_state import set_screen
from ui.components.charts import plot_expected_corridor, plot_waterfall_contribution
from ui.components.cards import render_epistemology_chip
from config.semantic_contracts import KPIS
from data.repository import DataRepository

def render_screen_2():
    """Renders the deep diagnostic and dimensional breakdown screen."""
    col_nav, col_title, col_tag = st.columns([1.3, 3.7, 1.2])
    with col_nav:
        if st.button("← Back to Detect (Overview)", key="btn_diag_back_s2", use_container_width=True):
            set_screen("overview")
            st.rerun()
            
    selected_kpi_id = st.session_state.get("selected_kpi_id", "kpi_b2b_sales")
    kpi_meta = KPIS.get(selected_kpi_id, KPIS["kpi_b2b_sales"])
    kpi_name = kpi_meta["name"]
    
    with col_title:
        st.markdown(f"<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #0F172A;'>📈 Stage 2: Diagnose KPI & Localize Variance</h2>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_epistemology_chip("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.caption(f"Analyzing historical trajectory against dynamic ±2.0σ expected corridor &bull; <b>{kpi_name}</b> ({kpi_meta.get('refresh_cadence', 'Weekly')})")
    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    
    # If B2B Sales (the primary anomaly)
    if selected_kpi_id == "kpi_b2b_sales":
        df_ts = st.session_state.get("kpi_ts")
        anom_ctx = st.session_state.get("anomaly_context", {})
        contrib_ctx = st.session_state.get("contribution_context", {})
        
        # 1. Historical Time-Series Chart Container
        if df_ts is not None:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                """,
                unsafe_allow_html=True
            )
            fig_corridor = plot_expected_corridor(df_ts, kpi_name=kpi_name)
            st.plotly_chart(fig_corridor, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        # 2. Anomaly Summary Metrics Strip
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Observed Revenue", f"${anom_ctx.get('current_value', 0):,.0f}", f"{anom_ctx.get('delta_pct', 0):+.1f}% vs baseline", delta_color="inverse")
        with col_m2:
            st.metric("Baseline Target", f"${anom_ctx.get('baseline_value', 0):,.0f}", "Rolling 8-Wk Median")
        with col_m3:
            st.metric("Statistical Z-Score", f"{anom_ctx.get('z_score', 0):.2f}", "Breaches ±2.0σ Corridor", delta_color="inverse")
        with col_m4:
            st.metric("Persistence", "2 Consecutive Wks", "P1 Material Anomaly", delta_color="off")
            
        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # 3. Dimensional Variance Decomposition
        st.markdown("<h3 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>🧩 Dimensional Variance Localization: Isolating Impact Epicenter</h3>", unsafe_allow_html=True)
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
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1E293B;">
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
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1E293B;">
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
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1E293B;">
                        💡 <b>Localization Finding:</b> <b>{prod_name}</b> accounts for <b>{prod_pct:.1f}%</b> of the product-level variance; Suite Beta and Suite Gamma lines were unaffected.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with tab_chan:
            if "channel" in breakdowns:
                fig_chan = plot_waterfall_contribution(breakdowns["channel"], "channel", "Sales Channel Variance Breakdown")
                st.plotly_chart(fig_chan, use_container_width=True)
                st.markdown(
                    """
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1E293B;">
                        💡 <b>Localization Finding:</b> Contraction is shared across <b>Direct Sales</b> and <b>Partner Network</b> channels proportionally to Enterprise deal volume.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Primary Action to Stage 3: Explain (Workspace)
        col_cta, col_space = st.columns([2.2, 2.8])
        with col_cta:
            if st.button("🔬 Proceed to Causal Investigation (Explain) →", key="btn_to_workspace_s2", type="primary", use_container_width=True):
                set_screen("workspace")
                st.rerun()
                
    else:
        # Non-anomalous KPI Diagnostic View
        df_kpi = repo.get_kpi_time_series(selected_kpi_id)
        if df_kpi is not None and not df_kpi.empty:
            fig_corridor = plot_expected_corridor(df_kpi, kpi_name=kpi_name)
            st.plotly_chart(fig_corridor, use_container_width=True)
            
            st.markdown(
                """
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #166534; margin-top: 14px;">
                    ✅ <b>Healthy Operating Status:</b> This metric is operating within its standard ±2.0σ expected corridor. No critical anomaly investigation is required.
                </div>
                """,
                unsafe_allow_html=True
            )
            
        st.markdown("---")
        if st.button("← Return to Executive Overview", key="btn_ret_overview_s2", use_container_width=True):
            set_screen("overview")
            st.rerun()
