# EDITH: AI-Assisted Business Intelligence Investigation System
**Accenture Innovation Challenge 2026 — Problem Track 3: BusinessIntelligence.ai**

Developed by **Team IIT Kanpur** (Chhavi Tanwar & Karan Kosta)

---

## 🎯 Executive Summary
Conventional Business Intelligence dashboards show **what happened** (e.g., *Monthly B2B Sales dropped 10.5% in Region B*), but leave the critical questions—**why did it happen?**, **what evidence supports that?**, and **what should we do next?**—to days of manual analyst drill-downs.

**EDITH** is an evidence-grounded KPI intelligence and investigation system that enforces an explicit analytical chain:
$$\text{OBSERVE} \longrightarrow \text{DETECT} \longrightarrow \text{LOCALIZE} \longrightarrow \text{INVESTIGATE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{SIMULATE} \longrightarrow \text{ACT}$$

Unlike generic chatbot copilots that hallucinate numbers, EDITH strictly decouples **deterministic analytical algorithms** (anomaly detection, dimensional variance localization, metric dependency DAG traversal, exact mathematical decomposition, lagged cross-correlations, control group selection, pre-trend validation, and composite 0–100 Cause Evidence Scoring) from **downstream natural language AI synthesis**.

---

## 🚀 Key Features

1. **Progressive Disclosure Workflow**:
   - **Screen 1 (Business Overview)**: Portfolio health scan across 4 enterprise KPIs with automatic P1 Anomaly detection.
   - **Screen 2 (KPI Deep Diagnostic)**: 52-week historical trend vs. dynamic $\pm 2.0\sigma$ expected corridor and dimensional variance localization (Region $\rightarrow$ Tier $\rightarrow$ Product $\rightarrow$ Channel).
   - **Screen 3 (Dual-Pane Investigation Workspace)**: Side-by-side transparent analytical canvas with 8 structured competing hypotheses ($H_1 \dots H_8$), deterministic prediction testing, metric DAG dependency roles, mathematical revenue decomposition, data-driven control group selection, pre-trend validation, confounder analysis, and interactive Edith reasoning console.
   - **Screen 4 (Scenario Simulation Workbench)**: Interactive what-if sandbox allowing business leaders to adjust price and marketing levers, simulate counterfactual recovery curves, and export an auditable Decision Summary package.

2. **How EDITH Determines Root Cause**:
   $$\text{Base Score} = w_{\text{temp}} S_{\text{temp}} + w_{\text{mag}} S_{\text{mag}} + w_{\text{dir}} S_{\text{dir}} + w_{\text{hist}} S_{\text{hist}} + w_{\text{dep}} S_{\text{dep}} + w_{\text{contrib}} S_{\text{contrib}}$$
   $$\text{Final Cause Score} = \text{clamp}_{[0, 100]} \Big( \text{Base Score} - w_{\text{counter}} P_{\text{counter}} - w_{\text{conf}} P_{\text{conf}} - w_{\text{pre}} P_{\text{pre}} \Big) \times Q$$
   - **Temporal Precedence**: Candidate movement lead-time ($\tau \in [1, 3]$ weeks vs post-anomaly penalty).
   - **Magnitude / Effect Size**: Normalized deviation and $Z$-score.
   - **Directional Consistency**: Verification against economic domain theory (e.g. Price $\uparrow \implies$ Volume $\downarrow$).
   - **Historical Lag Analysis**: Lag cross-correlations ($r_k$ for lags $0..4$) to identify `best_lag` and `lag_strength`.
   - **Metric Dependency Graph**: Distinguishes direct upstream drivers from downstream effects (e.g. Gross Margin compression).
   - **Mathematical Decomposition**: Exact identity breakdown ($\Delta \text{Revenue} = \text{Volume Effect} + \text{Price Effect}$; volume explains $111.5\%$ of gross decline).
   - **Control-Group Selection & Pre-Trends**: Evaluates candidate cohorts and validates parallel pre-trends across Weeks 1–48 ($\Delta\beta = 0.00027$).
   - **Counter-Evidence & Confounders**: Quantifies negative evidence (warehouse fill rates $99.4\%$) and concurrent shocks (ApexTech discount).

3. **Intellectually Honest Confidence Classification**:
   - `HIGH-CONFIDENCE DRIVER` ($\ge 75$)
   - `POSSIBLE DRIVER` ($50 - 74$)
   - `CORRELATED SIGNAL` ($25 - 49$)
   - `DOWNSTREAM EFFECT` (e.g. Gross Margin / Profit)
   - `REFUTED BY DATA` (e.g. Inventory)
   - `NOT TESTABLE (MISSING TELEMETRY)` (e.g. Channel Commissions)

4. **Guaranteed 100% Demo Reliability (Zero-Key Offline Mode)**:
   - Connects live to **Google Gemini** (`gemini-2.5-flash` / `gemini-1.5-flash`) via `google-genai` SDK when `GEMINI_API_KEY` is provided.
   - Seamlessly falls back to an integrated **Deterministic Offline Reasoner** (`OfflineEdithReasoner`) when offline or without an API key.

---

## 📂 Project Structure

```
Edith_New/
├── app.py                         # Streamlit entrypoint & workflow stage routing
├── render.yaml                    # Render Blueprint specification
├── requirements.txt               # Python package dependencies
├── runtime.txt                    # Python runtime version for cloud deployment
├── .env.example                   # Environment variable template
├── .gitignore                     # Git tracking exclusions
├── .streamlit/
│   └── config.toml                # Cloud-optimized Streamlit server configuration
├── config/
│   ├── settings.py                # Configurable weights, thresholds, API keys, assumptions
│   └── semantic_contracts.py      # KPI definitions, metric definitions, driver catalog
├── data/
│   ├── generator.py               # Coherent 52-week relational synthetic data generator
│   └── repository.py              # In-memory query repository & aggregation layer
├── core/
│   ├── baseline_engine.py         # Rolling baseline, expected corridor (±2σ), anomaly detection
│   ├── contribution_engine.py     # Multi-dimensional variance localization
│   ├── dependency_graph.py        # Metric dependency DAG & mathematical decomposition
│   ├── evidence_engine.py         # Multi-hypothesis causal scorer, lag analysis & control selector
│   └── simulation_engine.py       # Parametric what-if counterfactual elasticity model
├── ai/
│   ├── llm_client.py              # Google GenAI SDK client with automatic offline fallback
│   ├── prompts.py                 # Grounded, evidence-cited prompt templates
│   └── offline_reasoner.py        # Deterministic offline reasoning engine
├── state/
│   └── session_state.py           # Centralized typed session state manager
├── ui/
│   ├── components/
│   │   ├── cards.py               # Metric cards, cause score cards, math decomposition cards
│   │   ├── charts.py              # Interactive Plotly charts (corridor, waterfall, DiD, simulation)
│   │   └── chat_pane.py           # Split-pane interactive dialogue console
│   └── screens/
│       ├── s1_overview.py         # Screen 1: Business Overview
│       ├── s2_diagnostic.py       # Screen 2: KPI Deep Diagnostic
│       ├── s3_workspace.py        # Screen 3: Dual-Pane Investigation Workspace
│       └── s4_simulation.py       # Screen 4: Scenario Simulation Workbench
├── tests/
│   ├── test_causal_reasoning.py   # 6 comprehensive tests for causal engine, math & lag analysis
│   ├── test_analytics.py          # Automated tests for baseline, contribution, scoring, simulation
│   ├── test_llm_fallback.py       # Verification tests for offline reasoner & grounding
│   ├── test_all_screens.py        # 4-screen data contract tests
│   ├── test_all_imports.py        # All-module packaging and import tests
│   ├── test_live_server_startup.py# Live Streamlit server boot test on 0.0.0.0:10000
│   ├── audit_numbers.py           # Rigorous end-to-end numerical verification script
│   └── red_team_audit.py          # Hostile input, boundary & denominator test suite
├── README.md                      # Project overview & running instructions
└── HOW_IT_WORKS.md                # Detailed technical and user guide
```

---

## 🌐 Quick Start (Local & Render)

### Quick Start (Local)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open `http://localhost:8501` to use EDITH.
