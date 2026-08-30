import io
import unittest
import pandas as pd
import numpy as np
from starlette.testclient import TestClient
from main import app
from data.source_manager import DataProfiler

class TestKpiCandidateRanking(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_kpi_ranking_order_priority(self):
        """Verifies KPI keyword ranks higher than neutral and driver keywords."""
        df = pd.DataFrame({
            "units_sold": [100, 105, 110, 95, 120, 115, 130],
            "discount_pct": [0.1, 0.1, 0.15, 0.2, 0.1, 0.1, 0.05],
            "marketing_spend": [5000, 5200, 6000, 5800, 7000, 6500, 7200],
            "gross_revenue_usd": [10000, 10500, 11000, 9500, 12000, 11500, 13000],
            "region": ["North"] * 7,
            "date": pd.date_range("2026-01-01", periods=7, freq="D")
        })
        profile = DataProfiler.profile_dataset(df, dataset_name="Revenue Analysis")
        kpi_cands = profile.get("kpi_candidates", [])
        
        self.assertGreater(len(kpi_cands), 0)
        self.assertEqual(kpi_cands[0]["column_name"], "gross_revenue_usd")
        self.assertIn("revenue", kpi_cands[0]["rationale"].lower())
        
        col_scores = {c["column_name"]: c["score"] for c in kpi_cands}
        if "units_sold" in col_scores and "marketing_spend" in col_scores:
            self.assertGreater(col_scores["gross_revenue_usd"], col_scores["units_sold"])
            self.assertGreater(col_scores["units_sold"], col_scores["marketing_spend"])

    def test_driver_keyword_never_beats_strong_kpi_even_with_perfect_null_coverage(self):
        """Ad spend with 100% coverage should not outrank churn_rate with minor nulls."""
        df = pd.DataFrame({
            "ad_spend_usd": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
            "churn_rate": [0.05, 0.04, np.nan, 0.06, 0.05, 0.07],
            "date": pd.date_range("2026-01-01", periods=6, freq="D")
        })
        profile = DataProfiler.profile_dataset(df)
        kpi_cands = profile.get("kpi_candidates", [])
        
        self.assertEqual(kpi_cands[0]["column_name"], "churn_rate")
        self.assertGreater(kpi_cands[0]["score"], kpi_cands[1]["score"])

    def test_upload_api_returns_kpi_candidates(self):
        """Verifies /api/data/upload returns kpi_candidates for both single and multi-file uploads."""
        csv_content = (
            "units_sold,discount_pct,marketing_spend,gross_revenue_usd,region,date\n"
            "100,0.10,5000,10000,North,2026-01-01\n"
            "105,0.10,5200,10500,North,2026-01-02\n"
            "110,0.15,6000,11000,North,2026-01-03\n"
            "95,0.20,5800,9500,North,2026-01-04\n"
            "120,0.10,7000,12000,North,2026-01-05\n"
        )
        files = [("files", ("test_sales.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"))]
        res = self.client.post("/api/data/upload", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        # Check top-level kpi_candidates
        self.assertIn("kpi_candidates", data)
        self.assertGreater(len(data["kpi_candidates"]), 0)
        self.assertEqual(data["kpi_candidates"][0]["column_name"], "gross_revenue_usd")
        
        # Check file-level kpi_candidates in files array
        self.assertIn("files", data)
        file_0 = data["files"][0]
        self.assertIn("kpi_candidates", file_0)
        self.assertEqual(file_0["kpi_candidates"][0]["column_name"], "gross_revenue_usd")

    def test_built_in_benchmarks_unaffected(self):
        """Verifies built-in benchmarks retain their contractual primary measures."""
        from data.repository import DataRepository
        repo = DataRepository.get_instance()
        
        repo.switch_benchmark("b2b_saas_pricing")
        self.assertEqual(repo.active_source_info["primary_measure_label"], "Gross Revenue")
        
        repo.switch_benchmark("saas_churn_roas")
        self.assertEqual(repo.active_source_info["primary_measure_label"], "Customer Churn Rate")
        
        repo.switch_benchmark("retail_fulfillment")
        self.assertEqual(repo.active_source_info["primary_measure_label"], "Weekly Store Revenue")
        
        repo.switch_benchmark("manufacturing_quality")
        self.assertEqual(repo.active_source_info["primary_measure_label"], "First-Pass Yield (%)")

if __name__ == "__main__":
    unittest.main()
