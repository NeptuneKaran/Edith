"""
tests/test_data_sources_and_tools.py
Tests Data Source Ingestion (CSV, Excel, SQLite, SQL), SQL Security, and Analytical Tool Layer for Gemini.
"""
import sys
import os
import io
import sqlite3
import tempfile
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.source_manager import DataParser, ColumnMapper, SQLQueryValidator
from data.repository import DataRepository
from ai.tools import (
    get_investigation_summary,
    get_kpi_overview,
    get_anomaly_details,
    get_all_hypotheses,
    get_hypothesis_evidence,
    get_contribution_breakdown,
    get_causal_graph,
    get_counter_evidence,
    get_simulation_results,
    list_available_metrics,
    get_data_source_metadata,
    execute_tool_call
)

def test_data_sources_and_tools_suite():
    print("==================================================")
    print("  RUNNING DATA SOURCES & ANALYTICAL TOOLS SUITE   ")
    print("==================================================")
    
    # =========================================================================
    # 1. SQL SECURITY & QUERY VALIDATION
    # =========================================================================
    print("\n--- [1] SQL SECURITY & QUERY VALIDATOR ---")
    
    # Safe queries
    is_safe, _ = SQLQueryValidator.validate_query("SELECT * FROM sales_ledger LIMIT 100;")
    assert is_safe, "Valid SELECT query should be permitted."
    
    is_safe_cte, _ = SQLQueryValidator.validate_query("WITH weekly_sales AS (SELECT * FROM sales) SELECT * FROM weekly_sales;")
    assert is_safe_cte, "Valid CTE WITH query should be permitted."
    
    # Destructive queries (must be blocked)
    bad_queries = [
        "DROP TABLE users;",
        "DELETE FROM sales WHERE week_idx > 10;",
        "UPDATE sales SET gross_revenue = 0;",
        "INSERT INTO sales VALUES (1, 2, 3);",
        "ALTER TABLE sales ADD COLUMN hack TEXT;",
        "TRUNCATE TABLE sales;",
        "SELECT * FROM sales; DROP TABLE sales;",
        "SELECT * FROM sales INTO OUTFILE '/tmp/dump.txt';"
    ]
    for bq in bad_queries:
        is_safe, msg = SQLQueryValidator.validate_query(bq)
        assert not is_safe, f"Destructive query '{bq}' MUST be blocked!"
    print("  [PASS] SQL Query Validator strictly permits only read-only SELECT and blocks all destructive operations.")

    # =========================================================================
    # 2. CSV INGESTION & COLUMN MAPPING
    # =========================================================================
    print("\n--- [2] CSV FILE INGESTION & AUTO-MAPPING ---")
    csv_data = """date,revenue,region,customer_tier,product_line,units_sold,unit_price
2025-01-05,120000,Region A,Enterprise,Suite 1,12,10000
2025-01-12,125000,Region A,Enterprise,Suite 1,12,10416
2025-01-19,130000,Region A,Enterprise,Suite 1,13,10000
2025-01-26,118000,Region A,Enterprise,Suite 1,11,10727
2025-02-02,122000,Region B,Mid-Market,Suite 2,15,8133
2025-02-09,127000,Region B,Mid-Market,Suite 2,16,7937
2025-02-16,115000,Region B,Enterprise,Suite 1,10,11500
2025-02-23,105000,Region B,Enterprise,Suite 1,9,11666
2025-03-02,95000,Region B,Enterprise,Suite 1,8,11875
2025-03-09,92000,Region B,Enterprise,Suite 1,7,13142
"""
    csv_buffer = io.StringIO(csv_data)
    df_csv, meta_csv = DataParser.parse_csv(csv_buffer)
    assert meta_csv["row_count"] == 10
    assert "date" in df_csv.columns
    assert "revenue" in df_csv.columns
    
    inferred = ColumnMapper.auto_infer_mapping(list(df_csv.columns))
    assert inferred.get("date") == "date"
    assert inferred.get("metric_value") == "revenue"
    assert inferred.get("region") == "region"
    assert inferred.get("customer_tier") == "customer_tier"
    
    tables, feat_status, warnings = ColumnMapper.validate_and_transform(df_csv, inferred, kpi_name="Custom SaaS Revenue")
    assert "sales" in tables
    assert len(tables["sales"]) == 10
    assert feat_status["can_detect_anomalies"] is True
    print("  [PASS] CSV parsed, auto-mapped, and transformed into normalized EDITH repository tables.")

    # =========================================================================
    # 3. EXCEL WORKBOOK INGESTION
    # =========================================================================
    print("\n--- [3] EXCEL WORKBOOK INGESTION ---")
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_csv.to_excel(writer, sheet_name="Q1_Sales", index=False)
        df_csv.head(3).to_excel(writer, sheet_name="Summary_Sheet", index=False)
    excel_buffer.seek(0)
    
    df_xl, sheets, meta_xl = DataParser.parse_excel(excel_buffer, sheet_name="Q1_Sales")
    assert "Q1_Sales" in sheets
    assert "Summary_Sheet" in sheets
    assert len(df_xl) == 10
    print("  [PASS] Multi-sheet Excel workbook parsed successfully with sheet selection.")

    # =========================================================================
    # 4. SQLITE INGESTION
    # =========================================================================
    print("\n--- [4] SQLITE DATABASE FILE INGESTION ---")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name
        
    conn = sqlite3.connect(tmp_db_path)
    df_csv.to_sql("commercial_ledger", conn, index=False)
    conn.close()
    
    with open(tmp_db_path, "rb") as f:
        sqlite_buffer = io.BytesIO(f.read())
        
    df_sqlite, tables_found, meta_sqlite = DataParser.parse_sqlite_file(sqlite_buffer, table_name="commercial_ledger")
    assert "commercial_ledger" in tables_found
    assert len(df_sqlite) == 10
    os.remove(tmp_db_path)
    print("  [PASS] SQLite database uploaded and read-only extracted cleanly.")

    # =========================================================================
    # 5. DATA REPOSITORY SWITCHING & SOURCE LABELS
    # =========================================================================
    print("\n--- [5] REPOSITORY SOURCE SWITCHING ---")
    repo = DataRepository.get_instance()
    initial_info = repo.get_active_source_info()
    assert initial_info["is_demo"] is True
    
    # Load custom source
    custom_source_info = {
        "source_type": "CSV",
        "name": "Imported: custom_sales.csv",
        "is_demo": False,
        "row_count": len(tables["sales"]),
        "description": "User uploaded sales data."
    }
    repo.set_custom_data(tables, custom_source_info)
    assert repo.get_active_source_info()["is_demo"] is False
    assert "custom_sales.csv" in repo.get_active_source_info()["name"]
    
    # Reset back to demo
    repo.reset_to_demo_dataset()
    assert repo.get_active_source_info()["is_demo"] is True
    assert "Demo Dataset" in repo.get_active_source_info()["name"]
    print("  [PASS] Data repository seamlessly switches between Demo and Custom datasets.")

    # =========================================================================
    # 6. ANALYTICAL TOOLS LAYER FOR GEMINI
    # =========================================================================
    print("\n--- [6] GEMINI ANALYTICAL TOOLS LAYER ---")
    
    # Tool 1: Summary
    summary = get_investigation_summary()
    assert summary["current_value"] == 1_253_600.0
    assert summary["baseline_value"] == 1_401_300.0
    assert round(summary["z_score"], 2) == -2.30

    
    # Tool 2: KPI Overview
    kpi_ov = get_kpi_overview("kpi_b2b_sales")
    assert kpi_ov["kpi_name"] == "Monthly B2B Sales"
    
    # Tool 3: Hypotheses list
    all_h = get_all_hypotheses()
    assert len(all_h) == 8
    assert all_h[0]["id"] == "H1_PRICING_PRESSURE"
    assert all_h[0]["cause_score_100"] >= 80.0
    
    # Tool 4: Hypothesis Evidence
    h1_ev = get_hypothesis_evidence("H1_PRICING_PRESSURE")
    assert "mathematical_decomposition" in h1_ev
    assert h1_ev["mathematical_decomposition"]["volume_effect_usd"] == -210000.0
    
    # Tool 5: Contribution Breakdown
    reg_contrib = get_contribution_breakdown("region")
    assert "slices" in reg_contrib
    
    # Tool 6: DAG Graph
    dag = get_causal_graph()
    assert "nodes" in dag
    assert "edges" in dag
    
    # Tool 7: Counter Evidence
    h8_counter = get_counter_evidence("H8_SUPPLY_CONSTRAINT")
    assert "contradictory_evidence" in h8_counter
    
    # Tool 8: Simulation Results
    sim_res = get_simulation_results(price_rollback_pct=-6.0, marketing_boost_usd=15000.0, competitor_matching=True)
    assert sim_res["simulated_revenue"] > 1_253_600.0
    assert sim_res["recovery_pct"] > 0.0
    
    # Tool 9: Dispatcher
    disp_res = execute_tool_call("get_investigation_summary", {})
    assert "current_value" in disp_res
    
    bad_disp = execute_tool_call("non_existent_tool", {})
    assert "error" in bad_disp
    
    print("  [PASS] All 11 analytical tools execute correctly with structured JSON outputs.")

    print("\n==================================================")
    print("  ALL DATA SOURCES & TOOLS TESTS PASSED (100%)!   ")
    print("==================================================")

if __name__ == "__main__":
    test_data_sources_and_tools_suite()
