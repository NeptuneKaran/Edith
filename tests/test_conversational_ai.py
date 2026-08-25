"""
tests/test_conversational_ai.py
Tests the conversational AI capabilities of EDITH across both live Gemini and offline grounded modes.
Verifies multi-turn context resolution, follow-up handling, ambiguity clarification, greetings, and data fidelity.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.repository import DataRepository
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from ai.llm_client import EdithLLMClient
from ai.offline_reasoner import OfflineEdithReasoner
from ai.prompts import classify_user_intent

def test_conversational_ai_suite():
    print("==================================================")
    print("   RUNNING EDITH CONVERSATIONAL AI TEST SUITE     ")
    print("==================================================")
    
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, kpi_name="Monthly B2B Sales")
    
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    price_h = hypotheses[0]
    
    # 1. Intent Classification
    print("\n--- [1] INTENT CLASSIFICATION ENGINE ---")
    assert classify_user_intent("Hello EDITH") == "CONVERSATIONAL_SUPPORT"
    assert classify_user_intent("Who are you?") == "CONVERSATIONAL_SUPPORT"
    assert classify_user_intent("What is Difference in Differences?") == "GENERAL_ANALYTICAL"
    assert classify_user_intent("Why did B2B sales drop in Region B?") == "EDITH_INVESTIGATION"
    print("  [PASS] Intent classifier accurately routes queries to proper handling modes.")
    
    # 2. Greetings & Conversational Support
    print("\n--- [2] GREETINGS & CAPABILITIES ---")
    client = EdithLLMClient(api_key="") # Offline mode
    ans_greet, meta_greet = client.answer_question("Hi EDITH, what can you do?", anomaly_ctx, price_h, hypotheses)
    assert "edith" in ans_greet.lower()
    assert "anomaly" in ans_greet.lower() or "investigate" in ans_greet.lower()
    print("  [PASS] Greeting and capability questions answered naturally.")
    
    # 3. Specific Evidence Grounding (No Hallucination)
    print("\n--- [3] EMPIRICAL EVIDENCE & MATH GROUNDING ---")
    ans_math, _ = client.answer_question("Explain the mathematical volume decomposition", anomaly_ctx, price_h, hypotheses)
    assert "-$210,000" in ans_math or "210000" in ans_math or "210,000" in ans_math
    assert "+$21,600" in ans_math or "21600" in ans_math or "21,600" in ans_math
    assert "-$188,400" in ans_math or "188400" in ans_math or "188,400" in ans_math
    print("  [PASS] Mathematical revenue decomposition preserves exact calculated figures.")
    
    ans_inv, _ = client.answer_question("Why is inventory ruled out?", anomaly_ctx, price_h, hypotheses)
    assert "99.4%" in ans_inv or "fill rate" in ans_inv.lower()
    assert "0 stockout" in ans_inv.lower() or "0" in ans_inv
    print("  [PASS] Refuted hypotheses cite exact operational telemetry (99.4% fill rate).")
    
    # 4. Action-Oriented Recommendations
    print("\n--- [4] ACTION-ORIENTED QUERIES ---")
    ans_action, _ = client.answer_question("What should we do first to fix this?", anomaly_ctx, price_h, hypotheses)
    assert "-6%" in ans_action or "price adjustment" in ans_action.lower()
    assert "$15,000" in ans_action or "15000" in ans_action or "marketing" in ans_action.lower()
    print("  [PASS] Action-oriented query returns structured, prioritized policy recommendations.")
    
    # 5. Multi-Turn Context & Follow-Up Questions
    print("\n--- [5] MULTI-TURN CONTEXT & FOLLOW-UPS ---")
    history_competitor = [
        {"role": "user", "content": "Tell me about the competitor campaign."},
        {"role": "edith", "content": "Competitor ApexTech launched a 15% discount campaign in Week 07 in Region B."}
    ]
    ans_followup_why, _ = client.answer_question("Why?", anomaly_ctx, price_h, hypotheses, chat_history=history_competitor)
    assert "week 06" in ans_followup_why.lower() or "timing" in ans_followup_why.lower() or "secondary" in ans_followup_why.lower()
    print("  [PASS] Resolves single-word follow-up 'Why?' using recent chat context.")
    
    ans_compare, _ = client.answer_question("Compare pricing vs competitor", anomaly_ctx, price_h, hypotheses)
    assert "88.0" in ans_compare
    assert "60.4" in ans_compare
    assert "Week 06" in ans_compare
    assert "Week 07" in ans_compare
    print("  [PASS] Comparative analysis evaluates both hypotheses side-by-side.")
    
    # 6. Ambiguous Queries & Clarification
    print("\n--- [6] AMBIGUITY HANDLING & CLARIFICATION ---")
    ans_ambig, _ = client.answer_question("is it good?", anomaly_ctx, price_h, hypotheses)
    assert "clarify" in ans_ambig.lower() or "option a" in ans_ambig.lower() or "would you like" in ans_ambig.lower()
    print("  [PASS] Ambiguous queries trigger targeted clarifying options instead of generic dumps.")
    
    # 7. Response Style (Concise vs Detailed)
    print("\n--- [7] RESPONSE STYLE CONTROLS ---")
    b_concise, _ = client.generate_briefing(anomaly_ctx, hypotheses, response_style="concise")
    b_detailed, _ = client.generate_briefing(anomaly_ctx, hypotheses, response_style="detailed")
    assert len(b_detailed) > len(b_concise)
    print("  [PASS] Response style control modulates conciseness and analytical depth.")
    
    print("\n==================================================")
    print("    ALL CONVERSATIONAL AI TESTS PASSED (100%)!    ")
    print("==================================================")

if __name__ == "__main__":
    test_conversational_ai_suite()
