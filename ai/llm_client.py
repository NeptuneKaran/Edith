"""
ai/llm_client.py
Unified LLM Gateway for EDITH Conversational AI with Tool-Calling capabilities.
Executes Gemini with safe read-only analytical tools and automatic fallback to OfflineEdithReasoner.
"""
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from ai.prompts import EDITH_SYSTEM_PROMPT, classify_user_intent
from ai.tools import AVAILABLE_TOOLS, execute_tool_call
from ai.offline_reasoner import OfflineEdithReasoner
from config.settings import DEFAULT_GEMINI_MODEL

class EdithLLMClient:
    """Conversational Agent Gateway managing Gemini tool-calling and offline fallback."""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[LLM Client] Failed to initialize Google GenAI: {e}")
                self.client = None

    def generate_briefing(
        self,
        anomaly_context: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        response_style: str = "concise"
    ) -> Tuple[str, Dict[str, Any]]:
        """Generates the primary executive briefing using tool-grounded Gemini or deterministic fallback."""
        start_time = time.time()
        
        # If client is configured, attempt live call with tools
        if self.client:
            try:
                prompt = f"Synthesize an executive diagnostic briefing for the active anomaly ({anomaly_context.get('kpi_name', 'Monthly B2B Sales')}). Response style: {response_style}."
                response = self.client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=prompt,
                    config={
                        "system_instruction": EDITH_SYSTEM_PROMPT,
                        "tools": AVAILABLE_TOOLS,
                        "temperature": 0.2
                    }
                )
                latency = round(time.time() - start_time, 2)
                text = response.text if hasattr(response, "text") and response.text else ""
                if text:
                    metadata = {
                        "provider": "Google Gemini (Tool-Equipped Agent)",
                        "model": DEFAULT_GEMINI_MODEL,
                        "latency_sec": latency,
                        "mode": "Live Tool-Calling Agent",
                        "status": "Success"
                    }
                    return text, metadata
            except Exception as e:
                print(f"[LLM Client] Gemini briefing call failed ({e}). Falling back to Offline Reasoner.")

        # Fallback to Deterministic Reasoner
        fallback_text = OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, hypotheses, response_style=response_style)
        latency = round(time.time() - start_time, 3)
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "latency_sec": latency,
            "mode": "Deterministic Offline Evidence Mode (Zero-Key)",
            "status": "Active (Offline Mode)"
        }
        return fallback_text, metadata

    def answer_question(
        self,
        query: str,
        anomaly_context: Dict[str, Any],
        selected_hypothesis: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        chat_history: List[Dict[str, Any]] = None,
        simulation_levers: Dict[str, Any] = None,
        response_style: str = "concise"
    ) -> Tuple[str, Dict[str, Any]]:
        """Answers user queries via tool-calling Gemini agent with guaranteed offline fallback."""
        start_time = time.time()
        intent = classify_user_intent(query)
        tools_called = []
        
        if self.client:
            try:
                # Format conversation contents
                contents = []
                if chat_history:
                    for msg in chat_history[-6:]:
                        role = "user" if msg.get("role") == "user" else "model"
                        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
                        
                # Current user message with style context
                styled_query = f"{query}\n\n(Style: {response_style})"
                contents.append({"role": "user", "parts": [{"text": styled_query}]})
                
                # Execute with tools enabled
                response = self.client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=contents,
                    config={
                        "system_instruction": EDITH_SYSTEM_PROMPT,
                        "tools": AVAILABLE_TOOLS,
                        "temperature": 0.2
                    }
                )
                
                # Inspect for tool usage metadata if available
                if hasattr(response, "function_calls") and response.function_calls:
                    for fc in response.function_calls:
                        tools_called.append(fc.name)
                        
                latency = round(time.time() - start_time, 2)
                text = response.text if hasattr(response, "text") and response.text else ""
                
                if text:
                    metadata = {
                        "provider": "Google Gemini (Tool-Equipped Agent)",
                        "model": DEFAULT_GEMINI_MODEL,
                        "latency_sec": latency,
                        "mode": "Live Tool-Calling Agent",
                        "intent": intent,
                        "tools_called": tools_called,
                        "status": "Success"
                    }
                    return text, metadata
            except Exception as e:
                print(f"[LLM Client] Gemini tool-calling turn failed ({e}). Falling back to Offline Reasoner.")

        # Fallback to Conversational Offline Reasoner
        fallback_text = OfflineEdithReasoner.answer_conversational_query(
            query=query,
            anomaly_context=anomaly_context,
            selected_hypothesis=selected_hypothesis,
            all_hypotheses=hypotheses,
            chat_history=chat_history,
            simulation_levers=simulation_levers,
            response_style=response_style
        )
        latency = round(time.time() - start_time, 3)
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "latency_sec": latency,
            "mode": "Offline Evidence Mode (Zero-Key)",
            "intent": intent,
            "tools_called": ["offline_deterministic_lookup"],
            "status": "Active (Offline Mode)"
        }
        return fallback_text, metadata

    def chat_turn(
        self,
        query: str,
        anomaly_context: Dict[str, Any],
        selected_hypothesis: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        chat_history: List[Dict[str, Any]] = None,
        simulation_levers: Dict[str, Any] = None,
        response_style: str = "concise"
    ) -> Tuple[str, Dict[str, Any]]:
        """Alias for answer_question providing conversational parity."""
        return self.answer_question(
            query=query,
            anomaly_context=anomaly_context,
            selected_hypothesis=selected_hypothesis,
            hypotheses=hypotheses,
            chat_history=chat_history,
            simulation_levers=simulation_levers,
            response_style=response_style
        )
