# EDITH: Executive Decision Intelligence Platform
**Accenture Innovation Challenge 2026 — Problem Track 3: BusinessIntelligence.ai**

Developed by **Team IIT Kanpur** (Chhavi Tanwar & Karan Kosta)

---

## 🎯 Executive Summary
Conventional Business Intelligence dashboards show **what happened** (e.g., *Monthly B2B Sales dropped 10.5% in Region B*), but leave the critical questions—**why did it happen?**, **what evidence supports that?**, and **what should we do next?**—to days of manual analyst drill-downs.

**EDITH** is an evidence-grounded KPI intelligence and investigation system that enforces an explicit analytical chain:
$$\text{SOURCES} \longrightarrow \text{DETECT} \longrightarrow \text{DIAGNOSE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{SIMULATE} \longrightarrow \text{ACT}$$

Unlike generic chatbot copilots that hallucinate numbers, EDITH strictly decouples **deterministic analytical algorithms** (anomaly detection, dimensional variance localization, metric dependency DAG traversal, exact mathematical decomposition, lagged cross-correlations, control group selection, pre-trend validation, and composite 0–100 Cause Evidence Scoring) from **downstream natural language AI synthesis**.

---

## 🚀 Key Features

1. **Executive Command Center & Investigation Flow**:
   - **0. Data Sources Manager (`s0_data_sources.py`)**: Load and analyze custom enterprise datasets from CSV, Excel (`.xlsx`), SQLite (`.db`), or remote SQL databases (PostgreSQL, MySQL, SQL Server) with safe read-only SQL validation and schema mapping.
   - **1. Detect — Executive Command Center (`s1_overview.py`)**: Incident hero banner for active P1 commercial anomalies, severity badges, and portfolio health scan.
   - **2. Diagnose — KPI Diagnostic (`s2_diagnostic.py`)**: 52-week historical trend vs. dynamic $\pm 2.0\sigma$ expected corridor and multi-dimensional variance localization (Region $\rightarrow$ Tier $\rightarrow$ Product $\rightarrow$ Channel).
   - **3. Explain — Causal Investigation Workspace (`s3_workspace.py`)**: 8 competing candidate hypotheses ($H_1 \dots H_8$), metric DAG dependency roles, mathematical revenue decomposition, control group selection, pre-trend validation, and counter-evidence.
   - **4. Simulate — Policy Scenario Workbench (`s4_simulation.py`)**: Interactive what-if sandbox allowing business leaders to adjust price and marketing levers, simulate 8-week counterfactual recovery curves, and export an auditable Decision Summary package.
   - **5. EDITH Console (`s5_console.py`)**: Full-page conversational assistant powered by an autonomous Gemini tool-calling agent.

2. **Gemini Tool-Using Conversational Agent**:
   - Equips Gemini with **11 safe, read-only analytical tools** (`ai/tools.py`) that ground every response in verified calculations.
   - 100% Zero-Key Offline Mode fallback using `OfflineEdithReasoner`.

3. **Modern Executive Light Theme**:
   - Clean slate and white editorial palette (`#F8FAFC`, `#FFFFFF`, `#0F172A`).
   - Generous top-padding, responsive card layouts, high-contrast typography, and native markdown chat rendering.

---

## 📂 Project Structure

```
Edith_New/
├── app.py                         # Streamlit entrypoint & workflow stage routing
├── render.yaml                    # Render Blueprint specification
├── requirements.txt               # Python package dependencies
├── runtime.txt                    # Python runtime version for cloud deployment
├── .env.example                   # Environment variable template
├── config/
│   ├── settings.py                # Environment configuration & statistical thresholds
│   └── semantic_contracts.py      # Governed KPI definitions, DAG metadata & driver catalog
├── data/
│   ├── generator.py               # Deterministic synthetic data generator (52 weeks)
│   ├── repository.py              # In-memory analytical data mart & custom source repository
│   └── source_manager.py          # CSV/Excel/SQLite parser, SQL connector & query validator
├── core/
│   ├── baseline_engine.py         # Rolling corridor (±2σ), Z-score, & anomaly detection
│   ├── contribution_engine.py     # Dimensional variance decomposition
│   ├── evidence_engine.py         # Multi-factor causal evidence scoring & hypothesis ranking
│   ├── dependency_graph.py        # Metric DAG traversal & revenue decomposition
│   └── simulation_engine.py       # Counterfactual simulation & 8-week trajectory projection
├── ai/
│   ├── llm_client.py              # Unified LLM Gateway with Gemini tool-calling agent
│   ├── tools.py                   # 11 safe read-only analytical tools for Gemini
│   ├── prompts.py                 # Grounded system prompts & intent classification
│   └── offline_reasoner.py        # Deterministic offline conversational engine
├── state/
│   └── session_state.py           # Typed Streamlit session state management
├── ui/
│   ├── components/
│   │   ├── cards.py               # Incident banner & KPI metric card components
│   │   ├── charts.py              # Plotly corridor, waterfall, & trajectory charts
│   │   └── chat_pane.py           # Investigation chat pane
│   └── screens/
│       ├── s0_data_sources.py     # Data sources & ingestion manager
│       ├── s1_overview.py         # Detect: Executive Command Center
│       ├── s2_diagnostic.py       # Diagnose: 52-week corridor & dimensional waterfall
│       ├── s3_workspace.py        # Explain: Causal Investigation Workspace
│       ├── s4_simulation.py       # Simulate: Policy Scenario Workbench
│       └── s5_console.py          # Dedicated full-page EDITH Console
└── tests/
    ├── test_all_imports.py
    ├── test_all_screens.py
    ├── test_data_sources_and_tools.py
    ├── test_gemini_tool_agent.py
    ├── test_conversational_ai.py
    ├── test_causal_reasoning.py
    ├── test_analytics.py
    ├── audit_numbers.py
    ├── red_team_audit.py
    ├── check_deployment_readiness.py
    └── test_deployment_simulation.py
```

---

## 🏃 Quickstart & Local Execution

```bash
# 1. Clone repository
git clone https://github.com/NeptuneKaran/NewEdith.git
cd NewEdith

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure Gemini API Key
export GEMINI_API_KEY="your_api_key_here"

# 4. Launch Streamlit Application
streamlit run app.py
```

---

## 🧪 Automated Test Suite (100% Pass)

```bash
python tests/test_all_imports.py
python tests/test_all_screens.py
python tests/test_data_sources_and_tools.py
python tests/test_gemini_tool_agent.py
python tests/test_conversational_ai.py
python tests/test_causal_reasoning.py
python tests/test_analytics.py
python tests/audit_numbers.py
python tests/red_team_audit.py
python tests/check_deployment_readiness.py
python tests/test_deployment_simulation.py
```

---

## 📄 License & Intellectual Property
Accenture Innovation Challenge 2026 Submission. Developed by Team IIT Kanpur.
