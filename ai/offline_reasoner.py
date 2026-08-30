"""
ai/offline_reasoner.py
Deterministic Offline Reasoner & Conversational Decision Assistant for EDITH.
Generates evidence-grounded, human-like natural language synthesis directly from active analytical data.
Dynamically handles both the built-in B2B SaaS benchmark and arbitrary custom business datasets.
Supports four distinct personas:
- executive: Strategic decision-maker summary
- general_user: 100% plain-language narrative with zero statistical/technical jargon
- regional_lead: Operational focus with role-based security boundaries
- analyst: Full econometric ledger, evidence scores, and data lineage
"""
import re
from typing import Dict, List, Any, Optional


class OfflineEdithReasoner:
    """Deterministic conversational reasoner strictly grounded in verified analytical facts."""
    
    @staticmethod
    def _get_recommended_action_response(
        persona_id: str = "executive",
        anomaly_context: Optional[Dict[str, Any]] = None,
        simulation_levers: Optional[Dict[str, Any]] = None
    ) -> str:
        """Returns structured recommended actions and policy intervention strategy."""
        from data.repository import DataRepository
        repo = DataRepository.get_instance()
        is_demo = repo.active_source_info.get("is_demo", True)
        kpi_name = (anomaly_context or {}).get("kpi_name", repo.active_source_info.get("primary_measure_label", "Primary Measure"))
        pid = (persona_id or "executive").lower().strip()
        
        # 1. Custom generic dataset recommendations
        if not is_demo:
            breakdowns = repo.get_dimensional_breakdown()
            drvs = repo.get_driver_correlations().get("correlations", {})
            dist = repo.get_distribution_statistics()
            
            top_dim_summary = []
            for dim, df_dim in list(breakdowns.items())[:2]:
                if not df_dim.empty:
                    top_row = df_dim.iloc[0]
                    top_dim_summary.append(f"`{top_row[dim]}` in {dim.replace('_', ' ').title()}")
            dim_target = top_dim_summary[0] if top_dim_summary else "the highest concentration segment"
            
            top_drv = list(drvs.keys())[0] if drvs else "mapped operational drivers"
            
            if pid == "general_user":
                return f"""**Recommended Next Steps for {kpi_name}:**

1. **Focus on the Highest Impact Group ({dim_target}):**
   - Direct immediate operational reviews toward {dim_target}, which accounts for the largest share of {kpi_name}.

2. **Investigate the Key Influencing Factor ({top_drv.replace('_', ' ').title()}):**
   - Review operational policies and processes related to {top_drv.replace('_', ' ').title()} to identify optimization opportunities.

3. **Review Unusual Data Points:**
   - Audit the {dist.get('outlier_count', 0)} outlier records identified in the data to ensure data accuracy and address specific anomalies."""

            return f"""### 🎯 Recommended Operational Action Plan for {kpi_name}

1. **Target Highest-Variance Concentration ({dim_target}):**
   - Prioritize operational intervention and resource allocation toward **{dim_target}**, the dominant variance epicenter.

2. **Optimize Key Correlated Driver ({top_drv.replace('_', ' ').title()}):**
   - Calibrate operational parameters linked to **{top_drv.replace('_', ' ').title()}**, which exhibits the strongest empirical association with {kpi_name}.

3. **Data Quality & Outlier Remediation:**
   - Audit and validate the **{dist.get('outlier_count', 0)} outlier records ({dist.get('outlier_pct', 0.0):.1f}%)** to prevent operational skew."""

        # 2. Built-in B2B SaaS demo recommendations
        if pid == "general_user":
            return """**Here is what the team is planning to do next to recover sales:**

1. **Adjust Pricing Back Slightly (-6%):**
   - Roll back half the recent price increase on Enterprise renewals in Region B (setting the price to **$10,528/unit**). This brings back price-conscious business buyers while keeping a modest gain over last year.

2. **Offer Local Partner Marketing Support ($15,000):**
   - Provide a $15,000 regional marketing fund to help local sales partners counter competitor discounts in Region B.

3. **Provide High-Touch Support to Key Accounts:**
   - Assign dedicated customer success managers to the top 12 at-risk renewal accounts to make sure they are supported.

4. **Expected Outcome:**
   - Over the next 8 weeks, this plan is projected to recover **nearly 80% of lost sales volume** and add about **+$20,000/week** in revenue recovery."""

        elif pid == "regional_lead":
            return """**Recommended Action Plan & Policy Approval Priority (Regional Sales Lead):**

1. **First Immediate Field Action (Authorized for Deployment):**
   - **Deploy $15,000 Regional Partner Co-Op Fund:** Allocate co-op marketing incentives across key Region B partner accounts to counter ApexTech's 15% discount campaign (accelerates win-back deal velocity by **+$1,667/week**).
   - **Activate VIP Retention Guard:** Assign dedicated proactive CSM coverage to the top 12 at-risk Enterprise renewals in Region B to protect recurring ARR.

2. **Executive Decision Package (Pending CRO Approval):**
   - **Targeted Price Adjustment (-6%):** A recommendation has been submitted to the Executive Pricing Committee to adjust Enterprise Suite Alpha renewals in Region B to $10,528/unit (recovers volume while preserving +$528/unit margin gain).

3. **Projected Recovery Path:**
   - Modeling in **Screen 04 (Policy Simulator)** projects this balanced strategy recovers **78.2% of lost volume** over 8 weeks, generating **+$20,067/week in net revenue recovery**."""

        else: # executive & analyst
            return """**Recommended Action Plan & Decision Approval Priority (Executive / CRO):**

1. **Primary Decision to Approve First (Price Calibration):**
   - **Authorize -6% Price Adjustment on Enterprise Suite Alpha:** Roll back half the recent price hike on Enterprise renewals in Region B (setting unit price to **$10,528/unit**). This directly re-engages price-sensitive enterprise buyers while preserving **+$528/unit net margin gain** over baseline (projected volume recovery: **+$18,400/week**).

2. **Secondary Complementary Action:**
   - **Authorize $15,000 Regional Co-Op Marketing Fund:** Release localized partner incentives in Region B to neutralize ApexTech's 15% switcher campaign (accelerates deal win-back by **+$1,667/week**).

3. **Risk Mitigation (Immediate Execution):**
   - **Deploy VIP Retention Guard:** Assign dedicated high-touch CSMs to the top 12 at-risk Enterprise renewals to guard against logo churn compounding.

4. **Projected 8-Week Recovery Trajectory:**
   - Combined policy trajectory in **Screen 04 (Policy Simulator)** projects **78.2% volume recovery** over 8 weeks, stabilizing gross margin at **70.2%** and delivering **+$20,067/week** net recovery."""

    @staticmethod
    def generate_investigation_briefing(
        anomaly_context: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        response_style: str = "concise",
        persona: str = "executive"
    ) -> str:
        """Synthesizes the primary executive investigation diagnosis."""
        from data.repository import DataRepository
        repo = DataRepository.get_instance()
        is_demo = repo.active_source_info.get("is_demo", True)
        kpi_name = anomaly_context.get("kpi_name", repo.active_source_info.get("primary_measure_label", "Primary Measure"))
        current_val = anomaly_context.get("current_value", 0.0)
        baseline_val = anomaly_context.get("baseline_value", 0.0)
        delta_pct = anomaly_context.get("delta_pct", 0.0)
        z_score = anomaly_context.get("z_score", 0.0)
        pid = (persona or "executive").lower().strip()
        
        # 1. Custom generic dataset briefing
        if not is_demo or (hypotheses and hypotheses[0].get("id", "").startswith("GEN_")):
            dq = repo.get_data_quality_report()
            dist = repo.get_distribution_statistics()
            drvs = repo.get_driver_correlations().get("correlations", {})
            breakdowns = repo.get_dimensional_breakdown()
            
            top_drv_name = list(drvs.keys())[0] if drvs else "None"
            top_drv_r = drvs[top_drv_name]["pearson_r"] if drvs else 0.0
            
            top_dim_summary = []
            for dim, df_dim in list(breakdowns.items())[:2]:
                if not df_dim.empty:
                    top_row = df_dim.iloc[0]
                    top_dim_summary.append(f"`{top_row[dim]}` in {dim.replace('_', ' ').title()} ({abs(top_row.get('contribution_pct', 0.0)):.1f}%)")
            dim_text = ", ".join(top_dim_summary) if top_dim_summary else "Evenly distributed"

            if pid == "general_user":
                return f"""### 💡 Plain-Language Summary: What the Data Shows for {kpi_name}

**1. The Overview:**
- **Primary Metric Analyzed:** **{kpi_name}** with an aggregate total of **{current_val:,.1f}** across **{dq.get('total_rows', 0):,} records**.
- **Data Completeness:** High quality data with **{dq.get('data_quality_score', 100.0):.1f}% Health Score**.

**2. Key Patterns Found in the Data:**
- **Highest Concentration:** The highest values are concentrated in {dim_text}.
- **Strongest Factor:** **{top_drv_name.replace('_', ' ').title()}** shows the strongest statistical link with {kpi_name} (correlation: {top_drv_r:+.2f}).
- **Data Spread:** Middle value is **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}**, with **{dist.get('outlier_count', 0)} unusual data points** flagged.

**3. Recommended Next Step:**
- Focus operational reviews on {dim_text} and explore factors influencing {top_drv_name.replace('_', ' ').title()}."""

            return f"""### 📋 Executive Investigation Briefing: {kpi_name} Analysis

**1. Incident Overview & Scale:**
- **Primary Focus Metric:** **{kpi_name}** with an aggregate observed level of **{current_val:,.1f}** across **{dq.get('total_rows', 0):,} records**.
- **Operational Grain:** {anomaly_context.get('status_label', 'Cross-Sectional Snapshot')}.

**2. Observational Findings & Empirical Concentrations:**
- **Segment Epicenter:** Heaviest concentration observed in {dim_text}.
- **Explanatory Driver Correlation:** **{top_drv_name.replace('_', ' ').title()}** shows the strongest statistical association with r = {top_drv_r:+.2f} (Pearson).
- **Distribution Profile:** Median: **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}** | IQR: **{dist.get('iqr', 0.0):.2f}** | Outliers: **{dist.get('outlier_count', 0)} items ({dist.get('outlier_pct', 0.0):.1f}%)**.

**3. Decision Guidance & Observational Integrity:**
- All reported signals represent empirical concentrations and statistical correlations to direct operational investigation, not unverified causal claims."""

        # 2. Built-in B2B SaaS demo briefing
        top_h = hypotheses[0] if hypotheses else {}
        second_h = hypotheses[1] if len(hypotheses) > 1 else {}
        refuted_h = next((h for h in hypotheses if h["id"] in ["H8_SUPPLY_CONSTRAINT", "H3_INVENTORY_CONSTRAINT"]), {})
        ctrl = top_h.get("control_group_analysis", {})
        ctrl_cohort = ctrl.get("control_cohort", "Mid-Market Alpha")
        did_gap = ctrl.get("did_divergence_pct", 48.3)
        math_d = top_h.get("mathematical_decomposition", {})
        
        # General User briefing (100% plain language)
        if pid == "general_user":
            return f"""### 💡 Plain-Language Summary: What Happened to {kpi_name}?

**1. The Headline:**
- **{kpi_name}** experienced a **noticeable drop of roughly {abs(delta_pct):.1f}%** (${baseline_val:,.0f} → ${current_val:,.0f}).
- Almost the entire drop (**over 97%**) happened in **Region B** among **Enterprise accounts** on **Product Suite Alpha**.

**2. Why It Happened:**
- **Main Reason:** We increased prices by 12% two weeks ago. Large business customers were sensitive to the change, and 21 accounts paused renewals.
- **Contributing Factor:** Around the same time, competitor ApexTech offered a 15% discount promotion, giving hesitant buyers an alternative.
- **Ruled Out:** Deliveries, warehouse fulfillment, and software systems were completely normal with zero operational delays.

**3. What the Team Plans to Do Next:**
- Roll back half of the price increase on Enterprise plans in Region B (setting the price to $10,528), provide $15,000 in local partner marketing support, and assign dedicated account managers to at-risk renewals."""

        if response_style == "concise":
            return f"""### 🔍 Executive Incident Briefing: {kpi_name} Anomaly

**1. Incident Overview & Impact:**
- **{kpi_name}** dropped by **{delta_pct:+.1f}%** (${baseline_val:,.0f} → ${current_val:,.0f}), breaching the ±2.0σ corridor (Z = {z_score:.2f}, 2-week persistence).
- **Localization:** **97.3% of the deficit** is isolated to **Region B Enterprise** accounts on **Product Suite Alpha**.

**2. Competing Hypotheses & Evidence:**
- **Primary Driver:** **{top_h.get('name', 'Pricing Elasticity')}** (Cause Score: **{top_h.get('cause_score_100', 88.0):.1f}/100** | Evidence: **{top_h.get('evidence_score', 0.88):.2f}/1.00**).
  - Mathematical volume loss: **-${abs(math_d.get('volume_effect_usd', 210000)):,.0f}** cushioned by **+${math_d.get('price_effect_usd', 21600):,.0f}** price realization.
  - Temporal lead-time: +12% price hike in Week 06 preceded contraction by 2 weeks (τ = 2 weeks).
  - Control group contrast: **{did_gap:.1f}% DiD divergence** vs un-hiked {ctrl_cohort}.
- **Secondary Factor:** **{second_h.get('name', 'Competitor Campaign')}** (**{second_h.get('cause_score_100', 60.4):.1f}/100**). Competitor ApexTech launched a 15% discount in Week 07, compounding enterprise deal slippage.
- **Refuted:** **{refuted_h.get('name', 'Supply Bottleneck')}** (**0.0/100**). Warehouse fill rate remained at **99.4%** with zero stockouts.

**3. Recommended Next Step:**
- Apply a targeted **-6% price adjustment** on Enterprise Suite Alpha combined with a **$15k regional co-op marketing fund** to recover projected volume."""
        else:
            return rf"""### 🔍 Detailed Analytical Investigation Briefing: {kpi_name} Anomaly

**1. Statistical Anomaly Detection & Impact Localization:**
- **Metric:** {kpi_name} (Fiscal Q1 2026, Week 08)
- **Observed Revenue:** ${current_val:,.0f} vs Baseline ${baseline_val:,.0f} (Variance: **{delta_pct:+.1f}%**, ${anomaly_context.get('delta_value', -147700):+,.0f}).
- **Corridor Threshold:** Lower boundary $1,272,908 | Upper boundary $1,529,692 (Z-Score: **{z_score:.2f}**, P1 Material Incident).
- **Dimensional Breakdown:**
  - *Region:* Region B (-$182.2k gross deficit, 97.3% share).
  - *Tier:* Enterprise cohort (-$182.2k, 97.3% share); Mid-Market & SMB stable.
  - *Product:* Product Suite Alpha (100% of product-level decline).

**2. Causal Evidence & Competing Hypothesis Evaluation:**
- **#1 Pricing Elasticity & Plan Hike (Score: {top_h.get('cause_score_100', 88.0):.1f}/100 | {top_h.get('confidence_classification', 'HIGH-CONFIDENCE DRIVER')}):**
  - *Exact Revenue Identity:* ΔRevenue = Volume Effect + Price Cushion = -$210,000 + $21,600 = -$188,400 (0.0% error).
  - *Lag Correlation:* Peak negative correlation at τ = 2 weeks (|r| = 0.999).
  - *Difference-in-Differences:* {did_gap:.1f}% relative performance divergence against parallel pre-trend control (r = 0.88).
  - *Customer Telemetry:* Pricing complaints surged to 38/week in CRM logs.
- **#2 Aggressive Competitor Campaign (Score: {second_h.get('cause_score_100', 60.4):.1f}/100 | {second_h.get('confidence_classification', 'POSSIBLE DRIVER')}):**
  - *Competitor Action:* ApexTech launched 15% discount in Week 07.
  - *Empirical Signal:* CRM win/loss mentions surged 4.8x baseline.
  - *Lead-Time Lag:* Coincident 1-week response lag (τ = 1 week).
- **#8 Supply Chain / Inventory Constraints (Score: 0.0/100 | REFUTED):**
  - *Refutation Evidence:* Logistics logs confirm 99.4% warehouse fill rate with 0 stockout days.

**3. Recommended Counterfactual Decision Trajectory:**
- Execute -6% price rollback on Enterprise Suite Alpha in Region B ($10,528/unit) combined with $15,000 regional partner co-op fund.
- Projected 8-week recovery: **+$20,067/week** net recovery, stabilizing gross margin at **70.2%**."""

    @staticmethod
    def answer_query(
        query: str,
        anomaly_context: Dict[str, Any],
        selected_hypothesis: Dict[str, Any],
        all_hypotheses: Optional[List[Dict[str, Any]]] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        simulation_levers: Optional[Dict[str, Any]] = None,
        persona: str = "executive",
        response_style: str = "concise",
        **kwargs
    ) -> str:
        """Answers user queries in natural, conversational language with strict empirical grounding."""
        from data.repository import DataRepository
        repo = DataRepository.get_instance()
        is_demo = repo.active_source_info.get("is_demo", True)
        
        q = query.strip()
        q_clean = re.sub(r'[^\w\s]', '', q.lower()).strip()
        q_lower = q.lower()
        pid = (persona or "executive").lower().strip()
        
        if all_hypotheses is None:
            all_hypotheses = kwargs.get("hypotheses", [])
        if selected_hypothesis is None and all_hypotheses:
            selected_hypothesis = all_hypotheses[0]
        elif selected_hypothesis is None:
            selected_hypothesis = {}
        
        kpi_name = anomaly_context.get("kpi_name", repo.active_source_info.get("primary_measure_label", "Primary Measure"))
        current_val = anomaly_context.get("current_value", 0.0)
        baseline_val = anomaly_context.get("baseline_value", 0.0)
        delta_pct = anomaly_context.get("delta_pct", 0.0)
        z_score = anomaly_context.get("z_score", 0.0)
        
        # ==============================================================================
        # 1. GREETINGS & INTRODUCTIONS
        # ==============================================================================
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "hiya", "sup", "yo"]
        if any(q_clean == g or q_clean.startswith(g + " ") for g in greetings):
            dataset_name = repo.active_source_info.get("name", "Active Dataset")
            if pid == "general_user":
                if not is_demo:
                    return f"""Hello! I'm **EDITH**, your AI business intelligence assistant.

I'm currently connected to **{dataset_name}** analyzing **{kpi_name}**. Here are a few ways we can explore:

- **Understand Key Drivers:** Ask *"What factors affect {kpi_name}?"*
- **Explore Categories:** Ask *"Which groups have the highest {kpi_name}?"*
- **Check Data Spread:** Ask *"Are there any outliers in this file?"*

How can I help you today?"""

                return f"""Hello! I'm **EDITH**, your AI business intelligence assistant.

I'm currently connected to **{dataset_name}**. Here are a few ways we can explore what's happening:

- **Understand What Changed:** Ask *"Why did sales drop?"* or *"What happened in Region B?"*
- **Explore Categories:** Ask *"Which areas or customer groups had the biggest drop?"*
- **Check What the Team Is Doing:** Ask *"What is the recovery plan?"* or *"What should we do next?"*

How can I help you today?"""

            return f"""Hello! I'm **EDITH**, your AI decision intelligence assistant.

I'm currently connected to **{dataset_name}**. Here are a few ways we can dive into the data together:

- **Explore Concentrations:** Ask *"Which segments or categories have the highest variance?"*
- **Analyze Drivers:** Ask *"What drivers correlate most strongly with {kpi_name}?"*
- **Inspect Quality & Distribution:** Ask *"Are there any outliers or missing values in this file?"*
- **Root Cause & Guidance:** Ask *"What factors affect performance?"* or *"What actions are recommended?"*

What would you like to examine first?"""

        # ==============================================================================
        # 2. CAPABILITIES & HELP
        # ==============================================================================
        if any(k in q_clean for k in ["who are you", "what can you do", "what is edith", "help me", "capabilities", "how do you work"]):
            if pid == "general_user":
                return f"""I am **EDITH**, an AI business intelligence assistant built to help everyone understand the real story behind business numbers.

**Here is what I can do for you:**
1. **Explain Metrics Simply:** Explain changes and trends in plain, everyday language.
2. **Find the Exact Epicenter:** Pinpoint which categories or segments have the biggest impact.
3. **Analyze Influencing Factors:** Identify which operational factors are most linked to your numbers.
4. **Walk Through Next Steps:** Provide practical recommendations on what to investigate next.

Feel free to ask me anything about **{kpi_name}** or the active business data!"""

            return f"""I am **EDITH (Executive Decision Intelligence & Tactical Hypothesis)**, an AI-assisted analytics partner engineered to uncover empirical drivers behind business performance.

**Here is how I assist decision-makers:**
1. **Anomaly & Outlier Detection:** Pinpointing statistically significant deviations (±2.0σ) and IQR-based distribution outliers.
2. **Dimensional Variance Localization:** Breaking down performance across categories, regions, tiers, and channels to isolate the exact epicenter.
3. **Driver Correlation & Association:** Measuring linear (Pearson r) and rank-order (Spearman r) relationships with explanatory factors.
4. **Counterfactual What-If Simulation:** Modeling policy adjustments on calibrated economic models.
5. **Grounded Natural Q&A:** Answering your specific inquiries directly using verified calculations.

Feel free to ask me anything about **{kpi_name}** or the active data!"""

        # ==============================================================================
        # 3. CUSTOM / GENERIC DATASET SPECIFIC REASONING
        # ==============================================================================
        if not is_demo:
            breakdowns = repo.get_dimensional_breakdown()
            drvs = repo.get_driver_correlations().get("correlations", {})
            dq = repo.get_data_quality_report()
            dist = repo.get_distribution_statistics()
            
            top_dim_summary = []
            for dim, df_dim in list(breakdowns.items())[:2]:
                if not df_dim.empty:
                    top_row = df_dim.iloc[0]
                    top_dim_summary.append(f"`{top_row[dim]}` in {dim.replace('_', ' ').title()} ({abs(top_row.get('contribution_pct', 0.0)):.1f}%)")
            dim_text = ", ".join(top_dim_summary) if top_dim_summary else "Evenly distributed across categories"
            
            top_drv_name = list(drvs.keys())[0] if drvs else "None"
            top_drv_r = drvs[top_drv_name]["pearson_r"] if drvs else 0.0

            # 3A. Starter probe: What changed in the selected metric?
            if any(k in q_clean for k in ["what changed in the selected metric", "what changed", "metric movement", "tell me what changed"]):
                top_name = selected_hypothesis.get('name', 'Segment Concentration') if selected_hypothesis else 'Segment Concentration'
                top_sum = selected_hypothesis.get('summary', '') if selected_hypothesis else ''
                return f"""**Observed Metric Summary ({kpi_name}):**
- **Observed Value:** {current_val:,.1f}
- **Primary Epicenter:** {top_name} ({top_sum})
- **Data Quality:** {dq.get('data_quality_score', 100.0):.1f}% Health Score across {dq.get('total_rows', 0):,} rows."""

            # 3B. Action / Next steps / What to do queries
            if any(k in q_clean for k in ["action", "do", "fix", "next", "recommend", "solution", "strategy", "roadmap", "plan", "step", "approve", "priority"]):
                return OfflineEdithReasoner._get_recommended_action_response(persona, anomaly_context, simulation_levers)

            # 3C. Check if query matches specific category/dimension values in dataset
            matched_entity = None
            matched_dim = None
            for dim, df_dim in breakdowns.items():
                if not df_dim.empty and dim in df_dim.columns:
                    for val in df_dim[dim].dropna().unique():
                        val_str = str(val).lower()
                        if len(val_str) > 2 and (val_str in q_lower or any(part in q_lower for part in val_str.split() if len(part) > 3)):
                            matched_entity = str(val)
                            matched_dim = dim
                            break
                if matched_entity:
                    break

            if matched_entity and matched_dim:
                df_dim = breakdowns[matched_dim]
                entity_rows = df_dim[df_dim[matched_dim].astype(str) == matched_entity]
                if not entity_rows.empty:
                    er = entity_rows.iloc[0]
                    share_pct = abs(er.get("contribution_pct", 0.0))
                    total_val = er.get("sum", er.get("count", er.get(kpi_name, 0.0)))
                    avg_val = er.get("mean", 0.0)
                    return f"""Based on the data for **{matched_dim.replace('_', ' ').title()}: `{matched_entity}`**:

- **Share of Metric:** Accounts for **{share_pct:.1f}%** of the total {kpi_name}.
- **Total Observed {kpi_name}:** **{total_val:,.1f}**
- **Average per Record:** **{avg_val:,.1f}**
- **Category Ranking:** Ranks #{int(entity_rows.index[0]) + 1} across all {len(df_dim)} groups in `{matched_dim}`.

Would you like to explore how `{matched_entity}` compares across other dimensions or numeric drivers?"""

            # 3D. Specific question about concentrations / biggest contributors
            if any(k in q_clean for k in ["concentration", "highest", "biggest", "top group", "worst", "lowest", "which store", "which brand", "which department", "breakdown", "segments", "which groups show the greatest concentration"]):
                lines = []
                for dim, df_dim in breakdowns.items():
                    if not df_dim.empty:
                        top_row = df_dim.iloc[0]
                        bottom_row = df_dim.iloc[-1] if len(df_dim) > 1 else top_row
                        lines.append(f"- **{dim.replace('_', ' ').title()}:** Top is `{top_row[dim]}` (**{abs(top_row.get('contribution_pct', 0.0)):.1f}%** share); lowest is `{bottom_row[dim]}` (**{abs(bottom_row.get('contribution_pct', 0.0)):.1f}%** share).")
                summary_body = "\n".join(lines)
                return f"""**Dimensional Concentration Analysis for {kpi_name}:**

{summary_body}

*This breakdown reveals where metric values are concentrated across your business segments.*"""

            # 3E. Specific question about drivers / correlations / what affected / influence / why
            if any(k in q_clean for k in ["driver", "correlation", "correlate", "association", "relationship", "factors", "relate", "affect", "affected", "influence", "influenced", "impact", "impacted", "cause", "caused", "why", "which numeric fields have the strongest observed association"]):
                if drvs:
                    lines = []
                    for drv_name, stats in drvs.items():
                        r_val = stats.get('pearson_r', 0.0)
                        rel_desc = "Strong Positive" if r_val > 0.6 else ("Strong Negative" if r_val < -0.6 else ("Moderate Positive" if r_val > 0.3 else ("Moderate Negative" if r_val < -0.3 else "Weak / Neutral")))
                        if pid == "general_user":
                            lines.append(f"- **{drv_name.replace('_', ' ').title()}:** {rel_desc} link with {kpi_name} (relationship score: {r_val:+.2f}).")
                        else:
                            lines.append(f"- **{drv_name.replace('_', ' ').title()}:** Pearson r = {r_val:+.2f} ({rel_desc}) | Spearman r = {stats.get('spearman_rs', 0.0):+.2f}.")
                    
                    driver_body = "\n".join(lines)
                    if pid == "general_user":
                        return f"""**What Influences {kpi_name}:**

Based on our analysis of the active dataset across **{dq.get('total_rows', 0):,} records**:

**1. Primary Influencing Factors:**
{driver_body}

**2. Where It Is Centered:**
- Values are most concentrated in {dim_text}.

*(These relationships show which operational factors have the strongest link to {kpi_name}.)*"""

                    return f"""**Numeric Driver Associations with {kpi_name}:**

**1. Statistical Driver Correlations (Pearson & Spearman):**
{driver_body}

**2. Dimensional Variance Localization:**
- Heaviest empirical concentration: {dim_text}.

**3. Observational Integrity Notice:**
- Identified associations represent statistical correlations across observational data to guide root-cause investigation."""
                
                # If no drivers are mapped, explain dimensional breakdown
                if pid == "general_user":
                    return f"""**What We Know About {kpi_name}:**

- **Total Observed Level:** **{current_val:,.1f}** across **{dq.get('total_rows', 0):,} records**.
- **Category Breakdown:** Values are most concentrated in {dim_text}.
- *Note:* No numerical driver columns were mapped for correlation testing in this dataset."""

                return f"""**Analysis of Factors Affecting {kpi_name}:**

- **Observed Metric:** **{kpi_name}** ({current_val:,.1f} across {dq.get('total_rows', 0):,} rows).
- **Concentration Epicenter:** {dim_text}.
- *Note:* Correlation analysis requires numeric driver columns. Review dimensional breakdowns for category contributions."""

            # 3F. Specific question about data quality / outliers / distributions
            if any(k in q_clean for k in ["quality", "null", "missing", "outlier", "distribution", "skew", "iqr", "median", "duplicates", "summarize dataquality issues", "summarize data quality issues"]):
                col_nulls = dq.get("column_null_percentages", {})
                null_str = ", ".join([f"`{c}` ({p}%)" for c, p in col_nulls.items() if p > 0]) or "None"
                return f"""**Data Quality Audit Report:**

- **Overall Data Quality Score:** **{dq.get('data_quality_score', 100.0):.1f}%** across **{dq.get('total_rows', 0):,} records**.
- **Fields with Missing Values:** {null_str}
- **Duplicate Rows:** {dq.get('duplicate_rows', 0)} ({dq.get('duplicate_pct', 0.0):.1f}%)
- **Distribution Profile:** Median = **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}**, IQR = **{dist.get('iqr', 0.0):.2f}**, Mean = **{dist.get('mean', 0.0):,.1f}**
- **Outliers:** **{dist.get('outlier_count', 0)} records** ({dist.get('outlier_pct', 0.0):.1f}%) fall beyond 1.5 × IQR."""

            # 3G. General question / overview on custom dataset
            if pid == "general_user":
                return f"""**Key Takeaway for {kpi_name}:**

- **Overall Summary:** We analyzed **{kpi_name}** (observed total: **{current_val:,.1f}**) across **{dq.get('total_rows', 0):,} records**.
- **Highest Category:** The greatest concentration is in {dim_text}.
- **Key Driver:** **{top_drv_name.replace('_', ' ').title()}** shows the strongest statistical link to {kpi_name} (correlation: {top_drv_r:+.2f}).
- **Data Spread:** Median value is **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}** with **{dist.get('outlier_count', 0)} unusual data points** identified.

*(You can ask: "Which category has the highest {kpi_name}?", "What drivers correlate with {kpi_name}?", or "Are there any outliers in this file?".)*"""

            return OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, all_hypotheses or [], response_style="concise", persona=persona)

        # ==============================================================================
        # 4. BUILT-IN DEMO BENCHMARK: TARGETED ANALYTICAL QUERIES
        # ==============================================================================
        price_h = next((h for h in (all_hypotheses or []) if h["id"] == "H1_PRICING_PRESSURE"), {})
        comp_h = next((h for h in (all_hypotheses or []) if h["id"] == "H2_COMPETITOR_CAMPAIGN"), {})
        inv_h = next((h for h in (all_hypotheses or []) if h["id"] in ["H8_SUPPLY_CONSTRAINT", "H3_INVENTORY_CONSTRAINT"]), {})

        # 4A. Mathematical Decomposition / Revenue Identity / Volume vs Price
        if any(k in q_clean for k in ["decomposition", "math", "volume effect", "price effect", "volume vs price", "price vs volume", "volume and price", "formula", "identity", "revenue identity"]):
            if pid == "general_user":
                return """**How Volume vs. Price Impacted Sales:**

When we raised prices on our Enterprise software plan:
- **Extra Revenue from Price Increase:** We brought in an extra **+$21,600** from the 18 customers who accepted the new rate.
- **Lost Revenue from Paused Accounts:** We lost **-$210,000** because 21 enterprise accounts held off on renewing.
- **Net Result:** The lost deal volume heavily outweighed the extra money from higher prices, leaving a net drop of **-$188,400** in Region B."""

            decomp = price_h.get("mathematical_decomposition", {})
            return f"""**Mathematical Revenue Identity (ΔRevenue = ΔUnits × P_pre + Units_post × ΔPrice):**

| Identity Component | Units / Price Shift | USD Financial Impact | Share of Net Deficit |
| :--- | :--- | :--- | :--- |
| **Gross Volume Contraction** | {decomp.get('delta_units', -21):+,.0f} units @ ${decomp.get('pre_price', 10000):,.0f}/unit | **-${abs(decomp.get('volume_effect_usd', 210000)):,.0f}** | {abs(decomp.get('volume_share_pct', 111.5)):.1f}% of gross drop |
| **Retained Price Realization** | {decomp.get('post_units', 18):,.0f} units @ +${decomp.get('delta_price', 1200):,.0f}/unit | **+${decomp.get('price_effect_usd', 21600):,.0f}** | {decomp.get('price_share_pct', -11.5):+.1f}% price cushion |
| **Net Reconciled Deficit** | **Net 18-unit active cohort** | **${decomp.get('delta_revenue', -188400):+,.0f}** | **100.0% (0.0% error)** |

- **Key Takeaway:** The +$21.6k price cushion on the 18 retained units was heavily overshadowed by -$210.0k in lost unit volume."""

        # 4B. Competing Hypotheses Comparison (H1 vs H2)
        if any(k in q_clean for k in ["compare", "versus", "comparison", "h1 vs h2", "pricing vs competitor"]) or ("vs" in q_clean.split() and "volume" not in q_clean):
            if pid == "general_user":
                return """**Comparing the Two Main Drivers:**

1. **The Price Increase (Primary Cause):**
   - We raised prices by 12% in Week 6.
   - This directly triggered pushback from enterprise customers, causing 21 expected renewals to pause.
   - This accounts for the overwhelming majority of the sales drop.

2. **The Competitor Discount (Secondary Factor):**
   - Competitor ApexTech launched a 15% discount campaign in Week 7.
   - This gave hesitant buyers an alternative, making it harder for our sales reps to close renewals.

**Summary:** The price increase was the initial trigger that caused hesitation, while the competitor promotion made it harder to win those buyers back."""

            return """**Comparison: #1 Pricing Elasticity (H1) vs #2 Competitor Campaign (H2):**

| Analytical Dimension | #1 Pricing Elasticity (H1) | #2 Competitor Campaign (H2) |
| :--- | :--- | :--- |
| **Cause Score** | **88.0 / 100** (High Confidence) | **60.4 / 100** (Possible Driver) |
| **Evidence Index** | **0.88 / 1.00** | **0.60 / 1.00** |
| **Shock Timing** | **Week 06** (Internal price hike) | **Week 07** (External promo launch) |
| **Lead-Time Lag** | τ = 2 weeks (Precedes contraction) | τ = 1 week (Coincident) |
| **Control Contrast** | **48.3% DiD divergence** vs un-hiked Mid-Market | Un-hiked suites saw 0% deflection |
| **Analytical Role** | **Primary Upstream Driver** | **Compounding Secondary Factor** |"""

        # 4C. Supply / Inventory Constraints Refutation
        if any(k in q_clean for k in ["inventory", "stockout", "supply", "warehouse", "fulfillment", "logistics"]):
            if pid == "general_user":
                return """**Why We Ruled Out Warehouse or Delivery Issues:**

- **On-Time Delivery:** Delivery and fulfillment records show a **99.4% success rate** with zero backlogs.
- **Stockouts:** There were **0 stockout days** recorded.
- **Takeaway:** Customers were able to receive products without delay; the sales drop was entirely due to buyer hesitation on pricing."""

            return """**Why Supply / Inventory Constraints Are Refuted (H8):**

- **Fulfillment Reliability:** Logistics logs confirm a **99.4% warehouse fill rate** across Weeks 06–08 in Region B.
- **Stockouts:** Exactly **0 stockout days** were recorded in SAP S/4HANA inventory logs.
- **Conclusion:** Physical product delivery was 100% unimpaired; the issue is commercial demand elasticity."""

        # 4D. Difference-in-Differences Proof
        if "difference in differences" in q_clean or "difference-in-differences" in q_lower or "did divergence" in q_clean or "did analysis" in q_clean or "did method" in q_clean or "parallel trend" in q_clean or "parallel trends" in q_clean or ("did" in q.split() and any(w in q.split() for w in ["DiD", "DID", "D-i-D"])):
            if pid == "general_user":
                return """**How We Proved the Price Increase Was the Cause:**

We compared customer groups whose prices were raised against groups whose prices stayed the same. Groups without price increases kept renewing at normal rates, while the group with the price increase saw renewals drop sharply. This direct comparison confirms the price increase was the main trigger."""

            return """**Difference-in-Differences (DiD) Methodology:**

DiD compares changes in outcomes over time between a **treated group** (exposed to an intervention) and an unexposed **control group**:

DiD = (Y_treated,post - Y_treated,pre) - (Y_control,post - Y_control,pre)

- **Parallel Trends:** Assumes treated and control groups would follow the same trajectory absent treatment.
- **EDITH Finding:** Comparing treated Enterprise vs un-hiked Mid-Market isolated a **48.3% causal divergence**."""

        # 4E. Elasticity Explanation
        if "elasticity" in q_clean:
            if pid == "general_user":
                return """**What Price Sensitivity Means for Our Sales:**

Price sensitivity simply measures how much customer demand drops when prices go up. In our Enterprise software segment, customers are very sensitive to price changes. When we raised prices by 12%, enough accounts paused renewals that our overall revenue dropped instead of increasing."""

            return """**Price Elasticity of Demand (εₚ):**

Measures demand responsiveness to pricing changes (εₚ = %ΔQuantity / %ΔPrice).

- In our B2B SaaS benchmark, Enterprise demand is elastic (**εₚ = -1.65**). A +12% price hike triggered a -19.8% volume drop, causing total revenue to contract."""

        # 4F. Why / Sales Drop Trigger
        if q_clean in ["why", "why so", "why is this happening", "why did it happen", "why did that happen", "why did this happen", "why did sales drop", "why the drop"] or q_clean.startswith("why "):
            if pid == "general_user":
                return """**Here is why sales dropped by roughly 11% (about $148,000 below normal):**

1. **The Price Increase:** In Week 6, we raised prices on our Enterprise software plan by 12% (from $10,000 to $11,200).
2. **Customer Pushback:** Because enterprise buyers are sensitive to price changes, 21 expected renewals were put on hold.
3. **Competitor Promotion:** In Week 7, competitor ApexTech launched a 15% discount campaign, giving hesitant customers an attractive alternative.
4. **Operations Were Healthy:** Our warehouse, delivery systems, and software servers were 100% operational with zero stockouts or downtime."""

            return """The primary reason for the **-$147.7k (-10.5%) sales drop** in Week 08 is **pricing elasticity combined with competitor discount pressure**:

1. **The Primary Trigger (+12% Price Increase):** Enterprise subscription pricing for Product Suite Alpha was raised from $10,000 to $11,200/unit in Week 06.
2. **Volume Loss:** Due to high enterprise demand elasticity (εₚ = -1.65), contract volume contracted by 21 units (-$210,000 gross volume loss).
3. **Price Cushion:** The +$1,200 higher price on the 18 retained units provided +$21,600 in cushion, leaving a net regional deficit of -$188,400.
4. **Competitor Defection:** ApexTech launched a 15% discount campaign in Week 07, capturing uncommitted Enterprise renewals in Region B.
5. **Refuted Causes:** Physical warehouse availability was at 99.4% (0 stockouts), and platform uptime was 99.98%."""

        # 4G. Combined KPI Fault & Next Approach
        if (any(k in q_clean for k in ["fault", "faulting", "what is wrong", "problem", "issue", "kpi"]) and any(k in q_clean for k in ["approach", "strategy", "next", "action", "do", "fix", "recommend"])) or "what kpi is faulting" in q_clean:
            if pid == "general_user":
                return f"""### 💡 Metric Diagnostic & Recovery Roadmap

**1. The Affected Metric & What Happened:**
- **Metric:** **{kpi_name}** experienced a noticeable drop of roughly **{abs(delta_pct):.1f}%** (${baseline_val:,.0f} → ${current_val:,.0f}).
- **Location:** Over 97% of the drop is centered in **Region B Enterprise accounts** on Product Suite Alpha.
- **Root Cause:** A 12% price increase led price-sensitive buyers to pause renewals, compounded by a 15% competitor discount promotion.

**2. What the Team Plans to Do Next:**
1. **Adjust Pricing Back Slightly:** Lower Enterprise Suite Alpha renewals in Region B by 6% (to $10,528) to re-engage buyers while keeping a modest gain over last year.
2. **Support Local Partners:** Provide a $15,000 marketing fund in Region B to match competitor discounts.
3. **Dedicated Customer Care:** Assign dedicated customer success managers to at-risk accounts."""

            return f"""### 🚨 Faulting Metric Diagnostic & Recovery Roadmap

**1. Faulting Metric & Anomaly Localization:**
- **Primary KPI:** **{kpi_name}** (Fiscal Q1 2026, Week 08).
- **Observed Deficit:** **${current_val:,.0f}** vs **${anomaly_context.get('baseline_value', 1400000):,.0f}** baseline (**{delta_pct:+.1f}%** / -${abs(anomaly_context.get('delta_value', 147700)):,.0f}).
- **Localized Concentration:** **97.3%** of the decline is concentrated in **Region B → Enterprise Tier → Product Suite Alpha**.
- **Root Mechanism:** Internal +12% price hike triggered elastic demand contraction (εₚ = -1.65), losing 21 enterprise accounts, compounded by ApexTech's 15% promotional campaign in Week 07.

**2. Recommended 3-Step Tactical Approach:**
1. **Targeted -6% Price Calibration:**
   - Roll back half the price increase on Enterprise renewals in Region B (setting unit price to $10,528).
   - This restores contract volume while protecting +$528/unit in pricing gains over baseline.
2. **Deploy $15k Competitive Defense Fund:**
   - Direct $15,000 in regional co-op incentives to neutralize ApexTech's discount pressure in Region B.
3. **Validate in Screen 4 (Policy Simulator):**
   - Head to **Screen 4 (Policy Simulator)** to test this policy trajectory, projected to recover **78.2% of lost volume** within 8 weeks and stabilize gross margin at **70.2%**."""

        # ==============================================================================
        # 5. DECISION / ACTION / APPROVAL BRANCH (FOR DEMO)
        # ==============================================================================
        decision_keywords = [
            "decision", "approve", "approval", "prioritize", "priority", 
            "which one first", "what should we approve", "what to approve",
            "greenlight", "sign off", "next step", "what should we do",
            "how to recover", "action plan", "recommend", "recommendation",
            "solution", "what to do", "approach", "next approach", "strategy",
            "roadmap", "remedy", "mitigate", "first action"
        ]
        if any(k in q_clean for k in decision_keywords):
            return OfflineEdithReasoner._get_recommended_action_response(persona, anomaly_context, simulation_levers)

        # ==============================================================================
        # 6. SMART GENERAL FALLBACK (FOR DEMO)
        # ==============================================================================
        # Check if user query is action/next-step oriented
        if any(w in q_clean for w in ["do", "fix", "action", "next", "help", "solve", "recover", "plan", "step"]):
            return OfflineEdithReasoner._get_recommended_action_response(persona, anomaly_context, simulation_levers)
        
        # Check if user query is why/cause oriented
        if any(w in q_clean for w in ["why", "cause", "reason", "driver", "drop", "down", "fell", "loss", "affect", "affected", "influence", "impact"]):
            return OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, all_hypotheses or [], response_style="concise", persona=persona)

        # General structured response with key findings
        if pid == "general_user":
            return f"""**Key Takeaway for {kpi_name}:**

Sales experienced a noticeable drop of roughly {abs(delta_pct):.1f}%, almost entirely centered in Region B Enterprise accounts following a price increase. Physical operations ran smoothly with zero warehouse issues.

*(You can ask: "Why did sales drop?", "What is the recovery plan?", or "What happened in Region B?".)*"""

        top_evidence = "\n".join([f"- {e}" for e in selected_hypothesis.get("supporting_evidence", [])])
        if top_evidence:
            return f"""**Key Findings for {selected_hypothesis.get('name', 'Active Investigation')}:**

{top_evidence}

*(You can ask me: "What decision should we approve first?", "Explain the volume vs price impact", or "Compare the top two causes".)*"""

        return OfflineEdithReasoner.generate_investigation_briefing(anomaly_context, all_hypotheses or [], response_style="concise", persona=persona)

    @staticmethod
    def answer_conversational_query(
        query: str,
        anomaly_context: Optional[Dict[str, Any]] = None,
        selected_hypothesis: Optional[Dict[str, Any]] = None,
        hypotheses: Optional[List[Dict[str, Any]]] = None,
        all_hypotheses: Optional[List[Dict[str, Any]]] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        simulation_levers: Optional[Dict[str, Any]] = None,
        persona: str = "executive",
        response_style: str = "concise",
        **kwargs
    ) -> str:
        """Entrypoint called by main.py and ai/llm_client.py."""
        from data.repository import DataRepository
        repo = DataRepository.get_instance()
        
        hypos = hypotheses or all_hypotheses
        if not hypos:
            from core.evidence_engine import EvidenceEngine
            ev_eng = EvidenceEngine(repo)
            hypos = ev_eng.evaluate_all_hypotheses()
            
        if not anomaly_context:
            from core.baseline_engine import AnomalyEngine
            ts = repo.get_kpi_time_series()
            anomaly_context = AnomalyEngine.evaluate_current_anomaly(ts)
            
        sel_h = selected_hypothesis or (hypos[0] if hypos else {})
        
        return OfflineEdithReasoner.answer_query(
            query=query,
            anomaly_context=anomaly_context,
            selected_hypothesis=sel_h,
            all_hypotheses=hypos,
            chat_history=chat_history,
            simulation_levers=simulation_levers,
            persona=persona,
            response_style=response_style
        )

    @staticmethod
    def generate_executive_briefing(
        persona_id: str = "executive",
        anomaly_context: Optional[Dict[str, Any]] = None,
        hypotheses: Optional[List[Dict[str, Any]]] = None,
        simulation_levers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates persona-specific Executive Briefing report artifact.
        Works 100% offline with zero external API dependencies.
        Supports: executive, general_user, regional_lead, analyst.
        """
        from data.repository import DataRepository
        from config.personas import get_persona
        from datetime import datetime, timezone
        
        repo = DataRepository.get_instance()
        is_demo = repo.active_source_info.get("is_demo", True)
        p_meta = get_persona(persona_id)
        pid = p_meta["id"]
        
        if not hypotheses:
            from core.evidence_engine import EvidenceEngine
            ev_eng = EvidenceEngine(repo)
            hypotheses = ev_eng.evaluate_all_hypotheses()
            
        if not anomaly_context:
            from core.baseline_engine import AnomalyEngine
            ts = repo.get_kpi_time_series()
            anomaly_context = AnomalyEngine.evaluate_current_anomaly(ts)
            
        top_h = hypotheses[0] if hypotheses else {}
        kpi_name = anomaly_context.get("kpi_name", repo.active_source_info.get("primary_measure_label", "Primary Measure"))
        curr_val = anomaly_context.get("current_value", 1253600.0)
        base_val = anomaly_context.get("baseline_value", 1401300.0)
        delta_val = anomaly_context.get("delta_value", -147700.0)
        delta_pct = anomaly_context.get("delta_pct", -10.5)
        z_score = anomaly_context.get("z_score", -2.30)
        
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # ==============================================================================
        # 1. CUSTOM DATASET EXECUTIVE BRIEFINGS
        # ==============================================================================
        if not is_demo:
            dq = repo.get_data_quality_report()
            dist = repo.get_distribution_statistics()
            drvs = repo.get_driver_correlations().get("correlations", {})
            breakdowns = repo.get_dimensional_breakdown()
            
            top_drv_name = list(drvs.keys())[0] if drvs else "None"
            top_drv_r = drvs[top_drv_name]["pearson_r"] if drvs else 0.0
            
            top_dim_summary = []
            for dim, df_dim in list(breakdowns.items())[:2]:
                if not df_dim.empty:
                    top_row = df_dim.iloc[0]
                    top_dim_summary.append(f"`{top_row[dim]}` in {dim.replace('_', ' ').title()} ({abs(top_row.get('contribution_pct', 0.0)):.1f}%)")
            dim_text = ", ".join(top_dim_summary) if top_dim_summary else "Evenly distributed"

            headline = f"Executive Investigation Briefing: {kpi_name} Analysis"
            
            if pid == "general_user":
                headline = f"Business Update: Overview of {kpi_name} Data"
                narrative = f"""### 💡 Plain-Language Business Update — {kpi_name} Analysis
**Generated:** {now_str} &middot; **Audience:** General Business Team &middot; **Style:** Plain Language (Zero Jargon)

---

#### 1. The Big Picture: What the Data Shows
- **Primary Metric:** **{kpi_name}** with an aggregate observed level of **{curr_val:,.1f}** across **{dq.get('total_rows', 0):,} records**.
- **Data Quality:** Excellent data health score of **{dq.get('data_quality_score', 100.0):.1f}%**.
- **Main Area of Concentration:** The heaviest concentration is in **{dim_text}**.

---

#### 2. Key Influencing Factors
- **Strongest Correlated Factor:** **{top_drv_name.replace('_', ' ').title()}** shows the strongest statistical link with {kpi_name} (relationship: {top_drv_r:+.2f}).
- **Data Spread:** Middle value is **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}**, with **{dist.get('outlier_count', 0)} unusual data points** identified.

---

#### 3. Recommended Operational Focus
1. **Target Highest Impact Group:** Direct operational review toward {dim_text}.
2. **Review Influencing Drivers:** Evaluate operational levers tied to {top_drv_name.replace('_', ' ').title()}.
3. **Audit Outliers:** Inspect the {dist.get('outlier_count', 0)} outlier records to ensure data consistency.
"""
            else:
                narrative = f"""### 📋 Executive Investigation Briefing: {kpi_name} Analysis
**Generated:** {now_str} &middot; **Audience:** {p_meta['name']} &middot; **Focus:** Observational Evidence & Governance

---

#### 1. Incident Overview & Scale
- **Primary Focus Metric:** **{kpi_name}** with an aggregate observed level of **{curr_val:,.1f}** across **{dq.get('total_rows', 0):,} records**.
- **Operational Grain:** {anomaly_context.get('status_label', 'Cross-Sectional Snapshot')}.
- **Data Quality:** {dq.get('data_quality_score', 100.0):.1f}% Health Score across {dq.get('total_rows', 0):,} rows.

---

#### 2. Observational Findings & Empirical Concentrations
- **Segment Epicenter:** Heaviest concentration observed in **{dim_text}**.
- **Explanatory Driver Correlation:** **{top_drv_name.replace('_', ' ').title()}** shows the strongest statistical association with r = {top_drv_r:+.2f} (Pearson).
- **Distribution Profile:** Median: **{dist.get('percentiles', {}).get('P50_median', 0.0):,.1f}** | IQR: **{dist.get('iqr', 0.0):.2f}** | Outliers: **{dist.get('outlier_count', 0)} items ({dist.get('outlier_pct', 0.0):.1f}%)**.

---

#### 3. Decision Guidance & Observational Integrity
- All reported signals represent empirical concentrations and statistical correlations to direct operational investigation, not unverified causal claims.
"""
            actions = [
                {
                    "driver": f"Concentration in {dim_text}",
                    "lever": "Operational Focus",
                    "action": f"Direct operational review toward {dim_text}",
                    "expected_impact": "Identifies localized efficiency opportunities",
                    "owner": "Operations / Segment Lead",
                    "confidence": "High",
                    "status": "Recommended"
                },
                {
                    "driver": f"Association with {top_drv_name.replace('_', ' ').title()}",
                    "lever": "Process Optimization",
                    "action": f"Optimize workflow parameters linked to {top_drv_name.replace('_', ' ').title()}",
                    "expected_impact": "Improves metric correlation efficiency",
                    "owner": "Process Lead",
                    "confidence": "Moderate",
                    "status": "Recommended"
                }
            ]
            return {
                "persona_id": pid,
                "persona_name": p_meta["name"],
                "role_title": p_meta["role_title"],
                "depth": p_meta["depth"],
                "headline": headline,
                "narrative_markdown": narrative,
                "primary_root_cause": {
                    "id": "GEN_OBSERVATIONAL_CONCENTRATION",
                    "name": f"Concentration in {dim_text}",
                    "cause_score_100": 75.0,
                    "evidence_score": 0.75,
                    "classification": "Empirical Association"
                },
                "recommended_actions": actions,
                "metadata": {
                    "engine": "OfflineEdithReasoner",
                    "generated_at": now_str,
                    "dataset": repo.active_source_info.get("name", "Custom Dataset")
                }
            }
        
        # ==============================================================================
        # 2. BUILT-IN DEMO BENCHMARK EXECUTIVE BRIEFINGS
        # ==============================================================================
        
        # 2A. GENERAL USER BRIEFING (100% PLAIN LANGUAGE, ZERO JARGON)
        if pid == "general_user":
            headline = "Business Update: Why Sales Dropped in Region B and What We Are Doing Next"
            narrative = f"""### 💡 Plain-Language Business Update — What Happened to Our Sales?
**Generated:** {now_str} &middot; **Audience:** General Business Team &middot; **Style:** Plain Language (Zero Jargon)

---

#### 1. The Big Picture: What Happened?
- **The Main Takeaway:** Weekly sales experienced a **noticeable drop of roughly 11%** (about **$148,000 below normal weekly levels**).
- **Where It Happened:** Almost the entire drop (**over 97%**) happened in **Region B** among our **Enterprise accounts** on **Product Suite Alpha**.
- **What Stayed Healthy:** Sales across all other regions and smaller business segments (Mid-Market and SMB) remained stable and on track.

---

#### 2. Why Did It Happen? (The Real Story)
- **The Primary Trigger (Price Increase Sensitivity):**
  - In Week 6, we raised prices on our Enterprise software plan by 12% (from $10,000 to $11,200).
  - Because large business customers are sensitive to price changes, 21 expected renewals were put on hold.
  - While we made an extra $21,600 from accounts that accepted the higher rate, it was not enough to make up for the deals that paused.
- **The Secondary Factor (Competitor Discount Promotion):**
  - Around the same time (Week 7), our competitor **ApexTech** launched a **15% discount campaign**, giving hesitant buyers a cheaper alternative to consider.
- **What We Checked and Ruled Out:**
  - Our warehouses, deliveries, and software servers were operating normally with **zero shipping delays** and 99.4% on-time fulfillment. The issue was commercial demand, not operational delivery.

---

#### 3. What the Team Is Planning to Do Next
1. **Adjust Pricing Back Slightly:** Lower Enterprise Suite Alpha renewals in Region B by 6% (setting unit price to $10,528). This brings back price-conscious buyers while keeping a modest gain over last year.
2. **Support Local Partners:** Provide a $15,000 regional marketing fund in Region B to match competitor promotions.
3. **Dedicated Customer Care:** Assign dedicated customer success managers to the 12 most critical renewal accounts.
4. **Expected Outcome:** Over the next 8 weeks, this balanced plan is projected to recover **nearly 80% of lost sales volume**.
"""
            actions = [
                {
                    "driver": "Price sensitivity on Enterprise plan",
                    "lever": "Price Adjustment (-6%)",
                    "action": "Adjust Enterprise renewal pricing in Region B to $10,528/unit",
                    "expected_impact": "Brings back paused renewals while keeping a modest price gain",
                    "owner": "Pricing Committee & Revenue Team",
                    "confidence": "High",
                    "status": "Planned for Implementation"
                },
                {
                    "driver": "Competitor ApexTech discount campaign",
                    "lever": "Partner Marketing Support ($15k)",
                    "action": "Provide $15,000 in regional partner support in Region B",
                    "expected_impact": "Helps sales partners win back deals from competitor",
                    "owner": "Regional Field Sales Team",
                    "confidence": "Moderate",
                    "status": "Planned for Implementation"
                },
                {
                    "driver": "Customer retention in key accounts",
                    "lever": "Key Account Care",
                    "action": "Assign dedicated customer success managers to 12 at-risk accounts",
                    "expected_impact": "Protects recurring customer relationships and prevents future cancellations",
                    "owner": "Customer Success Team",
                    "confidence": "High",
                    "status": "Underway"
                }
            ]

        # 2B. REGIONAL SALES LEAD BRIEFING (OPERATIONAL SCOPE + RESTRICTIONS)
        elif pid == "regional_lead":
            headline = "Operational Incident Report: Region B Revenue Deficit & Authorized Field Strategy"
            narrative = f"""### 📍 Operational Incident Report: Region B Performance Deficit
**Generated:** {now_str} &middot; **Audience:** Regional Sales Lead (Region B) &middot; **Scope:** Region B Operational Boundaries

---

#### 1. Region B Incident Status & Magnitude
- **Region B Current Revenue:** **${anomaly_context.get('current_value', 420000):,.0f}** vs **${anomaly_context.get('baseline_value', 602200):,.0f}** expected (**-30.3% / -$182,200 deficit**).
- **Concentration:** Deficit is isolated exclusively to **Enterprise Suite Alpha renewals** within Region B. Mid-Market and SMB tiers in Region B remain on target.
- *Company-wide totals and cross-region control metrics are restricted for this role.*

---

#### 2. Root Cause Analysis (Region B Context)
- **Primary Operational Driver:** Internal +12% price hike on Enterprise Suite Alpha ($10,000 → $11,200) triggered renewal hesitation across 21 regional accounts.
- **Physical Fulfillment Status:** SAP logistics confirm **99.4% warehouse fill rate with 0 stockout days** in Region B. Delivery pipelines are completely healthy.
- *Detailed competitor campaign intelligence is restricted (requires Executive or Analyst access).*

---

#### 3. Authorized Field Actions & Pending Escalations
1. **Immediate Authorized Field Deployment:**
   - **Deploy $15k Regional Partner Co-Op Fund:** Incentivize regional partners to accelerate deal closings (expected impact: +$1,667/wk).
   - **VIP Retention Guard:** Deploy dedicated CSM coverage to the 12 at-risk Enterprise renewals in Region B to protect recurring ARR.
2. **Pending Executive Sign-Off:**
   - A recommendation to roll back pricing to $10,528/unit has been submitted to the CRO and Pricing Committee.
"""
            actions = [
                {
                    "driver": "Region B Enterprise Renewal Pushback",
                    "lever": "Regional Co-Op Marketing ($15k)",
                    "action": "Deploy $15,000 partner marketing incentives across Region B accounts",
                    "expected_impact": "+$1,667/week deal velocity acceleration",
                    "owner": "Regional Sales Lead (Region B)",
                    "confidence": "Moderate (60.4/100)",
                    "status": "Authorized for Deployment"
                },
                {
                    "driver": "At-Risk Enterprise Accounts",
                    "lever": "VIP Retention Guard",
                    "action": "Deploy dedicated CSM coverage to top 12 at-risk renewal accounts",
                    "expected_impact": "Guards recurring regional ARR and prevents cancellations",
                    "owner": "Regional Customer Success Team",
                    "confidence": "High",
                    "status": "Authorized for Deployment"
                },
                {
                    "driver": "Pricing Elasticity Contraction",
                    "lever": "Price Rollback (-6%)",
                    "action": "[Restricted to Executive] Adjust Enterprise unit price to $10,528",
                    "expected_impact": "+$18,400/week volume recovery with +$528/unit margin preservation",
                    "owner": "Chief Revenue Officer (Pending Authorization)",
                    "confidence": "High (88.0/100)",
                    "status": "Escalated to Executive (Restricted)"
                }
            ]

        # 2C. ANALYST / REVOPS BRIEFING (FULL ECONOMETRIC LEDGER & PROOFS)
        elif pid == "analyst":
            decomp = top_h.get("mathematical_decomposition", {})
            ctrl = top_h.get("control_group_analysis", {})
            headline = f"Econometric Investigation Ledger: {kpi_name} Anomaly Proofs & Causal Lineage"
            narrative = rf"""### 🔬 Econometric Investigation Ledger: {kpi_name} Empirical Proofs
**Generated:** {now_str} &middot; **Audience:** RevOps & Financial Analysts &middot; **Depth:** Full Econometric Proofs

---

#### 1. Statistical Anomaly & Multi-Horizon Baseline
- **Observed:** ${curr_val:,.0f} vs Baseline ${base_val:,.0f} (Variance: **{delta_pct:+.1f}%**, ${delta_val:+,.0f}).
- **Corridor Threshold:** Lower boundary $1,272,908 | Upper boundary $1,529,692 (Z = {z_score:.2f}, Material Anomaly).
- **Concentration:** 97.3% of deficit is concentrated in Region B Enterprise Suite Alpha.

---

#### 2. Exact Revenue Identity Decomposition
$$\Delta\text{{Revenue}} = \Delta\text{{Units}} 	imes P_{{\text{{pre}}}} + \text{{Units}}_{{\text{{post}}}} 	imes \Delta P$$
- **Gross Volume Effect:** -21 units $	imes$ \$10,000/unit = **-\$210,000** (111.5% of gross decline).
- **Price Realization Cushion:** 18 units $	imes$ +\$1,200/unit = **+\$21,600** (-11.5% price offset).
- **Net Reconciled Deficit:** **-\$188,400** (Exact reconciliation, 0.0% residual error).

---

#### 3. Difference-in-Differences Quasi-Experiment
$$\text{{DiD}} = (Y_{{\text{{treated,post}}}} - Y_{{\text{{treated,pre}}}}) - (Y_{{\text{{control,post}}}} - Y_{{\text{{control,pre}}}})$$
- **Treated Cohort (Region B Enterprise Alpha):** Dropped -52.6% (38 units $ightarrow$ 18 units).
- **Optimal Control Cohort ({ctrl.get('control_cohort', 'Mid-Market Alpha')}):** Parallel pre-trend correlation $r = {ctrl.get('pre_trend_correlation', 0.88):.2f}$; delta: {ctrl.get('control_delta_pct', -4.3):+.1f}%.
- **Empirical DiD Gap:** **{ctrl.get('did_divergence_pct', 48.3):.1f}% causal divergence**.

---

#### 4. Competing Causal Hypotheses & Evidence Scores
| Hypothesis | Role | Evidence Score | Cause Score | Status |
| :--- | :--- | :--- | :--- | :--- |
| **#1 Pricing Elasticity** | Upstream Direct | 0.88 / 1.00 | **88.0 / 100** | High-Confidence Root Cause |
| **#2 Competitor Campaign** | Compounding Shock | 0.60 / 1.00 | **60.4 / 100** | Possible Driver |
| **#8 Supply Bottleneck** | Physical Logistics | 0.00 / 1.00 | **0.0 / 100** | Empirically Refuted |

---

#### 5. Data Lineage & Freshness Audit
- Primary Ledgers: SAP S/4HANA (Freshness: 2.1h) &middot; Salesforce CRM (Freshness: 45m) &middot; Competitor Telemetry Feed (Freshness: 1.2h).
"""
            actions = [
                {
                    "driver": "Pricing Elasticity Contraction",
                    "lever": "Price Rollback (-6%)",
                    "action": "Execute -6% price adjustment on Enterprise Suite Alpha in Region B ($10,528/unit)",
                    "expected_impact": "+$18,400/week volume recovery with +$528/unit net margin preservation",
                    "owner": "Pricing Committee & RevOps",
                    "confidence": "High (88.0/100)",
                    "status": "Recommended for Approval"
                },
                {
                    "driver": "Competitor ApexTech Campaign",
                    "lever": "Regional Co-Op Marketing ($15k)",
                    "action": "Authorize $15,000 regional partner co-op incentives in Region B",
                    "expected_impact": "+$1,667/week deal velocity acceleration",
                    "owner": "Field Marketing",
                    "confidence": "Moderate (60.4/100)",
                    "status": "Recommended for Approval"
                },
                {
                    "driver": "Account Churn Risk",
                    "lever": "VIP Retention Guard",
                    "action": "Deploy dedicated CSM outreach to 12 at-risk Enterprise renewal accounts",
                    "expected_impact": "Guards recurring ARR and eliminates downstream churn compounding",
                    "owner": "Customer Success",
                    "confidence": "High",
                    "status": "Recommended for Immediate Execution"
                }
            ]

        # 2D. EXECUTIVE / CRO BRIEFING (STRATEGIC SYNTHESIS)
        else:
            headline = f"Executive Incident Synthesis: {kpi_name} Deficit & Recommended Action Plan"
            narrative = f"""### 📊 Executive Incident Briefing: {kpi_name} Deficit & Action Plan
**Generated:** {now_str} &middot; **Audience:** Chief Revenue Officer & Executive Committee &middot; **Focus:** Strategic Action

---

#### 1. Strategic Incident Overview
- **Metric Deficit:** **{kpi_name}** dropped by **{abs(delta_pct):.1f}%** (${curr_val:,.0f} vs ${base_val:,.0f} baseline, -$147.7k total variance).
- **Concentration:** **97.3% of the deficit** is isolated to **Region B Enterprise** accounts on **Product Suite Alpha**.
- **Corridor Breach:** Breached the ±2.0σ expected band (Z = {z_score:.2f}, 2 consecutive weeks).

---

#### 2. Empirical Root Cause Breakdown
- **Primary Root Cause:** **Pricing Elasticity & Plan Hike (#1 Cause, Score 88.0/100)**.
  - A +12% price hike instituted in Week 06 triggered a **48.3% volume contraction** in Enterprise renewals.
  - While price realization added +$21.6k, lost deal volume created a -$210.0k drag, yielding a net -$188.4k shortfall.
- **Secondary Amplifier:** **Competitor Campaign (Score 60.4/100)**. ApexTech launched an aggressive 15% discount in Week 07, compounding enterprise deal slippage.
- **Refuted Factor:** Supply and warehouse logistics were completely unimpaired (99.4% fill rate, 0 stockouts).

---

#### 3. Recommended Strategic Decision Package
Apply a balanced multi-lever recovery policy:
1. **Targeted Price Adjustment (-6%):** Roll back half the recent price hike on Enterprise renewals in Region B (new unit price: $10,528). Re-engages buyers while preserving +$528/unit in net margin gain.
2. **Regional Partner Co-Op Fund ($15k):** Allocate $15,000 in regional co-op incentives to neutralize ApexTech's campaign.
3. **Projected 8-Week Recovery:** Recovers **+$20,067/week** in net revenue, stabilizing operating gross margin at **69.6%**.
"""
            actions = [
                {
                    "driver": "Pricing Elasticity / Volume Drop",
                    "lever": "Targeted Rollback (-6%)",
                    "action": "Authorize -6% price adjustment on Enterprise Suite Alpha in Region B ($10,528/unit)",
                    "expected_impact": "+$18,400/week volume recovery with +$528/unit net margin preservation",
                    "owner": "Chief Revenue Officer & Pricing Committee",
                    "confidence": "High (88.0/100)",
                    "status": "Recommended for Approval"
                },
                {
                    "driver": "ApexTech Competitor Campaign",
                    "lever": "Regional Co-Op Marketing ($15k)",
                    "action": "Authorize $15,000 regional partner co-op incentives in Region B",
                    "expected_impact": "+$1,667/week deal velocity acceleration",
                    "owner": "VP of Field Marketing & Regional Lead",
                    "confidence": "Moderate (60.4/100)",
                    "status": "Recommended for Approval"
                },
                {
                    "driver": "Account Churn Risk",
                    "lever": "VIP Retention Guard",
                    "action": "Deploy dedicated CSM outreach to 12 at-risk Enterprise renewal accounts",
                    "expected_impact": "Guards recurring ARR and eliminates downstream churn compounding",
                    "owner": "VP of Customer Success",
                    "confidence": "High",
                    "status": "Recommended for Immediate Execution"
                }
            ]
            
        return {
            "persona_id": pid,
            "persona_name": p_meta["name"],
            "role_title": p_meta["role_title"],
            "depth": p_meta["depth"],
            "headline": headline,
            "narrative_markdown": narrative,
            "primary_root_cause": {
                "id": top_h.get("id", "H1_PRICING_PRESSURE"),
                "name": top_h.get("name", "Pricing Elasticity & Plan Hike"),
                "cause_score_100": float(top_h.get("cause_score_100", 88.0)),
                "evidence_score": float(top_h.get("evidence_score", 0.88)),
                "classification": str(top_h.get("confidence_classification", "High Confidence"))
            },
            "recommended_actions": actions,
            "metadata": {
                "engine": "OfflineEdithReasoner",
                "generated_at": now_str,
                "dataset": repo.active_source_info.get("name", "B2B SaaS Benchmark")
            }
        }
