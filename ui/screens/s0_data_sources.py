"""
ui/screens/s0_data_sources.py
Screen 0: Data Sources & Ingestion Manager for EDITH.
Allows users to securely load, preview, map, and analyze custom CSV, Excel, SQLite, and SQL datasets.
"""
import streamlit as st
import pandas as pd
from data.repository import DataRepository
from data.source_manager import DataParser, ColumnMapper, SQLQueryValidator
from state.session_state import set_screen
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine

def render_screen_0():
    """Renders the Data Sources management and ingestion screen."""
    st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #0F172A;'>📂 Data Sources & Ingestion Manager</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 13px; color: #64748B; margin-top: 2px;'>Select the built-in demo dataset or securely import and map real business data from CSV, Excel, or SQL sources.</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    active_source = repo.get_active_source_info()
    
    # 1. Active Data Source Status Banner
    is_demo = active_source.get("is_demo", True)
    badge_bg = "#EFF6FF" if is_demo else "#F0FDF4"
    badge_color = "#1D4ED8" if is_demo else "#166534"
    badge_border = "#BFDBFE" if is_demo else "#BBF7D0"
    source_label = "Built-in Demo Dataset" if is_demo else "Custom Imported Dataset"
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid {badge_border}; border-left: 5px solid {badge_color}; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 11px; font-weight: 800; color: {badge_color}; letter-spacing: 0.5px; text-transform: uppercase;">ACTIVE INVESTIGATION DATA SOURCE</div>
                    <div style="font-size: 17px; font-weight: 800; color: #0F172A; margin-top: 2px;">{active_source.get('name', 'EDITH Dataset')}</div>
                    <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
                        Type: <b>{active_source.get('source_type', 'Demo')}</b> &bull; Rows: <b>{active_source.get('row_count', 0):,}</b> &bull; {active_source.get('description', '')}
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 6px;">
                        {source_label}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2. Source Ingestion Tabs
    tab_demo, tab_file, tab_sql = st.tabs([
        "📊 Built-in Demo Dataset",
        "📁 Upload File (CSV / Excel / SQLite)",
        "🔌 Connect SQL Database"
    ])
    
    # -------------------------------------------------------------------------
    # TAB 1: BUILT-IN DEMO DATASET
    # -------------------------------------------------------------------------
    with tab_demo:
        st.markdown("<h3 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>Standard Enterprise B2B SaaS Benchmark</h3>", unsafe_allow_html=True)
        st.write("""
        The built-in dataset represents a 52-week commercial ledger for a multi-regional B2B SaaS company ($1.4M weekly run rate).
        It includes logged marketing campaigns, price adjustments, inventory logistics, competitor scraper feeds, and customer feedback logs.
        """)
        
        col_d1, col_d2 = st.columns([1.5, 3.0])
        with col_d1:
            if st.button("🔄 Activate / Reset Built-in Demo Dataset", key="btn_reset_demo_data", type="primary", use_container_width=True):
                repo.reset_to_demo_dataset()
                _reinitialize_analytics()
                st.success("✅ Demo dataset activated successfully!")
                st.rerun()
                
    # -------------------------------------------------------------------------
    # TAB 2: FILE UPLOAD (CSV / Excel / SQLite)
    # -------------------------------------------------------------------------
    with tab_file:
        st.markdown("<h3 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>Upload Structured File</h3>", unsafe_allow_html=True)
        st.caption("Upload `.csv`, `.xlsx`, `.xls`, or `.db`/`.sqlite` files. Data is session-scoped and never stored permanently.")
        
        uploaded_file = st.file_uploader(
            "Choose a business data file",
            type=["csv", "xlsx", "xls", "db", "sqlite"],
            key="file_uploader_input"
        )
        
        if uploaded_file is not None:
            file_name = uploaded_file.name.lower()
            df_raw = None
            meta_raw = {}
            
            try:
                if file_name.endswith(".csv"):
                    df_raw, meta_raw = DataParser.parse_csv(uploaded_file)
                elif file_name.endswith((".xlsx", ".xls")):
                    # Check sheet selection
                    xl = pd.ExcelFile(uploaded_file)
                    sheets = xl.sheet_names
                    sel_sheet = sheets[0]
                    if len(sheets) > 1:
                        sel_sheet = st.selectbox("Select Worksheet:", options=sheets, key="excel_sheet_selector")
                    df_raw, _, meta_raw = DataParser.parse_excel(uploaded_file, sheet_name=sel_sheet)
                elif file_name.endswith((".db", ".sqlite")):
                    df_raw, _, meta_raw = DataParser.parse_sqlite_file(uploaded_file)
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                
            if df_raw is not None and not df_raw.empty:
                # File Preview Strip
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin: 12px 0; font-size: 12px; color: #334155;">
                        📄 <b>File Summary:</b> {uploaded_file.name} &bull; <b>{len(df_raw):,}</b> rows &bull; <b>{len(df_raw.columns)}</b> columns
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                with st.expander("👁️ Preview Raw Data & Data Types (First 10 Rows)", expanded=False):
                    st.dataframe(df_raw.head(10), use_container_width=True)
                    st.json(meta_raw.get("dtypes", {}))
                    
                st.markdown("---")
                st.markdown("<h4 style='font-size: 14px; font-weight: 700; color: #0F172A;'>🗺️ Step 2: Map Columns to EDITH Analytical Schema</h4>", unsafe_allow_html=True)
                st.caption("Map your dataset's columns to EDITH's core dimensions:")
                
                # Auto inference
                inferred = ColumnMapper.auto_infer_mapping(list(df_raw.columns))
                all_cols_with_none = ["None / Unmapped"] + list(df_raw.columns)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    metric_name_input = st.text_input("Target Metric / KPI Name:", value="Monthly Business Sales", key="map_kpi_name")
                    
                    # Date (Required)
                    default_date_idx = all_cols_with_none.index(inferred.get("date")) if inferred.get("date") in all_cols_with_none else 1
                    map_date = st.selectbox("Date / Timestamp Column (*Required):", options=list(df_raw.columns), index=default_date_idx-1 if default_date_idx > 0 else 0, key="map_date_sel")
                    
                    # Metric Value (Required)
                    default_val_idx = all_cols_with_none.index(inferred.get("metric_value")) if inferred.get("metric_value") in all_cols_with_none else 0
                    map_val = st.selectbox("Metric Value / Revenue Column (*Required):", options=list(df_raw.columns), index=default_val_idx-1 if default_val_idx > 0 else 0, key="map_val_sel")
                    
                    # Region
                    default_reg_idx = all_cols_with_none.index(inferred.get("region")) if inferred.get("region") in all_cols_with_none else 0
                    map_reg = st.selectbox("Region / Geography (Optional):", options=all_cols_with_none, index=default_reg_idx, key="map_reg_sel")
                    
                with col_m2:
                    # Customer Tier
                    default_tier_idx = all_cols_with_none.index(inferred.get("customer_tier")) if inferred.get("customer_tier") in all_cols_with_none else 0
                    map_tier = st.selectbox("Customer Tier / Segment (Optional):", options=all_cols_with_none, index=default_tier_idx, key="map_tier_sel")
                    
                    # Product Line
                    default_prod_idx = all_cols_with_none.index(inferred.get("product_line")) if inferred.get("product_line") in all_cols_with_none else 0
                    map_prod = st.selectbox("Product Line / SKU (Optional):", options=all_cols_with_none, index=default_prod_idx, key="map_prod_sel")
                    
                    # Channel
                    default_chan_idx = all_cols_with_none.index(inferred.get("channel")) if inferred.get("channel") in all_cols_with_none else 0
                    map_chan = st.selectbox("Sales Channel (Optional):", options=all_cols_with_none, index=default_chan_idx, key="map_chan_sel")
                    
                    # Unit Price driver
                    default_p_idx = all_cols_with_none.index(inferred.get("unit_price")) if inferred.get("unit_price") in all_cols_with_none else 0
                    map_price = st.selectbox("Unit Price Driver (Optional):", options=all_cols_with_none, index=default_p_idx, key="map_price_sel")
                    
                user_mapping = {
                    "date": map_date,
                    "metric_value": map_val,
                    "region": None if map_reg == "None / Unmapped" else map_reg,
                    "customer_tier": None if map_tier == "None / Unmapped" else map_tier,
                    "product_line": None if map_prod == "None / Unmapped" else map_prod,
                    "channel": None if map_chan == "None / Unmapped" else map_chan,
                    "unit_price": None if map_price == "None / Unmapped" else map_price,
                    "units_sold": None
                }
                
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                
                if st.button("🚀 Validate & Load Custom Dataset for Investigation", key="btn_confirm_import_file", type="primary", use_container_width=True):
                    try:
                        tables, feat_status, warnings = ColumnMapper.validate_and_transform(df_raw, user_mapping, kpi_name=metric_name_input)
                        
                        source_info = {
                            "source_type": meta_raw.get("source_type", "File Upload"),
                            "name": f"Imported: {uploaded_file.name}",
                            "is_demo": False,
                            "row_count": len(tables["sales"]),
                            "description": f"Custom dataset ({feat_status['date_range']}) with {len(feat_status['mapped_dimensions'])} mapped dimensions.",
                            "feature_status": feat_status
                        }
                        
                        repo.set_custom_data(tables, source_info)
                        _reinitialize_analytics(kpi_name=metric_name_input)
                        
                        st.success(f"✅ Successfully imported {uploaded_file.name}! {len(tables['sales']):,} rows loaded.")
                        if warnings:
                            for w in warnings:
                                st.warning(f"⚠️ {w}")
                        set_screen("overview")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Validation Error: {str(e)}")

    # -------------------------------------------------------------------------
    # TAB 3: CONNECT SQL DATABASE
    # -------------------------------------------------------------------------
    with tab_sql:
        st.markdown("<h3 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>Connect to SQL Database</h3>", unsafe_allow_html=True)
        st.caption("Securely connect to PostgreSQL, MySQL, SQLite, or Microsoft SQL Server in read-only mode.")
        
        col_db1, col_db2 = st.columns(2)
        with col_db1:
            db_type = st.selectbox("Database Engine:", options=["PostgreSQL", "MySQL", "Microsoft SQL Server"], key="sql_db_type")
            host = st.text_input("Host / Server:", value="localhost", key="sql_host")
            default_port = 5432 if db_type == "PostgreSQL" else (3306 if db_type == "MySQL" else 1433)
            port = st.number_input("Port:", value=default_port, step=1, key="sql_port")
            dbname = st.text_input("Database Name:", value="analytics_db", key="sql_dbname")
            
        with col_db2:
            user = st.text_input("Username:", value="edith_reader", key="sql_user")
            password = st.text_input("Password:", type="password", key="sql_password", help="Credentials are session-only and never logged or stored.")
            ssl_choice = st.selectbox("SSL Mode:", options=["prefer", "require", "disable"], key="sql_ssl")
            read_only_query = st.text_area("Read-Only SQL Query (Optional):", value="SELECT * FROM sales_ledger LIMIT 10000;", help="Must be a single SELECT statement. Modifying statements are blocked.", key="sql_query_input")

        st.info("ℹ️ **Render Deployment Notice:** Cloud-hosted deployments cannot access local private databases unless exposed via public IP/tunnel or secure cloud gateway.")
        
        if st.button("🔌 Test Connection & Fetch SQL Data", key="btn_test_sql_conn", type="secondary", use_container_width=True):
            try:
                df_sql, tables, meta_sql = DataParser.parse_sql_connection(
                    db_type=db_type,
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    query=read_only_query,
                    ssl_mode=ssl_choice
                )
                st.success(f"✅ Successfully queried {len(df_sql):,} rows from {dbname}!")
                st.dataframe(df_sql.head(5), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Connection / Query Failed: {str(e)}")

def _reinitialize_analytics(kpi_name: str = "Monthly B2B Sales"):
    """Recalculates baselines and hypotheses for newly loaded data source."""
    repo = DataRepository.get_instance()
    df_ts = repo.get_kpi_time_series("kpi_b2b_sales")
    df_analyzed = AnomalyEngine.calculate_baseline_and_corridor(df_ts)
    anomaly_ctx = AnomalyEngine.evaluate_current_anomaly(df_analyzed, kpi_name=kpi_name)
    
    contribution_ctx = ContributionEngine.calculate_variance_decomposition(repo, "kpi_b2b_sales")
    evidence_eng = EvidenceEngine(repo)
    hypotheses = evidence_eng.evaluate_all_hypotheses("kpi_b2b_sales")
    
    st.session_state.kpi_ts = df_analyzed
    st.session_state.anomaly_context = anomaly_ctx
    st.session_state.contribution_context = contribution_ctx
    st.session_state.hypotheses = hypotheses
    st.session_state.edith_briefing = ""
    st.session_state.chat_history = []
