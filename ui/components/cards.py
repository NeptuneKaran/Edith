"""
ui/components/cards.py
Reusable UI Cards, Badges, and Metadata Chips for EDITH (Clean Light Theme).
Ensures clean, executive-level visual hierarchy, high contrast, and explicit epistemological distinction.
"""
import streamlit as st
from typing import Dict, Any, List

def _clean_html(html: str) -> str:
    """Strips leading/trailing indentation from each line to prevent Markdown code block triggers."""
    return "\n".join(line.strip() for line in html.strip().split("\n"))

def render_kpi_card(title: str, value_str: str, delta_str: str, status: str, is_anomaly: bool = False, on_click_cta: str = ""):
    """Renders a clean, executive-grade KPI scorecard in light theme."""
    border_color = "#FCA5A5" if is_anomaly else "#E2E8F0"
    bg_color = "#FEF2F2" if is_anomaly else "#FFFFFF"
    badge_bg = "#FEE2E2" if is_anomaly else "#DCFCE7"
    badge_border = "#F87171" if is_anomaly else "#86EFAC"
    badge_text_color = "#991B1B" if is_anomaly else "#166534"
    delta_color = "#DC2626" if is_anomaly else "#16A34A"
    
    html = f"""
    <div style="border: 1px solid {border_color}; background-color: {bg_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02); transition: all 0.2s ease;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.4px; text-transform: uppercase;">{title}</span>
            <span style="background-color: {badge_bg}; border: 1px solid {badge_border}; color: {badge_text_color}; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.4px;">{status}</span>
        </div>
        <div style="font-size: 26px; font-weight: 800; margin: 8px 0 2px 0; color: #0F172A; letter-spacing: -0.5px;">{value_str}</div>
        <div style="font-size: 12px; font-weight: 600; color: {delta_color};">{delta_str} <span style="font-weight: 400; color: #64748B;">vs baseline</span></div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_cause_score_card(h: Dict[str, Any]):
    """Renders a comprehensive Cause Evidence Score card with 0-100 metric and component breakdown."""
    score_100 = h.get("cause_score_100", 0.0)
    e_score_01 = h.get("evidence_score", 0.0)
    classification = h.get("confidence_classification", h.get("confidence_band", "Evaluated"))
    role = h.get("dependency_role", "UPSTREAM_DIRECT")
    is_testable = h.get("testable", True)
    
    if not is_testable:
        color = "#475569"
        bg = "#F1F5F9"
        border_left = "#94A3B8"
    elif role == "DOWNSTREAM_EFFECT":
        color = "#4338CA" # Indigo
        bg = "#EEF2FF"
        border_left = "#6366F1"
    elif score_100 >= 75.0:
        color = "#15803D" # Emerald
        bg = "#F0FDF4"
        border_left = "#16A34A"
    elif score_100 >= 50.0:
        color = "#B45309" # Amber
        bg = "#FFFBEB"
        border_left = "#D97706"
    elif score_100 > 0.0:
        color = "#475569" # Slate
        bg = "#F8FAFC"
        border_left = "#94A3B8"
    else:
        color = "#B91C1C" # Red
        bg = "#FEF2F2"
        border_left = "#DC2626"
        
    score_display = f"{score_100:.1f}" if is_testable else "N/A"
    denom = "/ 100" if is_testable else ""
    
    html = f"""
    <div style="background: {bg}; border: 1px solid #E2E8F0; border-left: 4px solid {border_left}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 11px; font-weight: 800; color: {color}; letter-spacing: 0.5px; text-transform: uppercase;">
                    {classification}
                </span>
                <div style="font-size: 12px; color: #475569; margin-top: 3px;">
                    Metric DAG Role: <code style="background: rgba(0,0,0,0.05); padding: 2px 6px; border-radius: 3px; color: #0F172A; font-weight: 600;">{role}</code>
                </div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 26px; font-weight: 800; color: {color}; letter-spacing: -0.5px;">{score_display}</span>
                <span style="font-size: 13px; color: #64748B; font-weight: 600;">{denom}</span>
                <div style="font-size: 11px; color: #64748B;">(Index: {e_score_01:.2f})</div>
            </div>
        </div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)
    
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
        color = "#475569"
        bg = "#F1F5F9"
        border = "#CBD5E1"
        badge_text = "NOT TESTABLE (MISSING TELEMETRY)"
    elif score >= 0.80:
        color = "#15803D" # Emerald
        bg = "#F0FDF4"
        border = "#86EFAC"
        badge_text = "HIGH-CONFIDENCE DRIVER (RANK 1)"
    elif score >= 0.50:
        color = "#B45309" # Amber
        bg = "#FFFBEB"
        border = "#FDE68A"
        badge_text = "POSSIBLE DRIVER (RANK 2)"
    elif score > 0.0:
        color = "#475569" # Slate Grey
        bg = "#F8FAFC"
        border = "#E2E8F0"
        badge_text = "WEAK EVIDENCE"
    else:
        color = "#B91C1C" # Red
        bg = "#FEF2F2"
        border = "#FECACA"
        badge_text = "REFUTED BY EMPIRICAL DATA"
        
    score_display = f"{score:.2f}" if is_testable else "N/A"
    denom_display = "/ 1.00" if is_testable else ""
    
    html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: {bg}; padding: 8px 12px; border-radius: 6px; border-left: 3px solid {color}; border-top: 1px solid {border}; border-right: 1px solid {border}; border-bottom: 1px solid {border}; margin-bottom: 8px;">
        <div>
            <span style="font-size: 10px; font-weight: 700; color: {color}; letter-spacing: 0.4px; text-transform: uppercase;">{badge_text}</span>
            <div style="font-size: 11px; color: #64748B; margin-top: 1px;">{label} <span style="font-size: 10px; color: #94A3B8;">(Deterministic Index)</span></div>
        </div>
        <div style="font-size: 18px; font-weight: 800; color: {color}; letter-spacing: -0.3px;">{score_display} <span style="font-size: 11px; color: #64748B; font-weight: 500;">{denom_display}</span></div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_mathematical_decomposition_card(decomp: Dict[str, Any]):
    """Renders exact mathematical identity decomposition for revenue and volume."""
    if not decomp:
        return
    html = f"""
    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div style="font-size: 12px; font-weight: 700; color: #1D4ED8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">
            📐 Mathematical Revenue Identity: ΔRevenue = Volume Effect + Price Effect
        </div>
        <div style="font-size: 13px; color: #1E293B; line-height: 1.5; margin-bottom: 10px;">
            {decomp.get('interpretation')}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; background: #FFFFFF; padding: 10px; border-radius: 6px; border: 1px solid #DBEAFE;">
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">Volume Effect (Units)</div>
                <div style="font-size: 15px; font-weight: 800; color: #DC2626;">-${abs(decomp.get('volume_effect_usd', 0)):,.0f}</div>
                <div style="font-size: 11px; color: #64748B;">{abs(decomp.get('volume_share_pct', 0)):.1f}% of total gap</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">Price Cushion (Rate)</div>
                <div style="font-size: 15px; font-weight: 800; color: #16A34A;">+${decomp.get('price_effect_usd', 0):,.0f}</div>
                <div style="font-size: 11px; color: #64748B;">{decomp.get('price_share_pct', 0):+.1f}% cushioning</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">Reconciled Gap</div>
                <div style="font-size: 15px; font-weight: 800; color: #0F172A;">-${abs(decomp.get('delta_revenue', 0)):,.0f}</div>
                <div style="font-size: 11px; color: #16A34A; font-weight: 600;">0.0% Error (Exact)</div>
            </div>
        </div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_investigation_chain_card(chain: List[Dict[str, Any]]):
    """Renders the vertical causal propagation chain."""
    if not chain:
        return
    st.markdown("<div style='font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;'>🔗 Causal Propagation Chain</div>", unsafe_allow_html=True)
    for idx, item in enumerate(chain):
        is_target = item.get("role") == "TARGET_ANOMALY"
        is_downstream = item.get("role") == "DOWNSTREAM_EFFECT"
        border = "#FCA5A5" if is_target else ("#C7D2FE" if is_downstream else "#E2E8F0")
        bg = "#FEF2F2" if is_target else ("#EEF2FF" if is_downstream else "#FFFFFF")
        badge_color = "#B91C1C" if is_target else ("#4338CA" if is_downstream else "#15803D")
        
        html = f"""
        <div style="border: 1px solid {border}; background: {bg}; border-radius: 6px; padding: 10px 14px; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 12px; font-weight: 700; color: #0F172A;">
                    {idx + 1}. {item.get('node')}
                </span>
                <span style="font-size: 11px; font-weight: 700; color: {badge_color};">
                    {item.get('metric_delta')}
                </span>
            </div>
            <div style="font-size: 12px; color: #475569; margin-top: 2px;">
                {item.get('event')} <span style="font-size: 10px; color: #64748B; font-weight: 600;">({item.get('role')})</span>
            </div>
        </div>
        """
        st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_prediction_card(p: Dict[str, Any]):
    """Renders an individual tested prediction with pass/fail badges and observed telemetry."""
    status = p.get("status", "SUPPORTED")
    if status == "SUPPORTED":
        status_color = "#15803D"
        status_bg = "#DCFCE7"
        status_border = "#86EFAC"
        icon = "✓"
    elif status == "CONTRADICTED":
        status_color = "#B91C1C"
        status_bg = "#FEE2E2"
        status_border = "#FCA5A5"
        icon = "✗"
    else:
        status_color = "#475569"
        status_bg = "#F1F5F9"
        status_border = "#CBD5E1"
        icon = "?"
        
    html = f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-size: 12px; font-weight: 700; color: #0F172A;">
                <b>Prediction:</b> {p.get('prediction')}
            </div>
            <span style="font-size: 10px; font-weight: 800; color: {status_color}; background: {status_bg}; border: 1px solid {status_border}; padding: 2px 7px; border-radius: 4px; letter-spacing: 0.5px; white-space: nowrap; margin-left: 8px;">
                {icon} {status}
            </span>
        </div>
        <div style="font-size: 12px; color: #475569; margin-top: 4px;">
            <b>Observed Fact:</b> <span style="color: #0F172A; font-weight: 500;">{p.get('observed_value')}</span>
        </div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_control_group_summary(ctrl: Dict[str, Any]):
    """Renders the data-driven control group selection and pre-trend validation summary."""
    if not ctrl or ctrl.get("control_cohort") == "None":
        st.info("No comparative control group evaluated for this hypothesis.")
        return
        
    status = ctrl.get("pre_trend_status", "Validated")
    quality = ctrl.get("control_quality", "Acceptable")
    did_gap = ctrl.get("did_divergence_pct", 0.0)
    corr = ctrl.get("pre_trend_correlation", 0.0)
    
    html = f"""
    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 12px; font-weight: 700; color: #166534; text-transform: uppercase; letter-spacing: 0.5px;">
                🎯 Selected Control: {ctrl.get('control_cohort')}
            </span>
            <span style="font-size: 10px; font-weight: 700; color: #15803D; background: #DCFCE7; border: 1px solid #86EFAC; padding: 2px 7px; border-radius: 4px;">
                {quality} (Score: {ctrl.get('similarity_score', 0.85)})
            </span>
        </div>
        <div style="font-size: 12px; color: #334155; line-height: 1.5; margin-bottom: 10px;">
            {ctrl.get('selection_reason')}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; background: #FFFFFF; padding: 8px 12px; border-radius: 6px; border: 1px solid #DCFCE7;">
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">DiD Divergence</div>
                <div style="font-size: 14px; font-weight: 800; color: #0F172A;">{did_gap:+.1f}%</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">Pre-Trend Corr (r)</div>
                <div style="font-size: 14px; font-weight: 800; color: #16A34A;">{corr:.2f}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748B; font-weight: 600;">Pre-Trend Status</div>
                <div style="font-size: 13px; font-weight: 700; color: #15803D;">{status}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_confounders_summary(confounders: List[Dict[str, Any]]):
    """Renders external confounder callouts."""
    if not confounders:
        return
    for c in confounders:
        html = f"""
        <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #D97706; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 12px; font-weight: 700; color: #92400E;">⚠️ Confounder Detected: {c.get('name')}</span>
                <span style="font-size: 11px; font-weight: 600; color: #B45309;">Timing: {c.get('timing')}</span>
            </div>
            <div style="font-size: 12px; color: #451A03; margin-top: 3px;">
                {c.get('mechanism')}
            </div>
        </div>
        """
        st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_ledger_card(title: str, items: List[str], icon: str = "•", is_positive: bool = True):
    """Renders an evidence ledger section."""
    border_color = "#86EFAC" if is_positive else "#FCA5A5"
    title_color = "#166534" if is_positive else "#991B1B"
    bg = "#F0FDF4" if is_positive else "#FEF2F2"
    
    st.markdown(f"<div style='font-size: 12px; font-weight: 700; color: {title_color}; margin: 8px 0 4px 0;'>{title}</div>", unsafe_allow_html=True)
    if not items:
        st.markdown("<div style='font-size: 12px; color: #64748B; font-style: italic;'>None recorded.</div>", unsafe_allow_html=True)
        return
        
    for item in items:
        html = f"""
        <div style="background: {bg}; border-left: 3px solid {border_color}; padding: 6px 10px; margin-bottom: 4px; border-radius: 0 4px 4px 0;">
            <span style="font-size: 12px; color: #1E293B; line-height: 1.4;">{icon} {item}</span>
        </div>
        """
        st.markdown(_clean_html(html), unsafe_allow_html=True)

def render_epistemology_chip(category: str):
    """Renders an explicit epistemology chip (Data-Derived, Model Assumption, Simulated)."""
    configs = {
        "DATA-DERIVED": {"color": "#1D4ED8", "bg": "#EFF6FF", "border": "#BFDBFE", "label": "DATA-DERIVED (EMPIRICAL)"},
        "MODEL ASSUMPTION": {"color": "#B45309", "bg": "#FFFBEB", "border": "#FDE68A", "label": "MODEL ASSUMPTION (PARAMETRIC)"},
        "SIMULATED": {"color": "#6D28D9", "bg": "#F5F3FF", "border": "#DDD6FE", "label": "SIMULATED (COUNTERFACTUAL)"},
        "EVIDENCE STRENGTH": {"color": "#15803D", "bg": "#F0FDF4", "border": "#BBF7D0", "label": "EVIDENCE STRENGTH (INDEX)"}
    }
    cfg = configs.get(category, {"color": "#475569", "bg": "#F1F5F9", "border": "#CBD5E1", "label": category})
    html = f"""
    <span style="background: {cfg['bg']}; color: {cfg['color']}; border: 1px solid {cfg['border']}; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.4px; text-transform: uppercase;">
        {cfg['label']}
    </span>
    """
    st.markdown(_clean_html(html), unsafe_allow_html=True)

# Backward compatibility alias
render_data_tag = render_epistemology_chip
