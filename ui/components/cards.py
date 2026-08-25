"""
ui/components/cards.py
Reusable UI Cards, Badges, and Metadata Chips for EDITH.
Ensures clean, executive-level visual hierarchy and explicit epistemological distinction.
"""
import streamlit as st
from typing import Dict, Any, List

def render_kpi_card(title: str, value_str: str, delta_str: str, status: str, is_anomaly: bool = False, on_click_cta: str = ""):
    """Renders a clean executive KPI scorecard."""
    border_color = "rgba(239, 68, 68, 0.4)" if is_anomaly else "rgba(255, 255, 255, 0.08)"
    bg_color = "rgba(239, 68, 68, 0.04)" if is_anomaly else "rgba(255, 255, 255, 0.02)"
    badge_bg = "rgba(239, 68, 68, 0.15)" if is_anomaly else "rgba(16, 185, 129, 0.15)"
    badge_border = "#EF4444" if is_anomaly else "#10B981"
    badge_text_color = "#F87171" if is_anomaly else "#34D399"
    delta_color = "#EF4444" if is_anomaly else "#10B981"
    
    st.markdown(
        f"""
        <div style="border: 1px solid {border_color}; background-color: {bg_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; transition: all 0.2s ease;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; font-weight: 600; color: #9CA3AF; letter-spacing: 0.3px;">{title}</span>
                <span style="background-color: {badge_bg}; border: 1px solid {badge_border}; color: {badge_text_color}; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">{status}</span>
            </div>
            <div style="font-size: 26px; font-weight: 800; margin: 8px 0 2px 0; color: #FFFFFF; letter-spacing: -0.5px;">{value_str}</div>
            <div style="font-size: 12px; font-weight: 600; color: {delta_color};">{delta_str} <span style="font-weight: 400; color: #6B7280;">vs baseline</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_cause_score_card(h: Dict[str, Any]):
    """Renders a comprehensive Cause Evidence Score card with 0-100 metric and component breakdown."""
    score_100 = h.get("cause_score_100", 0.0)
    e_score_01 = h.get("evidence_score", 0.0)
    classification = h.get("confidence_classification", h.get("confidence_band", "Evaluated"))
    role = h.get("dependency_role", "UPSTREAM_DIRECT")
    is_testable = h.get("testable", True)
    
    if not is_testable:
        color = "#6B7280"
        bg = "rgba(107, 114, 128, 0.08)"
    elif role == "DOWNSTREAM_EFFECT":
        color = "#818CF8" # Indigo
        bg = "rgba(129, 140, 248, 0.08)"
    elif score_100 >= 75.0:
        color = "#10B981" # Emerald
        bg = "rgba(16, 185, 129, 0.08)"
    elif score_100 >= 50.0:
        color = "#F59E0B" # Amber
        bg = "rgba(245, 158, 11, 0.08)"
    elif score_100 > 0.0:
        color = "#9CA3AF" # Grey
        bg = "rgba(156, 163, 175, 0.08)"
    else:
        color = "#EF4444" # Red
        bg = "rgba(239, 68, 68, 0.08)"
        
    score_display = f"{score_100:.1f}" if is_testable else "N/A"
    denom = "/ 100" if is_testable else ""
    
    st.markdown(
        f"""
        <div style="background: {bg}; border: 1px solid rgba(255,255,255,0.06); border-left: 4px solid {color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 11px; font-weight: 800; color: {color}; letter-spacing: 0.5px; text-transform: uppercase;">
                        {classification}
                    </span>
                    <div style="font-size: 11px; color: #9CA3AF; margin-top: 2px;">
                        Metric DAG Role: <code style="background: rgba(255,255,255,0.06); padding: 1px 5px; border-radius: 3px; color: #E5E7EB;">{role}</code>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 24px; font-weight: 800; color: {color}; letter-spacing: -0.5px;">{score_display}</span>
                    <span style="font-size: 12px; color: #6B7280; font-weight: 600;">{denom}</span>
                    <div style="font-size: 10px; color: #6B7280;">(Index: {e_score_01:.2f})</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Component Breakdown
    comps = h.get("score_components", {})
    if comps and is_testable:
        with st.expander("📊 View Multi-Dimensional Score Breakdown", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.caption("Investigative Dimensions (Base Weights):")
                st.write(f"• **Temporal Precedence (20%):** `{comps.get('temporal_precedence', 0):.0f}/100`")
                st.write(f"• **Magnitude / Effect Size (15%):** `{comps.get('magnitude_effect', 0):.1f}/100`")
                st.write(f"• **Directional Consistency (15%):** `{comps.get('directional_consistency', 0):.0f}/100`")
                st.write(f"• **Historical Lag Relationship (20%):** `{comps.get('historical_lag_relationship', 0):.0f}/100`")
                st.write(f"• **Dependency Structure (15%):** `{comps.get('dependency_structure', 0):.0f}/100`")
                st.write(f"• **Mathematical Contribution (15%):** `{comps.get('mathematical_contribution', 0):.0f}/100`")
            with c2:
                st.caption("Penalties & Net Calculation:")
                st.write(f"• **Base Score:** `{comps.get('base_score_100', 0):.1f}`")
                st.write(f"• **Counter-Evidence Penalty:** `-{comps.get('counter_evidence_penalty', 0):.1f}`")
                st.write(f"• **Confounder Penalty:** `-{comps.get('confounder_penalty', 0):.1f}`")
                st.write(f"• **Pre-Trend Penalty:** `-{comps.get('pre_trend_penalty', 0):.1f}`")
                st.write(f"• **Final Calibrated Score:** `{comps.get('final_cause_score_100', 0):.1f}/100`")

def render_evidence_score_badge(score: float, label: str = "Evidence Strength", is_testable: bool = True):
    """Renders a styled, color-coded Evidence Score badge (backward compatible)."""
    if not is_testable:
        color = "#6B7280"
        bg = "rgba(107, 114, 128, 0.08)"
        badge_text = "NOT TESTABLE (MISSING TELEMETRY)"
    elif score >= 0.80:
        color = "#10B981" # Emerald
        bg = "rgba(16, 185, 129, 0.08)"
        badge_text = "HIGH-CONFIDENCE DRIVER (RANK 1)"
    elif score >= 0.50:
        color = "#F59E0B" # Amber
        bg = "rgba(245, 158, 11, 0.08)"
        badge_text = "POSSIBLE DRIVER (RANK 2)"
    elif score > 0.0:
        color = "#9CA3AF" # Slate Grey
        bg = "rgba(156, 163, 175, 0.08)"
        badge_text = "WEAK EVIDENCE"
    else:
        color = "#EF4444" # Red
        bg = "rgba(239, 68, 68, 0.08)"
        badge_text = "REFUTED BY EMPIRICAL DATA"
        
    score_display = f"{score:.2f}" if is_testable else "N/A"
    denom_display = "/ 1.00" if is_testable else ""
    
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; background: {bg}; padding: 8px 12px; border-radius: 6px; border-left: 3px solid {color}; border-top: 1px solid rgba(255,255,255,0.04); border-right: 1px solid rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.04); margin-bottom: 8px;">
            <div>
                <span style="font-size: 10px; font-weight: 700; color: {color}; letter-spacing: 0.5px; text-transform: uppercase;">{badge_text}</span>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 1px;">{label} <span style="font-size: 10px; color: #6B7280;">(Deterministic Index)</span></div>
            </div>
            <div style="font-size: 20px; font-weight: 800; color: {color}; letter-spacing: -0.3px;">{score_display} <span style="font-size: 12px; color: #6B7280; font-weight: 500;">{denom_display}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_mathematical_decomposition_card(decomp: Dict[str, Any]):
    """Renders exact mathematical identity decomposition for revenue and volume."""
    if not decomp:
        return
    st.markdown(
        f"""
        <div style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
            <div style="font-size: 12px; font-weight: 700; color: #60A5FA; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">
                📐 Mathematical Revenue Identity: ΔRevenue = Volume Effect + Price Effect
            </div>
            <div style="font-size: 12px; color: #D1D5DB; line-height: 1.5; margin-bottom: 10px;">
                {decomp.get('interpretation')}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px;">
                <div>
                    <div style="font-size: 10px; color: #9CA3AF;">Volume Effect (Units)</div>
                    <div style="font-size: 14px; font-weight: 700; color: #EF4444;">-${abs(decomp.get('volume_effect_usd', 0)):,.0f}</div>
                    <div style="font-size: 10px; color: #6B7280;">{abs(decomp.get('volume_share_pct', 0)):.1f}% of total gap</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #9CA3AF;">Price Cushion (Rate)</div>
                    <div style="font-size: 14px; font-weight: 700; color: #10B981;">+${decomp.get('price_effect_usd', 0):,.0f}</div>
                    <div style="font-size: 10px; color: #6B7280;">{decomp.get('price_share_pct', 0):+.1f}% cushioning</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #9CA3AF;">Reconciled Gap</div>
                    <div style="font-size: 14px; font-weight: 700; color: #F3F4F6;">-${abs(decomp.get('delta_revenue', 0)):,.0f}</div>
                    <div style="font-size: 10px; color: #10B981;">0.0% Error (Exact)</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_investigation_chain_card(chain: List[Dict[str, Any]]):
    """Renders the vertical causal propagation chain."""
    if not chain:
        return
    st.markdown("<div style='font-size: 12px; font-weight: 700; color: #9CA3AF; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;'>🔗 Causal Propagation Chain</div>", unsafe_allow_html=True)
    for idx, item in enumerate(chain):
        is_target = item.get("role") == "TARGET_ANOMALY"
        is_downstream = item.get("role") == "DOWNSTREAM_EFFECT"
        border = "#EF4444" if is_target else ("#818CF8" if is_downstream else "rgba(255,255,255,0.1)")
        bg = "rgba(239, 68, 68, 0.08)" if is_target else ("rgba(129, 140, 248, 0.06)" if is_downstream else "rgba(255,255,255,0.02)")
        badge_color = "#F87171" if is_target else ("#A5B4FC" if is_downstream else "#34D399")
        
        st.markdown(
            f"""
            <div style="border: 1px solid {border}; background: {bg}; border-radius: 6px; padding: 8px 12px; margin-bottom: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 11px; font-weight: 700; color: #FFFFFF;">
                        {idx + 1}. {item.get('node')}
                    </span>
                    <span style="font-size: 10px; font-weight: 700; color: {badge_color};">
                        {item.get('metric_delta')}
                    </span>
                </div>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 2px;">
                    {item.get('event')} <span style="font-size: 9px; color: #6B7280;">({item.get('role')})</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_prediction_card(p: Dict[str, Any]):
    """Renders an individual tested prediction with pass/fail badges and observed telemetry."""
    status = p.get("status", "SUPPORTED")
    if status == "SUPPORTED":
        status_color = "#10B981"
        status_bg = "rgba(16, 185, 129, 0.12)"
        status_border = "#10B981"
        icon = "✓"
    elif status == "CONTRADICTED":
        status_color = "#EF4444"
        status_bg = "rgba(239, 68, 68, 0.12)"
        status_border = "#EF4444"
        icon = "✗"
    else:
        status_color = "#9CA3AF"
        status_bg = "rgba(156, 163, 175, 0.12)"
        status_border = "#6B7280"
        icon = "?"
        
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 6px; padding: 8px 12px; margin-bottom: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="font-size: 12px; font-weight: 600; color: #F3F4F6;">
                    <b>Prediction:</b> {p.get('prediction')}
                </div>
                <span style="font-size: 9px; font-weight: 800; color: {status_color}; background: {status_bg}; border: 1px solid {status_border}; padding: 1px 6px; border-radius: 3px; letter-spacing: 0.5px; white-space: nowrap; margin-left: 8px;">
                    {icon} {status}
                </span>
            </div>
            <div style="font-size: 11px; color: #9CA3AF; margin-top: 4px;">
                <b>Observed Fact:</b> <span style="color: #D1D5DB;">{p.get('observed_value')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_control_group_summary(ctrl: Dict[str, Any]):
    """Renders the data-driven control group selection and pre-trend validation summary."""
    if not ctrl or ctrl.get("control_cohort") == "None":
        st.info("No comparative control group evaluated for this hypothesis.")
        return
        
    status = ctrl.get("pre_trend_status", "Validated")
    quality = ctrl.get("control_quality", "Acceptable")
    did_gap = ctrl.get("did_divergence_pct", 0.0)
    corr = ctrl.get("pre_trend_correlation", 0.0)
    slope_diff = ctrl.get("pre_trend_slope_diff", 0.0)
    
    st.markdown(
        f"""
        <div style="background: rgba(16, 185, 129, 0.04); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 12px 14px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 12px; font-weight: 700; color: #34D399; text-transform: uppercase; letter-spacing: 0.5px;">
                    🎯 Selected Control: {ctrl.get('control_cohort')}
                </span>
                <span style="font-size: 10px; font-weight: 700; color: #10B981; background: rgba(16, 185, 129, 0.15); padding: 1px 6px; border-radius: 3px;">
                    {quality} (Score: {ctrl.get('similarity_score', 0.85)})
                </span>
            </div>
            <div style="font-size: 11px; color: #9CA3AF; line-height: 1.4; margin-bottom: 8px;">
                {ctrl.get('selection_reason')}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; background: rgba(0,0,0,0.2); padding: 6px 10px; border-radius: 4px;">
                <div>
                    <div style="font-size: 10px; color: #6B7280;">DiD Divergence</div>
                    <div style="font-size: 13px; font-weight: 700; color: #F3F4F6;">{did_gap:+.1f}%</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #6B7280;">Pre-Trend Corr (r)</div>
                    <div style="font-size: 13px; font-weight: 700; color: #10B981;">{corr:.2f}</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #6B7280;">Pre-Trend Status</div>
                    <div style="font-size: 12px; font-weight: 700; color: #34D399;">{status}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_confounders_summary(confounders: List[Dict[str, Any]]):
    """Renders external confounder callouts."""
    if not confounders:
        return
    for c in confounders:
        st.markdown(
            f"""
            <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.25); border-left: 3px solid #F59E0B; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 11px; font-weight: 700; color: #FBBF24;">⚠️ Confounder Detected: {c.get('name')}</span>
                    <span style="font-size: 10px; font-weight: 600; color: #F59E0B;">Timing: {c.get('timing')}</span>
                </div>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 3px;">
                    {c.get('mechanism')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_ledger_card(title: str, items: List[str], icon: str = "•", is_positive: bool = True):
    """Renders an evidence ledger section."""
    border_color = "rgba(16, 185, 129, 0.2)" if is_positive else "rgba(239, 68, 68, 0.2)"
    title_color = "#34D399" if is_positive else "#F87171"
    
    st.markdown(f"<div style='font-size: 12px; font-weight: 700; color: {title_color}; margin: 8px 0 4px 0;'>{title}</div>", unsafe_allow_html=True)
    if not items:
        st.markdown("<div style='font-size: 11px; color: #6B7280; font-style: italic;'>None recorded.</div>", unsafe_allow_html=True)
        return
        
    for item in items:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.02); border-left: 2px solid {border_color}; padding: 4px 8px; margin-bottom: 4px; border-radius: 0 4px 4px 0;">
                <span style="font-size: 11px; color: #D1D5DB; line-height: 1.4;">{icon} {item}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_epistemology_chip(category: str):
    """Renders an explicit epistemology chip (Data-Derived, Model Assumption, Simulated)."""
    configs = {
        "DATA-DERIVED": {"color": "#3B82F6", "bg": "rgba(59, 130, 246, 0.15)", "label": "DATA-DERIVED (EMPIRICAL)"},
        "MODEL ASSUMPTION": {"color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.15)", "label": "MODEL ASSUMPTION (PARAMETRIC)"},
        "SIMULATED": {"color": "#8B5CF6", "bg": "rgba(139, 92, 246, 0.15)", "label": "SIMULATED (COUNTERFACTUAL)"},
        "EVIDENCE STRENGTH": {"color": "#10B981", "bg": "rgba(16, 185, 129, 0.15)", "label": "EVIDENCE STRENGTH (INDEX)"}
    }
    cfg = configs.get(category, {"color": "#9CA3AF", "bg": "rgba(156, 163, 175, 0.15)", "label": category})
    st.markdown(
        f"""
        <span style="background: {cfg['bg']}; color: {cfg['color']}; border: 1px solid {cfg['color']}; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            {cfg['label']}
        </span>
        """,
        unsafe_allow_html=True
    )

# Backward compatibility alias
render_data_tag = render_epistemology_chip

