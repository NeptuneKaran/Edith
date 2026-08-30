import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from core.feedback import (
    submit_hypothesis_feedback, submit_action_rating,
    get_feedback_log, get_hypothesis_annotations,
    annotate_hypotheses, clear_feedback
)

class TestFeedback(unittest.TestCase):
    def setUp(self):
        clear_feedback()
    
    def test_submit_and_retrieve_confirmation(self):
        result = submit_hypothesis_feedback("H1_PRICING_PRESSURE", "confirmed", persona_id="analyst")
        self.assertEqual(result["action"], "confirmed")
        self.assertEqual(result["hypothesis_id"], "H1_PRICING_PRESSURE")
        log = get_feedback_log()
        self.assertEqual(len(log), 1)
    
    def test_submit_override_with_reason(self):
        submit_hypothesis_feedback("S2_MARKETING_REALLOCATION", "overridden", reason="Marketing shift happened after churn started", persona_id="analyst")
        ann = get_hypothesis_annotations("S2_MARKETING_REALLOCATION")
        self.assertEqual(ann["override_count"], 1)
        self.assertEqual(ann["overrides"][0]["reason"], "Marketing shift happened after churn started")
    
    def test_annotations_dont_alter_score(self):
        hypotheses = [
            {"id": "H1_PRICING_PRESSURE", "cause_score_100": 88.0, "name": "Pricing Elasticity"},
            {"id": "H2_COMPETITOR_CAMPAIGN", "cause_score_100": 60.4, "name": "Competitor Campaign"}
        ]
        submit_hypothesis_feedback("H1_PRICING_PRESSURE", "confirmed", persona_id="analyst")
        submit_hypothesis_feedback("H1_PRICING_PRESSURE", "confirmed", persona_id="executive")
        submit_hypothesis_feedback("H2_COMPETITOR_CAMPAIGN", "overridden", reason="Timing doesn't match", persona_id="analyst")
        
        annotated = annotate_hypotheses(hypotheses)
        self.assertEqual(annotated[0]["cause_score_100"], 88.0)  # Score unchanged
        self.assertEqual(annotated[0]["feedback_annotations"]["confirmation_count"], 2)
        self.assertEqual(annotated[1]["cause_score_100"], 60.4)  # Score unchanged
        self.assertEqual(annotated[1]["feedback_annotations"]["override_count"], 1)
    
    def test_action_rating(self):
        submit_action_rating("action_price_rollback", "helpful", persona_id="executive")
        log = get_feedback_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["rating"], "helpful")

if __name__ == "__main__":
    unittest.main()
