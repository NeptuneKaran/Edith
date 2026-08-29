# EDITH: Architecture & Technical Guide (How It Works)
**Accenture Innovation Challenge 2026 — Problem Track 3: BusinessIntelligence.ai**

---

## 1. Overall System Architecture

EDITH is an **evidence-grounded KPI intelligence and investigation system**. Its core innovation is an architectural firewall separating **deterministic quantitative analytics** from **downstream cognitive language synthesis**:

```
+----------------------------------------------------------------------------------------------------+
|                                           DATA LAYER                                               |
|  - 52-Week Relational Sales Mart (ERP / CRM / Inventory / Competitor / Feedback)                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
|                         DETERMINISTIC CAUSAL & ANALYTICAL ENGINE (Python)                          |
|  • Rolling 8-Week Baseline & Robust IQR Expected Corridor (±2.0σ)                                  |
|  • Materiality & Temporal Persistence Anomaly Filters                                              |
|  • Dimensional Variance Localization (Region → Customer Tier → Product → Channel)                  |
|  • Metric Dependency DAG (Upstream Policy → Volume Driver → Target Anomaly → Downstream Effect)   |
|  • Exact Mathematical Identity Decomposition (Revenue = Units Sold × Unit Price)                   |
|  • Empirical Prediction Verification (SUPPORTED / CONTRADICTED / NOT_TESTABLE)                     |
|  • Directional Consistency Validation (Theoretical Domain Signs)                                  |
|  • Historical Lagged Cross-Correlation (L0..L4: Best Lag τ and Strength |r|)                      |
|  • Data-Driven Control Group Selection (Similarity Scoring & Unexposed Validation)                 |
|  • Pre-Trend Parallel Trend Validation (Linear Slope Divergence Δβ across W01–W48)                |
|  • Temporal Sequence & Lead-Time Window Enforcement (τ in [1, 3] weeks)                            |
|  • External Confounder Detection & Penalty Allocation (ApexTech Rebate Overlap)                    |
|  • 7-Component Cause Evidence Score Engine [0–100 & 0.0–1.0] with Confidence Classification       |
|  • Parametric What-If Scenario Simulation Engine                                                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                Structured JSON Evidence State
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
|                                  EDITH REASONING LAYER (LLM / Offline)                             |
|  • Ingests Structured Analytical JSON (Source of Truth)                                            |
|  • Translates Ledgers into Plain-Language Diagnostic Briefings                                     |
|  • Explicitly Highlights Mathematical Attribution, Lag Relationships & Counter-Evidence            |
|  • Distinguishes Upstream Drivers from Downstream Effects (e.g. Margin Compression)                |
|  • Answers Follow-up Questions Strictly Using Verified Facts (No Arithmetic Hallucinations)        |
|  • Seamless Fallback: Live Google GenAI ↔ Deterministic Offline Reasoner                           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
|                             FASTAPI & ALPINE.JS INVESTIGATION DASHBOARD                            |
|  Screen 0: Data Sources  →  Screen 1: Overview  →  Screen 2: Diagnostic  →  Screen 3: Workspace   |
|  Screen 4: Simulation    →  Screen 5: Conversational Console                                       |
+----------------------------------------------------------------------------------------------------+

```

---

## 2. How EDITH Determines Root Cause (The 11-Stage Engine)

Rather than naively treating co-occurring abnormal metrics as causes (correlation $\neq$ causation), EDITH executes an 11-stage causal investigation process:

```
[1. Anomaly Detection]
       ↓
[2. Candidate Driver Generation (DAG & Catalog)]
       ↓
[3. Temporal Precedence & Lead-Time Analysis]
       ↓
[4. Magnitude & Effect Size Analysis]
       ↓
[5. Directional Consistency Validation]
       ↓
[6. Historical Lagged Cross-Correlation]
       ↓
[7. Metric Dependency & Structural Role]
       ↓
[8. Mathematical Identity Decomposition]
       ↓
[9. Counter-Evidence & Confounder Penalties]
       ↓
[10. Confidence Classification]
       ↓
[11. LLM & Offline Explanation Synthesis]
```

### Stage 1: Anomaly Detection
Computes an 8-week rolling median baseline ($\hat{y}_t$) and robust Interquartile Range ($IQR$) corridor:
$$\hat{\sigma} = \frac{IQR(\text{residuals})}{1.349}$$
$$\text{Expected Corridor}_t = \left[ \hat{y}_t - 2.0\hat{\sigma}, \quad \hat{y}_t + 2.0\hat{\sigma} \right]$$
A breach is flagged as a **P1 Material Anomaly** if $|Z_t| \ge 2.0$ ($Z = -2.30$), $|\Delta\%| \ge 5.0\%$ ($-10.5\%$), $|\Delta \$| \ge \$50\text{k}$, and persists for $\ge 2$ consecutive cycles.

### Stage 2: Candidate Driver Generation
Traverses the `MetricDependencyGraph` and candidate hypothesis catalog ($H_1 \dots H_8$) across commercial strategy, customer sentiment, external market, supply chain, and engineering quality.

### Stage 3: Temporal Precedence Analysis
Calculates driver onset week $t_{\text{driver}}$ relative to anomaly onset $t_{\text{target}}$:
- Lead time $\tau \in [1, 3]$ weeks: Scored **$95 - 100$** (Optimal enterprise purchasing lead-time).
- Simultaneous movement ($\tau = 0$): Scored **$60$** (Concurrent / ambiguous).
- Post-anomaly movement ($\tau < 0$): Heavily penalized to **$10$** (cannot cause a past event).

### Stage 4: Magnitude & Effect Size Analysis
Computes normalized deviation $|\Delta\%| / (\sigma/\mu)$ and $Z$-score. Enterprise Alpha volume fell $-48.3\%$ ($Z \approx -4.2$), receiving maximum magnitude weight ($96.6/100$).

### Stage 5: Directional Consistency Validation
Verifies whether observed movement matches theoretical domain signs:
- Price $\uparrow \implies$ Volume $\downarrow$ (Consistent with negative demand elasticity: Score **$100$**).
- Complaints $\uparrow \implies$ Win Rate $\downarrow$ (Score **$100$**).
- Inconsistent directions are penalized to **$15$**.

### Stage 6: Historical Lagged Cross-Correlation
Computes Pearson cross-correlation across lags $k \in [0, 1, 2, 3, 4]$ over pre-shock window (Weeks 1–48):
$$r_k = \text{Corr}(X_{t-k}, Y_t)$$
Identifies `best_lag` ($\tau = 2$ weeks), `lag_strength` ($|r| = 0.85$), and `lag_direction` (`+`).

### Stage 7: Metric Dependency Structure (DAG)
Classifies candidate roles in the metric graph:
- `UPSTREAM_DIRECT`: Direct mathematical components (Units Sold, List Price) $\implies$ Score **$100$**.
- `UPSTREAM_INDIRECT`: Customer sentiment, defect tickets $\implies$ Score **$85$**.
- `EXTERNAL_FACTOR`: Competitor campaigns, macro indices $\implies$ Score **$85$**.
- `DOWNSTREAM_EFFECT`: Metrics impacted *by* the target (Gross Margin, Net Profit) $\implies$ Score **$10$** and categorized as consequences, not causes.

### Stage 8: Mathematical Identity Decomposition
Where mathematical formulas exist, exact dollar contributions are computed:
$$\Delta \text{Revenue} = (\text{Units}_{\text{post}} - \text{Units}_{\text{pre}}) \cdot \text{Price}_{\text{pre}} + \text{Units}_{\text{post}} \cdot (\text{Price}_{\text{post}} - \text{Price}_{\text{pre}})$$
$$\Delta \text{Revenue} = \text{Volume Effect} + \text{Price Effect}$$

### Stage 9: Counter-Evidence & Confounders
Actively checks for falsifying facts:
- Control group stability in un-hiked Mid-Market accounts ($0.0\%$ delta) proves specificity.
- Warehouse fill rate of $99.4\%$ and 0 stockout days directly refutes inventory bottlenecks (Score: $0.0/100$).
- Overlapping shocks (ApexTech discount in Week 07) apply a $-12.0$ confounder penalty.

### Stage 10: Cause Evidence Score & Confidence Classification
$$\text{Base Score} = w_{\text{temp}} S_{\text{temp}} + w_{\text{mag}} S_{\text{mag}} + w_{\text{dir}} S_{\text{dir}} + w_{\text{hist}} S_{\text{hist}} + w_{\text{dep}} S_{\text{dep}} + w_{\text{contrib}} S_{\text{contrib}}$$
$$\text{Final Cause Score} = \text{clamp}_{[0, 100]} \Big( \text{Base Score} - w_{\text{counter}} P_{\text{counter}} - w_{\text{conf}} P_{\text{conf}} - w_{\text{pre}} P_{\text{pre}} \Big) \times Q$$
- **`HIGH-CONFIDENCE DRIVER`** ($\ge 75$): Upstream structural driver with verified lead-time, high contribution, and corroboration.
- **`POSSIBLE DRIVER`** ($50 - 74$): Secondary/external factor (Competitor Campaign).
- **`CORRELATED SIGNAL`** ($25 - 49$): Co-moving metric without proven mechanism.
- **`DOWNSTREAM EFFECT`**: Financial consequences (Gross Margin / Profit).
- **`REFUTED BY DATA`**: Contradicted by empirical facts (Inventory).
- **`NOT TESTABLE`**: Missing required telemetry (Partner Commissions).

### Stage 11: LLM & Offline Explanation Synthesis
Deterministic Python analytics passes the structured JSON object to the LLM (or Offline Reasoner), which produces plain-language briefings with verified numbers and zero hallucinations.

---

## 3. Concrete Worked Example (Actual EDITH Dataset)

### Target Anomaly:
- **Metric**: Monthly B2B Sales (`gross_revenue`)
- **Observed Shock**: Dropped from expected $\$1,401,300$ to $\$1,253,600$ ($-10.5\%$, $-\$147,700$, $Z = -2.30$).
- **Locus**: Region B Enterprise accounts purchasing Product Suite Alpha ($97.3\%$ of total decline).

### Evaluation of Top Candidate: `H1_PRICING_PRESSURE`
1. **Temporal Precedence**: List price increased $+12\%$ in Week 06 ($t=49$), anomaly detected in Week 08 ($t=51$) $\implies \tau = 2$ weeks ($S_{\text{temp}} = 95.0$).
2. **Magnitude**: Enterprise volume dropped from $39 \to 18$ units ($-48.3\%$) ($S_{\text{mag}} = 96.6$).
3. **Directional Consistency**: Price up $\implies$ volume down ($S_{\text{dir}} = 100.0$).
4. **Historical Lag Correlation**: CRM pricing complaints show strong lag correlation with deal conversion ($S_{\text{hist}} = 85.0$).
5. **Dependency DAG**: Unit Price and Volume are direct upstream inputs to Gross Revenue ($S_{\text{dep}} = 100.0$).
6. **Mathematical Decomposition**:
   $$\Delta \text{Revenue} = (18 - 39) \times \$10,000 + 18 \times (\$11,200 - \$10,000)$$
   $$\Delta \text{Revenue} = -\$210,000 \text{ (Volume Effect)} + \$21,600 \text{ (Price Effect)} = -\$188,400$$
   - Volume contraction explains **$111.5\%$** of gross revenue loss, cushioned by **$+\$21,600$** from higher prices on retained contracts ($S_{\text{contrib}} = 95.0$).
7. **Control Cohort & Pre-Trends**:
   - Selected Control: `Region B Mid-Market Product Suite Alpha` (Similarity: $0.85$).
   - Difference-in-Differences divergence: $48.3\%$ ($0.0\%$ control vs $-48.3\%$ treated).
   - Pre-trend slope divergence: $\Delta\beta = 0.00027$ (Parallel pre-trends validated).
8. **Confounder Penalty**: ApexTech 15% discount campaign launched in Week 07 ($-12.0$ penalty).
9. **Final Cause Score**:
   $$\text{Base Score} = 0.20(95) + 0.15(96.6) + 0.15(100) + 0.20(85) + 0.15(100) + 0.15(95) = 94.7$$
   $$\text{Net Score} = 94.7 - 0.50(5.0) - 0.20(12.0) - 0.20(0.0) = 89.8$$
   $$\text{Final Score} = 89.8 \times 0.98 = \mathbf{88.0 / 100} \quad (\text{Evidence Index: } \mathbf{0.88 / 1.00})$$
   - **Classification**: **`HIGH-CONFIDENCE DRIVER`** (Rank 1).

---

## 4. Epistemological Distinction: Data vs. Assumption vs. Simulation

To guarantee clarity, every number displayed in EDITH is explicitly categorized:
- **DATA-DERIVED**: Empirically computed from source data (e.g., *Revenue dropped $10.5\%$, $Z = -2.30$, volume explains $111.5\%$ of decline, CRM complaints jumped to $38/\text{wk}$*).
- **MODEL ASSUMPTION**: Parametric constants defined in governed configuration (e.g., *Enterprise Price Elasticity $\varepsilon_p = -1.65$, Marketing Response Coefficient $\beta_m = 0.25$*).
- **SIMULATED**: Counterfactual outputs computed by the simulation model (e.g., *Projected revenue recovery under a 6% price rollback*).
- **EVIDENCE STRENGTH**: Calibrated composite index ($0 - 100$) measuring empirical support without claiming absolute causal certainty.

---

## 5. Zero-Downtime LLM Gateway & Offline Resilience

- **Live Mode**: Uses `@google/genai` with `gemini-2.5-flash` or `gemini-1.5-flash` when `GEMINI_API_KEY` is present.
- **Offline Mode**: Uses `OfflineEdithReasoner` directly in Python when no API key is provided or if network fails.
- **Zero Hallucination Guarantee**: Both live LLM and offline reasoner receive structured analytical JSON containing verified facts, predictions, control metrics, and pre-trend statistics. No numbers are generated by the LLM.

---

## 6. Cloud Deployment (Render)

EDITH is packaged for single-click deployment on Render:
- **Port Binding**: Respects Render's `$PORT` environment variable and binds to `0.0.0.0`.
- **Runtime**: Tested and certified for `python-3.11.9`.
- **Zero Secrets Required**: Works out of the box with built-in deterministic reasoning.
