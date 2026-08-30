import unittest
import io
import pandas as pd
from starlette.testclient import TestClient
from main import app, _UPLOAD_CACHE
from data.repository import DataRepository

class TestMultiFileUpload(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.repo = DataRepository.get_instance()
        _UPLOAD_CACHE.clear()

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

    def test_multiple_file_upload_and_configure(self):
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
            "analysis_grain": "Time Series (Weekly / Monthly / Daily)",
            "primary_measure": "sales_usd",
            "file_roles": [
                {"filename": "fact.csv", "role": "fact", "join_keys": []},
                {"filename": "dim.csv", "role": "dimension", "join_keys": []},
                {"filename": "unstr.csv", "role": "unstructured", "join_keys": []}
            ]
        }
        
        conf_response = self.client.post("/api/data/configure", json=config_payload)
        self.assertEqual(conf_response.status_code, 200)
        
        # Check repo tables
        self.assertIn("sales", self.repo.tables)
        self.assertIn("dim", self.repo.tables)
        self.assertIn("unstr", self.repo.tables)

if __name__ == "__main__":
    unittest.main()
