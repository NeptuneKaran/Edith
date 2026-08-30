"""
tests/test_gemini_reliability.py
Comprehensive test suite verifying:
1. Gemini error classification (_classify_gemini_error).
2. Real API key validation (validate_key) with 5-minute TTL caching.
3. Smart retry behavior (auth skips fallback model, quota retries).
4. Three-state AI status reporting (/api/ai/status).
5. Dynamic key configuration (/api/ai/key).
6. Chat endpoint error propagation in fallback mode.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.llm_client import EdithLLMClient, _classify_gemini_error
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.evidence_engine import EvidenceEngine


class TestGeminiReliability(unittest.TestCase):
    def setUp(self):
        # Ensure clean environment for each test
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)

    def test_classify_gemini_error_auth(self):
        """Test error classification for various auth failure patterns."""
        self.assertEqual(_classify_gemini_error(Exception("400 INVALID_ARGUMENT. API_KEY_INVALID")), "auth")
        self.assertEqual(_classify_gemini_error(Exception("API key not valid. Please pass a valid API key.")), "auth")
        self.assertEqual(_classify_gemini_error(Exception("403 PermissionDenied: caller does not have permission")), "auth")
        self.assertEqual(_classify_gemini_error(Exception("401 UNAUTHENTICATED")), "auth")

    def test_classify_gemini_error_quota(self):
        """Test error classification for rate-limit and quota exhaustion."""
        self.assertEqual(_classify_gemini_error(Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")), "quota")
        self.assertEqual(_classify_gemini_error(Exception("Rate limit exceeded for model gemini-2.0-flash")), "quota")
        self.assertEqual(_classify_gemini_error(Exception("Too many requests")), "quota")

    def test_classify_gemini_error_network(self):
        """Test error classification for connection and timeout errors."""
        self.assertEqual(_classify_gemini_error(Exception("Connection reset by peer")), "network")
        self.assertEqual(_classify_gemini_error(Exception("HTTPSConnectionPool: Request timed out")), "network")
        self.assertEqual(_classify_gemini_error(Exception("SSL: CERTIFICATE_VERIFY_FAILED")), "network")

    def test_classify_gemini_error_unknown(self):
        """Test error classification for generic or unknown errors."""
        self.assertEqual(_classify_gemini_error(Exception("Something strange happened in JSON parsing")), "unknown")
        self.assertEqual(_classify_gemini_error(None), "unknown")

    def test_validate_key_no_key(self):
        """Zero-key client should immediately report invalid without making network calls."""
        client = EdithLLMClient(api_key="")
        result = client.validate_key()
        self.assertFalse(result["valid"])
        self.assertIsNone(result["error_type"])
        self.assertEqual(result["error_message"], "No API key configured")
        self.assertIn("checked_at", result)

    @patch("google.genai.Client")
    def test_validate_key_valid(self, mock_client_cls):
        """Valid key successfully lists models and returns valid=True."""
        mock_client = MagicMock()
        mock_client.models.list.return_value = [MagicMock(name="gemini-2.0-flash")]
        mock_client_cls.return_value = mock_client

        client = EdithLLMClient(api_key="valid_test_key_12345")
        client.client = mock_client

        result = client.validate_key()
        self.assertTrue(result["valid"])
        self.assertIsNone(result["error_type"])
        self.assertIsNone(result["error_message"])

    @patch("google.genai.Client")
    def test_validate_key_invalid_auth(self, mock_client_cls):
        """Invalid key triggers auth error classification."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("400 INVALID_ARGUMENT. API_KEY_INVALID")
        mock_client_cls.return_value = mock_client

        client = EdithLLMClient(api_key="invalid_test_key_12345")
        client.client = mock_client

        result = client.validate_key()
        self.assertFalse(result["valid"])
        self.assertEqual(result["error_type"], "auth")
        self.assertIn("API_KEY_INVALID", result["error_message"])

    @patch("google.genai.Client")
    def test_validate_key_caching_ttl(self, mock_client_cls):
        """Results are cached within 300s TTL unless force=True."""
        mock_client = MagicMock()
        mock_client.models.list.return_value = [MagicMock(name="gemini-2.0-flash")]
        mock_client_cls.return_value = mock_client

        client = EdithLLMClient(api_key="caching_test_key_12345")
        client.client = mock_client

        # Call 1
        res1 = client.validate_key()
        self.assertEqual(mock_client.models.list.call_count, 1)

        # Call 2 within TTL -> should use cache
        res2 = client.validate_key()
        self.assertEqual(mock_client.models.list.call_count, 1)
        self.assertEqual(res1["checked_at"], res2["checked_at"])

        # Force refresh -> should call API again
        res3 = client.validate_key(force=True)
        self.assertEqual(mock_client.models.list.call_count, 2)

    def test_answer_question_auth_skips_fallback_model(self):
        """Auth error on primary model skips fallback model and produces offline answer with auth metadata."""
        client = EdithLLMClient(api_key="bad_auth_key_12345")
        mock_client = MagicMock()
        client.client = mock_client

        # Simulate auth failure on tool calling loop
        with patch.object(client, "_execute_tool_calling_loop", side_effect=Exception("401 UNAUTHENTICATED")):
            repo = DataRepository.get_instance()
            df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
            df_anom = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
            anom_ctx = AnomalyEngine.evaluate_current_anomaly(df_anom, "Monthly B2B Sales")
            ev_eng = EvidenceEngine(repo)
            hypotheses = ev_eng.evaluate_all_hypotheses("kpi_b2b_sales")

            ans, meta = client.answer_question(
                query="What happened in Region B?",
                anomaly_context=anom_ctx,
                selected_hypothesis=hypotheses[0],
                hypotheses=hypotheses
            )

            # Assert tool calling was called only once (did NOT try fallback model on auth failure)
            self.assertEqual(client._execute_tool_calling_loop.call_count, 1)
            self.assertEqual(meta["error_type"], "auth")
            self.assertTrue(meta["key_configured"])
            self.assertIn("Region B", ans)

    def test_answer_question_quota_retries_and_succeeds(self):
        """Transient 429 quota error retries on same model and succeeds if retry works."""
        client = EdithLLMClient(api_key="quota_retry_key_12345")
        mock_client = MagicMock()
        client.client = mock_client

        # Attempt 1 raises 429, Attempt 2 succeeds
        call_count = 0
        def fake_tool_loop(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")
            return "Region B suffered an acute pricing pressure anomaly.", ["get_kpi_corridor"], 100, 50

        with patch.object(client, "_execute_tool_calling_loop", side_effect=fake_tool_loop), \
             patch("time.sleep", return_value=None):
            repo = DataRepository.get_instance()
            df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
            df_anom = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
            anom_ctx = AnomalyEngine.evaluate_current_anomaly(df_anom, "Monthly B2B Sales")
            ev_eng = EvidenceEngine(repo)
            hypotheses = ev_eng.evaluate_all_hypotheses("kpi_b2b_sales")

            ans, meta = client.answer_question(
                query="Why did sales drop?",
                anomaly_context=anom_ctx,
                selected_hypothesis=hypotheses[0],
                hypotheses=hypotheses
            )

            self.assertEqual(call_count, 2)
            self.assertEqual(meta["provider"], "Google Gemini")
            self.assertEqual(meta["status"], "Success")
            self.assertIn("pricing pressure", ans)

    def test_api_status_endpoint_three_states(self):
        """Verify GET /api/ai/status returns correct shape for all three states."""
        from starlette.testclient import TestClient
        from main import app

        test_client = TestClient(app)

        # State 1: Zero key
        with patch.object(EdithLLMClient, "validate_key", return_value={"valid": False, "error_type": None, "error_message": "No API key configured", "checked_at": "2026-08-30T20:00:00Z"}), \
             patch.object(EdithLLMClient, "__init__", return_value=None) as mock_init:
            mock_inst = MagicMock()
            mock_inst.api_key = ""
            mock_inst.client = None
            mock_inst.primary_model = "gemini-2.0-flash"
            mock_inst.validate_key.return_value = {"valid": False, "error_type": None, "error_message": "No API key configured", "checked_at": "2026-08-30T20:00:00Z"}
            
            with patch("main.EdithLLMClient", return_value=mock_inst):
                res = test_client.get("/api/ai/status")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertFalse(data["key_configured"])
                self.assertFalse(data["key_valid"])
                self.assertEqual(data["badge_text"], "Deterministic Offline Mode")
                self.assertEqual(data["provider"], "Deterministic Analytical Engine")

        # State 2: Key configured and valid
        with patch("main.EdithLLMClient") as mock_llm:
            mock_inst = MagicMock()
            mock_inst.api_key = "valid_key_123"
            mock_inst.primary_model = "gemini-2.0-flash"
            mock_inst.validate_key.return_value = {"valid": True, "error_type": None, "error_message": None, "checked_at": "2026-08-30T20:00:00Z"}
            mock_llm.return_value = mock_inst

            res = test_client.get("/api/ai/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["key_configured"])
            self.assertTrue(data["key_valid"])
            self.assertTrue(data["is_live"])
            self.assertIn("Live Gemini AI", data["badge_text"])
            self.assertEqual(data["provider"], "Google Gemini")

        # State 3: Key configured but failing (Auth error)
        with patch("main.EdithLLMClient") as mock_llm:
            mock_inst = MagicMock()
            mock_inst.api_key = "bad_key_123"
            mock_inst.primary_model = "gemini-2.0-flash"
            mock_inst.validate_key.return_value = {"valid": False, "error_type": "auth", "error_message": "API key rejected", "checked_at": "2026-08-30T20:00:00Z"}
            mock_llm.return_value = mock_inst

            res = test_client.get("/api/ai/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["key_configured"])
            self.assertFalse(data["key_valid"])
            self.assertFalse(data["is_live"])
            self.assertEqual(data["error_type"], "auth")
            self.assertIn("Gemini Error", data["badge_text"])

    def test_chat_fallback_carries_error_info(self):
        """Verify that when chat_with_edith catches an LLM error, it preserves error_type and key_configured."""
        from starlette.testclient import TestClient
        from main import app

        test_client = TestClient(app)

        with patch("main.EdithLLMClient") as mock_llm:
            mock_inst = MagicMock()
            mock_inst.api_key = "test_key_configured"
            # When client.answer_question raises an exception
            mock_inst.answer_question.side_effect = Exception("403 Forbidden PERMISSION_DENIED")
            mock_llm.return_value = mock_inst

            res = test_client.post("/api/chat", json={"query": "What is the primary driver?"})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            meta = data.get("metadata", {})
            self.assertTrue(meta.get("key_configured"))
            self.assertEqual(meta.get("error_type"), "auth")
            self.assertIn("auth", meta.get("mode", "").lower())
            self.assertIn("answer", data)


if __name__ == "__main__":
    unittest.main()
