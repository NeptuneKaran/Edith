"""
ai/llm_client.py
Unified LLM Gateway for EDITH.
Supports Google Gemini via google-genai SDK with transparent, guaranteed fallback to OfflineEdithReasoner.
"""
import os
import time
from typing import Dict, List, Any, Tuple
from ai.prompts import EDITH_SYSTEM_PROMPT, format_investigation_prompt
from ai.offline_reasoner import OfflineEdithReasoner
from config.settings import DEFAULT_GEMINI_MODEL, FALLBACK_GEMINI_MODEL

class EdithLLMClient:
    """Gateway managing LLM calls with automatic offline fallback."""
    
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

    def generate_briefing(self, anomaly_context: Dict[str, Any], hypotheses: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Generates the primary executive briefing using Gemini or deterministic fallback."""
        start_time = time.time()
        
        # If client is configured, attempt live call
        if self.client:
            prompt = format_investigation_prompt(anomaly_context, hypotheses)
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
                print(f"[LLM Client] Gemini call failed ({e}). Falling back to Offline Reasoner.")

        # Fallback to Deterministic Reasoner
        fallback_text = OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, hypotheses)
        latency = round(time.time() - start_time, 3)
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v1.0",
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
        hypotheses: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """Answers an interactive user question grounded in analytical state."""
        start_time = time.time()
        
        if self.client:
            prompt = format_investigation_prompt(anomaly_context, hypotheses, user_query=query)
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
                metadata = {
                    "provider": "Google Gemini",
                    "model": DEFAULT_GEMINI_MODEL,
                    "latency_sec": latency,
                    "mode": "Live Cloud LLM",
                    "status": "Success"
                }
                return response.text, metadata
            except Exception as e:
                print(f"[LLM Client] Gemini Q&A failed ({e}). Using Offline Reasoner.")

        # Fallback Q&A
        fallback_text = OfflineEdithReasoner.answer_followup_question(query, selected_hypothesis, hypotheses)
        latency = round(time.time() - start_time, 3)
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v1.0",
            "latency_sec": latency,
            "mode": "Deterministic Offline Fallback (100% Grounded)",
            "status": "Active (Zero-Key Mode)"
        }
        return fallback_text, metadata
