# EDITH: AI-Assisted Business Intelligence Investigation System
**Accenture Innovation Challenge 2026 — Problem Track 3: BusinessIntelligence.ai**

Developed by **Team IIT Kanpur** (Chhavi Tanwar & Karan Kosta)

---

## 🎯 Executive Summary
Conventional Business Intelligence dashboards show **what happened** (e.g., *Monthly B2B Sales dropped 10.5% in Region B*), but leave the critical questions—**why did it happen?**, **what evidence supports that?**, and **what should we do next?**—to days of manual analyst drill-downs.

**EDITH** is an evidence-grounded KPI intelligence and investigation system that enforces an explicit analytical chain:
$$\text{OBSERVE} \longrightarrow \text{DETECT} \longrightarrow \text{INVESTIGATE} \longrightarrow \text{EVIDENCE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{SIMULATE} \longrightarrow \text{ACT}$$

Unlike generic chatbot copilots that hallucinate numbers, EDITH strictly decouples **deterministic analytical algorithms** (anomaly detection, dimensional variance decomposition, Difference-in-Differences, and composite Evidence Scoring) from **downstream natural language AI synthesis**.

---

## 🚀 Key Features

1. **Progressive Disclosure Workflow**:
   - **Screen 1 (Business Overview)**: Portfolio health scan across 4 enterprise KPIs with automatic P1 Anomaly detection.
   - **Screen 2 (KPI Deep Diagnostic)**: 52-week historical trend vs. dynamic $\pm 2.0\sigma$ expected corridor and dimensional variance decomposition (Region $\rightarrow$ Tier $\rightarrow$ Product $\rightarrow$ Channel).
   - **Screen 3 (Dual-Pane Investigation Workspace)**: Side-by-side transparent analytical canvas with deterministic Evidence Scores ($[0.0, 1.0]$), temporal lead-time checks, supporting/contradictory evidence ledgers, and interactive Edith reasoning console.
   - **Screen 4 (Scenario Simulation Workbench)**: Interactive what-if sandbox allowing business leaders to adjust price and marketing levers, simulate counterfactual recovery curves, and export an auditable Decision Summary package.

2. **Interpretable Composite Evidence Score**:
   $$S(H_k) = \text{clamp}_{[0.0, 1.0]} \left( w_T \cdot T_k + w_E \cdot E_k + w_C \cdot C_k - w_D \cdot D_k \right) \times Q_k$$
   - $T_k$: Temporal precedence ($+12\%$ price hike preceded drop by $\tau = 2$ weeks).
   - $E_k$: Difference-in-Differences effect size vs unaffected control cohort.
   - $C_k$: Corroborating signals (CRM pricing complaints surge to $38/\text{wk}$).
   - $D_k$: Contradictory penalty (Warehouse fill rate was $99.4\% \rightarrow$ refuting inventory stockouts).
   - $Q_k$: Data freshness and sample size factor.

3. **Guaranteed 100% Demo Reliability (Zero-Key Offline Mode)**:
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
│   └── semantic_contracts.py      # KPI definitions, dimensions, driver metadata catalog
├── data/
│   ├── generator.py               # Coherent 52-week relational synthetic data generator
│   └── repository.py              # In-memory query repository & aggregation layer
├── core/
│   ├── baseline_engine.py         # Rolling baseline, expected corridor (±2σ), anomaly detection
│   ├── contribution_engine.py     # Multi-dimensional variance decomposition
│   ├── evidence_engine.py         # Multi-hypothesis tester & deterministic Evidence Scorer
│   └── simulation_engine.py       # Parametric what-if counterfactual elasticity model
├── ai/
│   ├── llm_client.py              # Google GenAI SDK client with automatic offline fallback
│   ├── prompts.py                 # Grounded, evidence-cited prompt templates
│   └── offline_reasoner.py        # Deterministic offline reasoning engine
├── state/
│   └── session_state.py           # Centralized typed session state manager
├── ui/
│   ├── components/
│   │   ├── cards.py               # Metric cards, anomaly badges, metadata chips
│   │   ├── charts.py              # Interactive Plotly charts (corridor, waterfall, DiD, simulation)
│   │   └── chat_pane.py           # Split-pane interactive dialogue console
│   └── screens/
│       ├── s1_overview.py         # Screen 1: Business Overview
│       ├── s2_diagnostic.py       # Screen 2: KPI Deep Diagnostic
│       ├── s3_workspace.py        # Screen 3: Dual-Pane Investigation Workspace
│       └── s4_simulation.py       # Screen 4: Scenario Simulation Workbench
├── tests/
│   ├── test_analytics.py          # Automated tests for baseline, contribution, scoring, simulation
│   ├── test_llm_fallback.py       # Verification tests for offline reasoner & grounding
│   ├── audit_numbers.py           # Rigorous end-to-end numerical verification script
│   └── red_team_audit.py          # Hostile input, boundary & denominator test suite
├── README.md                      # Project overview & running instructions
└── HOW_IT_WORKS.md                # Detailed technical and user guide
```

---

## 🌐 Deploying EDITH to Render (Step-by-Step Guide)

EDITH is fully configured for zero-friction cloud deployment on [Render](https://render.com) as a Python Web Service.

### Step 1: Push Code to GitHub
1. Initialize git and commit the project files:
   ```bash
   git init
   git add .
   git commit -m "Prepare EDITH for Render deployment"
   git branch -M main
   ```
2. Create a new repository on your GitHub account (e.g. `edith-bi-investigation`).
3. Push to your GitHub repository:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Render will automatically detect `render.yaml` or you can configure manually:
   - **Name**: `edith-bi-investigation`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - **Plan**: `Free`

### Step 3: Configure Environment Variables (Optional)
In your Render Service Dashboard, navigate to **Environment**:
- Add `GEMINI_API_KEY`: Paste your key from [Google AI Studio](https://aistudio.google.com/).
- *(Note: If `GEMINI_API_KEY` is omitted, EDITH automatically and seamlessly operates in 100% deterministic offline fallback mode with zero downtime).*

### Step 4: Access Your Live Application
Click **Create Web Service**. Within 2–3 minutes, Render will build and deploy EDITH. Open the generated public URL (e.g. `https://edith-bi-investigation.onrender.com`).

---

## ⚡ Local Quick Start

### 1. Requirements
- Python 3.10+
- Packages: `pip install -r requirements.txt`

### 2. Run Automated Verification Tests
```bash
python tests/test_analytics.py
python tests/test_llm_fallback.py
python tests/audit_numbers.py
python tests/red_team_audit.py
```

### 3. Launch Local Streamlit Server
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🎬 Presentation Demo Script (4 Minutes)
1. **Screen 1 (Overview)**: Show the 4 enterprise KPIs; point out the **P1 Material Anomaly** on *Monthly B2B Sales* (-10.5% drop from $1.40M to $1.25M). Click **`🔍 Investigate Anomaly →`**.
2. **Screen 2 (Diagnostic)**: Show the 52-week time series breaching below the shaded $\pm 2.0\sigma$ corridor ($Z = -2.30$). Show the dimensional waterfall proving **Region B Enterprise** accounts for $97.3\%$ of the drop. Click **`🚀 Analyze Root Causes →`**.
3. **Screen 3 (Workspace - Left)**: Show ranked candidate causes: **Pricing Pressure** ($0.90$) vs **Competitor Action** ($0.55$) vs **Inventory Bottleneck** ($0.00$). Highlight the contradictory evidence refuting inventory (Warehouse stock was $99.4\%$).
4. **Screen 3 (Workspace - Right)**: Show Edith’s executive diagnosis. Click **`❓ Why is inventory ruled out?`** and **`❓ Why is competitor action secondary?`** to demonstrate evidence grounding. Click **`🛠️ Simulate Action Impact →`**.
5. **Screen 4 (Simulation)**: Adjust the price rollback slider to $-6\%$ and add $\$15\text{k}$ promo budget. Watch the projected recovery curve rebound. Review the structured Decision Summary and click **`📥 Export Decision Package`**.
