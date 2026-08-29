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
    is_demo = repo.active_source_info.get("is_demo", True)
    sem_model = repo.get_semantic_model()
    unit_sym = sem_model.primary_measure_unit if (sem_model and sem_model.primary_measure_unit) else "$"
    
    is_temporal = repo.active_source_info.get("feature_status", {}).get("is_temporal", True)
    if sem_model and any(kw in sem_model.analysis_grain.lower() for kw in ["snapshot", "cross-sectional", "record", "event"]):
        is_temporal = False

    def fmt_v(v: float) -> str:
        if unit_sym == "$":
            return f"${v:,.0f}"
        elif unit_sym == "%":
            return f"{v:.1f}%"
        else:
            return f"{v:,.1f} {unit_sym}".strip()

    # Primary Investigated Metric
    if selected_kpi_id == "kpi_b2b_sales":
        df_ts = st.session_state.get("kpi_ts")
        anom_ctx = st.session_state.get("anomaly_context", {})
        contrib_ctx = st.session_state.get("contribution_context", {})
        
        # 1. Historical Time-Series Chart Container (Temporal datasets only)
        if is_temporal and df_ts is not None and len(df_ts) > 1:
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
                val_lbl = "Observed Revenue" if is_demo else "Observed Value"
                st.metric(val_lbl, fmt_v(anom_ctx.get('current_value', 0)), f"{anom_ctx.get('delta_pct', 0):+.1f}% vs baseline", delta_color="inverse")
            with col_m2:
                base_lbl = "Baseline Target" if is_demo else "Expected Baseline"
                st.metric(base_lbl, fmt_v(anom_ctx.get('baseline_value', 0)), "Rolling Baseline")
            with col_m3:
                st.metric("Statistical Z-Score", f"{anom_ctx.get('z_score', 0):.2f}", "Corridor Variance", delta_color="inverse")
            with col_m4:
                st.metric("Persistence", "2 Consecutive Wks" if is_demo else "Active Telemetry", "Material Variance" if anom_ctx.get('is_anomaly') else "Normal", delta_color="off")
        else:
            # Non-temporal Snapshot Mode: Display Distribution Profile
            dist_stats = repo.get_distribution_statistics()
            outlier_cnt = dist_stats.get("outlier_count", 0)
            outlier_pct = dist_stats.get("outlier_pct", 0.0)
            p50_val = dist_stats.get("percentiles", {}).get("P50_median", anom_ctx.get('current_value', 0))
            iqr_val = dist_stats.get("iqr", 0.0)
            skew_val = dist_stats.get("skewness", 0.0)
            
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; font-size: 15px; font-weight: 800; color: #0F172A;">📊 Cross-Sectional Distribution & Outlier Profile</h4>
                        <span style="background: #EFF6FF; color: #1D4ED8; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 4px;">Snapshot Grain</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; line-height: 1.5;">
                        Parametric and non-parametric distribution statistics across active records. Identifies concentration spread and empirical outlier boundaries ($1.5 \\times \\text{{IQR}}$).
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Observed Aggregate", fmt_v(anom_ctx.get('current_value', 0)), f"{dist_stats.get('count', 0):,} Records")
            with col_m2:
                st.metric("Median (P50)", fmt_v(p50_val), f"IQR: {iqr_val:.2f}")
            with col_m3:
                st.metric("Distribution Skewness", f"{skew_val:.2f}", "Symmetric" if abs(skew_val) < 0.5 else ("Right-Skewed" if skew_val > 0 else "Left-Skewed"))
            with col_m4:
                st.metric("Empirical Outliers", f"{outlier_cnt} ({outlier_pct:.1f}%)", "Outside 1.5x IQR", delta_color="off")
            
        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # 3. Dimensional Variance / Concentration Decomposition
        decomp_title = "🧩 Dimensional Variance Localization: Isolating Impact Epicenter" if is_demo else "🧩 Dimensional Breakdown & Segment Concentration"
        st.markdown(f"<h3 style='font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>{decomp_title}</h3>", unsafe_allow_html=True)
        st.caption("Decomposes aggregate variance to localize where the measure is concentrated (empirical locus of effect, distinct from causal mechanism):")
        
        breakdowns = contrib_ctx.get("breakdowns", {})
        if breakdowns:
            tab_labels = [f"📊 By {dim.replace('_', ' ').title()}" for dim in breakdowns.keys()]
            tabs = st.tabs(tab_labels)
            for tab_i, (dim_name, df_dim) in enumerate(breakdowns.items()):
                with tabs[tab_i]:
                    fig_dim = plot_waterfall_contribution(df_dim, dim_name, f"{dim_name.replace('_', ' ').title()} Breakdown")
                    st.plotly_chart(fig_dim, use_container_width=True)
                    if not df_dim.empty:
                        top_seg = str(df_dim.iloc[0][dim_name])
                        top_pct = float(df_dim.iloc[0].get("contribution_pct", 0.0))
                        st.markdown(
                            f"""
                            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 4px solid #2563EB; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #1E293B;">
                                💡 <b>Concentration Finding:</b> <b>{top_seg}</b> accounts for <b>{top_pct:.1f}%</b> of the {dim_name.replace('_', ' ').title()}-level total.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.info("ℹ️ No categorical dimensions mapped for variance breakdown.")
                
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Primary Action to Stage 3: Explain (Workspace)
        col_cta, col_space = st.columns([2.2, 2.8])
        with col_cta:
            btn_label = "🔬 Proceed to Causal Investigation (Explain) →" if is_demo else "🔬 Proceed to Investigation Workspace (Explain) →"
            if st.button(btn_label, key="btn_to_workspace_s2", type="primary", use_container_width=True):
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
