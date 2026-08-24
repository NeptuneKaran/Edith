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
|                                DETERMINISTIC ANALYTICAL ENGINE (Python)                            |
|  • Rolling 8-Week Baseline & Robust IQR Expected Corridor (±2.0σ)                                  |
|  • Materiality & Temporal Persistence Filters                                                      |
|  • Multi-Dimensional Variance Decomposition (Region → Customer Tier → Product → Channel)           |
|  • Time-Lagged Cross-Correlation (τ) & Difference-in-Differences (DiD) Cohort Testing               |
|  • Deterministic Composite Evidence Score Engine [0.0, 1.0]                                        |
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
|  • Explicitly Highlights Contradictory Evidence & Calibrated Uncertainty                           |
|  • Answers Follow-up Questions Strictly Using Verified Facts                                       |
|  • Seamless Fallback: Live Google GenAI ↔ Deterministic Offline Reasoner                           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
|                                  STREAMLIT INVESTIGATION WORKSPACE                                 |
|  Screen 1: Overview  →  Screen 2: Diagnostic  →  Screen 3: Workspace  →  Screen 4: Simulation     |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. The 7-Stage Investigation Workflow

Edith replaces passive dashboard monitoring with an active, progressive investigation workflow:

1. **OBSERVE (Screen 1)**: Scan executive scorecards across connected KPIs (Revenue, Margin, Churn, ROAS).
2. **DETECT (Screen 1 & 2)**: Identify statistically significant breaches outside the rolling $\pm 2.0\sigma$ corridor that meet business materiality ($\ge 5\%$ drop, $\ge \$50\text{k}$) and persistence ($\ge 2$ weeks).
3. **INVESTIGATE (Screen 2)**: Decompose variance down the dimensional hierarchy to isolate the geographic, customer tier, and product epicenter.
4. **EVIDENCE (Screen 3 - Left Pane)**: Evaluate candidate hypotheses against empirical data; verify temporal lead times, run Difference-in-Differences against control cohorts, and compile supporting vs. contradictory ledgers.
5. **EXPLAIN (Screen 3 - Right Pane)**: Synthesize findings into clear executive briefings with interactive Q&A and cited evidence tags.
6. **SIMULATE (Screen 4)**: Adjust controllable business levers (price adjustments, promo funds) and simulate 8-week counterfactual recovery trajectories.
7. **ACT (Screen 4)**: Export an auditable decision package with assigned ownership and monitoring milestones.

---

## 3. Epistemological Distinction: Data vs. Assumption vs. Simulation

To guarantee clarity, every number displayed in EDITH is explicitly categorized:
- **DATA-DERIVED**: Empirically computed from source data (e.g., *Gross Revenue dropped 10.5% from $1,401,300 to $1,253,600*, *$Z = -2.30$*, *Region B accounts for 97.3% of variance*, *CRM complaints jumped to 38/week*).
- **MODEL ASSUMPTION**: Parametric constants defined in governed configuration (e.g., *Enterprise Price Elasticity $\varepsilon_p = -1.65$*, *Marketing Response Coefficient $\beta_m = 0.25$*, *Adoption Lag $\tau = 2$ weeks*).
- **SIMULATED**: Counterfactual outputs computed by the simulation model (e.g., *Projected revenue recovery under a 6% price adjustment*).

---

## 4. Deterministic Analytical Engine

### A. Dynamic Expected Corridor & Anomaly Detection
To establish what is "abnormal", EDITH computes a rolling 8-week robust median baseline ($\hat{y}_t$) and calculates standard error from the Interquartile Range ($IQR$):
$$\hat{\sigma} = \frac{IQR(\text{residuals})}{1.349}$$
$$\text{Expected Corridor}_t = \left[ \hat{y}_t - 2.0 \cdot \hat{\sigma}, \quad \hat{y}_t + 2.0 \cdot \hat{\sigma} \right]$$
A point is flagged as a **P1 Material Anomaly** if:
1. $|Z_t| \ge 2.0$ ($Z = -2.30$)
2. $|\Delta\%| \ge 5.0\%$ ($-10.5\%$) or $|\Delta \$| \ge \$50,000$ ($-\$147,700$)
3. Breach persists for $\ge 2$ consecutive recording cycles.

### B. Multi-Dimensional Contribution Slicing
For total drop $\Delta Y = Y_t - Y_{\text{baseline}}$, each slice $i$ within dimension $D$ contributes:
$$\text{Contribution Share}_i = \frac{y_{i, t} - y_{i, \text{baseline}}}{\Delta Y} \times 100\%$$
Identifies that Region B accounts for $97.3\%$ of the variance, Enterprise Tier accounts for $97.3\%$, and Product Suite Alpha accounts for $100.0\%$.

---

## 5. Interpretable Composite Evidence Score

The **Evidence Score** $S(H_k) \in [0.0, 1.0]$ is a deterministic ranking metric:

$$S(H_k) = \text{clamp}_{[0.0, 1.0]} \left( w_T \cdot T_k + w_E \cdot E_k + w_C \cdot C_k - w_D \cdot D_k \right) \times Q_k$$

Where weights are centralized in `config/settings.py` ($w_T = 0.25, w_E = 0.35, w_C = 0.40, w_D = 0.45$):
- **Temporal Precedence ($T_k$)**: $1.0$ if driver shock occurred 1–3 weeks before the drop; $0.5$ if simultaneous; $0.0$ if after.
- **Effect & Control Alignment ($E_k$)**: Normalized Difference-in-Differences vs. unaffected control cohort.
- **Corroborating Signals ($C_k$)**: Proportion of independent verifying signals (CRM complaint surges, win/loss notes).
- **Contradictory Penalty ($D_k$)**: Heavy penalty for empirical facts refuting the hypothesis (e.g., warehouse fill rate was $99.4\% \rightarrow D = 0.95$, dropping inventory score to $0.00$).
- **Data Quality Multiplier ($Q_k$)**: Discounts score if data is stale or sample size is small ($N < 30$).

---

## 6. LLM Boundary & Offline Fallback Architecture

### Strict LLM Boundaries:
- The LLM **never** performs math, calculates statistics, or estimates parameters.
- The LLM **never** invents hypothetical events or alters Evidence Scores.
- All numbers, dates, and evidence facts are passed as structured JSON in the prompt.
- If information is missing from the analytical state, the LLM is instructed to state that it is unavailable.

### Deterministic Offline Reasoner:
If no `GEMINI_API_KEY` is provided or if network connectivity is absent, `ai/llm_client.py` seamlessly switches to `OfflineEdithReasoner`. This module deterministically formats the exact verified analytical findings, ensuring **100% demo reliability** during live evaluation.

---

## 7. Parametric Scenario Simulation Model

The simulation engine models counterfactual interventions on the affected cohort:
$$\hat{Q}_{\text{region}} = Q_{\text{current}} \times \left( 1 + |\varepsilon_p| \cdot \frac{|\Delta P\%|}{100} + \beta_m \cdot \ln\left(1 + \frac{\Delta M}{M_0}\right) \right) \times \gamma_{\text{comp}}$$
$$\text{Simulated Total Revenue} = \text{Unaffected Revenue} + (\hat{Q}_{\text{region}} \times P_{\text{new}})$$
$$\text{Recovery \%} = \min\left(100\%, \frac{\text{Simulated Revenue} - \text{Current Revenue}}{\text{Baseline Revenue} - \text{Current Revenue}} \times 100\%\right)$$

---

## 8. Streamlit State Management

All state transitions are persisted in `st.session_state`:
- `st.session_state.current_screen`: Controls active view (`overview`, `diagnostic`, `workspace`, `simulation`).
- `st.session_state.selected_kpi_id`: Tracks the inspected KPI (`kpi_b2b_sales`, `kpi_gross_margin`, etc.).
- `st.session_state.anomaly_context`: Stores current $Z$-score, baseline values, and breach status.
- `st.session_state.hypotheses`: Stores evaluated candidate causes with Evidence Scores and ledgers.
- `st.session_state.selected_hypothesis_id`: Tracks the currently inspected hypothesis card.
- `st.session_state.chat_history`: Stores multi-turn user/Edith dialogue.
- `st.session_state.simulation_levers`: Retains slider settings across screen transitions.

---

## 9. How to Run the Application

```bash
# 1. Run automated analytical verification tests
python tests/test_analytics.py
python tests/test_llm_fallback.py
python tests/audit_numbers.py

# 2. Launch the Streamlit application
streamlit run app.py
```
Open `http://localhost:8501` in your browser.
