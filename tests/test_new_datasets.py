import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import pandas as pd
from data.generator import generate_enterprise_dataset, generate_subscription_dataset, generate_retail_dataset
from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.evidence_engine import EvidenceEngine
from core.simulation_engine import SimulationEngine
from ai.tools import search_unstructured_evidence, AVAILABLE_TOOLS, TOOL_REGISTRY
from ai.offline_reasoner import OfflineEdithReasoner


class TestNewDatasets(unittest.TestCase):
    def test_dataset_generators(self):
        """Validates that all 3 dataset generators produce complete, valid tables."""
        # Benchmark 1: B2B SaaS Commercial Ledger
        ds1 = generate_enterprise_dataset()
        self.assertIn("sales", ds1)
        self.assertIn("pricing", ds1)
        self.assertIn("competitor", ds1)
        self.assertIn("inventory", ds1)
        self.assertIn("feedback", ds1)
        self.assertGreater(len(ds1["sales"]), 0)

        # Benchmark 2: Subscription Growth & Retention
        ds2 = generate_subscription_dataset()
        self.assertIn("subscriptions_weekly", ds2)
        self.assertIn("marketing_spend_daily", ds2)
        self.assertIn("support_tickets_monthly", ds2)
        self.assertIn("cs_call_notes", ds2)
        self.assertIn("exit_survey_comments", ds2)
        self.assertGreater(len(ds2["subscriptions_weekly"]), 0)
        self.assertEqual(len(ds2["marketing_spend_daily"]), 5824)
        self.assertGreaterEqual(len(ds2["cs_call_notes"]), 3)

        # Benchmark 3: Regional Retail Demand & Fulfillment
        ds3 = generate_retail_dataset()
        self.assertIn("store_sales_weekly", ds3)
        self.assertIn("inventory_daily", ds3)
        self.assertIn("supplier_shipment_logs", ds3)
        self.assertIn("regional_events_monthly", ds3)
        self.assertIn("supplier_emails", ds3)
        self.assertIn("customer_reviews", ds3)
        self.assertGreater(len(ds3["store_sales_weekly"]), 0)
        self.assertEqual(len(ds3["inventory_daily"]), 5824)
        self.assertGreaterEqual(len(ds3["supplier_shipment_logs"]), 3)

    def test_benchmark_switching(self):
        """Validates dynamic benchmark switching in DataRepository."""
        repo = DataRepository.get_instance()

        # Switch to Benchmark 2
        repo.switch_benchmark("saas_churn_roas")
        self.assertEqual(repo.active_benchmark_id, "saas_churn_roas")
        self.assertIn("subscriptions_weekly", repo.tables)
        self.assertEqual(repo.active_source_info["primary_measure_label"], "Customer Churn Rate")

        # Switch to Benchmark 3
        repo.switch_benchmark("retail_fulfillment")
        self.assertEqual(repo.active_benchmark_id, "retail_fulfillment")
        self.assertIn("store_sales_weekly", repo.tables)
        self.assertEqual(repo.active_source_info["primary_measure_label"], "Weekly Store Revenue")

        # Reset to Benchmark 1
        repo.switch_benchmark("b2b_saas_pricing")
        self.assertEqual(repo.active_benchmark_id, "b2b_saas_pricing")
        self.assertIn("sales", repo.tables)

    def test_sparse_history_detection(self):
        """Validates sparse history (<8 periods) detection on newly launched products/tiers."""
        repo = DataRepository.get_instance()
        repo.switch_benchmark("saas_churn_roas")

        sparse_segments = repo.get_sparse_segments()
        self.assertGreater(len(sparse_segments), 0)
        ai_beta = [s for s in sparse_segments if "AI Add-on Beta" in s["segment"]]
        self.assertEqual(len(ai_beta), 1)
        self.assertEqual(ai_beta[0]["recorded_periods"], 4)
        self.assertEqual(ai_beta[0]["status"], "INSUFFICIENT_HISTORY")

        # Test baseline engine with sparse dataframe (4 periods)
        df_sparse = pd.DataFrame({
            "week_idx": [49, 50, 51, 52],
            "week_label": ["2026-W05", "2026-W06", "2026-W07", "2026-W08"],
            "week_date": ["2026-02-01", "2026-02-08", "2026-02-15", "2026-02-22"],
            "value": [8400.0, 10200.0, 12000.0, 13800.0]
        })
        res = AnomalyEngine.evaluate_current_anomaly(df_sparse, kpi_name="AI Beta MRR")
        self.assertTrue(res["insufficient_history"])
        self.assertIn("INSUFFICIENT_HISTORY", res["status_label"])

    def test_subscription_hypothesis_evaluation(self):
        """Validates causal scoring, confounder separation, and unstructured evidence for Benchmark 2."""
        repo = DataRepository.get_instance()
        repo.switch_benchmark("saas_churn_roas")

        engine = EvidenceEngine(repo)
        hypotheses = engine.evaluate_all_hypotheses()

        self.assertEqual(len(hypotheses), 4)
        # S1: Onboarding flow change (HIGH-CONFIDENCE DRIVER)
        s1 = hypotheses[0]
        self.assertEqual(s1["id"], "S1_ONBOARDING_FLOW_CHANGE")
        self.assertEqual(s1["confidence_classification"], "HIGH-CONFIDENCE DRIVER")
        self.assertGreater(s1["cause_score_100"], 80.0)
        self.assertGreater(len(s1["unstructured_evidence"]), 0)
        # Verbatim quote check
        self.assertTrue(any("onboarding" in quote["quote"].lower() for quote in s1["unstructured_evidence"]))

        # S2: Marketing budget shift (CONFOUNDER / CORRELATED SIGNAL)
        s2 = next(h for h in hypotheses if h["id"] == "S2_MARKETING_REALLOCATION")
        self.assertEqual(s2["confidence_classification"], "CORRELATED SIGNAL")
        self.assertTrue(40.0 < s2["cause_score_100"] < 65.0)

        # S3: MRR Contraction (DOWNSTREAM EFFECT)
        s3 = next(h for h in hypotheses if h["id"] == "S3_MRR_CONTRACTION")
        self.assertEqual(s3["confidence_classification"], "DOWNSTREAM EFFECT")
        self.assertEqual(s3["dependency_role"], "DOWNSTREAM_EFFECT")

        # S4: Competitor Poaching (NOT TESTABLE)
        s4 = next(h for h in hypotheses if h["id"] == "S4_COMPETITOR_POACHING")
        self.assertEqual(s4["confidence_classification"], "NOT TESTABLE")
        self.assertEqual(s4["cause_score_100"], 0.0)

    def test_retail_hypothesis_evaluation_and_ambiguity(self):
        """Validates near-tied ambiguous pair, refuted pricing, and unstructured evidence for Benchmark 3."""
        repo = DataRepository.get_instance()
        repo.switch_benchmark("retail_fulfillment")

        engine = EvidenceEngine(repo)
        hypotheses = engine.evaluate_all_hypotheses()

        self.assertEqual(len(hypotheses), 4)
        r1 = hypotheses[0]
        r2 = hypotheses[1]

        # Check ambiguous near-tied pair
        self.assertEqual(r1["id"], "R1_SUPPLIER_STOCKOUT")
        self.assertEqual(r2["id"], "R2_REGIONAL_WEATHER_EVENT")
        score_delta = abs(r1["cause_score_100"] - r2["cause_score_100"])
        self.assertLessEqual(score_delta, 6.0)
        self.assertTrue(r1.get("is_ambiguous_pair"))
        self.assertIn("AMBIGUOUS", r1.get("ambiguity_warning", ""))

        # Unstructured evidence quotes in R1
        self.assertGreater(len(r1["unstructured_evidence"]), 0)

        # R3: Store pricing (REFUTED BY DATA)
        r3 = next(h for h in hypotheses if h["id"] == "R3_PRICING_CHANGE")
        self.assertEqual(r3["confidence_classification"], "REFUTED BY DATA")
        self.assertEqual(r3["empirical_prediction_status"], "CONTRADICTED")

        # R4: Competitor opening (NOT TESTABLE)
        r4 = next(h for h in hypotheses if h["id"] == "R4_COMPETITOR_STORE_OPENING")
        self.assertEqual(r4["confidence_classification"], "NOT TESTABLE")

    def test_unstructured_search_tool(self):
        """Validates Tool #15 search_unstructured_evidence."""
        self.assertIn("search_unstructured_evidence", TOOL_REGISTRY)
        self.assertIn(search_unstructured_evidence, AVAILABLE_TOOLS)

        repo = DataRepository.get_instance()

        # Search in Benchmark 2
        repo.switch_benchmark("saas_churn_roas")
        results = search_unstructured_evidence(query="onboarding wizard setup")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("onboarding" in r["quoted_text"].lower() for r in results))

        # Search in Benchmark 3
        repo.switch_benchmark("retail_fulfillment")
        results_retail = search_unstructured_evidence(query="customs port delay")
        self.assertGreater(len(results_retail), 0)
        self.assertTrue(any("customs" in r["quoted_text"].lower() or "port" in r["quoted_text"].lower() for r in results_retail))

    def test_multi_benchmark_simulation(self):
        """Validates counterfactual recovery simulations across all 3 benchmarks."""
        # Benchmark 1 Simulation
        res1 = SimulationEngine.simulate_lever_impact(price_rollback_pct=-6.0, promo_fund_k=15.0, churn_mitigation=True, benchmark_id="b2b_saas_pricing")
        self.assertEqual(res1["benchmark_id"], "b2b_saas_pricing")
        self.assertEqual(len(res1["trajectory_df"]), 8)
        self.assertGreater(res1["recovery_pct"], 60.0)

        # Benchmark 2 Simulation
        res2 = SimulationEngine.simulate_lever_impact(price_rollback_pct=-8.0, promo_fund_k=20.0, churn_mitigation=True, benchmark_id="saas_churn_roas")
        self.assertEqual(res2["benchmark_id"], "saas_churn_roas")
        self.assertIn("simulated_churn_rate", res2)
        self.assertLess(res2["simulated_churn_rate"], 8.6)
        self.assertEqual(len(res2["trajectory_df"]), 8)

        # Benchmark 3 Simulation
        res3 = SimulationEngine.simulate_lever_impact(price_rollback_pct=-10.0, promo_fund_k=25.0, churn_mitigation=True, benchmark_id="retail_fulfillment")
        self.assertEqual(res3["benchmark_id"], "retail_fulfillment")
        self.assertIn("simulated_stockout_rate", res3)
        self.assertLess(res3["simulated_stockout_rate"], 48.0)
        self.assertEqual(len(res3["trajectory_df"]), 8)

    def test_offline_reasoner_multi_benchmark(self):
        """Validates offline reasoning narrations and Q&A across all 3 benchmarks."""
        repo = DataRepository.get_instance()

        # Benchmark 2 Briefing & Q&A
        repo.switch_benchmark("saas_churn_roas")
        briefing_sub = OfflineEdithReasoner.generate_investigation_briefing(
            anomaly_context={"kpi_name": "Customer Churn", "current_value": 8.6, "baseline_value": 2.1},
            hypotheses=EvidenceEngine(repo).evaluate_all_hypotheses(),
            persona="executive"
        )
        self.assertIn("Onboarding Flow Redesign", briefing_sub)
        self.assertIn("Confounder Isolation", briefing_sub)
        self.assertIn("Sparse History", briefing_sub)

        ans_sub = OfflineEdithReasoner.answer_query("Why did customer churn increase?", persona_id="executive")
        self.assertIn("Onboarding", ans_sub)

        ans_roas = OfflineEdithReasoner.answer_query("What happened to marketing ROAS?", persona_id="executive")
        self.assertTrue("Confounder" in ans_roas or "Social" in ans_roas)

        # Benchmark 3 Briefing & Q&A
        repo.switch_benchmark("retail_fulfillment")
        briefing_ret = OfflineEdithReasoner.generate_investigation_briefing(
            anomaly_context={"kpi_name": "Weekly Store Revenue", "current_value": 118000.0, "baseline_value": 210000.0},
            hypotheses=EvidenceEngine(repo).evaluate_all_hypotheses(),
            persona="executive"
        )
        self.assertIn("Ambiguous Competing Drivers", briefing_ret)
        self.assertIn("Supplier Port Delays", briefing_ret)
        self.assertIn("Winter Blizzard", briefing_ret)

        ans_ret = OfflineEdithReasoner.answer_query("Why did store sales drop?", persona_id="executive")
        self.assertTrue("Ambiguous" in ans_ret or "ambiguous" in ans_ret)

        # Reset repository to Benchmark 1
        repo.switch_benchmark("b2b_saas_pricing")

    def test_dynamic_freshness_computation(self):
        """Validates that compute_freshness recomputes relative to current execution time."""
        from datetime import datetime, timezone, timedelta
        from core.evidence_engine import compute_freshness
        
        now = datetime.now(timezone.utc)
        
        # Test 2 hours ago
        df_2h = pd.DataFrame({"date": [now - timedelta(hours=2)]})
        freshness_2h = compute_freshness(df_2h)
        self.assertEqual(freshness_2h, "2 hours ago")
        
        # Test 5 days ago
        df_5d = pd.DataFrame({"date": [now - timedelta(days=5)]})
        freshness_5d = compute_freshness(df_5d)
        self.assertEqual(freshness_5d, "5 days ago")
        
        # Test empty or invalid
        self.assertEqual(compute_freshness(pd.DataFrame()), "Unknown")


if __name__ == "__main__":
    unittest.main()
