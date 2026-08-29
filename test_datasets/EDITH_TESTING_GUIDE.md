# EDITH Testing & User Guide: Ingesting, Profiling, and Analyzing Custom Business Data

Welcome to **EDITH (Executive Decision Intelligence & Tactical Hypothesis)**.

This guide provides practical, step-by-step instructions for testing EDITH using any of the 10 synthetic business datasets located in the `test_datasets/` folder. It is written in simple, non-technical language to walk you through uploading files, configuring columns, reading the analytical screens, and conversing with EDITH's AI assistant.

---

## 🚀 Before You Begin: How to Launch EDITH

1. **Open your terminal or command prompt** in the project directory:
   ```bash
   cd EDITH_Render_Final
   ```
2. **Start the EDITH application**:
   ```bash
   streamlit run app.py
   ```
3. **Open the application** in your web browser at `http://localhost:8501` (or click your live Render cloud deployment URL).
4. **Locate the Navigation Menu** in the left-hand sidebar. The screens are numbered in order of the investigation workflow:
   - **`0. 📂 Data Sources & Intake`** (Start here to upload and configure datasets)
   - **`1. 📊 Executive Overview`** (High-level trajectory, current baseline, and summary health)
   - **`2. 🔍 Diagnostic Decomposition`** (Dimensional breakdowns, concentration analysis, and outlier profiles)
   - **`3. 🔬 Investigation Workspace`** (Observational findings, driver associations, and evidence chains)
   - **`4. 🎯 Policy Simulator`** (Scenario simulation — active for calibrated econometric models)
   - **`5. 💬 EDITH Console`** (Natural language Q&A grounded strictly in verified data)

---

## 📖 Standard 4-Step Import Workflow

For every dataset you test, follow these 4 steps on Screen **`0. 📂 Data Sources & Intake`**:

1. **Select Data Source Type**: Choose **"📁 Upload File (CSV, Excel, SQLite)"**.
2. **Upload the CSV File**: Click **"Browse files"** (or drag and drop) and select a file from the `test_datasets/` folder.
3. **Review the Automated Data Profile**: EDITH will instantly inspect every column, displaying inferred data types, null percentages, unique value counts, sample values, and suggested semantic roles.
4. **Configure the Semantic Model**: Fill in the dropdown fields matching the dataset specification below, then click **"🚀 Apply Semantic Model & Ingest Dataset"**.

---

# 📂 Dataset Testing Catalog (1 to 10)

---

### Dataset 1: `01_hr_workforce_trends.csv`

#### 1. File & Grain
- **File:** `01_hr_workforce_trends.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `HR Workforce Retention & Attrition`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `attrition_rate`
- **Primary Measure Label:** `Weekly Attrition Rate`
- **Primary Measure Unit:** `%`
- **Aggregation Method:** `Mean / Average`
- **Date / Timestamp Column:** `snapshot_date`
- **Primary Categorical Dimensions:** Select `department`, `office_location`, and `job_level`
- **Explanatory Numeric Drivers:** Select `engagement_score`, `average_salary`, and `average_tenure_years`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **Time-series trajectory** of workforce attrition with rolling baseline corridors.
- **Dimensional concentration** identifying which departments and offices have abnormal turnover.
- **Driver correlation** between engagement scores, salary levels, and attrition.

#### 4. The Hidden Anomaly to Discover
Starting in Week 32, the **Engineering** department in the **Austin** office experiences a steady collapse in `engagement_score` (falling from 82 to 35) and a sharp rise in `attrition_rate` (jumping from 2.1% to over 16.5%). All other departments remain healthy.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Observe the sudden upward breach in attrition rate past historical corridors in the final quarter.
2. **`2. 🔍 Diagnostic Decomposition`**: See `department` and `office_location` bar charts showing Austin Engineering contributing the vast majority of excess turnover.
3. **`3. 🔬 Investigation Workspace`**: Review observational findings highlighting the strong negative correlation ($r < -0.80$) between `engagement_score` and attrition.
4. **`4. 🎯 Policy Simulator`**: *Note: Simulation is unavailable for custom datasets because counterfactual policy levers require a calibrated econometric model.*
5. **`5. 💬 EDITH Console`**: Ask conversational questions to investigate the findings.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 2: `02_manufacturing_quality.csv`

#### 1. File & Grain
- **File:** `02_manufacturing_quality.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Factory Defect & Quality Control`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `defect_count`
- **Primary Measure Label:** `Total Defect Count`
- **Primary Measure Unit:** `Defects`
- **Aggregation Method:** `Sum`
- **Date / Timestamp Column:** `production_date`
- **Primary Categorical Dimensions:** Select `plant`, `production_line`, and `shift`
- **Explanatory Numeric Drivers:** Select `downtime_hours`, `machine_speed_rpm`, and `maintenance_hours`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **Corridor breach detection** on weekly manufacturing defects.
- **Plant and shift breakdowns** pinpointing defective equipment.
- **Driver associations** connecting maintenance cuts and machine downtime to defect spikes.

#### 4. The Hidden Anomaly to Discover
Starting in Week 36, **Plant Stuttgart** on **Assembly-02** during the **Night Shift** suffers a severe defect spike (rising from ~12 to 180+ defects/week), directly accompanied by surging `downtime_hours` and a reduction in `maintenance_hours`.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Check the defect volume surge breaching the $\pm 2\sigma$ corridor.
2. **`2. 🔍 Diagnostic Decomposition`**: Identify `Plant Stuttgart` and `Assembly-02` as the primary concentration epicenters.
3. **`3. 🔬 Investigation Workspace`**: View driver correlation cards showing strong positive association with `downtime_hours` ($r > 0.85$).
4. **`5. 💬 EDITH Console`**: Query EDITH for summary findings and data quality.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 3: `03_customer_support_snapshot.csv`

#### 1. File & Grain
- **File:** `03_customer_support_snapshot.csv`
- **Data Grain:** **Cross-Sectional Snapshot** (1,250 Records, No Date Column)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Customer Support Ticket Audit`
- **Analysis Grain:** `Cross-Sectional Snapshot`
- **Primary Business Measure:** `resolution_hours`
- **Primary Measure Label:** `Resolution Time`
- **Primary Measure Unit:** `Hours`
- **Aggregation Method:** `Mean / Average`
- **Date / Timestamp Column:** `None (Snapshot / No Date Column)`
- **Primary Categorical Dimensions:** Select `team`, `channel`, `priority`, `issue_type`, and `customer_segment`
- **Explanatory Numeric Drivers:** Select `csat_score` and `reopen_count`
- **Primary Identifier Column:** `ticket_id`

#### 3. What EDITH Analyzes
- **Distribution statistics & outlier boundaries** (Median P50, IQR, skewness, and extreme value counts outside $1.5 	imes 	ext{IQR}$).
- **Cross-sectional segment shares** without fabricating fake time periods.
- **Quality and driver associations** between resolution delays, ticket reopens, and satisfaction scores.

#### 4. The Hidden Anomaly to Discover
**Tier 2 Escalations** handling **Integration Error** and **Billing Dispute** tickets exhibit massive resolution time outliers (45 to 180+ hours vs normal 6 hours), with severely depressed `csat_score` (mean 2.2 vs 4.4 benchmark) and high ticket reopen counts.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Notice the **Cross-Sectional Snapshot Hero Banner** with record counts and data health score (no artificial dates).
2. **`2. 🔍 Diagnostic Decomposition`**: Review the 4-card **Distribution & Outlier Profile** showing right-skewed outliers and categorical concentration in Tier 2 Escalations.
3. **`3. 🔬 Investigation Workspace`**: Confirm observational findings of low CSAT association without causal overreach.
4. **`5. 💬 EDITH Console`**: Ask about concentration and data quality.

#### 6. Example Questions to Ask in the Console
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*
- *"Summarize data-quality issues."*

---

### Dataset 4: `04_marketing_campaign_performance.csv`

#### 1. File & Grain
- **File:** `04_marketing_campaign_performance.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Marketing Performance & ROAS`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `conversions`
- **Primary Measure Label:** `Total Conversions`
- **Primary Measure Unit:** `Conversions`
- **Aggregation Method:** `Sum`
- **Date / Timestamp Column:** `campaign_date`
- **Primary Categorical Dimensions:** Select `campaign_name`, `channel`, and `region`
- **Explanatory Numeric Drivers:** Select `media_spend`, `clicks`, and `impressions`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **Conversion trajectory** tracking ad channel efficiency over 52 weeks.
- **Channel and campaign share breakdowns** identifying underperforming media channels.
- **Correlation divergence** highlighting where spend increases fail to generate conversions.

#### 4. The Hidden Anomaly to Discover
The **Competitor Conquest** campaign on **LinkedIn Paid** in **North America** experiences severe ad fatigue after Week 28: `media_spend` escalates from $8,000 to $25,000+/week, but `conversions` fall by 65%, creating a sharp negative efficiency divergence.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: View the full 52-week conversion baseline and deficit corridor.
2. **`2. 🔍 Diagnostic Decomposition`**: Inspect `campaign_name` and `channel` breakdowns isolating the LinkedIn Paid collapse.
3. **`3. 🔬 Investigation Workspace`**: Review correlation metrics between spend and conversion yield.
4. **`5. 💬 EDITH Console`**: Ask EDITH to explain the primary metric movements.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 5: `05_finance_cost_center.csv`

#### 1. File & Grain
- **File:** `05_finance_cost_center.csv`
- **Data Grain:** **Time-Series** (24 Monthly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Finance OpEx Ledger & Budget Variance`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `actual_cost`
- **Primary Measure Label:** `Actual OpEx Spend`
- **Primary Measure Unit:** `$`
- **Aggregation Method:** `Sum`
- **Date / Timestamp Column:** `posting_date`
- **Primary Categorical Dimensions:** Select `cost_center`, `department`, and `expense_category`
- **Explanatory Numeric Drivers:** Select `budget_cost` and `invoice_count`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **Monthly OpEx trajectory** with budget comparison baselines.
- **Cost center & expense category breakdowns** isolating overrun drivers.
- **Correlation** between budget targets and actual spending.

#### 4. The Hidden Anomaly to Discover
In Month 13 (January 2025), cost center **`CC-102 Cloud Infrastructure`** in expense category **`Cloud Compute & Hosting`** surges by +165% to +280% over budget ($120k–$190k/mo vs $55k budget), accounting for >80% of total company budget variance.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Observe the monthly spend jump starting at Month 13.
2. **`2. 🔍 Diagnostic Decomposition`**: See `cost_center` and `expense_category` variance shares isolating Cloud Infrastructure.
3. **`3. 🔬 Investigation Workspace`**: Examine the variance decomposition and driver associations.
4. **`5. 💬 EDITH Console`**: Explore cost center concentration in natural language.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Summarize data-quality issues."*

---

### Dataset 6: `06_supply_chain_delivery.csv`

#### 1. File & Grain
- **File:** `06_supply_chain_delivery.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Supply Chain Inbound & Logistics`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `on_time_delivery_pct`
- **Primary Measure Label:** `On-Time Delivery Rate`
- **Primary Measure Unit:** `%`
- **Aggregation Method:** `Mean / Average`
- **Date / Timestamp Column:** `shipment_date`
- **Primary Categorical Dimensions:** Select `supplier`, `warehouse`, and `product_category`
- **Explanatory Numeric Drivers:** Select `lead_time_days`, `freight_cost`, `units_ordered`, and `units_received`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **On-time delivery trajectory** across global hubs.
- **Supplier & warehouse variance breakdowns** isolating bottleneck vendors.
- **Lead-time and freight cost correlations** with shipping delays.

#### 4. The Hidden Anomaly to Discover
Supplier **`Titan Raw Materials`** shipping **`Microcontrollers`** to **`Hub-Rotterdam`** suffers a severe lead time blowout (escalating from 14 to 48+ days) starting in Week 26, causing on-time delivery to plummet from 94% to 38%.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Check the on-time delivery rate collapse breaching corridor thresholds.
2. **`2. 🔍 Diagnostic Decomposition`**: Identify Titan Raw Materials and Hub-Rotterdam as the primary deficit drivers.
3. **`3. 🔬 Investigation Workspace`**: Confirm strong negative correlation between `lead_time_days` and `on_time_delivery_pct`.
4. **`5. 💬 EDITH Console`**: Ask about vendor concentration and metric movements.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 7: `07_product_usage_events.csv`

#### 1. File & Grain
- **File:** `07_product_usage_events.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `SaaS Product Engagement & Telemetry`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `events_count`
- **Primary Measure Label:** `Weekly Event Volume`
- **Primary Measure Unit:** `Events`
- **Aggregation Method:** `Sum` *(or choose `Distinct Count` with `customer_id`)*
- **Date / Timestamp Column:** `event_date`
- **Primary Categorical Dimensions:** Select `plan_type`, `feature_name`, and `user_role`
- **Explanatory Numeric Drivers:** Select `error_count` and `session_minutes`
- **Primary Identifier Column:** `customer_id`

#### 3. What EDITH Analyzes
- **Usage event volume trends** by tier and feature.
- **Feature-level breakdowns** isolating declining workflows.
- **Error rate correlations** with customer drop-off.

#### 4. The Hidden Anomaly to Discover
**Enterprise Tier** accounts using **`API Webhooks`** experience a -70% drop in event volume starting in Week 30, perfectly synchronized with an `error_count` surge (jumping from <5 to >120 errors/week).

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: View the event drop in Q3.
2. **`2. 🔍 Diagnostic Decomposition`**: Inspect `feature_name` and `plan_type` breakdowns pinpointing API Webhooks.
3. **`3. 🔬 Investigation Workspace`**: Review the synchronous inverse correlation with `error_count`.
4. **`5. 💬 EDITH Console`**: Ask about the root factors behind the event decline.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 8: `08_healthcare_operations.csv`

#### 1. File & Grain
- **File:** `08_healthcare_operations.csv`
- **Data Grain:** **Time-Series** (52 Weekly Periods)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Hospital Capacity & Patient Flow`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `average_wait_minutes`
- **Primary Measure Label:** `Average Wait Time`
- **Primary Measure Unit:** `Minutes`
- **Aggregation Method:** `Mean / Average`
- **Date / Timestamp Column:** `visit_date`
- **Primary Categorical Dimensions:** Select `facility`, `department`, and `visit_type`
- **Explanatory Numeric Drivers:** Select `bed_occupancy_pct`, `staffing_level`, `patient_count`, and `readmission_rate`
- **Primary Identifier Column:** `None`

#### 3. What EDITH Analyzes
- **Hospital wait-time trends** and corridor alarms.
- **Facility and department breakdowns** isolating congested centers.
- **Correlations** between staffing cuts, bed occupancy, and patient wait times.

#### 4. The Hidden Anomaly to Discover
**Metro General Hospital** in **`Emergency Medicine`** experiences a capacity crisis from Week 38 onwards: `average_wait_minutes` spikes from 35 mins to 145+ mins and `bed_occupancy_pct` breaches 98%, strongly correlated with a 40% reduction in `staffing_level`.

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Observe the severe wait-time spike in late Q3/Q4.
2. **`2. 🔍 Diagnostic Decomposition`**: See Metro General Hospital Emergency Medicine contributing >85% of total wait-time inflation.
3. **`3. 🔬 Investigation Workspace`**: Examine negative correlation with `staffing_level` and positive correlation with `bed_occupancy_pct`.
4. **`5. 💬 EDITH Console`**: Ask about emergency department concentration.

#### 6. Example Questions to Ask in the Console
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*

---

### Dataset 9: `09_retail_inventory_snapshot.csv`

#### 1. File & Grain
- **File:** `09_retail_inventory_snapshot.csv`
- **Data Grain:** **Cross-Sectional Snapshot** (1,650 Records, No Date Column)

#### 2. Exact Recommended Configuration
- **Dataset Display Name:** `Retail Stockout & Margin Audit`
- **Analysis Grain:** `Cross-Sectional Snapshot`
- **Primary Business Measure:** `on_hand_units`
- **Primary Measure Label:** `On-Hand Inventory`
- **Primary Measure Unit:** `Units`
- **Aggregation Method:** `Sum`
- **Date / Timestamp Column:** `None (Snapshot / No Date Column)`
- **Primary Categorical Dimensions:** Select `store`, `city`, `product_category`, and `brand`
- **Explanatory Numeric Drivers:** Select `weekly_sales_units`, `reorder_point`, and `unit_margin`
- **Primary Identifier Column:** `sku_id`

#### 3. What EDITH Analyzes
- **Inventory distribution profiles** and zero-stock outlier concentrations.
- **Store and brand breakdowns** identifying critical stockout clusters.
- **Driver associations** connecting stockouts to high-margin, high-velocity items.

#### 4. The Hidden Anomaly to Discover
**Store #104 Galleria** and **Store #101 Downtown** suffer a severe stockout cluster (`on_hand_units == 0`) specifically concentrated in **`Electronics & Audio`** on **`AuraTech`** products, which represent the highest weekly sales velocity and top unit margins ($180–$420).

#### 5. Which Screens to Visit
1. **`1. 📊 Executive Overview`**: Review the Cross-Sectional Snapshot banner and total SKU count.
2. **`2. 🔍 Diagnostic Decomposition`**: View the Distribution Profile and category share bar charts isolating AuraTech stockouts.
3. **`3. 🔬 Investigation Workspace`**: Review driver correlations between unit margin and inventory levels.
4. **`5. 💬 EDITH Console`**: Ask about store inventory concentrations.

#### 6. Example Questions to Ask in the Console
- *"Which groups show the greatest concentration?"*
- *"Which numeric fields have the strongest observed association?"*
- *"Summarize data-quality issues."*

---

### Dataset 10: `10_data_quality_stress_test.csv` (Dedicated Stress-Test Guide)

#### 1. Purpose & What This Tests
This dataset deliberately contains real-world data flaws to test EDITH's automated profiler, type validation, and data cleaning engine.

#### 2. The Controlled Quality Flaws Injected
1. **Missing / Blank Values:** ~4% missing values in `metric_value` and ~5% missing values in `driver_a`.
2. **Formatted Strings in Numeric Columns:** ~18% of values written as currency strings (`"$1,240.50"`) or percentages (`"12.5%"`).
3. **Corrupted Dates:** A few unparseable date strings (`"2025-99-99"`, `"INVALID_DATE"`).
4. **Duplicate Rows:** 20 exact duplicate rows injected at the end of the file.
5. **Inconsistent Casing & Whitespace:** Categorical values with erratic spaces and mixed casing (`"  ENTERPRISE SYSTEMS "`, `"enterprise systems"`, `"Fintech  Ops"`).
6. **Authentic Underlying Signal:** Despite the data noise, Division **`Commercial Tech`** suffers a genuine 48% performance decline from Week 14 onwards.

#### 3. How to Configure the Import on Screen 0
- **File:** `10_data_quality_stress_test.csv`
- **Dataset Display Name:** `Data Quality Stress Test`
- **Analysis Grain:** `Time Series (Weekly / Monthly / Daily)`
- **Primary Business Measure:** `metric_value` *(Notice EDITH automatically detects currency formatting and cleans it)*
- **Primary Measure Label:** `Performance Index`
- **Primary Measure Unit:** `Pts`
- **Aggregation Method:** `Mean / Average`
- **Date / Timestamp Column:** `record_date`
- **Primary Categorical Dimensions:** Select `division` and `team`
- **Explanatory Numeric Drivers:** Select `driver_a` and `driver_b`
- **Primary Identifier Column:** `entity_id`
- **Data Cleaning Checkbox:** **Check the box "Drop invalid/unparseable rows (recommended for dirty files)"**.

#### 4. What EDITH Does During Ingestion
- **Automated Data Profile:** Displays explicit warnings showing null percentages, corrupted date counts, and formatted numeric values.
- **Smart Cleaning:** Cleans currency symbols (`$`, `,`) and percentages (`%`) into true floats, strips inconsistent padding and casing, drops duplicate rows, and reports dropped invalid date records cleanly in the warnings banner.
- **Signal Extraction:** Correctly identifies the 48% performance drop in `Commercial Tech` on Screen 1 and Screen 2 despite the noise!

#### 5. Which Screens to Visit
1. **`0. 📂 Data Sources & Intake`**: Inspect the **Data Profile** table and review the green **Ingestion Warnings** container.
2. **`1. 📊 Executive Overview`**: Confirm that the clean time series renders without crashing, showing the trajectory and corridor breach.
3. **`2. 🔍 Diagnostic Decomposition`**: See `Commercial Tech` clearly highlighted as the main deficit contributor.
4. **`5. 💬 EDITH Console`**: Ask EDITH to summarize data quality issues.

#### 6. Example Questions to Ask in the Console
- *"Summarize data-quality issues."*
- *"What changed in the selected metric?"*
- *"Which groups show the greatest concentration?"*

---

## 🛠️ Concise Troubleshooting Guide

| Issue / Symptom | Root Cause | Solution |
|---|---|---|
| **"Error: Primary measure contains non-numeric text"** | A non-numeric text column (such as a name or description) was selected as the Primary Measure. | Return to Screen `0. 📂 Data Sources & Intake` and select a numeric column from the dropdown (e.g. `headcount`, `actual_cost`, `conversions`). |
| **"Error: Failed to parse date column"** | An invalid column was chosen as the Date field, or the file contains unparseable dates. | Check the box **"Drop invalid/unparseable rows"** on Screen 0, or select **"None (Snapshot)"** if your dataset does not have time periods. |
| **"Simulation is unavailable for this dataset"** | Custom datasets do not have pre-calibrated econometric equations. | This is expected behavior. Counterfactual simulation is only enabled for calibrated structural models and the built-in B2B SaaS demo. For custom data, use Screens 1, 2, 3, and 5 for diagnostic analytics. |
| **"Zero variance or single point on Corridor Chart"** | A non-temporal dataset was loaded with snapshot grain. | This is correct behavior. Snapshot datasets do not have time series; visit Screen `2. 🔍 Diagnostic Decomposition` to view the **Distribution & Outlier Profile** instead of time-series corridors. |
| **"Missing values or NaN in breakdowns"** | The raw dataset has unpopulated fields in certain rows. | Ensure **"Drop invalid/unparseable rows"** is checked on Screen 0 to clean incomplete records during ingestion. |
