import unittest
from starlette.testclient import TestClient
from main import app

class TestPersonaBypass(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_overview_persona_bypass_ignored(self):
        res_no_param = self.client.get("/api/overview")
        res_with_param = self.client.get("/api/overview?persona=analyst")
        
        self.assertEqual(res_no_param.status_code, 200)
        self.assertEqual(res_with_param.status_code, 200)
        self.assertEqual(res_no_param.json(), res_with_param.json())

    def test_workspace_persona_bypass_ignored(self):
        res_no_param = self.client.get("/api/workspace")
        res_with_param = self.client.get("/api/workspace?persona=regional_lead")
        
        self.assertEqual(res_no_param.status_code, 200)
        self.assertEqual(res_with_param.status_code, 200)
        self.assertEqual(res_no_param.json(), res_with_param.json())

    def test_briefing_persona_bypass_ignored(self):
        res_no_param = self.client.get("/api/briefing")
        res_with_param = self.client.get("/api/briefing?persona=analyst")
        
        self.assertEqual(res_no_param.status_code, 200)
        self.assertEqual(res_with_param.status_code, 200)
        self.assertEqual(res_no_param.json(), res_with_param.json())

    def test_valid_session_scopes_response(self):
        # Using a valid session
        client = TestClient(app)
        
        # Unscoped overview response
        unscoped_res = client.get("/api/overview")
        self.assertEqual(unscoped_res.status_code, 200)
        unscoped_data = unscoped_res.json()
        
        # Set session cookie by posting to /session/select-persona
        login_res = client.post("/session/select-persona", data={"persona_id": "regional_lead"})
        self.assertTrue(login_res.status_code in (200, 302, 303))
        
        # Scoped overview response
        scoped_res = client.get("/api/overview")
        self.assertEqual(scoped_res.status_code, 200)
        scoped_data = scoped_res.json()
        
        # Verify that scoping happened (e.g. they should not be equal if unscoped and scoped differ)
        self.assertNotEqual(unscoped_data, scoped_data)
