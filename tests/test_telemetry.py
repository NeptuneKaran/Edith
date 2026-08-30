import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from core.telemetry import record_event, get_telemetry, get_rollup, clear_telemetry

class TestTelemetry(unittest.TestCase):
    def setUp(self):
        clear_telemetry()
    
    def test_record_and_retrieve(self):
        record_event(endpoint="/api/overview", provider="Deterministic Engine", latency_ms=12.5)
        events = get_telemetry()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["endpoint"], "/api/overview")
        self.assertEqual(events[0]["estimated_cost_usd"], 0.0)
    
    def test_live_vs_offline_cost(self):
        record_event(endpoint="/api/chat", provider="Google Gemini", latency_ms=1420.0, model_calls=2, prompt_tokens=500, completion_tokens=200)
        record_event(endpoint="/api/chat", provider="Deterministic Offline", latency_ms=3.5)
        events = get_telemetry()
        live_event = [e for e in events if e["provider"] == "Google Gemini"][0]
        offline_event = [e for e in events if e["provider"] == "Deterministic Offline"][0]
        self.assertGreater(live_event["estimated_cost_usd"], 0.0)
        self.assertEqual(offline_event["estimated_cost_usd"], 0.0)
    
    def test_rollup_stats(self):
        record_event(endpoint="/api/overview", provider="Deterministic Engine", latency_ms=10.0)
        record_event(endpoint="/api/chat", provider="Deterministic Offline", latency_ms=5.0)
        record_event(endpoint="/api/chat", provider="Google Gemini", latency_ms=1500.0, model_calls=1, prompt_tokens=100, completion_tokens=50)
        rollup = get_rollup()
        self.assertEqual(rollup["total_events"], 3)
        self.assertEqual(rollup["live_call_count"], 1)
        self.assertEqual(rollup["offline_call_count"], 1)
        self.assertEqual(rollup["engine_call_count"], 1)
        self.assertGreater(rollup["avg_latency_ms"], 0)

if __name__ == "__main__":
    unittest.main()
