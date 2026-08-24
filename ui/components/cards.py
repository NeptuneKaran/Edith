"""
ui/components/cards.py
Reusable UI Cards, Badges, and Metadata Chips for EDITH.
Ensures clean, executive-level visual hierarchy and explicit epistemological distinction.
"""
import streamlit as st

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

def render_evidence_score_badge(score: float, label: str = "Evidence Strength"):
    """Renders a styled, color-coded Evidence Score badge with clear heuristic definition."""
    if score >= 0.75:
        color = "#10B981" # Emerald
        bg = "rgba(16, 185, 129, 0.08)"
        badge_text = "STRONG EMPIRICAL SUPPORT"
    elif score >= 0.40:
        color = "#F59E0B" # Amber
        bg = "rgba(245, 158, 11, 0.08)"
        badge_text = "MODERATE SUPPORT"
    elif score > 0.0:
        color = "#9CA3AF" # Slate Grey
        bg = "rgba(156, 163, 175, 0.08)"
        badge_text = "WEAK SUPPORT"
    else:
        color = "#EF4444" # Red
        bg = "rgba(239, 68, 68, 0.08)"
        badge_text = "REFUTED BY EMPIRICAL DATA"
        
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; background: {bg}; padding: 8px 12px; border-radius: 6px; border-left: 3px solid {color}; border-top: 1px solid rgba(255,255,255,0.04); border-right: 1px solid rgba(255,255,255,0.04); border-bottom: 1px solid rgba(255,255,255,0.04); margin-bottom: 8px;">
            <div>
                <span style="font-size: 10px; font-weight: 700; color: {color}; letter-spacing: 0.5px; text-transform: uppercase;">{badge_text}</span>
                <div style="font-size: 11px; color: #9CA3AF; margin-top: 1px;">{label} <span style="font-size: 10px; color: #6B7280;">(Deterministic Index)</span></div>
            </div>
            <div style="font-size: 20px; font-weight: 800; color: {color}; letter-spacing: -0.3px;">{score:.2f} <span style="font-size: 12px; color: #6B7280; font-weight: 500;">/ 1.00</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_data_tag(tag_type: str = "DATA-DERIVED"):
    """Renders an epistemological badge: DATA-DERIVED vs MODEL ASSUMPTION vs SIMULATED vs EVIDENCE STRENGTH."""
    colors = {
        "DATA-DERIVED": ("#60A5FA", "rgba(59, 130, 246, 0.12)", "#3B82F6"),
        "MODEL ASSUMPTION": ("#FBBF24", "rgba(245, 158, 11, 0.12)", "#F59E0B"),
        "SIMULATED": ("#A78BFA", "rgba(139, 92, 246, 0.12)", "#8B5CF6"),
        "EVIDENCE STRENGTH": ("#34D399", "rgba(16, 185, 129, 0.12)", "#10B981")
    }
    color, bg, border = colors.get(tag_type, ("#9CA3AF", "rgba(156, 163, 175, 0.12)", "#6B7280"))
    st.markdown(
        f"""<span style="font-size: 9px; font-weight: 800; color: {color}; background-color: {bg}; border: 1px solid {border}; padding: 2px 7px; border-radius: 4px; letter-spacing: 0.6px; text-transform: uppercase;">{tag_type}</span>""",
        unsafe_allow_html=True
    )
