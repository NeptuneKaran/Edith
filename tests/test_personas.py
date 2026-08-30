"""
tests/test_personas.py
Comprehensive automated test suite for EDITH Multi-Page Architecture & Persona Governance:
1. Four enterprise personas listing (/api/personas)
2. Server-enforced persona gate redirects (protected HTML routes with no session redirect to /)
3. Session-based persona selection (/session/select-persona) and switch role (/session/switch-role)
4. Backward compatibility: Unscoped API requests (no session) return 100% full payloads
5. Role-based scoping for regional_lead (Region B focus, restricted company-wide & competitor telemetry, locked price rollback)
6. Unrestricted pass-through for executive, general_user, analyst
7. Standing Executive Briefing generation (/api/briefing) per persona with zero API key
8. Strict zero-jargon absence verification for general_user (no Z-scores, elasticity, DiD, DAG, sigma, p-value)
9. Live audit trail logging for gate selections, role switches, data access, and blocked attempts
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
from starlette.testclient import TestClient
from main import app
from data.repository import DataRepository
from core.access_control import clear_access_log, get_access_log


class TestPersonasAndMultiPageGate(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        DataRepository.get_instance().reset_to_demo()
        clear_access_log()

    def test_01_personas_listing_endpoint(self):
        """Verify GET /api/personas returns all four governed enterprise personas."""
        resp = self.client.get("/api/personas")
        self.assertEqual(resp.status_code, 200)
        personas = resp.json()
        self.assertEqual(len(personas), 4)
        ids = [p["id"] for p in personas]
        self.assertIn("executive", ids)
        self.assertIn("general_user", ids)
        self.assertIn("regional_lead", ids)
        self.assertIn("analyst", ids)

    def test_02_gate_page_and_protected_routes_redirect(self):
        """
        Verify that:
        1. GET / with no session renders the Persona Gate (gate.html).
        2. GET on protected routes (/overview, /diagnostic, etc.) without a session
           redirects to / with HTTP 303 and logs a BLOCKED_UNAUTHORIZED audit entry.
        """
        # 1. Root with no session -> renders gate
        root_resp = self.client.get("/", follow_redirects=False)
        self.assertEqual(root_resp.status_code, 200)
        self.assertIn("Who are you viewing as?", root_resp.text)
        self.assertIn("Executive / CRO", root_resp.text)
        self.assertIn("Non-Technical Business User", root_resp.text)

        # 2. Protected routes without session -> redirect to /
        protected_routes = ["/overview", "/diagnostic", "/workspace", "/simulation", "/console", "/sources"]
        for route in protected_routes:
            resp = self.client.get(route, follow_redirects=False)
            self.assertEqual(resp.status_code, 303, f"Route {route} did not redirect with 303 when unauthenticated")
            self.assertEqual(resp.headers.get("location"), "/")

        # 3. Check that blocked attempts were recorded in audit log
        logs = get_access_log(50)
        blocked_entries = [e for e in logs if e.get("action") == "BLOCKED_UNAUTHORIZED"]
        self.assertTrue(len(blocked_entries) >= len(protected_routes))

    def test_03_session_persona_selection_and_switch_role(self):
        """
        Verify that:
        1. POST /session/select-persona sets the session cookie and redirects to /overview.
        2. Subsequent GET /overview succeeds and serves the HTML page.
        3. GET /session/switch-role clears the session and redirects to /.
        4. Invalid persona selection returns 400.
        """
        # 1. Invalid persona -> 400
        bad_resp = self.client.post("/session/select-persona", data={"persona_id": "invalid_role"}, follow_redirects=False)
        self.assertEqual(bad_resp.status_code, 400)

        # 2. Valid selection -> sets session cookie and redirects to /overview
        select_resp = self.client.post("/session/select-persona", data={"persona_id": "executive"}, follow_redirects=False)
        self.assertEqual(select_resp.status_code, 303)
        self.assertEqual(select_resp.headers.get("location"), "/overview")

        # 3. Visit /overview with active session
        overview_resp = self.client.get("/overview", follow_redirects=False)
        self.assertEqual(overview_resp.status_code, 200)
        self.assertIn("Executive Overview", overview_resp.text)
        self.assertIn("Chief Revenue Officer", overview_resp.text)

        # 4. Switch role -> clears session and redirects to /
        switch_resp = self.client.get("/session/switch-role", follow_redirects=False)
        self.assertEqual(switch_resp.status_code, 303)
        self.assertEqual(switch_resp.headers.get("location"), "/")

        # 5. Subsequent visit to /overview without session -> redirected again
        post_switch_resp = self.client.get("/overview", follow_redirects=False)
        self.assertEqual(post_switch_resp.status_code, 303)

    def test_04_backward_compatibility_unscoped_api(self):
        """Calling /api/overview, /api/diagnostic, /api/workspace, /api/simulation without session returns full unscoped data."""
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("kpi_metrics", data)
        self.assertNotIn("restricted", data.get("kpi_metrics", {}))
        self.assertFalse(data.get("restricted", False))

        diag_resp = self.client.get("/api/diagnostic")
        self.assertEqual(diag_resp.status_code, 200)
        diag_data = diag_resp.json()
        self.assertFalse(diag_data.get("restricted", False))

    def test_05_session_scoped_regional_lead_api(self):
        """Setting session to regional_lead scopes API endpoints to Region B and restricts company-wide totals."""
        # Authenticate session as regional_lead
        self.client.post("/session/select-persona", data={"persona_id": "regional_lead"})

        # Overview
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("persona"), "regional_lead")
        self.assertTrue(data.get("restricted", False))
        self.assertIn("company_wide_total", data)
        self.assertTrue(data["company_wide_total"].get("restricted", False))

        # Diagnostic
        diag_resp = self.client.get("/api/diagnostic")
        self.assertEqual(diag_resp.status_code, 200)
        diag_data = diag_resp.json()
        self.assertTrue(diag_data.get("restricted", False))
        reg_breakdown = diag_data.get("breakdowns", {}).get("region", [])
        for row in reg_breakdown:
            if row.get("region") != "Region B":
                self.assertTrue(row.get("restricted", False))

        # Workspace
        ws_resp = self.client.get("/api/workspace")
        self.assertEqual(ws_resp.status_code, 200)
        ws_data = ws_resp.json()
        self.assertTrue(ws_data.get("competitor_intelligence", {}).get("restricted", False))
        self.assertTrue(ws_data.get("cross_region_control_groups", {}).get("restricted", False))

        # Simulation
        sim_resp = self.client.get("/api/simulation")
        self.assertEqual(sim_resp.status_code, 200)
        sim_data = sim_resp.json()
        self.assertTrue(sim_data.get("levers_permissions", {}).get("price_rollback_locked", False))

    def test_06_unrestricted_personas_overview(self):
        """Calling /api/overview for executive, general_user, or analyst passes with no restricted placeholders."""
        for p in ["executive", "general_user", "analyst"]:
            self.client.post("/session/select-persona", data={"persona_id": p})
            resp = self.client.get("/api/overview")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("persona"), p)
            self.assertFalse(data.get("restricted", False))
            self.assertNotIn("company_wide_total", data)

    def test_07_executive_briefing_per_persona(self):
        """Verify GET /api/briefing returns persona-tailored standing reports with zero API key."""
        for p in ["executive", "general_user", "regional_lead", "analyst"]:
            self.client.post("/session/select-persona", data={"persona_id": p})
            resp = self.client.get("/api/briefing")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("headline", data)
            self.assertIn("narrative_markdown", data)
            self.assertIn("recommended_actions", data)
            self.assertEqual(data.get("persona"), p)

    def test_08_general_user_plain_language_jargon_absence(self):
        """
        Verify that general_user briefing narrative and chat responses contain ZERO technical/statistical jargon:
        - No Z-score, elasticity coefficient, Difference-in-Differences / DiD, Cause Evidence Score,
          confidence %, DAG, upstream/downstream, sigma/σ, p-value.
        """
        self.client.post("/session/select-persona", data={"persona_id": "general_user"})
        
        # 1. Check standing briefing
        briefing_resp = self.client.get("/api/briefing")
        self.assertEqual(briefing_resp.status_code, 200)
        narrative = briefing_resp.json().get("narrative_markdown", "")
        
        forbidden_case_insensitive = [
            r"z-score",
            r"z score",
            r"elasticity",
            r"difference-in-differences",
            r"evidence index",
            r"evidence score",
            r"cause score",
            r"cause evidence",
            r"confidence %",
            r"confidence percentage",
            r"directed acyclic",
            r"upstream/downstream",
            r"p-value",
            r"p value",
            r"sigma"
        ]
        forbidden_case_sensitive = [
            r"DiD",
            r"D-i-D",
            r"DAG",
            r"σ",
            r"ε_p",
            r"\varepsilon"
        ]
        
        for pattern in forbidden_case_insensitive:
            matches = re.findall(pattern, narrative, re.IGNORECASE)
            self.assertEqual(len(matches), 0, f"Found forbidden jargon '{pattern}' in general_user briefing narrative: {matches}")
        
        for pattern in forbidden_case_sensitive:
            matches = re.findall(pattern, narrative)
            self.assertEqual(len(matches), 0, f"Found forbidden acronym '{pattern}' in general_user briefing narrative: {matches}")

        # 2. Check conversational Q&A for general_user
        test_queries = [
            "Why did sales drop?",
            "What happened in Region B?",
            "What is the recovery plan?",
            "Explain the pricing impact on customer renewals"
        ]
        for q in test_queries:
            chat_resp = self.client.post("/api/chat", json={"query": q})
            self.assertEqual(chat_resp.status_code, 200)
            ans = chat_resp.json().get("answer", "")
            for pattern in forbidden_case_insensitive:
                matches = re.findall(pattern, ans, re.IGNORECASE)
                self.assertEqual(len(matches), 0, f"Found forbidden jargon '{pattern}' in general_user chat for query '{q}': {matches}")
            for pattern in forbidden_case_sensitive:
                matches = re.findall(pattern, ans)
                self.assertEqual(len(matches), 0, f"Found forbidden acronym '{pattern}' in general_user chat for query '{q}': {matches}")

    def test_09_audit_trail_logging(self):
        """Verify that gate selections, role switches, scoped calls, and blocked attempts are logged to GET /api/access-log."""
        # 1. Gate selection
        self.client.post("/session/select-persona", data={"persona_id": "regional_lead"})
        
        # 2. Scoped requests
        self.client.get("/api/overview")
        self.client.get("/api/workspace")
        self.client.get("/api/briefing")
        self.client.get("/api/simulation")

        # 3. Switch role
        self.client.get("/session/switch-role")

        # 4. Blocked attempt
        self.client.get("/diagnostic", follow_redirects=False)
        
        resp = self.client.get("/api/access-log")
        self.assertEqual(resp.status_code, 200)
        log_data = resp.json()
        self.assertIn("events", log_data)
        events = log_data["events"]
        self.assertTrue(len(events) >= 6)
        
        actions = [e["action"] for e in events]
        self.assertIn("GATE_SELECTION", actions)
        self.assertIn("SWITCH_ROLE", actions)
        self.assertIn("BLOCKED_UNAUTHORIZED", actions)


if __name__ == "__main__":
    unittest.main()
