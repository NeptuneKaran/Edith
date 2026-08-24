"""
ui/components/chat_pane.py
Interactive Edith Reasoning Console for the Investigation Workspace (Screen 3).
"""
import streamlit as st
from ai.llm_client import EdithLLMClient

def render_edith_console(anomaly_context: dict, hypotheses: list, selected_hypothesis: dict):
    """Renders the split-pane conversational console on the right side of Screen 3."""
    col_hdr, col_reset = st.columns([3, 1])
    with col_hdr:
        st.markdown("<h3 style='margin:0; padding:0; font-size: 18px; font-weight: 700; color: #FFFFFF;'>🤖 EDITH Cognitive Reasoning Console</h3>", unsafe_allow_html=True)
    with col_reset:
        if st.button("🔄 Reset Dialogue", key="btn_reset_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.edith_briefing = None
            st.rerun()
            
    st.caption("Natural-language AI synthesis strictly grounded in pre-computed deterministic evidence ledgers.")
    
    # Initialize client with optional user-supplied API key
    user_key = st.session_state.get("api_key_input", "")
    client = EdithLLMClient(api_key=user_key)
    
    # Generate initial briefing if not already generated
    if not st.session_state.get("edith_briefing"):
        with st.spinner("EDITH is analyzing verified analytical evidence..."):
            briefing_text, metadata = client.generate_briefing(anomaly_context, hypotheses)
            st.session_state.edith_briefing = briefing_text
            st.session_state.llm_metadata = metadata

    # Telemetry / Grounding Chip
    meta = st.session_state.get("llm_metadata", {})
    mode = meta.get("mode", "Deterministic Grounded Fallback")
    latency = meta.get("latency_sec", 0.01)
    
    st.markdown(
        f"""
        <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 6px; padding: 6px 12px; font-size: 11px; color: #A5B4FC; margin: 8px 0 12px 0; display: flex; justify-content: space-between; align-items: center;">
            <span>🛡️ <b>Strict Analytical Grounding</b>: Downstream of Deterministic Engine</span>
            <span>⚡ <b>{mode}</b> ({latency}s)</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render primary executive briefing in a container
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            {st.session_state.edith_briefing}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h4 style='font-size: 14px; font-weight: 700; color: #E5E7EB; margin-bottom: 4px;'>💬 Interactive Grounded Probes</h4>", unsafe_allow_html=True)
    st.caption("Test hypothesis trade-offs or drill into contradictory empirical signals:")
    
    # Quick probe buttons
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("❓ Why is inventory ruled out?", use_container_width=True):
            _handle_user_query(client, "Why is inventory unlikely to be the cause?", anomaly_context, selected_hypothesis, hypotheses)
        if st.button("❓ Why is competitor action secondary?", use_container_width=True):
            _handle_user_query(client, "Why is competitor promotion secondary to pricing?", anomaly_context, selected_hypothesis, hypotheses)
    with col_q2:
        if st.button("❓ Explain pricing evidence", use_container_width=True):
            _handle_user_query(client, "What core evidence supports pricing pressure?", anomaly_context, selected_hypothesis, hypotheses)
        if st.button("❓ What is our calibrated uncertainty?", use_container_width=True):
            _handle_user_query(client, "What uncertainty or caveats exist?", anomaly_context, selected_hypothesis, hypotheses)

    # Free-form user input
    user_query = st.chat_input("Ask EDITH about data lineage, control cohorts, or trade-offs...")
    if user_query:
        _handle_user_query(client, user_query, anomaly_context, selected_hypothesis, hypotheses)

    # Render Q&A History
    if st.session_state.get("chat_history"):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("<h5 style='font-size: 13px; font-weight: 700; color: #9CA3AF;'>Investigation Q&A History:</h5>", unsafe_allow_html=True)
        for msg in reversed(st.session_state.chat_history[-4:]): # Show last 4 exchanges
            if msg["role"] == "user":
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.04); border-left: 3px solid #818CF8; border-radius: 4px; padding: 8px 12px; margin-bottom: 6px; font-size: 13px; color: #F3F4F6;">
                        <b>👤 You:</b> {msg['content']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="background: rgba(16, 185, 129, 0.04); border-left: 3px solid #10B981; border-radius: 4px; padding: 8px 12px; margin-bottom: 8px; font-size: 13px; color: #E5E7EB;">
                        <b>🤖 EDITH:</b><br>{msg['content']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def _handle_user_query(client, query: str, anomaly_ctx: dict, selected_h: dict, all_h: list):
    """Executes a grounded Q&A turn with the LLM or deterministic reasoner."""
    with st.spinner("EDITH is reviewing the evidence ledger..."):
        ans_text, metadata = client.answer_question(query, anomaly_ctx, selected_h, all_h)
        st.session_state.chat_history.append({"role": "user", "content": query})
        st.session_state.chat_history.append({"role": "edith", "content": ans_text, "metadata": metadata})
        st.rerun()
