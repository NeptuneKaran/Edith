# EDITH Synthetic Test Datasets Repository

This folder contains 10 diverse, fictional business datasets designed to validate and stress-test EDITH's generic structured data profiling, semantic mapping, dimensional decomposition, and diagnostic analytics across arbitrary business domains.

---

## Dataset Index & Analytical Mapping Guide

### 1. `01_hr_workforce_trends.csv`
- **Business Domain:** Human Resources, People Analytics & Workforce Retention
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `attrition_rate` (Unit: `%`, Aggregation: `mean`) or `headcount` (Unit: `Employees`, Aggregation: `sum`)
- **Recommended Dimensions:** `department`, `office_location`, `job_level`
- **Recommended Numeric Drivers:** `engagement_score`, `average_salary`, `average_tenure_years`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Engineering` department in the `Austin` office location.
  - **Behavior:** Starting at Week 32, `engagement_score` experiences a sustained decline (falling from ~82 to ~35), leading to a correlated spike in `attrition_rate` (surging from 2.1% to over 16.5%) and declining average tenure. Other departments and locations remain within normal historical baselines.

---

### 2. `02_manufacturing_quality.csv`
- **Business Domain:** Manufacturing, Plant Operations & Industrial Quality Control
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `defect_count` (Unit: `Defects`, Aggregation: `sum`) or `units_produced` (Unit: `Units`, Aggregation: `sum`)
- **Recommended Dimensions:** `plant`, `production_line`, `shift`
- **Recommended Numeric Drivers:** `downtime_hours`, `machine_speed_rpm`, `maintenance_hours`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Plant Stuttgart` on `Assembly-02` during the `Night Shift`.
  - **Behavior:** Beginning at Week 36, `defect_count` breaches normal corridor thresholds (surging from ~12 to 180+ defects/week), exhibiting strong parametric correlation (|r| > 0.85) with a sharp rise in `downtime_hours` and a drop in scheduled `maintenance_hours`.

---

### 3. `03_customer_support_snapshot.csv`
- **Business Domain:** Customer Support & Service Operations
- **Data Grain:** Cross-Sectional Snapshot / Record-Level (1,250 Records, **No Date Column**)
- **Intended Primary Measure:** `resolution_hours` (Unit: `Hours`, Aggregation: `mean`) or `csat_score` (Unit: `Score`, Aggregation: `mean`)
- **Recommended Dimensions:** `team`, `channel`, `priority`, `issue_type`, `customer_segment`
- **Recommended Numeric Drivers:** `csat_score`, `reopen_count`
- **Entity / ID Column:** `ticket_id`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Tier 2 Escalations` team handling `Integration Error` and `Billing Dispute` issues.
  - **Behavior:** Marked right-skewed distribution and outlier cluster exceeding the 1.5x IQR threshold (resolution times between 45 and 180+ hours), accompanied by depressed `csat_score` (mean 2.2 vs baseline 4.4) and frequent ticket reopens.

---

### 4. `04_marketing_campaign_performance.csv`
- **Business Domain:** Multi-Channel Digital Marketing, Attribution & Customer Acquisition
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `conversions` (Unit: `Conversions`, Aggregation: `sum`) or `attributed_revenue` (Unit: `$`, Aggregation: `sum`)
- **Recommended Dimensions:** `campaign_name`, `channel`, `region`
- **Recommended Numeric Drivers:** `media_spend`, `clicks`, `impressions`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Competitor Conquest` campaign on `LinkedIn Paid` in `North America`.
  - **Behavior:** From Week 28 onwards, `media_spend` is aggressively ramped up ($8,000 to $25,000+/week) driving higher impressions and clicks, but conversion efficiency collapses (conversion rate drops from ~6.5% to <1.0%), producing a severe negative divergence between spend and attributed revenue.

---

### 5. `05_finance_cost_center.csv`
- **Business Domain:** Corporate Finance, General Ledger & OpEx Budget Variance
- **Data Grain:** Time-Series (24 Monthly Periods: `2024-01-01` to `2025-12-01`)
- **Intended Primary Measure:** `actual_cost` (Unit: `$`, Aggregation: `sum`) or `variance` (Unit: `$`, Aggregation: `sum`)
- **Recommended Dimensions:** `cost_center`, `department`, `expense_category`
- **Recommended Numeric Drivers:** `budget_cost`, `invoice_count`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `CC-102 Cloud Infrastructure` (`IT & Infrastructure`) in category `Cloud Compute & Hosting`.
  - **Behavior:** Running in line with budget throughout 2024, but starting in Month 13 (January 2025), actual costs escalate by +165% to +280% over budget ($120k-$190k/mo vs $55k budget), accounting for over 80% of total company budget variance.

---

### 6. `06_supply_chain_delivery.csv`
- **Business Domain:** Supply Chain Logistics, Vendor Inbound & On-Time Performance
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `on_time_delivery_pct` (Unit: `%`, Aggregation: `mean`) or `lead_time_days` (Unit: `Days`, Aggregation: `mean`)
- **Recommended Dimensions:** `supplier`, `warehouse`, `product_category`
- **Recommended Numeric Drivers:** `units_ordered`, `units_received`, `freight_cost`, `lead_time_days`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** Supplier `Titan Raw Materials` delivering `Microcontrollers` to `Hub-Rotterdam`.
  - **Behavior:** Starting in Week 26, `lead_time_days` escalates from 14 days to 48+ days, and `on_time_delivery_pct` collapses from 94% to ~38%, linked with supply disruption and inflated freight expenses.

---

### 7. `07_product_usage_events.csv`
- **Business Domain:** SaaS Product Telemetry, User Engagement & Feature Adoption
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `events_count` (Unit: `Events`, Aggregation: `sum`) or `error_count` (Unit: `Errors`, Aggregation: `sum`)
- **Recommended Dimensions:** `plan_type`, `feature_name`, `user_role`
- **Recommended Numeric Drivers:** `session_minutes`, `error_count`
- **Distinct Entity / ID Column:** `customer_id` (enables `distinct_count` active customer tests)
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Enterprise Tier` accounts utilizing the `API Webhooks` feature.
  - **Behavior:** Post Week 30, feature usage collapses by -70%, exhibiting a direct synchronous correlation with an `error_count` spike (surging from <5 to >120 errors/week) caused by an API contract regression.

---

### 8. `08_healthcare_operations.csv`
- **Business Domain:** Healthcare Administration, Hospital Capacity & Patient Flow
- **Data Grain:** Time-Series (52 Weekly Periods: `2025-01-05` to `2025-12-28`)
- **Intended Primary Measure:** `average_wait_minutes` (Unit: `Minutes`, Aggregation: `mean`) or `bed_occupancy_pct` (Unit: `%`, Aggregation: `mean`)
- **Recommended Dimensions:** `facility`, `department`, `visit_type`
- **Recommended Numeric Drivers:** `patient_count`, `bed_occupancy_pct`, `staffing_level`, `readmission_rate`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Metro General Hospital` in `Emergency Medicine`.
  - **Behavior:** From Week 38 to 52, `average_wait_minutes` spikes from 35 mins to 145+ mins and `bed_occupancy_pct` reaches 98.5%, driven by high emergency volume combined with a drop in `staffing_level` (down 40%).

---

### 9. `09_retail_inventory_snapshot.csv`
- **Business Domain:** Omnichannel Retail Merchandising & Stockout Risk Management
- **Data Grain:** Cross-Sectional Snapshot (1,650 Records, **No Date Column**)
- **Intended Primary Measure:** `on_hand_units` (Unit: `Units`, Aggregation: `sum`) or `stockout_flag` (Unit: `Stockouts`, Aggregation: `sum`)
- **Recommended Dimensions:** `store`, `city`, `product_category`, `brand`
- **Recommended Numeric Drivers:** `weekly_sales_units`, `reorder_point`, `unit_margin`
- **Entity / ID Column:** `sku_id`
- **Hidden Anomaly / Pattern to Identify:**
  - **Epicenter:** `Store #104 Galleria` and `Store #101 Downtown` on `Electronics & Audio` products from the `AuraTech` brand.
  - **Behavior:** Critical zero-inventory stockout concentration (`stockout_flag == 1`, `on_hand_units == 0`) clustered specifically on high-velocity items with top weekly sales (>100 units/wk) and high unit margins ($180-$420), representing major missed revenue.

---

### 10. `10_data_quality_stress_test.csv`
- **Business Domain:** Multi-Division Performance Tracking & Data Engineering Stress Test
- **Data Grain:** Time-Series (26 Weekly Periods, 852 Records including duplicates and dirty values)
- **Intended Primary Measure:** `metric_value` (Unit: `Index`, Aggregation: `mean` or `sum`)
- **Recommended Dimensions:** `division`, `team`
- **Recommended Numeric Drivers:** `driver_a`, `driver_b`
- **Entity / ID Column:** `entity_id`
- **Intentional Controlled Quality Flaws to Test Profiler & Cleaning:**
  1. **Missing Values:** ~4% blank/empty strings in `metric_value` and ~5% missing values in `driver_a`.
  2. **Dirty Numeric Strings:** ~18% of numeric values formatted with currency signs and commas (`$1,240.50`), and percentages (`12.5%`).
  3. **Corrupted Dates:** A few unparseable date strings (`2025-99-99`, `INVALID_DATE`).
  4. **Duplicate Rows:** 20 exact duplicate rows injected at the end of the file.
  5. **Inconsistent Casing & Whitespace:** Category values with mixed casing and padding (e.g., `  ENTERPRISE SYSTEMS `, `enterprise systems`, `Fintech  Ops`).
  6. **True Analytical Pattern:** Despite the noise, Division `Commercial Tech` exhibits an authentic 48% performance decline from Week 14 onwards.
