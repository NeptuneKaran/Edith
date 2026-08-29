"""
tests/test_personas.py
Comprehensive automated test suite for EDITH Role-Based Personas, Security Access Control,
Persona-Scoped Analytics, Standing Executive Briefings, and the Live Access Audit Trail.
"""
import unittest
from fastapi.testclient import TestClient
from main import app
from config.personas import PERSONAS, get_personas, get_persona
from core.access_control import get_access_log, clear_access_log


class TestPersonasAndAccessControl(unittest.TestCase):
    """Test suite covering RBAC, persona scoping, executive briefings, and audit logs."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        clear_access_log()

    def test_01_personas_listing_endpoint(self):
        """Verify GET /api/personas returns all three governed enterprise personas."""
        resp = self.client.get("/api/personas")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        persona_ids = [p["id"] for p in data]
        self.assertIn("executive", persona_ids)
        self.assertIn("regional_lead", persona_ids)
        self.assertIn("analyst", persona_ids)

    def test_02_backward_compatibility_unscoped_overview(self):
        """Calling /api/overview without persona param returns full unscoped data with no restrictions."""
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("kpi_metrics", data)
        self.assertIn("time_series", data)
        self.assertNotIn("company_wide_summary", data)

    def test_03_regional_lead_scoped_overview(self):
        """Calling /api/overview?persona=regional_lead scopes metrics to Region B and restricts company-wide totals."""
        resp = self.client.get("/api/overview?persona=regional_lead")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Region B scoped metrics
        self.assertIn("kpi_metrics", data)
        self.assertIn("time_series", data)
        self.assertIn("company_wide_summary", data)
        self.assertTrue(data["company_wide_summary"].get("restricted"))
        self.assertIn("Requires Executive or Analyst access", data["company_wide_summary"].get("reason", ""))
        self.assertIn("persona_context", data)
        self.assertEqual(data["persona_context"]["persona_id"], "regional_lead")
        self.assertTrue(data["persona_context"]["is_restricted"])

    def test_04_executive_and_analyst_unrestricted_overview(self):
        """Calling /api/overview for executive or analyst passes with no restricted placeholders."""
        for p in ["executive", "analyst"]:
            resp = self.client.get(f"/api/overview?persona={p}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("kpi_metrics", data)
            self.assertFalse(data.get("company_wide_summary", {}).get("restricted", False))

    def test_05_regional_lead_scoped_diagnostic(self):
        """Calling /api/diagnostic?persona=regional_lead masks non-Region B rows with restricted notices."""
        resp = self.client.get("/api/diagnostic?persona=regional_lead")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("breakdowns", data)
        reg_breakdowns = data["breakdowns"].get("region", [])
        self.assertTrue(len(reg_breakdowns) > 0)
        
        for row in reg_breakdowns:
            if row.get("region") == "Region B":
                self.assertFalse(row.get("restricted", False))
                self.assertIsNotNone(row.get("curr_value"))
            else:
                self.assertTrue(row.get("restricted", False))
                self.assertIsNone(row.get("curr_value"))
                self.assertIn("Requires Executive or Analyst access", row.get("reason", ""))

    def test_06_regional_lead_scoped_workspace(self):
        """Calling /api/workspace?persona=regional_lead masks competitor intelligence and cross-region control groups."""
        resp = self.client.get("/api/workspace?persona=regional_lead")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        findings = data.get("findings", [])
        self.assertTrue(len(findings) > 0)
        
        # Check that competitor telemetry / cross region control groups are restricted
        for f in findings:
            if f.get("id") == "H2_COMPETITOR_CAMPAIGN":
                self.assertTrue(f.get("competitor_telemetry", {}).get("restricted"))
            ctrl = f.get("control_group_analysis")
            if ctrl:
                self.assertTrue(isinstance(ctrl, dict) and ctrl.get("restricted"))

    def test_07_regional_lead_simulation_price_rollback_locked(self):
        """Calling /api/simulation for regional_lead locks the Price Rollback lever."""
        resp = self.client.get("/api/simulation?persona=regional_lead")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("levers_access", data)
        self.assertTrue(data["levers_access"]["price_rollback"]["restricted"])
        self.assertFalse(data["levers_access"]["price_rollback"]["allowed"])
        self.assertTrue(data["levers_access"]["promo_fund"]["allowed"])
        self.assertTrue(data["levers_access"]["churn_mitigation"]["allowed"])

    def test_08_executive_briefing_per_persona(self):
        """Verify GET /api/briefing returns persona-tailored standing reports with zero API key."""
        for p in ["executive", "regional_lead", "analyst"]:
            resp = self.client.get(f"/api/briefing?persona={p}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("persona_id"), p)
            self.assertIn("headline", data)
            self.assertIn("narrative_markdown", data)
            self.assertIn("primary_root_cause", data)
            self.assertIn("recommended_actions", data)
            self.assertTrue(len(data["recommended_actions"]) > 0)

    def test_09_audit_trail_logging(self):
        """Verify that every scoped call is properly logged to GET /api/access-log."""
        self.client.get("/api/overview?persona=regional_lead")
        self.client.get("/api/workspace?persona=executive")
        self.client.get("/api/simulation?persona=regional_lead")
        
        resp = self.client.get("/api/access-log")
        self.assertEqual(resp.status_code, 200)
        log_data = resp.json()
        self.assertIn("events", log_data)
        events = log_data["events"]
        self.assertTrue(len(events) >= 3)
        
        # Verify event properties
        first_event = events[0]
        self.assertIn("timestamp", first_event)
        self.assertIn("persona", first_event)
        self.assertIn("endpoint", first_event)
        self.assertIn("status", first_event)
        self.assertIn("granted_sections", first_event)
        self.assertIn("restricted_sections", first_event)


if __name__ == "__main__":
    unittest.main()
