import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from data.repository import DataRepository
from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine

class TestManufacturingBenchmark(unittest.TestCase):
    def test_switch_and_load(self):
        repo = DataRepository.get_instance()
        repo.switch_benchmark("manufacturing_quality")
        self.assertEqual(repo.active_benchmark_id, "manufacturing_quality")
        self.assertIn("production_output_daily", repo.tables)
        self.assertIn("machine_calibration_logs", repo.tables)
        self.assertIn("qc_inspector_notes", repo.tables)
        self.assertIn("sales", repo.tables)  # Alias
        self.assertEqual(repo.active_source_info["primary_measure_label"], "First-Pass Yield (%)")
    
    def test_hypothesis_evaluation(self):
        repo = DataRepository.get_instance()
        repo.switch_benchmark("manufacturing_quality")
        engine = EvidenceEngine(repo)
        hypotheses = engine.evaluate_all_hypotheses()
        self.assertEqual(len(hypotheses), 4)
        
        m1 = hypotheses[0]
        self.assertEqual(m1["id"], "M1_CALIBRATION_DRIFT")
        self.assertEqual(m1["confidence_classification"], "HIGH-CONFIDENCE DRIVER")
        self.assertGreater(m1["cause_score_100"], 80.0)
        self.assertGreater(len(m1["unstructured_evidence"]), 0)
        
        m2 = next(h for h in hypotheses if h["id"] == "M2_SUPPLIER_MATERIAL_QUALITY")
        self.assertEqual(m2["confidence_classification"], "CORRELATED SIGNAL")
        
        m3 = next(h for h in hypotheses if h["id"] == "M3_OPERATOR_SHIFT_CHANGE")
        self.assertEqual(m3["confidence_classification"], "REFUTED BY DATA")
        
        m4 = next(h for h in hypotheses if h["id"] == "M4_HUMIDITY_TRANSIT_EXPOSURE")
        self.assertEqual(m4["confidence_classification"], "NOT TESTABLE")
        self.assertEqual(m4["cause_score_100"], 0.0)
    
    def test_simulation(self):
        res = SimulationEngine.simulate_lever_impact(
            price_rollback_pct=-8.0, promo_fund_k=20.0, churn_mitigation=True,
            benchmark_id="manufacturing_quality"
        )
        self.assertEqual(res["benchmark_id"], "manufacturing_quality")
        self.assertEqual(len(res["trajectory_df"]), 8)
        self.assertGreater(res["simulated_yield_pct"], 78.4)
        self.assertLess(res["simulated_scrap_cost"], 45000.0)
    
    def test_unstructured_quotes(self):
        repo = DataRepository.get_instance()
        repo.switch_benchmark("manufacturing_quality")
        engine = EvidenceEngine(repo)
        hypotheses = engine.evaluate_all_hypotheses()
        m1 = hypotheses[0]
        quotes = m1.get("unstructured_evidence", [])
        self.assertGreater(len(quotes), 0)
    def test_switch_benchmark_endpoint(self):
        from starlette.testclient import TestClient
        from main import app
        client = TestClient(app)
        res = client.post("/api/data/switch-benchmark", json={"benchmark_id": "manufacturing_quality"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["benchmark_id"], "manufacturing_quality")
        self.assertEqual(data["source_info"]["primary_measure_label"], "First-Pass Yield (%)")

    def tearDown(self):
        repo = DataRepository.get_instance()
        repo.switch_benchmark("b2b_saas_pricing")

if __name__ == "__main__":
    unittest.main()
