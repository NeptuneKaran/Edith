"""
ui/screens/s4_simulation.py
Screen 4: Scenario Simulation Workbench & Structured Decision Summary (Simulate Stage)
Clean, editorial Light Theme design with interactive levers, recovery trajectories, and exportable governance package.
"""
import streamlit as st
from state.session_state import set_screen
from ui.components.charts import plot_simulation_trajectory
from ui.components.cards import render_epistemology_chip
from core.simulation_engine import SimulationEngine

def render_screen_4():
    """Renders the what-if simulation workbench and final decision export package."""
    col_nav, col_title, col_tags = st.columns([1.3, 3.7, 1.4])
    with col_nav:
        if st.button("← Back to Explain (Workspace)", key="btn_sim_back_s4", use_container_width=True):
            set_screen("workspace")
            st.rerun()
            
    with col_title:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 20px; font-weight: 800; color: #0F172A;'>🔮 Stage 4: Scenario Simulation Workbench</h2>", unsafe_allow_html=True)
        st.caption("Simulate counterfactual recovery curves, evaluate economic trade-offs, and finalize action plans.")
    with col_tags:
        st.markdown("<div style='text-align: right; margin-top: 4px; display: flex; gap: 4px; justify-content: flex-end;'>", unsafe_allow_html=True)
        render_epistemology_chip("MODEL ASSUMPTION")
        render_epistemology_chip("SIMULATED")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
    
    col_levers, col_results = st.columns([1.0, 1.2], gap="large")
    
    # =========================================================================
    # LEFT COLUMN: CONTROLLABLE LEVER SLIDERS & ASSUMPTIONS
    # =========================================================================
    with col_levers:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 16px;">
                <h3 style='margin:0; padding:0; font-size: 16px; font-weight: 700; color: #0F172A;'>🎛️ Controllable Policy Levers</h3>
                <div style='font-size: 12px; color: #64748B; margin-top: 2px; margin-bottom: 14px;'>Adjust policy levers to simulate counterfactual recovery paths:</div>
            """,
            unsafe_allow_html=True
        )
        
        price_rollback = st.slider(
            "Price Adjustment on Enterprise Tier (%)",
            min_value=-15.0,
            max_value=5.0,
            value=float(st.session_state.simulation_levers["price_rollback_pct"]),
            step=1.0,
            help="Adjust Enterprise subscription price (e.g. -6% rolls back half of the +12% increase)."
        )
        st.session_state.simulation_levers["price_rollback_pct"] = price_rollback
        
        mkt_spend = st.slider(
            "Targeted Regional Promo / Co-op Fund ($)",
            min_value=0,
            max_value=50000,
            value=int(st.session_state.simulation_levers["marketing_boost_usd"]),
            step=5000,
            format="$%d",
            help="Additional targeted partner/field marketing spend allocated to Region B."
        )
        st.session_state.simulation_levers["marketing_boost_usd"] = mkt_spend
        
        comp_matching = st.checkbox(
            "Account for Competitor ApexTech Ongoing Campaign",
            value=st.session_state.simulation_levers["competitor_matching"],
            help="Applies market share retention damper if competitor maintains active promotion."
        )
        st.session_state.simulation_levers["competitor_matching"] = comp_matching
        
        st.markdown("---")
        
        # Transparent Model Assumptions Box
        st.markdown("<h4 style='font-size: 13px; font-weight: 700; color: #B45309; text-transform: uppercase; letter-spacing: 0.4px;'>⚙️ Explicit Model Assumptions:</h4>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 12px; font-size: 12px; color: #451A03;">
                <div>• <b>Price Elasticity (Enterprise):</b> ε<sub>p</sub> = -1.65 <span style="color:#64748B;">(Model parameter)</span></div>
                <div>• <b>Marketing Response Coeff:</b> β<sub>m</sub> = 0.25 <span style="color:#64748B;">(Model parameter)</span></div>
                <div>• <b>Adoption Lead Time:</b> τ = 2 weeks <span style="color:#64748B;">(Sigmoid S-curve adoption lag)</span></div>
                <div style="margin-top: 6px; font-size: 11px; color: #64748B;"><i>*Distinguished from data-derived empirical baseline measurements.</i></div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    anom_ctx = st.session_state.get("anomaly_context", {})
    contrib_ctx = st.session_state.get("contribution_context", {})
    hypotheses = st.session_state.get("hypotheses", [])
    
    # Dynamic regional values from contribution breakdown
    reg_breakdowns = contrib_ctx.get("breakdowns", {}).get("region")
    if reg_breakdowns is not None and not reg_breakdowns.empty:
        reg_b_row = reg_breakdowns[reg_breakdowns["region"] == "Region B"]
        if not reg_b_row.empty:
            regional_base = float(reg_b_row.iloc[0]["prev_value"])
            regional_curr = float(reg_b_row.iloc[0]["curr_value"])
        else:
            regional_base = 577200.0
            regional_curr = 400000.0
    else:
        regional_base = 577200.0
        regional_curr = 400000.0

    # Execute simulation calculation
    sim_out = SimulationEngine.simulate_lever_impact(
        baseline_revenue=float(anom_ctx.get("baseline_value", 1401300.0)),
        current_revenue=float(anom_ctx.get("current_value", 1253600.0)),
        regional_affected_baseline=regional_base,
        regional_affected_current=regional_curr,
        base_unit_price=11200.0,
        cogs_per_unit=3136.0,
        price_rollback_pct=price_rollback,
        marketing_boost_usd=float(mkt_spend),
        competitor_retaliation=comp_matching
    )
    
    # =========================================================================
    # RIGHT COLUMN: QUANTITATIVE RECOVERY TRAJECTORY & ADVISORY
    # =========================================================================
    with col_results:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 16px;">
                <h3 style='margin:0; padding:0; font-size: 16px; font-weight: 700; color: #0F172A;'>📈 Counterfactual Recovery Projection</h3>
                <div style='font-size: 12px; color: #64748B; margin-top: 2px; margin-bottom: 14px;'>Projected trajectory over an 8-week horizon under selected policy:</div>
            """,
            unsafe_allow_html=True
        )
        
        # Metric Cards Strip
        margin_delta = sim_out['simulated_margin_pct'] - 72.0
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(
                "Simulated Revenue",
                f"${sim_out['simulated_revenue']:,.0f}",
                f"{sim_out['net_revenue_delta']:+,.0f}/wk",
                delta_color="normal"
            )
        with col_m2:
            st.metric(
                "Projected Margin",
                f"{sim_out['simulated_margin_pct']:.1f}%",
                f"{margin_delta:+.1f}% vs baseline",
                delta_color="off"
            )
        with col_m3:
            st.metric(
                "Revenue Recovery %",
                f"{sim_out['recovery_pct']:.1f}%",
                "of lost revenue",
                delta_color="normal"
            )
            
        # Trajectory Chart
        fig_sim = plot_simulation_trajectory(sim_out["trajectory_df"])
        st.plotly_chart(fig_sim, use_container_width=True)
        
        # Edith Trade-Off Advisory
        st.markdown(
            f"""
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 6px; padding: 12px 14px; margin-top: 6px;">
                <div style="font-size: 11px; font-weight: 700; color: #166534; text-transform: uppercase;">🤖 EDITH Economic Trade-Off Advisory:</div>
                <div style="font-size: 13px; color: #1E293B; margin-top: 4px; line-height: 1.5;">
                    Applying a <b>{price_rollback:.1f}% price adjustment</b> alongside a <b>${mkt_spend:,.0f} co-op promotional boost</b> recovers approximately <b>{sim_out['recovery_pct']:.1f}% of lost sales volume</b> over the 8-week horizon.
                    <br><br>
                    <b>Trade-off:</b> Gross margin settles at <b>{sim_out['simulated_margin_pct']:.1f}%</b>, balancing volume recapture against per-unit margin realization.
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("---")
    
    # =========================================================================
    # DECISION SUMMARY & ACTION PACKAGE
    # =========================================================================
    st.markdown("<h3 style='margin:0; padding:0; font-size: 16px; font-weight: 700; color: #0F172A;'>📋 Final Decision Summary & Governance Package</h3>", unsafe_allow_html=True)
    st.caption("Auditable export package ready for executive sign-off and operational handoff:")
    
    top_h = hypotheses[0] if hypotheses else {"name": "Pricing Elasticity", "evidence_score": 0.90}
    second_h = hypotheses[1] if len(hypotheses) > 1 else {"name": "Competitor Campaign", "evidence_score": 0.55}
    refuted_h = next((h for h in hypotheses if h["id"] in ["H8_SUPPLY_CONSTRAINT", "H3_INVENTORY_CONSTRAINT"]), {"name": "Supply Bottleneck", "evidence_score": 0.00})
    
    wk_lbl = anom_ctx.get("current_week_label", "2026-W08")
    kpi_nm = anom_ctx.get("kpi_name", "Monthly B2B Sales")
    d_val = anom_ctx.get("delta_value", 0.0)
    d_pct = anom_ctx.get("delta_pct", 0.0)
    b_val = anom_ctx.get("baseline_value", 0.0)
    z_sc = anom_ctx.get("z_score", 0.0)
    
    reg_nm = contrib_ctx.get("primary_region", "Region B")
    reg_sh = contrib_ctx.get("primary_region_share", 97.3)
    tier_nm = contrib_ctx.get("primary_tier", "Enterprise")
    prod_nm = contrib_ctx.get("primary_product", "Product Suite Alpha")
    
    decision_summary_text = f"""================================================================================
EDITH DECISION AUDIT PACKAGE — ACCENTURE INNOVATION CHALLENGE 2026
================================================================================
1. DETECTED ISSUE:
   • KPI: {kpi_nm} ({wk_lbl})
   • Variance: ${d_val:+,.0f} ({d_pct:+.1f}%) below rolling baseline of ${b_val:,.0f}.
   • Statistical Severity: Z = {z_sc:.2f} (Breaches ±2.0σ expected corridor; 2-wk persistence).
   • Epicenter: {reg_nm} ({reg_sh:.1f}% share) -> {tier_nm} Tier -> {prod_nm}.

2. STRONGEST SUPPORTED EXPLANATION:
   • Cause: {top_h.get('name')} (Evidence Score: {top_h.get('evidence_score', 0.0):.2f} / 1.00)
   • Contributing Factor: {second_h.get('name')} (Evidence Score: {second_h.get('evidence_score', 0.0):.2f} / 1.00)
   • Refuted Cause: {refuted_h.get('name')} (Evidence Score: {refuted_h.get('evidence_score', 0.0):.2f} - Fill rate 99.4%)

3. EMPIRICAL EVIDENCE SUMMARY:
   • Temporal Alignment: +12% price hike logged on 2026-W06 (tau = 2 weeks prior).
   • Difference-in-Differences: Enterprise dropped significantly while un-hiked Mid-Market was flat.
   • Customer CRM Signals: Pricing complaints surged to 38/week in Region B.

4. SELECTED CORRECTIVE ACTION:
   • Action: Implement targeted {price_rollback:.1f}% price adjustment on Enterprise {prod_nm} in {reg_nm}.
   • Marketing: Deploy ${mkt_spend:,.0f} regional partner co-op fund.
   • Simulated Outcome: {sim_out['recovery_pct']:.1f}% volume recovery (${sim_out['net_revenue_delta']:+,.0f}/wk) at {sim_out['simulated_margin_pct']:.1f}% Gross Margin.

5. GOVERNANCE & OWNERSHIP:
   • Assigned Owner: VP of Commercial Operations / Regional Sales Director
   • Monitoring KPI: {reg_nm} Enterprise Weekly Bookings & CRM Win-Rate
   • Checkpoint Date: 3-Week Review Cycle
================================================================================"""

    st.code(decision_summary_text, language="text")
    
    col_exp, col_ask = st.columns([1.5, 1.0])
    with col_exp:
        st.download_button(
            label="📥 Export Decision Package (.txt)",
            data=decision_summary_text,
            file_name="EDITH_Decision_Package_B2B_Sales.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_ask:
        if st.button("💬 Ask EDITH Console →", key="btn_console_from_sim", use_container_width=True):
            set_screen("console")
            st.rerun()
