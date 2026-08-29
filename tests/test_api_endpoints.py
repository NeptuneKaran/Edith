"""
tests/test_api_endpoints.py
Comprehensive automated test suite for EDITH FastAPI REST API Endpoints.

Tests cover:
1. SPA dashboard serving (GET /)
2. File upload & profiling (POST /api/data/upload)
3. Semantic model configuration & ingestion (POST /api/data/configure)
4. Overview analytics (GET /api/overview)
5. Diagnostic decomposition & snapshot distribution (GET /api/diagnostic)
6. Investigation workspace observational integrity (GET /api/workspace)
7. Counterfactual simulation availability boundaries (GET / POST /api/simulation)
8. Reset to demo benchmark (POST /api/data/reset-demo)
9. Grounded conversational AI assistant (POST /api/chat)
10. Field-type validation rejection (non-numeric measures/drivers)
11. XSS / HTML injection safety on user-provided values
"""
import os
import sys
import unittest
import io
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from data.repository import DataRepository


class TestFastAPIEndpoints(unittest.TestCase):
    """Test suite for FastAPI REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Reset to clean demo state before each test
        DataRepository.get_instance().reset_to_demo_dataset()

    def test_01_serve_spa_index(self):
        """Verifies GET / serves the HTML SPA dashboard."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("EDITH", response.text)
        self.assertIn("Alpine", response.text)

    def test_02_upload_and_profile_dataset(self):
        """Verifies POST /api/data/upload accurately parses and profiles CSV files."""
        csv_content = (
            "snapshot_date,department,location,headcount,attrition_rate,avg_salary\n"
            "2025-01-05,Engineering,Austin,45,2.1,120000\n"
            "2025-01-12,Engineering,Austin,46,2.2,121000\n"
            "2025-01-19,Engineering,Austin,44,2.5,120500\n"
        )
        files = {"file": ("hr_sample.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        response = self.client.post("/api/data/upload", files=files)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_rows"], 3)
        self.assertIn("headcount", data["valid_numeric_columns"])
        self.assertIn("attrition_rate", data["valid_numeric_columns"])
        self.assertIn("snapshot_date", data["valid_date_columns"])
        self.assertEqual(len(data["profiles"]), 6)

    def test_03_configure_and_ingest_temporal_dataset(self):
        """Verifies POST /api/data/configure applies semantic model and updates DataRepository."""
        # 1. Upload
        csv_content = (
            "snapshot_date,department,location,headcount,attrition_rate,avg_salary\n"
            "2025-01-05,Engineering,Austin,45,2.1,120000\n"
            "2025-01-12,Engineering,Austin,46,2.2,121000\n"
            "2025-01-19,Engineering,Austin,44,2.5,120500\n"
            "2025-01-26,Engineering,Austin,42,3.1,119000\n"
        )
        files = {"file": ("hr_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        self.client.post("/api/data/upload", files=files)

        # 2. Configure
        payload = {
            "dataset_name": "HR Test Ingestion",
            "analysis_grain": "Time Series (Weekly / Monthly / Daily)",
            "primary_measure": "attrition_rate",
            "primary_measure_label": "Attrition Rate",
            "primary_measure_unit": "%",
            "aggregation_type": "mean",
            "date_column": "snapshot_date",
            "dimension_columns": ["department", "location"],
            "driver_columns": ["avg_salary", "headcount"],
            "drop_invalid_rows": True
        }
        res_cfg = self.client.post("/api/data/configure", json=payload)
        self.assertEqual(res_cfg.status_code, 200)
        data = res_cfg.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["source_info"]["name"], "HR Test Ingestion")
        self.assertFalse(data["source_info"]["is_demo"])

        # 3. Verify GET /api/data/source
        res_src = self.client.get("/api/data/source")
        self.assertEqual(res_src.status_code, 200)
        self.assertEqual(res_src.json()["name"], "HR Test Ingestion")

        # 4. Verify GET /api/overview
        res_ov = self.client.get("/api/overview")
        self.assertEqual(res_ov.status_code, 200)
        ov_data = res_ov.json()
        self.assertEqual(ov_data["dataset_name"], "HR Test Ingestion")
        self.assertFalse(ov_data["is_demo"])
        self.assertIn("kpi_metrics", ov_data)

    def test_04_snapshot_dataset_and_distribution_stats(self):
        """Verifies non-temporal snapshot datasets disable fake time-series and return distribution stats."""
        # 1. Upload snapshot CSV
        csv_content = (
            "ticket_id,team,channel,resolution_hours,csat_score\n"
            "TICK-001,Tier 1,Chat,4.5,4.5\n"
            "TICK-002,Tier 2,Email,24.0,2.0\n"
            "TICK-003,Tier 1,Phone,2.0,5.0\n"
            "TICK-004,Tier 2,Email,48.0,1.5\n"
            "TICK-005,Tier 1,Chat,6.0,4.0\n"
        )
        files = {"file": ("support_snapshot.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        self.client.post("/api/data/upload", files=files)

        # 2. Configure as snapshot
        payload = {
            "dataset_name": "Customer Support Snapshot",
            "analysis_grain": "Cross-Sectional Snapshot",
            "primary_measure": "resolution_hours",
            "primary_measure_label": "Resolution Time",
            "primary_measure_unit": "Hours",
            "aggregation_type": "mean",
            "date_column": "None (Snapshot)",
            "dimension_columns": ["team", "channel"],
            "driver_columns": ["csat_score"],
            "drop_invalid_rows": True
        }
        self.client.post("/api/data/configure", json=payload)

        # 3. Check Diagnostic Endpoint for distribution statistics
        res_diag = self.client.get("/api/diagnostic")
        self.assertEqual(res_diag.status_code, 200)
        diag_data = res_diag.json()
        self.assertFalse(diag_data["is_temporal"])
        self.assertIn("distribution_stats", diag_data)
        self.assertGreater(diag_data["distribution_stats"]["count"], 0)
        self.assertIn("p50", diag_data["distribution_stats"])
        self.assertIn("iqr", diag_data["distribution_stats"])

    def test_05_field_type_validation_rejection(self):
        """Verifies that selecting a non-numeric text column as primary measure returns 400 error."""
        csv_content = (
            "record_id,category_name,numeric_val\n"
            "1,Engineering,100\n"
            "2,Sales,200\n"
        )
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        self.client.post("/api/data/upload", files=files)

        # Attempt to configure text column 'category_name' as primary measure
        payload = {
            "dataset_name": "Invalid Test",
            "primary_measure": "category_name",
            "aggregation_type": "sum"
        }
        res_err = self.client.post("/api/data/configure", json=payload)
        self.assertEqual(res_err.status_code, 400)
        self.assertIn("contains non-numeric text", res_err.json()["detail"])

    def test_06_simulation_availability_boundaries(self):
        """Verifies simulation is available for demo dataset, but explicitly blocked for custom data."""
        # 1. Demo dataset simulation should be available
        res_demo_sim = self.client.get("/api/simulation")
        self.assertEqual(res_demo_sim.status_code, 200)
        self.assertTrue(res_demo_sim.json()["available"])
        self.assertIn("trajectory", res_demo_sim.json())

        # Update demo levers
        res_update = self.client.post("/api/simulation", json={"price_rollback_pct": 8.0, "promo_fund_k": 20.0, "churn_mitigation": True})
        self.assertEqual(res_update.status_code, 200)
        self.assertTrue(res_update.json()["available"])

        # 2. Upload custom dataset
        csv_content = "date,plant,defects\n2025-01-01,Alpha,10\n2025-01-08,Alpha,12\n"
        files = {"file": ("plant.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        self.client.post("/api/data/upload", files=files)
        self.client.post("/api/data/configure", json={"dataset_name": "Plant", "primary_measure": "defects", "date_column": "date"})

        # 3. Custom dataset simulation MUST be unavailable
        res_cust_sim = self.client.get("/api/simulation")
        self.assertEqual(res_cust_sim.status_code, 200)
        self.assertFalse(res_cust_sim.json()["available"])
        self.assertIn("restricted to calibrated econometric models", res_cust_sim.json()["reason"])

        # POST /api/simulation should reject custom dataset
        res_cust_post = self.client.post("/api/simulation", json={"price_rollback_pct": 5.0, "promo_fund_k": 10.0, "churn_mitigation": False})
        self.assertEqual(res_cust_post.status_code, 400)

    def test_07_reset_demo_dataset(self):
        """Verifies POST /api/data/reset-demo restores benchmark data."""
        res = self.client.post("/api/data/reset-demo")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["source_info"]["is_demo"])
        self.assertIn("Demo", data["source_info"]["name"])


    def test_08_conversational_chat_endpoint(self):
        """Verifies POST /api/chat generates grounded responses."""
        res = self.client.post("/api/chat", json={"query": "Explain the volume vs price loss"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answer", data)
        self.assertGreater(len(data["answer"]), 20)
        self.assertTrue(data["is_demo"])

    def test_09_xss_and_html_injection_safety(self):
        """Verifies uploaded user values with HTML/scripts are returned safely as structured data without execution."""
        csv_content = (
            "date,category_name,metric_val\n"
            "2025-01-01,<script>alert('xss')</script>,150\n"
            "2025-01-08,<b>BoldTag</b>,250\n"
        )
        files = {"file": ("xss_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res_up = self.client.post("/api/data/upload", files=files)
        self.assertEqual(res_up.status_code, 200)
        
        # Verify JSON returns pure strings, not executable HTML
        preview = res_up.json()["preview"]
        self.assertEqual(preview[0]["category_name"], "<script>alert('xss')</script>")
        self.assertEqual(preview[1]["category_name"], "<b>BoldTag</b>")


if __name__ == "__main__":
    unittest.main()
