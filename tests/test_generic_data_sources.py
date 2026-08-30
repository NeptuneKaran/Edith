"""
tests/test_generic_data_sources.py
Comprehensive automated test suite for EDITH's Generic Structured Data Ingestion,
Automated Profiling, Semantic Data Modeling, and Dynamic Analytics Architecture.

Tests cover:
1. DataProfiler (inferred types, null audits, summary statistics, semantic role heuristics)
2. SemanticDataModel & ColumnMapper transformation across 5 diverse business domains:
   - HR & Workforce (Headcount, Turnover, Department, Salary, Tenure)
   - Manufacturing & Operations (Defects, Plant, Line, Shift, Machine Speed)
   - Customer Support & Service (Resolution Time, CSAT, Channel, Priority)
   - Marketing Performance (CPL, Conversions, Campaign, Spend)
   - Finance & Cost Center Ledger (OpEx, Variance, Cost Center, Account)
3. Snapshot (cross-sectional / non-temporal) vs Time-Series data structures
4. AnalysisFeasibilityChecker (8-mode capability evaluation)
5. Dynamic Repository methods:
   - get_kpi_time_series() with custom aggregations (sum, mean, count, min, max)
   - get_dimensional_breakdown() across arbitrary multi-dimension sets
   - get_driver_correlations() with Pearson and Spearman metrics
   - get_distribution_statistics() with IQR boundaries and outlier detection
   - get_data_quality_report() with data health scores
6. Dynamic ContributionEngine & EvidenceEngine observational findings
"""
import sys
import os
import unittest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.source_manager import (
    DataProfiler,
    SemanticDataModel,
    AnalysisFeasibilityChecker,
    ColumnMapper
)
from data.repository import DataRepository
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine
from ai.offline_reasoner import OfflineEdithReasoner


class TestGenericDataSources(unittest.TestCase):
    """Test suite for generic structured business dataset profiling and dynamic analytics."""

    def setUp(self):
        """Set up diverse sample business datasets."""
        np.random.seed(42)
        
        # 1. HR Workforce Dataset
        departments = ["Engineering", "Sales", "Customer Success", "Marketing", "HR"]
        locations = ["US-West", "US-East", "EMEA", "APAC"]
        hr_records = []
        for month in range(1, 13):
            date_str = f"2025-{month:02d}-01"
            for dept in departments:
                for loc in locations:
                    hr_records.append({
                        "snapshot_date": date_str,
                        "department": dept,
                        "location": loc,
                        "headcount": np.random.randint(20, 150),
                        "turnover_rate": float(np.random.uniform(0.01, 0.08)),
                        "average_salary": float(np.random.uniform(70000, 160000)),
                        "average_tenure_years": float(np.random.uniform(1.2, 5.5))
                    })
        self.hr_df = pd.DataFrame(hr_records)

        # 2. Manufacturing Operations Dataset
        plants = ["Plant Alpha", "Plant Beta", "Plant Gamma"]
        lines = ["Line 1", "Line 2", "Line 3"]
        shifts = ["Day", "Night"]
        mfg_records = []
        for day in range(1, 31):
            date_str = f"2026-01-{day:02d}"
            for p in plants:
                for l in lines:
                    for s in shifts:
                        mfg_records.append({
                            "production_date": date_str,
                            "plant": p,
                            "line_id": l,
                            "shift": s,
                            "defect_count": np.random.randint(0, 45),
                            "units_produced": np.random.randint(500, 2000),
                            "machine_speed_rpm": float(np.random.uniform(1200, 1800)),
                            "downtime_hours": float(np.random.uniform(0.0, 4.5))
                        })
        self.mfg_df = pd.DataFrame(mfg_records)

        # 3. Customer Support Snapshot Dataset (Non-temporal)
        channels = ["Email", "Live Chat", "Phone", "Portal"]
        tiers = ["Tier 1", "Tier 2", "Escalations"]
        priorities = ["P1-Urgent", "P2-High", "P3-Medium", "P4-Low"]
        supp_records = []
        for i in range(500):
            supp_records.append({
                "ticket_id": f"TICK-{10000+i}",
                "channel": np.random.choice(channels),
                "tier": np.random.choice(tiers),
                "priority": np.random.choice(priorities),
                "resolution_time_hours": float(np.random.exponential(scale=6.0) + 0.5),
                "csat_score": float(np.random.uniform(1.0, 5.0)),
                "reopen_count": np.random.randint(0, 4)
            })
        self.supp_df = pd.DataFrame(supp_records)

    def test_01_data_profiler_comprehensive(self):
        """Verifies DataProfiler correctly profiles dtypes, nulls, cardinality, and role heuristics."""
        profiles = DataProfiler.profile_dataframe(self.hr_df)
        self.assertEqual(len(profiles), len(self.hr_df.columns))
        
        col_dict = {p["column_name"]: p for p in profiles}
        
        # Date detection
        self.assertEqual(col_dict["snapshot_date"]["semantic_guess"], "DATE")
        self.assertEqual(col_dict["snapshot_date"]["suggested_role"], "Date / Timestamp")
        
        # Category detection
        self.assertEqual(col_dict["department"]["semantic_guess"], "CATEGORY")
        self.assertIn(col_dict["location"]["semantic_guess"], ["GEOGRAPHY", "CATEGORY"])
        
        # Numeric measure & driver detection
        self.assertEqual(col_dict["headcount"]["semantic_guess"], "NUMERIC_MEASURE")
        self.assertIsNotNone(col_dict["average_salary"]["stats"])
        self.assertGreater(col_dict["average_salary"]["stats"]["mean"], 0)
        self.assertEqual(col_dict["turnover_rate"]["null_pct"], 0.0)

    def test_02_feasibility_time_series(self):
        """Verifies feasibility checks for a time-series dataset."""
        model = SemanticDataModel(
            dataset_name="HR Workforce",
            analysis_grain="Time Series",
            primary_measure="turnover_rate",
            primary_measure_label="Turnover Rate",
            primary_measure_unit="%",
            aggregation_type="mean",
            date_column="snapshot_date",
            dimension_columns=["department", "location"],
            driver_columns=["average_salary", "average_tenure_years"],
            is_demo=False
        )
        
        feas = AnalysisFeasibilityChecker.evaluate_feasibility(self.hr_df, model)
        self.assertTrue(feas["time_series_investigation"]["available"])
        self.assertTrue(feas["dimensional_breakdown"]["available"])
        self.assertTrue(feas["driver_correlation"]["available"])
        self.assertTrue(feas["data_quality_audit"]["available"])
        self.assertFalse(feas["counterfactual_simulation"]["available"])

    def test_03_feasibility_snapshot(self):
        """Verifies feasibility checks for a cross-sectional snapshot dataset."""
        model = SemanticDataModel(
            dataset_name="Support Snapshot",
            analysis_grain="Cross-Sectional Snapshot",
            primary_measure="resolution_time_hours",
            primary_measure_label="Resolution Time",
            primary_measure_unit="Hours",
            aggregation_type="mean",
            date_column=None,
            dimension_columns=["channel", "tier", "priority"],
            driver_columns=["csat_score", "reopen_count"],
            identifier_columns=["ticket_id"],
            is_demo=False
        )
        
        feas = AnalysisFeasibilityChecker.evaluate_feasibility(self.supp_df, model)
        self.assertTrue(feas["snapshot_analysis"]["available"])
        self.assertTrue(feas["dimensional_breakdown"]["available"])
        self.assertTrue(feas["driver_correlation"]["available"])
        self.assertTrue(feas["distribution_outlier"]["available"])
        self.assertFalse(feas["time_series_investigation"]["available"])


    def test_04_transform_generic_mfg_dataset(self):
        """Verifies ColumnMapper transforms a generic manufacturing dataset into normalized tables."""
        model = SemanticDataModel(
            dataset_name="Factory Defect Analytics",
            analysis_grain="Time Series",
            primary_measure="defect_count",
            primary_measure_label="Total Defects",
            primary_measure_unit="Defects",
            aggregation_type="sum",
            date_column="production_date",
            dimension_columns=["plant", "line_id", "shift"],
            driver_columns=["machine_speed_rpm", "downtime_hours"],
            is_demo=False
        )
        
        tables, feat_status, warnings = ColumnMapper.transform_generic_dataset(self.mfg_df, model)
        self.assertIn("sales", tables)
        df_sales = tables["sales"]
        
        self.assertIn("gross_revenue", df_sales.columns)
        self.assertIn("week_idx", df_sales.columns)
        self.assertIn("plant", df_sales.columns)
        self.assertIn("line_id", df_sales.columns)
        self.assertIn("shift", df_sales.columns)
        self.assertIn("machine_speed_rpm", df_sales.columns)
        self.assertIn("downtime_hours", df_sales.columns)
        self.assertEqual(len(df_sales), len(self.mfg_df))

    def test_05_repository_generic_hr_analytics(self):
        """Tests dynamic repository aggregation, dimensional breakdown, and driver correlations."""
        model = SemanticDataModel(
            dataset_name="HR Analytics",
            analysis_grain="Time Series",
            primary_measure="headcount",
            primary_measure_label="Total Headcount",
            primary_measure_unit="Employees",
            aggregation_type="sum",
            date_column="snapshot_date",
            dimension_columns=["department", "location"],
            driver_columns=["average_salary", "average_tenure_years"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(self.hr_df, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(
            tables=tables,
            source_info={"name": "HR Test", "is_demo": False, "row_count": len(self.hr_df)},
            semantic_model=model
        )
        
        # 1. KPI Time Series
        ts = repo.get_kpi_time_series()
        self.assertFalse(ts.empty)
        self.assertIn("week_idx", ts.columns)
        self.assertIn("value", ts.columns)
        self.assertGreater(ts["value"].sum(), 0)
        
        # 2. Dimensional Breakdown
        breakdowns = repo.get_dimensional_breakdown()
        self.assertIn("department", breakdowns)
        self.assertIn("location", breakdowns)
        self.assertFalse(breakdowns["department"].empty)
        self.assertIn("contribution_pct", breakdowns["department"].columns)
        
        # 3. Driver Correlations
        drv_corrs = repo.get_driver_correlations()
        self.assertIn("correlations", drv_corrs)
        self.assertIn("average_salary", drv_corrs["correlations"])
        self.assertIn("average_tenure_years", drv_corrs["correlations"])
        self.assertTrue(-1.0 <= drv_corrs["correlations"]["average_salary"]["pearson_r"] <= 1.0)
        
        # 4. Distribution Statistics
        dist_stats = repo.get_distribution_statistics()
        self.assertEqual(dist_stats["count"], len(self.hr_df))
        self.assertGreaterEqual(dist_stats["iqr"], 0)
        self.assertIn("outlier_count", dist_stats)
        
        # 5. Data Quality Report
        quality = repo.get_data_quality_report()
        self.assertGreaterEqual(quality["data_quality_score"], 95.0)
        self.assertEqual(quality["total_rows"], len(self.hr_df))

    def test_06_engines_observational_integrity(self):
        """Verifies that engines evaluate custom data as observational patterns without causal overreach."""
        model = SemanticDataModel(
            dataset_name="Plant Operations",
            analysis_grain="Time Series",
            primary_measure="defect_count",
            primary_measure_label="Defect Count",
            primary_measure_unit="Units",
            aggregation_type="sum",
            date_column="production_date",
            dimension_columns=["plant", "line_id", "shift"],
            driver_columns=["machine_speed_rpm", "downtime_hours"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(self.mfg_df, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(
            tables=tables,
            source_info={"name": "Plant Test", "is_demo": False, "row_count": len(self.mfg_df)},
            semantic_model=model
        )
        
        # Variance decomposition
        decomp = ContributionEngine.calculate_variance_decomposition(repo)
        self.assertIn(decomp["primary_dimension_name"], ["plant", "line_id", "shift"])
        self.assertIn("breakdowns", decomp)
        
        # Evidence Engine: Observational patterns
        ev_engine = EvidenceEngine(repo)
        patterns = ev_engine.evaluate_all_hypotheses()
        self.assertGreater(len(patterns), 0)
        
    def test_07_finance_cost_center_ledger(self):
        """Verifies finance OpEx ledger analysis (dates, cost center, expense category, actual cost, budget cost, variance)."""
        cost_centers = ["CC-101 Engineering", "CC-102 Marketing", "CC-103 Sales", "CC-104 Operations", "CC-105 G&A"]
        categories = ["Personnel", "Software Subscriptions", "Travel & Entertainment", "Consulting", "Facilities"]
        
        fin_records = []
        for m in range(1, 13):
            d_str = f"2025-{m:02d}-01"
            for cc in cost_centers:
                for cat in categories:
                    b_cost = float(np.random.uniform(5000, 50000))
                    a_cost = b_cost * float(np.random.uniform(0.85, 1.25))
                    fin_records.append({
                        "posting_date": d_str,
                        "cost_center": cc,
                        "expense_category": cat,
                        "actual_cost": a_cost,
                        "budget_cost": b_cost,
                        "variance": a_cost - b_cost
                    })
        fin_df = pd.DataFrame(fin_records)
        
        model = SemanticDataModel(
            dataset_name="Finance Cost Center Ledger",
            analysis_grain="Time Series",
            primary_measure="actual_cost",
            primary_measure_label="Actual OpEx",
            primary_measure_unit="$",
            aggregation_type="sum",
            date_column="posting_date",
            dimension_columns=["cost_center", "expense_category"],
            driver_columns=["budget_cost", "variance"],
            is_demo=False
        )
        
        tables, feat_status, warnings = ColumnMapper.transform_generic_dataset(fin_df, model)
        self.assertTrue(feat_status["is_temporal"])
        self.assertEqual(feat_status["total_records"], len(fin_df))
        
        repo = DataRepository.get_instance()
        repo.set_custom_data(tables, {"name": "Finance Ledger", "is_demo": False}, model)
        
        # Test dimensional breakdown
        breakdowns = repo.get_dimensional_breakdown()
        self.assertIn("cost_center", breakdowns)
        self.assertIn("expense_category", breakdowns)
        self.assertEqual(len(breakdowns["cost_center"]), len(cost_centers))
        
        # Test driver correlations
        drv_corrs = repo.get_driver_correlations()
        self.assertIn("budget_cost", drv_corrs["correlations"])
        self.assertGreater(drv_corrs["correlations"]["budget_cost"]["pearson_r"], 0.7)

    def test_08_marketing_performance_analytics(self):
        """Verifies multi-channel marketing campaign analysis (spend, impressions, clicks, conversions, revenue)."""
        campaigns = ["Spring Launch", "Brand Awareness", "Retargeting Q1", "Competitor Conquest"]
        channels = ["Google Search", "LinkedIn Ads", "Meta Ads", "YouTube Video", "Newsletter"]
        
        mkt_records = []
        for w in range(1, 21):
            d_str = f"2026-W{w:02d}"
            for camp in campaigns:
                for chan in channels:
                    spend = float(np.random.uniform(1000, 15000))
                    impr = int(spend * np.random.uniform(40, 100))
                    clicks = int(impr * np.random.uniform(0.01, 0.04))
                    convs = int(clicks * np.random.uniform(0.05, 0.15))
                    rev = float(convs * np.random.uniform(150, 450))
                    mkt_records.append({
                        "campaign_week": f"2026-01-{(w%28)+1:02d}",
                        "campaign_name": camp,
                        "channel": chan,
                        "media_spend": spend,
                        "impressions": impr,
                        "clicks": clicks,
                        "conversions": convs,
                        "attributed_revenue": rev
                    })
        mkt_df = pd.DataFrame(mkt_records)
        
        model = SemanticDataModel(
            dataset_name="Marketing Attribution & ROAS",
            analysis_grain="Time Series",
            primary_measure="conversions",
            primary_measure_label="Total Conversions",
            primary_measure_unit="Conversions",
            aggregation_type="sum",
            date_column="campaign_week",
            dimension_columns=["campaign_name", "channel"],
            driver_columns=["media_spend", "clicks", "impressions"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(mkt_df, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(tables, {"name": "Marketing Performance", "is_demo": False}, model)
        
        # Test time series aggregation
        ts = repo.get_kpi_time_series()
        self.assertGreater(len(ts), 1)
        self.assertGreater(ts["value"].sum(), 0)
        
        # Test correlations with multiple drivers
        corrs = repo.get_driver_correlations()["correlations"]
        self.assertIn("media_spend", corrs)
        self.assertIn("clicks", corrs)
        self.assertGreater(corrs["clicks"]["pearson_r"], 0.5)

    def test_09_snapshot_non_temporal_no_fake_dates(self):
        """Proves that datasets configured as Cross-Sectional Snapshot do NOT fabricate fake sequential dates or corridor anomalies."""
        from core.baseline_engine import AnomalyEngine
        
        snapshot_df = pd.DataFrame({
            "employee_id": [f"EMP-{i:04d}" for i in range(100)],
            "office_location": np.random.choice(["San Francisco", "New York", "London", "Tokyo"], 100),
            "job_family": np.random.choice(["Sales", "Engineering", "Design", "Product"], 100),
            "engagement_score": np.random.uniform(50, 100, 100),
            "tenure_months": np.random.randint(6, 60, 100)
        })
        
        model = SemanticDataModel(
            dataset_name="Q1 Employee Engagement Snapshot",
            analysis_grain="Cross-Sectional Snapshot",
            primary_measure="engagement_score",
            primary_measure_label="Engagement Score",
            primary_measure_unit="Score",
            aggregation_type="mean",
            date_column=None,
            dimension_columns=["office_location", "job_family"],
            driver_columns=["tenure_months"],
            identifier_columns=["employee_id"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(snapshot_df, model)
        df_sales = tables["sales"]
        
        # 1. Verify no fake sequential weeks were created
        self.assertFalse(feat_status["is_temporal"])
        self.assertEqual(df_sales["week_idx"].nunique(), 1)
        self.assertEqual(df_sales["week_label"].iloc[0], "Snapshot")
        self.assertEqual(feat_status["total_periods"], 1)
        
        # 2. Verify AnomalyEngine does NOT trigger false alarms
        repo = DataRepository.get_instance()
        repo.set_custom_data(tables, {"name": "Engagement Snapshot", "is_demo": False, "feature_status": feat_status}, model)
        
        ts = repo.get_kpi_time_series()
        anom_res = AnomalyEngine.evaluate_current_anomaly(ts, kpi_name="Engagement Score")
        self.assertFalse(anom_res["is_anomaly"])
        self.assertEqual(anom_res["z_score"], 0.0)
        self.assertEqual(anom_res["status_label"], "Cross-Sectional Snapshot")
        
        # 3. Verify snapshot dimensional breakdown runs cleanly
        breakdowns = repo.get_dimensional_breakdown()
        self.assertIn("office_location", breakdowns)
        self.assertIn("contribution_pct", breakdowns["office_location"].columns)

    def test_10_field_type_validation_rejection(self):
        """Verifies that non-numeric text selected as primary measure or numeric driver is strictly rejected."""
        dirty_df = pd.DataFrame({
            "record_id": [f"ID-{i}" for i in range(20)],
            "category_name": ["Alpha", "Beta", "Gamma", "Delta"] * 5,
            "pure_text_field": ["NonNumericText", "Words", "Labels", "Strings"] * 5,
            "valid_numeric": np.random.uniform(10, 100, 20),
            "invalid_dates": ["NotADate", "Invalid", "RandomString", "Broken"] * 5
        })
        
        # 1. Selecting pure text as Primary Measure MUST raise ValueError
        model_bad_measure = SemanticDataModel(
            dataset_name="Bad Measure Test",
            analysis_grain="Cross-Sectional Snapshot",
            primary_measure="pure_text_field",
            is_demo=False
        )
        with self.assertRaises(ValueError) as ctx_measure:
            ColumnMapper.transform_generic_dataset(dirty_df, model_bad_measure)
        self.assertIn("contains non-numeric text", str(ctx_measure.exception))
        
        # 2. Selecting pure text as Numeric Driver MUST raise ValueError
        model_bad_driver = SemanticDataModel(
            dataset_name="Bad Driver Test",
            analysis_grain="Cross-Sectional Snapshot",
            primary_measure="valid_numeric",
            driver_columns=["pure_text_field"],
            is_demo=False
        )
        with self.assertRaises(ValueError) as ctx_driver:
            ColumnMapper.transform_generic_dataset(dirty_df, model_bad_driver)
        self.assertIn("Numeric driver 'pure_text_field' contains non-numeric text", str(ctx_driver.exception))
        
        # 3. Profiler helper functions verify valid type columns
        valid_nums = DataProfiler.get_valid_numeric_columns(dirty_df)
        self.assertIn("valid_numeric", valid_nums)
        self.assertNotIn("pure_text_field", valid_nums)
        self.assertNotIn("category_name", valid_nums)

    def test_11_distinct_count_repeated_ids(self):
        """Verifies distinct-count aggregation correctly computes unique entity counts (nunique) across repeated IDs."""
        events_df = pd.DataFrame({
            "event_date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02", "2026-01-02"] * 10,
            "region": ["West", "West", "East", "East", "West"] * 10,
            "customer_id": ["CUST-001", "CUST-001", "CUST-002", "CUST-003", "CUST-001"] * 10, # CUST-001 repeated
            "event_value": [10.0, 20.0, 15.0, 30.0, 25.0] * 10
        })
        
        model = SemanticDataModel(
            dataset_name="User Event Stream",
            analysis_grain="Time Series",
            primary_measure="event_value",
            primary_measure_label="Active Customers",
            primary_measure_unit="Users",
            aggregation_type="distinct_count",
            distinct_entity_column="customer_id",
            date_column="event_date",
            dimension_columns=["region"],
            identifier_columns=["customer_id"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(events_df, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(tables, {"name": "Event Stream", "is_demo": False}, model)
        
        # 1. KPI time series distinct count
        ts = repo.get_kpi_time_series()
        self.assertFalse(ts.empty)
        # Total distinct customers overall is 3 (CUST-001, CUST-002, CUST-003)
        for _, row in ts.iterrows():
            self.assertLessEqual(row["value"], 3)
            
        # 2. Dimensional breakdown distinct count
        breakdowns = repo.get_dimensional_breakdown()
        self.assertIn("region", breakdowns)
        df_reg = breakdowns["region"]
        # CUST-001 in West; CUST-002 and CUST-003 in East
        west_val = df_reg[df_reg["region"] == "West"]["curr_value"].iloc[0]
        east_val = df_reg[df_reg["region"] == "East"]["curr_value"].iloc[0]
        self.assertEqual(west_val, 1) # CUST-001 only
        self.assertEqual(east_val, 2) # CUST-002 and CUST-003

    def test_12_dynamic_neutral_labels_and_briefing(self):
        """Verifies that OfflineEdithReasoner uses neutral dynamic terminology for custom datasets without sales jargon."""
        from ai.offline_reasoner import OfflineEdithReasoner
        
        model = SemanticDataModel(
            dataset_name="Plant Defect Audit",
            analysis_grain="Cross-Sectional Snapshot",
            primary_measure="defect_count",
            primary_measure_label="Defect Count",
            primary_measure_unit="Defects",
            aggregation_type="sum",
            dimension_columns=["plant", "line_id"],
            driver_columns=["machine_speed_rpm"],
            is_demo=False
        )
        
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(self.mfg_df, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(tables, {"name": "Plant Audit", "is_demo": False, "feature_status": feat_status}, model)
        
        ev = EvidenceEngine(repo)
        patterns = ev.evaluate_all_hypotheses()
        
        anom_ctx = {
            "kpi_name": "Defect Count",
            "current_value": 450.0,
            "status_label": "Cross-Sectional Snapshot",
            "is_anomaly": False
        }
        
        # 1. Generate Briefing
        briefing = OfflineEdithReasoner.generate_investigation_briefing(anom_ctx, patterns)
        self.assertIn("Defect Count Analysis", briefing)
        self.assertNotIn("Enterprise Suite Alpha", briefing)
        self.assertNotIn("Price Hike", briefing)
        self.assertIn("Observational Findings", briefing)
        
        # 2. Answer neutral starter questions
        resp_q1 = OfflineEdithReasoner.answer_query(
            "What changed in the selected metric?",
            anom_ctx, patterns[0], patterns
        )
        self.assertIn("Observed Metric Summary", resp_q1)
        
        resp_q2 = OfflineEdithReasoner.answer_query(
            "Which groups show the greatest concentration?",
            anom_ctx, patterns[0], patterns
        )
        self.assertIn("Dimensional Concentration Analysis", resp_q2)
        
        resp_q3 = OfflineEdithReasoner.answer_query(
            "Which numeric fields have the strongest observed association?",
            anom_ctx, patterns[0], patterns
        )
        self.assertIn("Numeric Driver Associations", resp_q3)
        self.assertIn("Pearson", resp_q3)
        
        resp_q4 = OfflineEdithReasoner.answer_query(
            "Summarize data-quality issues.",
            anom_ctx, patterns[0], patterns
        )
        self.assertIn("Data Quality Audit Report", resp_q4)
        self.assertIn("Overall Data Quality Score", resp_q4)

    def test_13_what_affected_custom_metric_plain_language(self):
        """
        Verifies that querying 'WHAT AFFECTED ATTRITION RATE' or similar factor questions
        on custom datasets returns grounded explanations without hallucinating demo sales/Region B facts.
        """
        import io
        hr_csv = """date,department,location,avg_salary,headcount,attrition_rate
2025-01-01,Engineering,US,120000,50,0.02
2025-01-08,Engineering,US,120000,52,0.01
2025-01-01,Sales,EU,90000,30,0.05
2025-01-08,Sales,EU,90000,28,0.07
"""
        df_hr = pd.read_csv(io.StringIO(hr_csv))
        model = SemanticDataModel(
            dataset_name="HR Workforce Analytics",
            primary_measure="attrition_rate",
            primary_measure_label="Attrition Rate",
            primary_measure_unit="%",
            aggregation_type="mean",
            date_column="date",
            dimension_columns=["department", "location"],
            driver_columns=["avg_salary", "headcount"],
            is_demo=False
        )
        tables, feat_status, _ = ColumnMapper.transform_generic_dataset(df_hr, model)
        repo = DataRepository.get_instance()
        repo.set_custom_data(
            tables=tables,
            source_info={"name": "HR Workforce Analytics", "is_demo": False, "row_count": len(df_hr), "primary_measure_label": "Attrition Rate"},
            semantic_model=model
        )
        
        anom_ctx = {
            "kpi_name": "Attrition Rate",
            "current_value": 0.04,
            "baseline_value": 0.03,
            "delta_pct": 33.3,
            "z_score": 1.5,
            "status_label": "Cross-Sectional Snapshot"
        }
        
        # Test Plain Language / Business User mode
        resp_gu = OfflineEdithReasoner.answer_query(
            "WHAT AFFECTED ATTRITION RATE",
            anom_ctx, {}, [], persona="general_user"
        )
        self.assertIn("Attrition Rate", resp_gu)
        self.assertIn("Avg Salary", resp_gu)
        self.assertNotIn("Enterprise Suite Alpha", resp_gu)
        self.assertNotIn("Region B", resp_gu)
        self.assertNotIn("warehouse", resp_gu.lower())
        self.assertNotIn("sales experienced a noticeable drop", resp_gu.lower())
        
        # Test Executive mode
        resp_exec = OfflineEdithReasoner.answer_query(
            "What factors drive attrition rate?",
            anom_ctx, {}, [], persona="executive"
        )
        self.assertIn("Attrition Rate", resp_exec)
        self.assertIn("Pearson", resp_exec)
        self.assertNotIn("ApexTech", resp_exec)
        self.assertNotIn("price hike", resp_exec.lower())

    def tearDown(self):
        """Reset repository to demo dataset benchmark after tests."""
        repo = DataRepository.get_instance()
        repo.reset_to_demo_dataset()


if __name__ == "__main__":
    unittest.main()


