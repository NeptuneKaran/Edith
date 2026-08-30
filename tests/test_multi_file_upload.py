import unittest
import io
import pandas as pd
from starlette.testclient import TestClient
from main import app, _UPLOAD_CACHE
from data.repository import DataRepository
from core.telemetry import get_telemetry, clear_telemetry

class TestMultiFileUpload(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.repo = DataRepository.get_instance()
        _UPLOAD_CACHE.clear()
        clear_telemetry()

    def test_single_file_upload_backward_compatibility(self):
        csv_data = "date,sales_usd,region\n2023-01-01,100,North\n2023-01-02,150,South"
        response = self.client.post(
            "/api/data/upload",
            files={"files": ("sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["files"]), 1)
        self.assertEqual(data["relationships"], [])
        
        self.assertIn("raw_df", _UPLOAD_CACHE)

    def test_multiple_file_upload_and_actual_join(self):
        fact_csv = "date,region,sales_usd\n2023-01-01,North,100\n2023-01-02,South,150"
        dim_csv = "region,region_name,country\nNorth,Northern Region,US\nSouth,Southern Region,US"
        unstr_csv = "date,region,note_text\n2023-01-01,North,Great sales\n2023-01-02,South,Okay sales"
        
        response = self.client.post(
            "/api/data/upload",
            files=[
                ("files", ("fact.csv", io.BytesIO(fact_csv.encode("utf-8")), "text/csv")),
                ("files", ("dim.csv", io.BytesIO(dim_csv.encode("utf-8")), "text/csv")),
                ("files", ("unstr.csv", io.BytesIO(unstr_csv.encode("utf-8")), "text/csv"))
            ]
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["files"]), 3)
        self.assertTrue(len(data["relationships"]) > 0)
        
        # Verify relationship found on 'region'
        found_region_rel = False
        for rel in data["relationships"]:
            if "region" in rel["join_keys"]:
                found_region_rel = True
                break
        self.assertTrue(found_region_rel)
        
        # Test configure
        config_payload = {
            "dataset_name": "Multi-Table Test",
            "analysis_grain": "Cross-Sectional Snapshot",
            "primary_measure": "sales_usd",
            "dimension_columns": ["region", "region_name", "country"],
            "file_roles": [
                {"filename": "fact.csv", "role": "fact", "join_keys": []},
                {"filename": "dim.csv", "role": "dimension", "join_keys": []},
                {"filename": "unstr.csv", "role": "unstructured", "join_keys": []}
            ]
        }
        
        conf_response = self.client.post("/api/data/configure", json=config_payload)
        self.assertEqual(conf_response.status_code, 200)
        
        # Check repo tables and actual merged columns
        self.assertIn("sales", self.repo.tables)
        sales_df = self.repo.tables["sales"]
        self.assertIn("region_name", sales_df.columns)
        self.assertIn("country", sales_df.columns)
        self.assertEqual(sales_df.loc[sales_df["region"] == "North", "country"].iloc[0], "US")
        self.assertEqual(sales_df.loc[sales_df["region"] == "North", "region_name"].iloc[0], "Northern Region")

    def test_mismatched_grain_merge_and_workspace_end_to_end(self):
        # 1. Daily fact table across 10 distinct dates for 2 regions
        fact_rows = ["date,region,sales_usd"]
        for day in range(1, 11):
            d_str = f"2025-01-{day:02d}"
            fact_rows.append(f"{d_str},North,{100 + day * 5}")
            fact_rows.append(f"{d_str},South,{150 + day * 3}")
        fact_csv = "\n".join(fact_rows)

        # 2. Weekly / Coarse supporting table on region + date (only 2 weekly dates)
        supp_csv = "date,region,promo_spend,manager_zone\n2025-01-01,North,500,Zone-A\n2025-01-08,North,750,Zone-A\n2025-01-01,South,300,Zone-B\n2025-01-08,South,450,Zone-B"

        upload_res = self.client.post(
            "/api/data/upload",
            files=[
                ("files", ("fact_daily.csv", io.BytesIO(fact_csv.encode("utf-8")), "text/csv")),
                ("files", ("supp_weekly.csv", io.BytesIO(supp_csv.encode("utf-8")), "text/csv"))
            ]
        )
        self.assertEqual(upload_res.status_code, 200)

        # Configure with promo_spend as driver and manager_zone as dimension
        config_payload = {
            "dataset_name": "Grain Mismatch Test",
            "analysis_grain": "Time Series (Weekly / Monthly / Daily)",
            "primary_measure": "sales_usd",
            "date_column": "date",
            "dimension_columns": ["region", "manager_zone"],
            "driver_columns": ["promo_spend"],
            "file_roles": [
                {"filename": "fact_daily.csv", "role": "fact", "join_keys": []},
                {"filename": "supp_weekly.csv", "role": "dimension", "join_keys": []}
            ]
        }

        conf_res = self.client.post("/api/data/configure", json=config_payload)
        self.assertEqual(conf_res.status_code, 200)

        sales_df = self.repo.tables["sales"]
        self.assertIn("promo_spend", sales_df.columns)
        self.assertIn("manager_zone", sales_df.columns)
        
        # Verify no NaNs produced by grain mismatch (forward/backward fill resolved it)
        self.assertFalse(sales_df["promo_spend"].isnull().any(), "promo_spend must not contain NaNs after merge")
        self.assertFalse(sales_df["manager_zone"].isnull().any(), "manager_zone must not contain NaNs after merge")

        # Test end-to-end: query /api/workspace and verify merged columns are analyzed
        # Set session for analyst persona
        ws_res = self.client.get("/api/workspace")
        self.assertEqual(ws_res.status_code, 200)
        ws_data = ws_res.json()
        
        # Check that findings or driver correlations reference the merged columns
        findings = ws_data.get("findings", [])
        driver_corrs = self.repo.get_driver_correlations().get("correlations", {})
        
        self.assertIn("promo_spend", driver_corrs, "Driver correlations must evaluate promo_spend from supporting table")
        
        # Verify telemetry recorded deterministic engine event
        telemetry = get_telemetry()
        engine_events = [e for e in telemetry if e.get("provider") == "Deterministic Engine"]
        self.assertGreater(len(engine_events), 0, "Deterministic Engine telemetry events must be recorded")

    def test_confirmed_relationships_gating(self):
        fact_csv = "date,region,sales_usd\n2023-01-01,North,100\n2023-01-02,South,150"
        dim_csv = "region,extra_dim_col\nNorth,ExtraNorth\nSouth,ExtraSouth"

        self.client.post(
            "/api/data/upload",
            files=[
                ("files", ("fact.csv", io.BytesIO(fact_csv.encode("utf-8")), "text/csv")),
                ("files", ("dim.csv", io.BytesIO(dim_csv.encode("utf-8")), "text/csv"))
            ]
        )

        # 1. User confirms EMPTY relationships -> no join should happen
        config_payload_empty = {
            "dataset_name": "Gating Test No Join",
            "analysis_grain": "Cross-Sectional Snapshot",
            "primary_measure": "sales_usd",
            "file_roles": [
                {"filename": "fact.csv", "role": "fact", "join_keys": []},
                {"filename": "dim.csv", "role": "dimension", "join_keys": []}
            ],
            "confirmed_relationships": []
        }
        res1 = self.client.post("/api/data/configure", json=config_payload_empty)
        self.assertEqual(res1.status_code, 200)
        self.assertNotIn("extra_dim_col", self.repo.tables["sales"].columns)

        # 2. User confirms the relationship -> join happens
        config_payload_confirmed = {
            "dataset_name": "Gating Test Join",
            "analysis_grain": "Cross-Sectional Snapshot",
            "primary_measure": "sales_usd",
            "file_roles": [
                {"filename": "fact.csv", "role": "fact", "join_keys": []},
                {"filename": "dim.csv", "role": "dimension", "join_keys": []}
            ],
            "confirmed_relationships": [
                {"left_file": "fact.csv", "right_file": "dim.csv", "join_keys": ["region"]}
            ]
        }
        res2 = self.client.post("/api/data/configure", json=config_payload_confirmed)
        self.assertEqual(res2.status_code, 200)
        self.assertIn("extra_dim_col", self.repo.tables["sales"].columns)

    def test_unjoinable_table_graceful_warning(self):
        fact_csv = "date,user_id,sales_usd\n2023-01-01,U1,100\n2023-01-02,U2,150"
        unrelated_csv = "sku_id,warehouse_temp\nSKU1,22.5\nSKU2,23.0"

        self.client.post(
            "/api/data/upload",
            files=[
                ("files", ("fact.csv", io.BytesIO(fact_csv.encode("utf-8")), "text/csv")),
                ("files", ("unrelated.csv", io.BytesIO(unrelated_csv.encode("utf-8")), "text/csv"))
            ]
        )

        config_payload = {
            "dataset_name": "Unjoinable Test",
            "analysis_grain": "Cross-Sectional Snapshot",
            "primary_measure": "sales_usd",
            "file_roles": [
                {"filename": "fact.csv", "role": "fact", "join_keys": []},
                {"filename": "unrelated.csv", "role": "dimension", "join_keys": []}
            ]
        }

        res = self.client.post("/api/data/configure", json=config_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        
        # Verify warning about unjoined table is present
        warnings = data.get("warnings", [])
        has_warning = any("unrelated.csv" in w and "no compatible shared join keys" in w for w in warnings)
        self.assertTrue(has_warning, f"Expected warning about unjoinable table in warnings list: {warnings}")

if __name__ == "__main__":
    unittest.main()
