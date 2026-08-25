"""
ai/llm_client.py
Unified LLM Gateway for EDITH Conversational AI.
Supports Google Gemini via google-genai SDK with transparent, guaranteed fallback to OfflineEdithReasoner.
Preserves multi-turn conversation history, response style preferences, and rigorous data grounding.
"""
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from ai.prompts import EDITH_SYSTEM_PROMPT, format_investigation_prompt, classify_user_intent
from ai.offline_reasoner import OfflineEdithReasoner
from config.settings import DEFAULT_GEMINI_MODEL, FALLBACK_GEMINI_MODEL

class EdithLLMClient:
    """Gateway managing conversational LLM interactions with automatic offline fallback."""
    
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
        """Generates the primary executive briefing using Gemini or deterministic fallback."""
        start_time = time.time()
        
        # If client is configured, attempt live call
        if self.client:
            prompt = format_investigation_prompt(anomaly_context, hypotheses, response_style=response_style)
            try:
                response = self.client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=prompt,
                    config={
                        "system_instruction": EDITH_SYSTEM_PROMPT,
                        "temperature": 0.2
                    }
                )
                latency = round(time.time() - start_time, 2)
                text = response.text
                metadata = {
                    "provider": "Google Gemini",
                    "model": DEFAULT_GEMINI_MODEL,
                    "latency_sec": latency,
                    "mode": "Live Cloud LLM",
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
            "mode": "Deterministic Offline Fallback (100% Grounded)",
            "status": "Active (Zero-Key Mode)"
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
        """Answers an interactive user question grounded in multi-turn conversational context."""
        start_time = time.time()
        intent = classify_user_intent(query)
        
        if self.client:
            prompt = format_investigation_prompt(
                anomaly_context=anomaly_context,
                hypotheses=hypotheses,
                user_query=query,
                chat_history=chat_history,
                simulation_levers=simulation_levers,
                response_style=response_style
            )
            try:
                response = self.client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=prompt,
                    config={
                        "system_instruction": EDITH_SYSTEM_PROMPT,
                        "temperature": 0.3
                    }
                )
                latency = round(time.time() - start_time, 2)
                metadata = {
                    "provider": "Google Gemini",
                    "model": DEFAULT_GEMINI_MODEL,
                    "latency_sec": latency,
                    "mode": "Live Conversational Assistant",
                    "intent": intent,
                    "status": "Success"
                }
                return response.text, metadata
            except Exception as e:
                print(f"[LLM Client] Gemini conversational turn failed ({e}). Using Offline Reasoner.")

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
            "mode": "Deterministic Grounded Assistant (Zero-Key)",
            "intent": intent,
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
