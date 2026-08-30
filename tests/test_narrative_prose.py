"""
tests/test_narrative_prose.py
Tests verifying that EDITH output is structured as genuine narrative prose:
- general_user and executive briefings contain 0 '###' / '####' markdown headers
- No more than 1 short bullet list in briefings
- All ground-truth numbers, facts, and citations are preserved
- monitoring_plan is present in recommended actions across all benchmarks
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from data.repository import DataRepository
from ai.offline_reasoner import OfflineEdithReasoner
from core.evidence_engine import EvidenceEngine


class TestNarrativeProse(unittest.TestCase):
    def setUp(self):
        self.repo = DataRepository.get_instance()

    def tearDown(self):
        self.repo.switch_benchmark("b2b_saas_pricing")

    def test_b2b_general_user_is_pure_prose(self):
        self.repo.switch_benchmark("b2b_saas_pricing")
        briefing = OfflineEdithReasoner.generate_executive_briefing(persona_id="general_user")
        narrative = briefing["narrative_markdown"]
        
        # Must contain ZERO ### or #### headers
        self.assertNotIn("###", narrative)
        self.assertNotIn("####", narrative)
        # Check that key numbers are preserved
        self.assertTrue("11%" in narrative or "148,000" in narrative)
        self.assertIn("Region B", narrative)
        self.assertIn("12%", narrative)
        self.assertIn("21", narrative)
        self.assertIn("10,528", narrative)
        self.assertIn("15,000", narrative)
        # Check monitoring plan in actions
        for act in briefing["recommended_actions"]:
            self.assertIn("monitoring_plan", act)
            self.assertTrue(len(act["monitoring_plan"]) > 10)

    def test_b2b_executive_narrative_lead_and_no_headers(self):
        self.repo.switch_benchmark("b2b_saas_pricing")
        briefing = OfflineEdithReasoner.generate_executive_briefing(persona_id="executive")
        narrative = briefing["narrative_markdown"]
        
        # Must contain ZERO ### or #### headers
        self.assertNotIn("###", narrative)
        self.assertNotIn("####", narrative)
        # Key numbers present
        self.assertIn("Region B", narrative)
        self.assertTrue("10.5%" in narrative or "147,700" in narrative)
        self.assertIn("88.0", narrative)
        self.assertIn("10,528", narrative)
        # Bullet list count <= 1
        bullet_lines = [l for l in narrative.split("\n") if l.strip().startswith(("-", "*", "1.", "2.", "3."))]
        self.assertLessEqual(len(bullet_lines), 5)
        # Check monitoring plan in actions
        for act in briefing["recommended_actions"]:
            self.assertIn("monitoring_plan", act)

    def test_subscription_benchmark_narratives(self):
        self.repo.switch_benchmark("saas_churn_roas")
        gen_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="general_user")
        gen_text = gen_brief["narrative_markdown"]
        self.assertNotIn("###", gen_text)
        self.assertNotIn("####", gen_text)
        self.assertIn("2.1%", gen_text)
        self.assertIn("8.6%", gen_text)
        self.assertIn("78,000", gen_text)
        
        exec_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="executive")
        exec_text = exec_brief["narrative_markdown"]
        self.assertNotIn("###", exec_text)
        self.assertNotIn("####", exec_text)
        self.assertIn("88.5", exec_text)

        for act in exec_brief["recommended_actions"]:
            self.assertIn("monitoring_plan", act)

    def test_retail_benchmark_narratives(self):
        self.repo.switch_benchmark("retail_fulfillment")
        gen_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="general_user")
        gen_text = gen_brief["narrative_markdown"]
        self.assertNotIn("###", gen_text)
        self.assertNotIn("####", gen_text)
        self.assertTrue("210,000" in gen_text or "$210k" in gen_text or "210" in gen_text)
        self.assertTrue("118,000" in gen_text or "$118k" in gen_text or "118" in gen_text)
        self.assertIn("48%", gen_text)
        self.assertIn("34%", gen_text)
        
        exec_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="executive")
        exec_text = exec_brief["narrative_markdown"]
        self.assertNotIn("###", exec_text)
        self.assertNotIn("####", exec_text)

        for act in exec_brief["recommended_actions"]:
            self.assertIn("monitoring_plan", act)

    def test_manufacturing_benchmark_narratives(self):
        self.repo.switch_benchmark("manufacturing_quality")
        gen_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="general_user")
        gen_text = gen_brief["narrative_markdown"]
        self.assertNotIn("###", gen_text)
        self.assertNotIn("####", gen_text)
        self.assertIn("96.2%", gen_text)
        self.assertIn("78.4%", gen_text)
        self.assertIn("M-07", gen_text)
        self.assertIn("Line 3", gen_text)
        self.assertIn("Plant Midwest", gen_text)
        
        exec_brief = OfflineEdithReasoner.generate_executive_briefing(persona_id="executive")
        exec_text = exec_brief["narrative_markdown"]
        self.assertNotIn("###", exec_text)
        self.assertNotIn("####", exec_text)
        self.assertIn("89.5", exec_text)
        self.assertIn("45,000", exec_text)

        for act in exec_brief["recommended_actions"]:
            self.assertIn("monitoring_plan", act)

    def test_investigation_briefing_prose(self):
        self.repo.switch_benchmark("b2b_saas_pricing")
        ev = EvidenceEngine(self.repo).evaluate_all_hypotheses()
        anom = {"kpi_name": "Gross Sales Revenue ($)", "current_value": 1253600.0, "baseline_value": 1401300.0, "delta_pct": -10.5, "z_score": -2.3}
        
        gen_inv = OfflineEdithReasoner.generate_investigation_briefing(anom, ev, persona="general_user")
        self.assertNotIn("###", gen_inv)
        self.assertNotIn("####", gen_inv)
        self.assertTrue("10.5%" in gen_inv or "11%" in gen_inv)

        exec_inv = OfflineEdithReasoner.generate_investigation_briefing(anom, ev, persona="executive")
        self.assertNotIn("###", exec_inv)
        self.assertNotIn("####", exec_inv)
        self.assertIn("88.0", exec_inv)


if __name__ == "__main__":
    unittest.main()
