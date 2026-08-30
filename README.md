# EDITH: Executive Decision Intelligence Platform
**Accenture Innovation Challenge 2026 — Problem Track 3: BusinessIntelligence.ai**

Developed by **Team IIT Kanpur** (Chhavi Tanwar & Karan Kosta)

[![Hosted on Render](https://img.shields.io/badge/Hosted%20on-Render-46E3B7?logo=render&logoColor=white)](https://newedith.onrender.com)
[![Live Demo](https://img.shields.io/badge/Live%20App-newedith.onrender.com-6F00B5?style=flat&logo=google-chrome&logoColor=white)](https://newedith.onrender.com)

🔗 **Live Application URL**: [https://newedith.onrender.com](https://newedith.onrender.com)

---

## Executive Summary
Conventional Business Intelligence dashboards show **what happened** (e.g., *Monthly B2B Sales dropped 10.5% in Region B*), but leave the critical questions—**why did it happen?**, **what evidence supports that?**, and **what should we do next?**—to days of manual analyst drill-downs.

**EDITH** is an evidence-grounded KPI intelligence and investigation system that enforces an explicit analytical chain:
$$\text{SOURCES} \longrightarrow \text{DETECT} \longrightarrow \text{DIAGNOSE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{SIMULATE} \longrightarrow \text{ACT}$$

Unlike generic chatbot copilots that hallucinate numbers, EDITH strictly decouples **deterministic analytical algorithms** (anomaly detection, dimensional variance localization, metric dependency DAG traversal, exact mathematical decomposition, lagged cross-correlations, control group selection, pre-trend validation, and composite 0–100 Cause Evidence Scoring) from **downstream natural language AI synthesis**.

---

## Key Features

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

## Project Structure

```
Edith_New/
├── main.py                        # FastAPI Application entrypoint & REST API Gateway
├── frontend/
│   └── index.html                 # Single-page application (Alpine.js + Tailwind + Plotly)
├── render.yaml                    # Render Cloud Blueprint specification
├── requirements.txt               # Python package dependencies
├── runtime.txt                    # Python runtime version for cloud deployment
├── .env.example                   # Environment variable template
├── config/
│   ├── settings.py                # Environment configuration & statistical thresholds
│   └── semantic_contracts.py      # Governed KPI definitions, DAG metadata & driver catalog
├── data/
│   ├── generator.py               # Deterministic synthetic data generator (52 weeks)
│   ├── repository.py              # In-memory analytical data mart & custom source repository
│   └── source_manager.py          # Generic profiler, semantic mapper, & SQL validator
├── core/
│   ├── baseline_engine.py         # Rolling corridor (±2σ), Z-score, & anomaly detection
│   ├── contribution_engine.py     # Dimensional variance decomposition
│   ├── evidence_engine.py         # Multi-factor causal evidence & observational findings
│   ├── dependency_graph.py        # Metric DAG traversal & revenue decomposition
│   └── simulation_engine.py       # Counterfactual simulation & 8-week trajectory projection
├── ai/
│   ├── llm_client.py              # Unified LLM Gateway with Gemini tool-calling agent
│   ├── tools.py                   # 11 safe read-only analytical tools for Gemini
│   ├── prompts.py                 # Grounded system prompts & intent classification
│   └── offline_reasoner.py        # Deterministic offline conversational engine
├── test_datasets/                 # 10 synthetic business domain datasets (HR, Finance, etc.)
│   ├── EDITH_TESTING_GUIDE.md     # Step-by-step user testing guide
│   └── README.md                  # Dataset catalog
└── tests/
    ├── test_api_endpoints.py      # FastAPI REST endpoint integration tests
    ├── test_generic_data_sources.py # Ingestion, validation & profiling tests
    ├── test_all_imports.py
    ├── test_data_sources_and_tools.py
    ├── test_conversational_ai.py
    ├── test_causal_reasoning.py
    ├── test_analytics.py
    └── check_deployment_readiness.py
```

---

## Quickstart & Local Execution

```bash
# 1. Clone repository
git clone https://github.com/NeptuneKaran/Edith.git
cd Edith

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure Gemini API Key
export GEMINI_API_KEY="your_api_key_here"

# 4. Launch EDITH FastAPI Single-Page Web Dashboard
uvicorn main:app --reload
```

Then navigate to `http://localhost:8000` (or `http://localhost:8501` if running with `python main.py`) in your web browser.

---

## Automated Test Suite (100% Pass)

```bash
python -m unittest tests/test_api_endpoints.py -v
python -m unittest tests/test_generic_data_sources.py -v
python tests/test_all_imports.py
python tests/test_data_sources_and_tools.py
python tests/test_conversational_ai.py
python tests/test_causal_reasoning.py
python tests/test_analytics.py
python tests/check_deployment_readiness.py
```

---

## 📄 License & Intellectual Property
Accenture Innovation Challenge 2026 Submission. Developed by Team IIT Kanpur.

