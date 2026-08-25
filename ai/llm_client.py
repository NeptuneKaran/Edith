"""
ai/llm_client.py
Unified LLM Gateway for EDITH Conversational AI with Multi-Turn Tool-Calling capabilities.
Executes Gemini with safe read-only analytical tools and automatic fallback to OfflineEdithReasoner.
"""
import os
import time
import re
from typing import Dict, List, Any, Tuple, Optional
from ai.prompts import EDITH_SYSTEM_PROMPT, classify_user_intent
from ai.tools import AVAILABLE_TOOLS, execute_tool_call
from ai.offline_reasoner import OfflineEdithReasoner
from config.settings import DEFAULT_GEMINI_MODEL, FALLBACK_GEMINI_MODEL

def _sanitize_log_message(msg: str, key: str = "") -> str:
    """Removes sensitive API key tokens from logs."""
    if key and len(key) > 6:
        msg = msg.replace(key, f"{key[:6]}...[REDACTED]")
    # Also strip common API key patterns
    msg = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[REDACTED_API_KEY]', msg)
    return msg

class EdithLLMClient:
    """Conversational Agent Gateway managing Gemini tool-calling loop and offline fallback."""
    
    def __init__(self, api_key: str = ""):
        # Priority: explicitly passed key -> environment variable GEMINI_API_KEY
        raw_key = api_key if api_key else os.getenv("GEMINI_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""
        self.client = None
        self.primary_model = DEFAULT_GEMINI_MODEL
        self.fallback_model = FALLBACK_GEMINI_MODEL
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                masked_prefix = self.api_key[:6] + "..." if len(self.api_key) > 6 else "***"
                print(f"[LLM Gateway] Initialized Google GenAI SDK (Key length: {len(self.api_key)}, Prefix: {masked_prefix})")
            except Exception as e:
                safe_err = _sanitize_log_message(str(e), self.api_key)
                print(f"[LLM Gateway] Failed to initialize Google GenAI SDK: {safe_err}")
                self.client = None
        else:
            print("[LLM Gateway] No GEMINI_API_KEY found. Operating in 100% Deterministic Offline Mode.")

    def generate_briefing(
        self,
        anomaly_context: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        response_style: str = "concise"
    ) -> Tuple[str, Dict[str, Any]]:
        """Generates the primary executive briefing using tool-grounded Gemini or deterministic fallback."""
        start_time = time.time()
        last_error = ""
        
        if self.client:
            prompt = f"Synthesize an executive diagnostic briefing for the active anomaly ({anomaly_context.get('kpi_name', 'Monthly B2B Sales')}). Style: {response_style}."
            for model_name in [self.primary_model, self.fallback_model]:
                try:
                    text, tools_called = self._execute_tool_calling_loop(
                        model_name=model_name,
                        initial_prompt=prompt,
                        chat_history=None
                    )
                    latency = round(time.time() - start_time, 2)
                    if text:
                        metadata = {
                            "provider": "Google Gemini",
                            "model": model_name,
                            "latency_sec": latency,
                            "mode": f"Live Gemini Agent ({model_name})",
                            "tools_called": tools_called,
                            "status": "Success"
                        }
                        return text, metadata
                except Exception as e:
                    last_error = _sanitize_log_message(str(e), self.api_key)
                    print(f"[LLM Gateway] Briefing failed on {model_name}: {last_error}")

        # Fallback to Deterministic Reasoner
        fallback_text = OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, hypotheses, response_style=response_style)
        latency = round(time.time() - start_time, 3)
        fallback_mode = "Deterministic Offline Mode (Zero-Key)" if not self.api_key else f"Offline Fallback (Gemini Error: {last_error[:40]})"
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "latency_sec": latency,
            "mode": fallback_mode,
            "status": "Active (Offline Mode)",
            "error_detail": last_error if last_error else None
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
        last_error = ""
        
        if self.client:
            styled_query = f"{query}\n\n(Style: {response_style})"
            for model_name in [self.primary_model, self.fallback_model]:
                try:
                    text, tools_called = self._execute_tool_calling_loop(
                        model_name=model_name,
                        initial_prompt=styled_query,
                        chat_history=chat_history
                    )
                    latency = round(time.time() - start_time, 2)
                    if text:
                        metadata = {
                            "provider": "Google Gemini",
                            "model": model_name,
                            "latency_sec": latency,
                            "mode": f"Live Gemini Agent ({model_name})",
                            "intent": intent,
                            "tools_called": tools_called,
                            "status": "Success"
                        }
                        return text, metadata
                except Exception as e:
                    last_error = _sanitize_log_message(str(e), self.api_key)
                    print(f"[LLM Gateway] Query failed on {model_name}: {last_error}")

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
        fallback_mode = "Offline Evidence Mode (Zero-Key)" if not self.api_key else f"Offline Fallback ({last_error[:40]})"
        metadata = {
            "provider": "Deterministic Analytical Engine",
            "model": "OfflineEdithReasoner v2.0",
            "latency_sec": latency,
            "mode": fallback_mode,
            "intent": intent,
            "tools_called": ["offline_deterministic_lookup"],
            "status": "Active (Offline Mode)",
            "error_detail": last_error if last_error else None
        }
        return fallback_text, metadata

    def _execute_tool_calling_loop(
        self,
        model_name: str,
        initial_prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        max_turns: int = 5
    ) -> Tuple[str, List[str]]:
        """
        Executes a bounded multi-turn tool-calling loop with Google GenAI SDK.
        1. Formats conversation messages.
        2. Calls Gemini with tools.
        3. If Gemini returns function_calls, executes each tool and passes results back.
        4. Continues until final text is synthesized or max_turns is reached.
        """
        from google.genai import types
        
        # Build contents from history
        contents: List[Any] = []
        if chat_history:
            for msg in chat_history[-6:]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.get("content", ""))]
                ))
                
        # Append current user prompt
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=initial_prompt)]
        ))
        
        config = types.GenerateContentConfig(
            system_instruction=EDITH_SYSTEM_PROMPT,
            tools=AVAILABLE_TOOLS,
            temperature=0.2
        )
        
        tools_called = []
        
        for turn_idx in range(max_turns):
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            
            # Case A: Model requested tool execution
            if hasattr(response, "function_calls") and response.function_calls:
                # Add model's function calls to contents
                model_parts = []
                for candidate in getattr(response, "candidates", []):
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        model_parts.extend(candidate.content.parts)
                if not model_parts:
                    for fc in response.function_calls:
                        fn_name = str(getattr(fc, "name", "tool"))
                        raw_args = getattr(fc, "args", {})
                        fn_args = dict(raw_args) if hasattr(raw_args, "items") else {}
                        model_parts.append(types.Part(function_call=types.FunctionCall(name=fn_name, args=fn_args)))
                contents.append(types.Content(role="model", parts=model_parts))

                
                # Execute each function call and create responses
                fn_response_parts = []
                for fc in response.function_calls:
                    fn_name = getattr(fc, "name", "")
                    fn_args = getattr(fc, "args", {}) or {}
                    if hasattr(fn_args, "items"):
                        args_dict = dict(fn_args)
                    else:
                        args_dict = {}
                    tools_called.append(fn_name)
                    
                    tool_result = execute_tool_call(fn_name, args_dict)
                    fn_response_parts.append(types.Part.from_function_response(
                        name=fn_name,
                        response={"result": tool_result}
                    ))
                    
                # Append function responses as user/tool role content
                contents.append(types.Content(role="user", parts=fn_response_parts))
                continue
                
            # Case B: Model returned direct text response
            final_text = response.text if hasattr(response, "text") and response.text else ""
            if final_text:
                return final_text, tools_called
                
        return "", tools_called

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
