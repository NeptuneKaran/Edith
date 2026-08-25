"""
app.py
Main Streamlit Application Entrypoint for EDITH (Clean Light Theme).
AI-Assisted Business Intelligence Investigation System for Accenture Innovation Challenge 2026.
"""
import streamlit as st
import os

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="EDITH | Decision Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Decision-Grade Light Theme CSS
st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Generous Header & Container Spacing (Prevents Top Clipping) */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }
    p, span, label, div {
        color: #334155;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.2px;
        transition: all 0.15s ease-in-out;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #0F172A;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        padding: 6px 14px;
    }
    .stButton>button:hover {
        border-color: #2563EB;
        background-color: #EFF6FF;
        color: #1D4ED8;
    }
    .stButton>button[kind="primary"] {
        background-color: #2563EB !important;
        border: 1px solid #1D4ED8 !important;
        color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.25);
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    
    /* Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #FFFFFF;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 600;
        color: #64748B;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #BFDBFE !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    
    /* Chat Input */
    div[data-testid="stChatInput"] {
        border-color: #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #F8FAFC;
    }
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
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
    
    # Global Top Header & Segmented Navigation
    col_brand, col_steps = st.columns([1.3, 3.7])
    with col_brand:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0;">
                <div style="background: #2563EB; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 900; color: white; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);">E</div>
                <div>
                    <div style="font-size: 18px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px; line-height: 1.1;">EDITH</div>
                    <div style="font-size: 11px; font-weight: 700; color: #2563EB; letter-spacing: 0.5px;">DECISION INTELLIGENCE</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_steps:
        # Segmented Stage Tabs Control
        screen = st.session_state.current_screen
        
        stages = [
            ("overview", "1. Overview"),
            ("diagnostic", "2. Diagnostic"),
            ("workspace", "3. Causal Workspace"),
            ("simulation", "4. Simulation")
        ]
        
        stepper_html = '<div style="display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 6px 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">'
        
        for idx, (s_key, s_label) in enumerate(stages):
            is_active = (screen == s_key)
            color = "#1D4ED8" if is_active else "#64748B"
            bg = "#EFF6FF" if is_active else "transparent"
            border = "1px solid #BFDBFE" if is_active else "1px solid transparent"
            weight = "700" if is_active else "500"
            
            stepper_html += f'<span style="color: {color}; background: {bg}; border: {border}; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: {weight};">{s_label}</span>'
            if idx < len(stages) - 1:
                stepper_html += '<span style="color: #CBD5E1; font-size: 12px; font-weight: 600;">→</span>'
                
        stepper_html += '</div>'
        st.markdown(stepper_html, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
    
    # Sidebar Navigation & Settings
    with st.sidebar:
        st.markdown("### 🧭 Investigation Workflow")
        
        if st.button("📊 1. Business Overview", use_container_width=True, type="primary" if screen == "overview" else "secondary"):
            set_screen("overview")
            
        if st.button("📈 2. KPI Diagnostic", use_container_width=True, type="primary" if screen == "diagnostic" else "secondary"):
            set_screen("diagnostic")
            
        if st.button("🔬 3. Causal Workspace", use_container_width=True, type="primary" if screen == "workspace" else "secondary"):
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
        `OBSERVE → DETECT → LOCALIZE → INVESTIGATE → EXPLAIN → SIMULATE → ACT`
        
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
