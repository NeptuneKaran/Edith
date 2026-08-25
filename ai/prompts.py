"""
ai/prompts.py
System prompts and structured templates for EDITH.
Enforces strict grounding in analytical facts, prohibits hallucinating numbers, and requires calibrated uncertainty.
"""

EDITH_SYSTEM_PROMPT = """You are EDITH, an AI-Assisted Business Intelligence Investigation Assistant.
Your core mission is to explain KPI anomalies using ONLY the structured analytical evidence provided to you by the deterministic analytical engine.

STRICT OPERATING PRINCIPLES:
1. GROUNDING: Never invent numbers, dates, or statistical calculations. All KPI values, percentages, Z-scores, and Evidence Scores must come directly from the supplied JSON context.
2. EVIDENCE CITATION: Always cite specific evidence from the supporting, contradictory, prediction, control-group, or mathematical decomposition ledgers when explaining findings.
3. CAUSALITY CAUTION: Do NOT claim that correlation proves absolute causation. Use calibrated phrasing such as "The data is consistent with...", "Evidence strongly supports...", "Likely primary driver...", or "Temporal alignment suggests...".
4. COMPETING HYPOTHESES: Always acknowledge secondary plausible causes (e.g. competitor campaigns), distinguish upstream causes from downstream consequences (e.g. Gross Margin compression), and explain why refuted hypotheses (e.g. inventory constraints) were ruled out by empirical data.
5. CALIBRATED UNCERTAINTY & CONFOUNDERS: Explicitly state when evidence has potential confounders or when certain hypotheses are not testable due to missing telemetry.
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
- Statistical Z-Score: {anomaly_context.get('z_score', 0):.2f} (Expected Corridor: +-2.0 sigma)
- Persistence: {anomaly_context.get('is_persistent')}

[EVALUATED HYPOTHESES & CAUSE SCORES]
"""
    for h in hypotheses:
        testable_str = "TESTABLE" if h.get('testable', True) else "NOT TESTABLE (MISSING TELEMETRY)"
        score_100_str = f"{h.get('cause_score_100', 0.0):.1f} / 100" if h.get('testable', True) else "N/A"
        evidence_01_str = f"{h.get('evidence_score', 0.0):.2f} / 1.00" if h.get('testable', True) else "N/A"
        role_str = h.get('dependency_role', 'UPSTREAM_DIRECT')
        cls_str = h.get('confidence_classification', h.get('confidence_band'))
        
        prompt += f"""
---
Hypothesis ID: {h.get('id')}
Name: {h.get('name')}
Category: {h.get('category')}
Metric DAG Role: {role_str}
Status: {testable_str}
Cause Score: {score_100_str} (0-1: {evidence_01_str}) | Classification: {cls_str}
Temporal Alignment: {h.get('temporal_alignment', {}).get('assessment')}
"""
        math_decomp = h.get('mathematical_decomposition')
        if math_decomp:
            prompt += f"Mathematical Decomposition: {math_decomp.get('interpretation')}\n"
            
        lag_eval = h.get('lag_analysis')
        if lag_eval:
            prompt += f"Lag Cross-Correlation: Best Lag = {lag_eval.get('best_lag')} wks (Strength: {lag_eval.get('lag_strength')})\n"
            
        ctrl = h.get('control_group_analysis', {})
        if ctrl and ctrl.get('control_cohort') != "None":
            prompt += f"Control Cohort: {ctrl.get('control_cohort')} (DiD Divergence: {ctrl.get('did_divergence_pct', 0.0):.1f}%, Pre-trend Status: {ctrl.get('pre_trend_status')})\n"
            
        preds = h.get('predictions', [])
        if preds:
            prompt += "Tested Predictions:\n"
            for p in preds:
                prompt += f"  [{p.get('status')}] {p.get('prediction')} -> Observed: {p.get('observed_value')}\n"
                
        prompt += "Supporting Evidence:\n"
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
1. What happened (data-derived impact localization).
2. The strongest supported upstream driver vs secondary external factors vs downstream consequences vs refuted hypotheses.
3. Mathematical decomposition shares and control cohort findings.
4. Recommended next investigative checks.
"""
    return prompt
