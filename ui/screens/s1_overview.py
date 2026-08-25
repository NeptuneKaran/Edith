"""
ui/screens/s1_overview.py
Screen 1: Business Overview (Portfolio Health & Anomaly Briefing)
Clean, editorial Light Theme design prioritizing narrative and high-contrast scannability.
"""
import streamlit as st
from ui.components.cards import render_epistemology_chip
from state.session_state import set_screen
from data.repository import DataRepository

def render_screen_1():
    """Renders the executive portfolio health & anomaly overview screen."""
    col_hdr, col_tag = st.columns([4, 1.2])
    with col_hdr:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #0F172A;'>📊 Portfolio Health & Anomaly Briefing</h2>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 13px; color: #64748B; margin-top: 2px;'>Continuous telemetry scan across commercial, financial, and retention metrics &bull; <b>Fiscal Q1 2026 (Week 08)</b></div>", unsafe_allow_html=True)
    with col_tag:
        st.markdown("<div style='text-align: right; margin-top: 4px;'>", unsafe_allow_html=True)
        render_epistemology_chip("DATA-DERIVED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    anom_ctx = st.session_state.get("anomaly_context", {})
    
    # 1. HORIZONTAL KPI SUMMARY STRIP (Single Unboxed Row with Clean Dividers)
    df_margin = repo.get_kpi_time_series("kpi_gross_margin")
    curr_margin = df_margin.iloc[-1]["value"]
    
    df_churn = repo.get_kpi_time_series("kpi_customer_churn")
    curr_churn = df_churn.iloc[-1]["value"]
    
    df_roas = repo.get_kpi_time_series("kpi_marketing_roas")
    curr_roas = df_roas.iloc[-1]["value"]
    
    curr_sales = anom_ctx.get("current_value", 1_253_600)
    sales_delta_pct = anom_ctx.get("delta_pct", -10.54)
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02); margin-bottom: 20px;">
            <div style="display: grid; grid-template-columns: 1.2fr 1fr 1fr 1fr; gap: 20px; align-items: center;">
                <!-- KPI 1: B2B Sales (Anomaly) -->
                <div style="border-right: 1px solid #F1F5F9; padding-right: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px;">Monthly B2B Sales</span>
                        <span style="background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 4px;">P1 Anomaly</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 800; color: #0F172A; margin: 4px 0 2px 0;">${curr_sales:,.0f}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #DC2626;">{sales_delta_pct:+.1f}% <span style="font-weight: 400; color: #64748B;">vs baseline</span></div>
                </div>
                
                <!-- KPI 2: Gross Margin -->
                <div style="border-right: 1px solid #F1F5F9; padding-right: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px;">Gross Margin %</span>
                        <span style="background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">Normal</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 800; color: #0F172A; margin: 4px 0 2px 0;">{curr_margin:.1f}%</div>
                    <div style="font-size: 12px; font-weight: 600; color: #16A34A;">+0.2% <span style="font-weight: 400; color: #64748B;">vs baseline</span></div>
                </div>
                
                <!-- KPI 3: Customer Churn -->
                <div style="border-right: 1px solid #F1F5F9; padding-right: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px;">Churn Rate</span>
                        <span style="background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">Normal</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 800; color: #0F172A; margin: 4px 0 2px 0;">{curr_churn:.2f}%</div>
                    <div style="font-size: 12px; font-weight: 600; color: #16A34A;">-0.04% <span style="font-weight: 400; color: #64748B;">vs baseline</span></div>
                </div>
                
                <!-- KPI 4: Marketing ROAS -->
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px;">Marketing ROAS</span>
                        <span style="background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">Normal</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 800; color: #0F172A; margin: 4px 0 2px 0;">{curr_roas:.2f}x</div>
                    <div style="font-size: 12px; font-weight: 600; color: #16A34A;">+0.08x <span style="font-weight: 400; color: #64748B;">vs baseline</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2. EDITORIAL ANOMALY FINDING & MEMO (Replacing Cluttered Alert Boxes)
    curr_val = anom_ctx.get("current_value", 1_253_600.0)
    base_val = anom_ctx.get("baseline_value", 1_401_300.0)
    d_val = anom_ctx.get("delta_value", -147_700.0)
    d_pct = anom_ctx.get("delta_pct", -10.54)
    z_sc = anom_ctx.get("z_score", -2.30)
    wk_lbl = anom_ctx.get("current_week_label", "Week 08, 2026")
    
    st.markdown(
        f"""
        <div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 10px; padding: 22px 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-size: 15px; font-weight: 800; color: #991B1B; letter-spacing: -0.2px;">
                    ⚠️ Active Incident Finding: Statistical Breach on Monthly B2B Sales ({wk_lbl})
                </div>
                <span style="background: #DC2626; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800;">
                    Z = {z_sc:.2f} (Breach &gt; 2.0σ)
                </span>
            </div>
            <div style="font-size: 14px; color: #334155; line-height: 1.6; margin-bottom: 16px;">
                Monthly B2B Sales fell by <b>-${abs(d_val):,.0f} ({d_pct:+.1f}%)</b> below expected baseline over the last 2 consecutive weeks, breaching the lower threshold boundary ($1.27M). Multi-dimensional variance localization isolates <b>97.3% of the deficit</b> to <b>Region B Enterprise contracts</b>.
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 6px;">
                <div style="background: #FFFFFF; padding: 12px 14px; border-radius: 6px; border: 1px solid #FEE2E2;">
                    <div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Observed Revenue</div>
                    <div style="font-size: 19px; font-weight: 800; color: #0F172A; margin-top: 2px;">${curr_val:,.0f}</div>
                </div>
                <div style="background: #FFFFFF; padding: 12px 14px; border-radius: 6px; border: 1px solid #FEE2E2;">
                    <div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Expected Baseline</div>
                    <div style="font-size: 19px; font-weight: 800; color: #2563EB; margin-top: 2px;">${base_val:,.0f}</div>
                </div>
                <div style="background: #FFFFFF; padding: 12px 14px; border-radius: 6px; border: 1px solid #FEE2E2;">
                    <div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Dollar Deficit</div>
                    <div style="font-size: 19px; font-weight: 800; color: #DC2626; margin-top: 2px;">${d_val:,.0f} ({d_pct:+.1f}%)</div>
                </div>
                <div style="background: #FFFFFF; padding: 12px 14px; border-radius: 6px; border: 1px solid #FEE2E2;">
                    <div style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Temporal Persistence</div>
                    <div style="font-size: 19px; font-weight: 800; color: #D97706; margin-top: 2px;">2 Consecutive Wks</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Primary CTA Button
    col_btn, col_empty = st.columns([1.5, 3])
    with col_btn:
        if st.button("🚀 Start Causal Investigation →", key="btn_start_investigation", type="primary", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_b2b_sales"
            set_screen("diagnostic")
            st.rerun()
            
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    
    # 3. QUICK ACCESS TO OTHER METRICS
    st.markdown("<h4 style='font-size: 14px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 8px;'>Other Monitored Portfolio KPIs</h4>", unsafe_allow_html=True)
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        if st.button("📈 View Gross Margin % Diagnostic", key="btn_diag_margin", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_gross_margin"
            set_screen("diagnostic")
            st.rerun()
    with col_q2:
        if st.button("📈 View Customer Churn Diagnostic", key="btn_diag_churn", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_customer_churn"
            set_screen("diagnostic")
            st.rerun()
    with col_q3:
        if st.button("📈 View Marketing ROAS Diagnostic", key="btn_diag_roas", use_container_width=True):
            st.session_state.selected_kpi_id = "kpi_marketing_roas"
            set_screen("diagnostic")
            st.rerun()
