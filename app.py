"""
app.py
Main Streamlit Application Entrypoint for EDITH.
AI-Assisted Business Intelligence Investigation System for Accenture Innovation Challenge 2026.
"""
import streamlit as st
import os

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="EDITH | AI-Assisted BI Investigation",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS (Palantir / McKinsey Decision-Grade Aesthetic)
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Global Header Spacing */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.3px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.12);
        background-color: rgba(255, 255, 255, 0.04);
        color: #E5E7EB;
    }
    .stButton>button:hover {
        border-color: #6366F1;
        background-color: rgba(99, 102, 241, 0.1);
        color: #FFFFFF;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
        border: 1px solid #6366F1;
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        box-shadow: 0 0 16px rgba(99, 102, 241, 0.5);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #9CA3AF !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.02);
        padding: 6px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 600;
        color: #9CA3AF;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.15) !important;
        color: #818CF8 !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Sliders */
    div[data-baseweb="slider"] {
        margin-top: 10px;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4B5563;
    }
</style>
""", unsafe_allow_html=True)

from state.session_state import init_session_state, set_screen
from ui.screens.s1_overview import render_screen_1
from ui.screens.s2_diagnostic import render_screen_2
from ui.screens.s3_workspace import render_screen_3
from ui.screens.s4_simulation import render_screen_4

def main():
    # Initialize state
    init_session_state()
    
    # Global Top Header & Stage Stepper
    col_brand, col_steps = st.columns([1.3, 3.7])
    with col_brand:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
                <div style="background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 900; color: white; box-shadow: 0 2px 10px rgba(99, 102, 241, 0.4);">E</div>
                <div>
                    <div style="font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.3px; line-height: 1.1;">EDITH</div>
                    <div style="font-size: 11px; font-weight: 600; color: #818CF8; letter-spacing: 0.4px;">DECISION INTELLIGENCE</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_steps:
        # Visual Stage Stepper
        screen = st.session_state.current_screen
        
        stages = [
            ("overview", "1. Overview"),
            ("diagnostic", "2. Diagnostic"),
            ("workspace", "3. Investigation"),
            ("simulation", "4. Simulation")
        ]
        
        stepper_html = '<div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 16px;">'
        
        for idx, (s_key, s_label) in enumerate(stages):
            is_active = (screen == s_key)
            color = "#818CF8" if is_active else "#6B7280"
            bg = "rgba(99, 102, 241, 0.12)" if is_active else "transparent"
            border = "1px solid rgba(99, 102, 241, 0.3)" if is_active else "1px solid transparent"
            weight = "700" if is_active else "500"
            
            stepper_html += f'<span style="color: {color}; background: {bg}; border: {border}; padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: {weight};">{s_label}</span>'
            if idx < len(stages) - 1:
                stepper_html += '<span style="color: #374151; font-size: 11px;">→</span>'
                
        stepper_html += '</div>'
        st.markdown(stepper_html, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)
    
    # Sidebar Navigation & Settings
    with st.sidebar:
        st.markdown("### 🧭 Investigation Workflow")
        
        if st.button("📊 1. Business Overview", use_container_width=True, type="primary" if screen == "overview" else "secondary"):
            set_screen("overview")
            
        if st.button("📈 2. KPI Diagnostic", use_container_width=True, type="primary" if screen == "diagnostic" else "secondary"):
            set_screen("diagnostic")
            
        if st.button("🔬 3. Investigation Workspace", use_container_width=True, type="primary" if screen == "workspace" else "secondary"):
            set_screen("workspace")
            
        if st.button("🔮 4. Scenario Simulation", use_container_width=True, type="primary" if screen == "simulation" else "secondary"):
            set_screen("simulation")
            
        st.markdown("---")
        st.markdown("### ⚙️ AI Engine Settings")
        
        # API Key input (optional)
        current_key = os.getenv("GEMINI_API_KEY", "")
        key_input = st.text_input(
            "Gemini API Key (Optional)",
            value=st.session_state.api_key_input or current_key,
            type="password",
            help="If left blank, EDITH operates in 100% deterministic offline fallback mode using pre-computed verified evidence."
        )
        st.session_state.api_key_input = key_input
        
        if key_input:
            st.success("🟢 Live Gemini API Configured")
        else:
            st.info("🛡️ Offline Fallback Active (Zero-Key Guaranteed Reliability)")
            
        st.markdown("---")
        st.markdown("### ℹ️ About EDITH")
        st.caption("""
        **Accenture Innovation Challenge 2026**
        Problem Track 3: BusinessIntelligence.ai
        
        **Mechanism:**
        `OBSERVE → DETECT → INVESTIGATE → EVIDENCE → EXPLAIN → SIMULATE → ACT`
        
        *Engineered by Team IIT Kanpur (2026).*
        """)

    # Screen Routing
    if screen == "overview":
        render_screen_1()
    elif screen == "diagnostic":
        render_screen_2()
    elif screen == "workspace":
        render_screen_3()
    elif screen == "simulation":
        render_screen_4()
    else:
        render_screen_1()

if __name__ == "__main__":
    main()
