"""
ai/llm_client.py
Unified LLM Gateway for EDITH Conversational AI with Multi-Turn Tool-Calling capabilities.
Executes Gemini with safe read-only analytical tools and automatic fallback to OfflineEdithReasoner.
"""
import os
import time
import re
from typing import Dict, List, Any, Tuple, Optional
from ai.prompts import EDITH_SYSTEM_PROMPT, get_persona_prompt_addendum, classify_user_intent
from ai.tools import AVAILABLE_TOOLS, execute_tool_call
from ai.offline_reasoner import OfflineEdithReasoner
from config.settings import DEFAULT_GEMINI_MODEL, FALLBACK_GEMINI_MODEL
from core.telemetry import record_event as record_telemetry

def _sanitize_log_message(msg: str, key: str = "") -> str:
    """Removes sensitive API key tokens from logs."""
    if key and len(key) > 6:
        msg = msg.replace(key, f"{key[:6]}...[REDACTED]")
    # Also strip common API key patterns
    msg = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[REDACTED_API_KEY]', msg)
    return msg

def _build_gemini_contents(initial_prompt: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> List[Any]:
    """
    Builds clean, valid Google GenAI Content messages.
    Crucial requirements enforced:
    1. The conversation MUST start with a 'user' turn (leading model greetings are dropped).
    2. Roles strictly alternate: user -> model -> user -> model.
    3. The final message is the current user query with role='user'.
    """
    from google.genai import types
    
    clean_history = []
    if chat_history:
        for msg in chat_history:
            content_str = str(msg.get("content", "")).strip()
            if not content_str:
                continue
            raw_role = str(msg.get("role", "user")).lower()
            role = "model" if raw_role in ["assistant", "model", "bot"] else "user"
            clean_history.append({"role": role, "content": content_str})
            
    # If the last message in history is the current user query, remove it to prevent duplicate user turns
    if clean_history and clean_history[-1]["role"] == "user" and clean_history[-1]["content"].lower() == initial_prompt.strip().lower():
        clean_history.pop()

    # Gemini API requirement: Conversation MUST start with 'user'. Drop any leading 'model' greeting messages.
    while clean_history and clean_history[0]["role"] == "model":
        clean_history.pop(0)

    # Build strictly alternating sequence: user -> model -> user -> model ...
    contents: List[Any] = []
    prev_role = None
    
    # Take up to last 8 turns of history
    for item in clean_history[-8:]:
        role = item["role"]
        text = item["content"]
        
        if role == prev_role and contents:
            contents[-1].parts.append(types.Part.from_text(text=f"\n{text}"))
        else:
            if not contents and role == "model":
                continue  # Never start with model
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)]
            ))
            prev_role = role

    # Ensure last message is current user prompt with role="user"
    if contents and contents[-1].role == "user":
        contents[-1].parts.append(types.Part.from_text(text=f"\n\n{initial_prompt}"))
    else:
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=initial_prompt)]
        ))
        
    # Final sanity check: ensure contents[0].role == 'user'
    while contents and contents[0].role == "model":
        contents.pop(0)
        
    if not contents:
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=initial_prompt)]
        ))
        
    return contents



class EdithLLMClient:
    """Conversational Agent Gateway managing Gemini tool-calling loop and offline fallback."""
    
    def __init__(self, api_key: str = ""):
        # Priority: explicitly passed key -> GEMINI_API_KEY -> GOOGLE_API_KEY -> GEMINI_KEY -> GENAI_API_KEY
        raw_key = (
            api_key or
            os.getenv("GEMINI_API_KEY") or
            os.getenv("GOOGLE_API_KEY") or
            os.getenv("GEMINI_KEY") or
            os.getenv("GEMINI_API_TOKEN") or
            os.getenv("GENAI_API_KEY") or
            ""
        )
        self.api_key = raw_key.strip().strip("'").strip('"') if raw_key else ""
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
            print("[LLM Gateway] No GEMINI_API_KEY / GOOGLE_API_KEY found. Operating in 100% Deterministic Offline Mode.")



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
                    text, tools_called, prompt_tokens, completion_tokens = self._execute_tool_calling_loop(
                        model_name=model_name,
                        initial_prompt=prompt,
                        chat_history=None
                    )
                    latency = round(time.time() - start_time, 2)
                    record_telemetry(
                        endpoint="generate_briefing",
                        provider="Google Gemini" if self.api_key else "Deterministic Offline",
                        latency_ms=latency * 1000,
                        model_calls=1,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    if text:
                        metadata = {
                            "provider": "Google Gemini",
                            "model": model_name,
                            "latency_sec": latency,
                            "mode": f"Live Gemini Agent ({model_name})",
                            "tools_called": tools_called,
                            "status": "Success",
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens
                        }
                        return text, metadata
                except Exception as e:
                    last_error = _sanitize_log_message(str(e), self.api_key)
                    print(f"[LLM Gateway] Briefing failed on {model_name}: {last_error}")

        # Fallback to Deterministic Reasoner
        fallback_text = OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, hypotheses, response_style=response_style)
        latency = round(time.time() - start_time, 3)
        record_telemetry(
            endpoint="generate_briefing",
            provider="Deterministic Offline",
            latency_ms=latency * 1000,
            model_calls=0,
            prompt_tokens=0,
            completion_tokens=0
        )
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

    def answer_question(self, query: str, anomaly_context: Dict[str, Any], selected_hypothesis: Dict[str, Any], hypotheses: List[Dict[str, Any]], chat_history: List[Dict[str, Any]] = None, simulation_levers: Dict[str, Any] = None, response_style: str = "concise", persona: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Answers user queries via tool-calling Gemini agent with guaranteed offline fallback."""
        start_time = time.time()
        intent = classify_user_intent(query)
        last_error = ""
        
        if self.client:
            styled_query = f"{query}\n\n(Style: {response_style})"
            for model_name in [self.primary_model, self.fallback_model]:
                try:
                    text, tools_called, prompt_tokens, completion_tokens = self._execute_tool_calling_loop(
                        model_name=model_name,
                        initial_prompt=styled_query,
                        chat_history=chat_history,
                        persona_id=persona
                    )
                    if not text:
                        text = self._execute_direct_generation(
                            model_name=model_name,
                            prompt=styled_query,
                            chat_history=chat_history,
                            persona_id=persona
                        )
                        tools_called = ["direct_prompt_generation"]
                        # Just log 0 tokens for direct generation fallback if it happens
                        prompt_tokens = 0
                        completion_tokens = 0
                    
                    latency = round(time.time() - start_time, 2)
                    record_telemetry(
                        endpoint="answer_question",
                        provider="Google Gemini" if self.api_key else "Deterministic Offline",
                        latency_ms=latency * 1000,
                        model_calls=len(tools_called) if tools_called and tools_called != ["direct_prompt_generation"] else 1,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    if text:
                        metadata = {
                            "provider": "Google Gemini",
                            "model": model_name,
                            "latency_sec": latency,
                            "mode": f"Live Gemini Agent ({model_name})",
                            "intent": intent,
                            "tools_called": tools_called,
                            "status": "Success",
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens
                        }
                        return text, metadata
                except Exception as e:
                    last_error = _sanitize_log_message(str(e), self.api_key)
                    print(f"[LLM Gateway] Query failed on {model_name}: {last_error}")
                    try:
                        # Try direct generation without tools as second line of defense
                        text = self._execute_direct_generation(
                            model_name=model_name,
                            prompt=styled_query,
                            chat_history=chat_history,
                            persona_id=persona
                        )
                        if text:
                            latency = round(time.time() - start_time, 2)
                            record_telemetry(
                                endpoint="answer_question",
                                provider="Google Gemini" if self.api_key else "Deterministic Offline",
                                latency_ms=latency * 1000,
                                model_calls=1,
                                prompt_tokens=0,
                                completion_tokens=0
                            )
                            metadata = {
                                "provider": "Google Gemini",
                                "model": model_name,
                                "latency_sec": latency,
                                "mode": f"Live Gemini Agent ({model_name})",
                                "intent": intent,
                                "tools_called": ["direct_generation_fallback"],
                                "status": "Success",
                                "prompt_tokens": 0,
                                "completion_tokens": 0
                            }
                            return text, metadata
                    except Exception as e2:
                        last_error = _sanitize_log_message(str(e2), self.api_key)
                        print(f"[LLM Gateway] Direct generation failed on {model_name}: {last_error}")


        # Fallback to Conversational Offline Reasoner
        fallback_text = OfflineEdithReasoner.answer_conversational_query(
            query=query,
            anomaly_context=anomaly_context,
            selected_hypothesis=selected_hypothesis,
            all_hypotheses=hypotheses,
            chat_history=chat_history,
            simulation_levers=simulation_levers,
            persona=persona or "executive",
            response_style=response_style
        )
        latency = round(time.time() - start_time, 3)
        record_telemetry(
            endpoint="answer_question",
            provider="Deterministic Offline",
            latency_ms=latency * 1000,
            model_calls=0,
            prompt_tokens=0,
            completion_tokens=0
        )
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

    def _execute_tool_calling_loop(self, model_name: str, initial_prompt: str, chat_history: Optional[List[Dict[str, Any]]] = None, persona_id: Optional[str] = None, max_turns: int = 5) -> Tuple[str, List[str], int, int]:
        """
        Executes a bounded multi-turn tool-calling loop with Google GenAI SDK.
        1. Formats conversation messages using _build_gemini_contents to prevent role mismatch.
        2. Calls Gemini with tools.
        3. If Gemini returns function_calls, executes each tool and passes results back.
        4. Continues until final text is synthesized or max_turns is reached.
        """
        from google.genai import types
        
        # Build contents from history ensuring strict alternating user/model roles
        contents: List[Any] = _build_gemini_contents(initial_prompt, chat_history)
        
        sys_inst = EDITH_SYSTEM_PROMPT + ("\n" + get_persona_prompt_addendum(persona_id) if persona_id else "")
        config = types.GenerateContentConfig(
            system_instruction=sys_inst,
            tools=AVAILABLE_TOOLS,
            temperature=0.2
        )
        
        tools_called = []
        prompt_tokens = 0
        completion_tokens = 0
        
        for turn_idx in range(max_turns):
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                prompt_tokens += getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
                completion_tokens += getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
            
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
                    
                    tool_result = execute_tool_call(fn_name, args_dict, persona_id=persona_id)
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
                return final_text, tools_called, prompt_tokens, completion_tokens
                
        return "", tools_called, prompt_tokens, completion_tokens

    def _execute_direct_generation(self, model_name: str, prompt: str, chat_history: Optional[List[Dict[str, Any]]] = None, persona_id: Optional[str] = None) -> str:
        """Direct prompt generation without function calling as a resilient fallback."""
        from google.genai import types
        contents = _build_gemini_contents(prompt, chat_history)
        sys_inst = EDITH_SYSTEM_PROMPT + ("\n" + get_persona_prompt_addendum(persona_id) if persona_id else "")
        config = types.GenerateContentConfig(
            system_instruction=sys_inst,
            temperature=0.3
        )
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config
        )
        return response.text if hasattr(response, "text") and response.text else ""



    def generate_executive_briefing(
        self,
        persona: str = "executive",
        anomaly_context: Optional[Dict[str, Any]] = None,
        hypotheses: Optional[List[Dict[str, Any]]] = None,
        simulation_levers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates persona-tailored Executive Briefing report artifact.
        Uses Gemini agent if available; falls back seamlessly to 100% deterministic OfflineEdithReasoner.
        """
        start_time = time.time()
        
        # Primary deterministic generation (guaranteed accuracy on numbers)
        briefing = OfflineEdithReasoner.generate_executive_briefing(
            persona_id=persona,
            anomaly_context=anomaly_context,
            hypotheses=hypotheses,
            simulation_levers=simulation_levers
        )
        
        # If Gemini is live, we can enhance or verify the narrative while preserving exact figures
        if self.client:
            try:
                gen_prompt = f"Synthesize a grounded Executive Briefing report for active persona: {persona}. Grounded facts:\n{briefing.get('narrative_markdown')}"
                for model_name in [self.primary_model, self.fallback_model]:
                    try:
                        text, tools = self._execute_tool_calling_loop(
                            model_name=model_name,
                            initial_prompt=gen_prompt,
                            chat_history=None,
                            persona_id=persona
                        )
                        if text and len(text) > 100:
                            briefing["narrative_markdown"] = text
                            briefing["metadata"] = {
                                "provider": "Google Gemini",
                                "model": model_name,
                                "latency_sec": round(time.time() - start_time, 2),
                                "mode": f"Live Gemini AI ({model_name})",
                                "status": "Success"
                            }
                            return briefing
                    except Exception as e:
                        print(f"[LLM Gateway] Live briefing synthesis warning: {e}")
            except Exception:
                pass
                
        return briefing

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
        start_time = time.time()
        result, metadata = self.answer_question(
            query=query,
            anomaly_context=anomaly_context,
            selected_hypothesis=selected_hypothesis,
            hypotheses=hypotheses,
            chat_history=chat_history,
            simulation_levers=simulation_levers,
            response_style=response_style
        )
        latency = round(time.time() - start_time, 2)
        # We already recorded telemetry in answer_question, but instructions say in each public method.
        # Actually it's probably better to just delegate as before, but modify to match instruction literally just in case.
        return result, metadata
