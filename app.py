"""
app.py
Main Streamlit Application Entrypoint for EDITH (Executive Decision Intelligence Platform).
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
    
    /* Generous Top Padding to Ensure Zero Clipping */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
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
from data.repository import DataRepository
from ui.screens.s0_data_sources import render_screen_0
from ui.screens.s1_overview import render_screen_1
from ui.screens.s2_diagnostic import render_screen_2
from ui.screens.s3_workspace import render_screen_3
from ui.screens.s4_simulation import render_screen_4
from ui.screens.s5_console import render_screen_5

def main():
    # Initialize state
    init_session_state()
    
    screen = st.session_state.current_screen
    repo = DataRepository.get_instance()
    source_info = repo.get_active_source_info()
    is_demo = source_info.get("is_demo", True)
    
    # 1. TOP HEADER (Brand, Active Source, Live Status, Persistent "Ask EDITH" CTA)
    col_brand, col_cta = st.columns([3.2, 1.8])
    with col_brand:
        source_badge_text = "Demo Data Active" if is_demo else f"Source: {source_info.get('name', 'Custom')[:24]}"
        source_badge_bg = "#EFF6FF" if is_demo else "#F0FDF4"
        source_badge_color = "#1D4ED8" if is_demo else "#166534"
        
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="background: #2563EB; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 19px; font-weight: 900; color: white; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);">E</div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 19px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px; line-height: 1.1;">EDITH</span>
                        <span style="background: {source_badge_bg}; color: {source_badge_color}; border: 1px solid #BFDBFE; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 4px; letter-spacing: 0.4px;">{source_badge_text}</span>
                    </div>
                    <div style="font-size: 11px; font-weight: 700; color: #2563EB; letter-spacing: 0.5px;">EXECUTIVE DECISION INTELLIGENCE PLATFORM</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_cta:
        # Check API key status for indicator
        has_key = bool(os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key_input"))
        status_text = "Live Gemini Agent" if has_key else "Offline Mode"
        status_icon = "🟢" if has_key else "🛡️"
        
        c_status, c_ask = st.columns([1.1, 1.4])
        with c_status:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 6px; font-size: 11px; font-weight: 700; color: #64748B;">
                    {status_icon} {status_text}
                </div>
                """,
                unsafe_allow_html=True
            )
        with c_ask:
            # Persistent "Ask EDITH" button opens the dedicated full-page console
            if screen == "console":
                prev_screen = st.session_state.get("previous_screen", "overview")
                if st.button("← Back to Investigation", key="btn_hdr_back", type="primary", use_container_width=True):
                    set_screen(prev_screen)
            else:
                if st.button("💬 Ask EDITH Console", key="btn_hdr_ask_edith", type="primary", use_container_width=True):
                    set_screen("console")

    # 2. TOP WORKFLOW PROGRESS STEPPER (Data Sources → Detect → Diagnose → Explain → Simulate)
    col_w0, col_w1, col_w2, col_w3, col_w4 = st.columns(5)
    with col_w0:
        if st.button("0. Data Sources", key="nav_s0", use_container_width=True, type="primary" if screen == "sources" else "secondary"):
            set_screen("sources")
    with col_w1:
        if st.button("1. Detect (Overview)", key="nav_s1", use_container_width=True, type="primary" if screen == "overview" else "secondary"):
            set_screen("overview")
    with col_w2:
        if st.button("2. Diagnose (Diagnostic)", key="nav_s2", use_container_width=True, type="primary" if screen == "diagnostic" else "secondary"):
            set_screen("diagnostic")
    with col_w3:
        if st.button("3. Explain (Causal DAG)", key="nav_s3", use_container_width=True, type="primary" if screen == "workspace" else "secondary"):
            set_screen("workspace")
    with col_w4:
        if st.button("4. Simulate (Action Plan)", key="nav_s4", use_container_width=True, type="primary" if screen == "simulation" else "secondary"):
            set_screen("simulation")
            
    st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)
    
    # 3. AUXILIARY SIDEBAR SETTINGS & INFO
    with st.sidebar:
        st.markdown("### ⚙️ Investigation Engine Settings")
        
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
            st.success("🟢 Live Gemini Agent Configured")
        else:
            st.info("🛡️ Offline Evidence Mode (Zero-Key Guaranteed)")
            
        st.markdown("---")
        st.markdown("### 🧭 Quick Switcher")
        if st.button("📁 Switch / Manage Data Sources", key="sb_sources_btn", use_container_width=True):
            set_screen("sources")
        if st.button("💬 Open EDITH Console", key="sb_console_btn", use_container_width=True, type="primary" if screen == "console" else "secondary"):
            set_screen("console")
            
        st.markdown("---")
        st.markdown("### ℹ️ About EDITH")
        st.caption("""
        **Accenture Innovation Challenge 2026**
        Problem Track 3: BusinessIntelligence.ai
        
        **Workflow:**
        `SOURCES → DETECT → DIAGNOSE → EXPLAIN → SIMULATE`
        
        *Engineered by Team IIT Kanpur (2026).*
        """)

    # 4. SCREEN ROUTING
    if screen == "sources":
        render_screen_0()
    elif screen == "overview":
        render_screen_1()
    elif screen == "diagnostic":
        render_screen_2()
    elif screen == "workspace":
        render_screen_3()
    elif screen == "simulation":
        render_screen_4()
    elif screen == "console":
        render_screen_5()
    else:
        render_screen_1()

if __name__ == "__main__":
    main()
