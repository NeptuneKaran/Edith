"""
ai/prompts.py
System prompts and structured templates for EDITH.
Enforces strict grounding in analytical facts, prohibits hallucinating numbers, and requires calibrated uncertainty.
"""

EDITH_SYSTEM_PROMPT = """You are EDITH, an AI-Assisted Business Intelligence Investigation Assistant.
Your core mission is to explain KPI anomalies using ONLY the structured analytical evidence provided to you by the deterministic analytical engine.

STRICT OPERATING PRINCIPLES:
1. GROUNDING: Never invent numbers, dates, or statistical calculations. All KPI values, percentages, Z-scores, and Evidence Scores must come directly from the supplied JSON context.
2. EVIDENCE CITATION: Always cite specific evidence from the supporting or contradictory ledgers when explaining findings.
3. CAUSALITY CAUTION: Do NOT claim that correlation proves causation. Use calibrated phrasing such as "The data is consistent with...", "Evidence strongly supports...", or "Temporal alignment suggests...".
4. COMPETING HYPOTHESES: Always acknowledge secondary plausible causes and explain why refuted hypotheses (e.g. inventory constraints) were ruled out by empirical data.
5. CALIBRATED UNCERTAINTY: Explicitly state when evidence is incomplete, confounded, or based on assumptions.
6. CONCISE & ACTIONABLE: Keep explanations focused, structured with markdown bullet points, and directly tied to actionable business levers.
"""

def format_investigation_prompt(anomaly_context: dict, hypotheses: list, user_query: str = "") -> str:
    """Formats the structured investigation state into a grounded prompt for the LLM."""
    prompt = f"""
STRUCTURED ANALYTICAL STATE (Source of Truth):

[ANOMALY CONTEXT]
- KPI: {anomaly_context.get('kpi_name')}
- Current Value: ${anomaly_context.get('current_value', 0):,.0f}
- Baseline Value: ${anomaly_context.get('baseline_value', 0):,.0f}
- Variance: {anomaly_context.get('delta_pct', 0):+.1f}% (${anomaly_context.get('delta_value', 0):+,.0f})
- Statistical Z-Score: {anomaly_context.get('z_score', 0):.2f} (Expected Corridor: ±2.0σ)
- Persistence: {anomaly_context.get('is_persistent')}

[EVALUATED HYPOTHESES & EVIDENCE SCORES]
"""
    for h in hypotheses:
        prompt += f"""
---
Hypothesis ID: {h.get('id')}
Name: {h.get('name')}
Category: {h.get('category')}
Evidence Score: {h.get('evidence_score')} / 1.00 ({h.get('confidence_band')})
Temporal Alignment: {h.get('temporal_alignment', {}).get('assessment')}
Supporting Evidence:
"""
        for s in h.get('supporting_evidence', []):
            prompt += f"  • {s}\n"
        prompt += "Contradictory Evidence / Caveats:\n"
        for c in h.get('contradictory_evidence', []):
            prompt += f"  • {c}\n"
        prompt += f"Data Lineage: {h.get('data_lineage')}\n"

    if user_query:
        prompt += f"""
[USER QUESTION]
{user_query}

Provide an evidence-grounded answer citing the analytical facts above.
"""
    else:
        prompt += """
[TASK]
Synthesize an executive diagnostic briefing explaining:
1. What happened (data-derived).
2. The strongest supported hypothesis vs secondary factors vs refuted hypotheses.
3. Recommended next investigative checks.
"""
    return prompt
