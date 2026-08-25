"""
ui/screens/s5_console.py
Screen 5: Dedicated Full-Page EDITH Conversational AI Console.
Natural-language decision intelligence assistant powered by Gemini tool-calling and safe native Markdown rendering.
"""
import streamlit as st
from state.session_state import set_screen
from ai.llm_client import EdithLLMClient
from data.repository import DataRepository

def render_screen_5():
    """Renders the dedicated full-page EDITH Conversational Console screen."""
    prev_screen = st.session_state.get("previous_screen", "overview")
    screen_names = {
        "sources": "Data Sources",
        "overview": "Overview (Detect)",
        "diagnostic": "Diagnostic (Diagnose)",
        "workspace": "Investigation Workspace (Explain)",
        "simulation": "Simulation Workbench (Simulate)"
    }
    prev_label = screen_names.get(prev_screen, "Investigation")
    repo = DataRepository.get_instance()
    source_info = repo.get_active_source_info()
    
    # 1. Top Action & Navigation Bar
    col_back, col_title, col_actions = st.columns([1.5, 3.2, 1.3])
    with col_back:
        if st.button(f"← Back to {prev_label}", key="btn_console_back", type="secondary", use_container_width=True):
            set_screen(prev_screen)
            st.rerun()
            
    with col_title:
        st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #0F172A;'>🤖 EDITH Conversational Assistant</h2>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 13px; color: #64748B; margin-top: 2px;'>Natural-language decision intelligence powered by analytical tool-calling and grounded evidence.</div>", unsafe_allow_html=True)
        
    with col_actions:
        st.markdown("<div style='text-align: right; display: flex; gap: 8px; justify-content: flex-end;'>", unsafe_allow_html=True)
        if st.button("🔄 Reset Conversation", key="btn_console_reset", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.edith_briefing = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    # Analytical Context & LLM Client Initialization
    anomaly_context = st.session_state.get("anomaly_context", {})
    hypotheses = st.session_state.get("hypotheses", [])
    selected_hypo_id = st.session_state.get("selected_hypothesis_id", "H1_PRICING_PRESSURE")
    selected_hypothesis = next((h for h in hypotheses if h["id"] == selected_hypo_id), hypotheses[0] if hypotheses else {})
    sim_levers = st.session_state.get("simulation_levers", {})
    
    user_key = (st.session_state.get("api_key_input") or os.getenv("GEMINI_API_KEY", "")).strip()
    client = EdithLLMClient(api_key=user_key)

    
    # Response Style Control in Session State
    if "response_style" not in st.session_state:
        st.session_state.response_style = "concise"

    # Status Bar & Controls Row
    col_status, col_style = st.columns([3.2, 1.8])
    with col_style:
        style_choice = st.radio(
            "Response Style:",
            options=["⚡ Executive (Concise)", "📑 Deep-Dive (Detailed)"],
            index=0 if st.session_state.response_style == "concise" else 1,
            horizontal=True,
            key="radio_resp_style"
        )
        st.session_state.response_style = "concise" if "Executive" in style_choice else "detailed"

    # Generate initial executive briefing if conversation is blank
    if not st.session_state.get("edith_briefing"):
        with st.spinner("EDITH is synthesizing verified analytical telemetry..."):
            briefing_text, metadata = client.generate_briefing(
                anomaly_context,
                hypotheses,
                response_style=st.session_state.response_style
            )
            st.session_state.edith_briefing = briefing_text
            st.session_state.llm_metadata = metadata

    meta = st.session_state.get("llm_metadata", {})
    mode = meta.get("mode", "Offline Evidence Mode (Zero-Key)")
    latency = meta.get("latency_sec", 0.01)
    provider = meta.get("provider", "Deterministic Engine")
    
    with col_status:
        st.markdown(
            f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 8px 14px; font-size: 12px; color: #1D4ED8; display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-weight: 800;">📁 Active Source:</span>
                    <span>{source_info.get('name', 'Demo Dataset')}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: #DBEAFE; color: #1E40AF; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;">{provider}</span>
                    <span>⚡ <b>{mode}</b> ({latency}s)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
    
    # 2. Executive Diagnostic Briefing Container
    with st.expander("📋 Active Incident Briefing (Grounded in Verified Data)", expanded=True):
        st.markdown(st.session_state.edith_briefing)
    
    # 3. Suggested Starter Probes
    st.markdown("<h4 style='font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 8px;'>💡 Suggested Investigation Questions</h4>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("👋 Hi EDITH, what can you do?", key="chip_greet", use_container_width=True):
            _handle_console_query(client, "Hello, what are your core capabilities?", anomaly_context, selected_hypothesis, hypotheses, sim_levers)
        if st.button("❓ Explain volume vs price loss", key="chip_math", use_container_width=True):
            _handle_console_query(client, "Explain the exact mathematical volume and price decomposition.", anomaly_context, selected_hypothesis, hypotheses, sim_levers)
    with col_p2:
        if st.button("❓ Compare pricing vs competitor", key="chip_comp", use_container_width=True):
            _handle_console_query(client, "Compare #1 Pricing Elasticity vs #2 Competitor Campaign.", anomaly_context, selected_hypothesis, hypotheses, sim_levers)
        if st.button("❓ Why is inventory ruled out?", key="chip_inv", use_container_width=True):
            _handle_console_query(client, "Why are supply and inventory constraints ruled out?", anomaly_context, selected_hypothesis, hypotheses, sim_levers)
    with col_p3:
        if st.button("❓ What should we do first?", key="chip_action", use_container_width=True):
            _handle_console_query(client, "What should we do first to fix this?", anomaly_context, selected_hypothesis, hypotheses, sim_levers)
        if st.button("❓ What is Difference-in-Differences?", key="chip_did_concept", use_container_width=True):
            _handle_console_query(client, "Explain what Difference-in-Differences is and how EDITH uses it.", anomaly_context, selected_hypothesis, hypotheses, sim_levers)

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    # 4. Render Dialogue History with native Streamlit chat bubbles (Zero HTML escaping issues)
    if st.session_state.get("chat_history"):
        st.markdown("<h4 style='font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 10px;'>💬 Conversation History</h4>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["content"])
                    msg_meta = msg.get("metadata", {})
                    provider = msg_meta.get("provider", "Deterministic Engine")
                    mode = msg_meta.get("mode", "Offline Mode")
                    tools_used = msg_meta.get("tools_called", [])
                    
                    if "Gemini" in provider:
                        st.caption(f"🟢 **{provider}** ({msg_meta.get('model', 'gemini-2.0-flash')}) &bull; Latency: {msg_meta.get('latency_sec', 0.1)}s")
                    else:
                        st.caption(f"🛡️ **{provider}** &bull; {mode}")
                        
                    if tools_used and tools_used != ["offline_deterministic_lookup"]:
                        st.caption(f"🔧 Tools executed: `{', '.join(tools_used)}`")

                
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
    
    # 5. Fixed Chat Input
    user_query = st.chat_input("Ask EDITH any question about root causes, evidence, trade-offs, or data...")
    if user_query:
        _handle_console_query(client, user_query, anomaly_context, selected_hypothesis, hypotheses, sim_levers)

def _handle_console_query(client, query: str, anomaly_ctx: dict, selected_h: dict, all_h: list, sim_levers: dict):
    """Executes a grounded Q&A turn with Gemini or deterministic reasoner."""
    with st.spinner("EDITH is analyzing..."):
        resp_style = st.session_state.get("response_style", "concise")
        history = st.session_state.get("chat_history", [])
        
        ans_text, metadata = client.answer_question(
            query=query,
            anomaly_context=anomaly_ctx,
            selected_hypothesis=selected_h,
            hypotheses=all_h,
            chat_history=history,
            simulation_levers=sim_levers,
            response_style=resp_style
        )
        st.session_state.chat_history.append({"role": "user", "content": query})
        st.session_state.chat_history.append({"role": "edith", "content": ans_text, "metadata": metadata})
        st.rerun()
