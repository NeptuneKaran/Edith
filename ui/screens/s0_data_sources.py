"""
ui/screens/s0_data_sources.py
Screen 0: Data Sources, Generic Profiling & Analytical Model Configuration for EDITH.
Allows users to securely load, profile, map, and analyze arbitrary business datasets
(HR, Operations, Finance, Support, Marketing, Manufacturing, Sales) from CSV, Excel, SQLite, and SQL databases.
"""
import streamlit as st
import pandas as pd
from data.repository import DataRepository
from data.source_manager import DataParser, ColumnMapper, SQLQueryValidator, DataProfiler, SemanticDataModel, AnalysisFeasibilityChecker
from state.session_state import set_screen
from core.baseline_engine import AnomalyEngine
from core.contribution_engine import ContributionEngine
from core.evidence_engine import EvidenceEngine


def render_screen_0():
    """Renders the Data Sources management, profiling, and configuration screen."""
    st.markdown("<h2 style='margin:0; padding:0; font-size: 22px; font-weight: 800; color: #0F172A;'>📂 Data Sources & Analytical Model Manager</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 13px; color: #64748B; margin-top: 2px;'>Select the built-in demo benchmark or securely profile and configure any structured business dataset (Operations, HR, Support, Finance, Marketing, Sales).</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    repo = DataRepository.get_instance()
    active_source = repo.get_active_source_info()
    
    # 1. Active Data Source Status Banner
    is_demo = active_source.get("is_demo", True)
    badge_bg = "#EFF6FF" if is_demo else "#F0FDF4"
    badge_color = "#1D4ED8" if is_demo else "#166534"
    badge_border = "#BFDBFE" if is_demo else "#BBF7D0"
    source_label = "Built-in Demo Benchmark" if is_demo else "Custom Configured Dataset"
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid {badge_border}; border-left: 5px solid {badge_color}; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 11px; font-weight: 800; color: {badge_color}; letter-spacing: 0.5px; text-transform: uppercase;">ACTIVE INVESTIGATION DATASET</div>
                    <div style="font-size: 17px; font-weight: 800; color: #0F172A; margin-top: 2px;">{active_source.get('name', 'EDITH Dataset')}</div>
                    <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
                        Type: <b>{active_source.get('source_type', 'Demo')}</b> &bull; Records: <b>{active_source.get('row_count', 0):,}</b> &bull; {active_source.get('description', '')}
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
        "📊 Built-in Demo Benchmark",
        "📁 Upload File (CSV / Excel / SQLite)",
        "🔌 Connect SQL Database"
    ])
    
    # -------------------------------------------------------------------------
    # TAB 1: BUILT-IN DEMO DATASET
    # -------------------------------------------------------------------------
    with tab_demo:
        st.markdown("<h3 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>Standard Enterprise B2B SaaS Benchmark</h3>", unsafe_allow_html=True)
        st.write("""
        The built-in benchmark represents a 52-week commercial ledger for a multi-regional B2B SaaS enterprise ($1.4M weekly run rate).
        It includes logged pricing changes, marketing campaigns, inventory fill rates, competitor scraper telemetry, and customer feedback logs.
        """)
        
        col_d1, col_d2 = st.columns([1.5, 3.0])
        with col_d1:
            if st.button("🔄 Activate / Reset Built-in Demo Dataset", key="btn_reset_demo_data", type="primary", use_container_width=True):
                repo.reset_to_demo_dataset()
                _reinitialize_analytics(kpi_name="Monthly B2B Sales")
                st.success("✅ Demo dataset activated successfully!")
                st.rerun()
                
    # -------------------------------------------------------------------------
    # TAB 2: FILE UPLOAD (CSV / Excel / SQLite)
    # -------------------------------------------------------------------------
    with tab_file:
        st.markdown("<h3 style='font-size: 15px; font-weight: 700; color: #0F172A; margin-bottom: 6px;'>Upload Business Data File</h3>", unsafe_allow_html=True)
        st.caption("Upload `.csv`, `.xlsx`, `.xls`, or `.db`/`.sqlite` files. Data is session-scoped and never stored permanently.")
        
        uploaded_file = st.file_uploader(
            "Choose a business data file (Operations, HR, Finance, Support, Marketing, Sales)",
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
                _render_profiling_and_configuration_flow(df_raw, source_name=uploaded_file.name, source_type=meta_raw.get("source_type", "File Upload"))

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
            read_only_query = st.text_area("Read-Only SQL Query (Optional):", value="SELECT * FROM production_ledger LIMIT 10000;", help="Must be a single SELECT statement. Modifying statements are blocked.", key="sql_query_input")

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
                st.session_state["active_sql_df"] = df_sql
                st.session_state["active_sql_meta"] = meta_sql
                st.success(f"✅ Successfully queried {len(df_sql):,} rows from {dbname}!")
            except Exception as e:
                st.error(f"❌ Connection / Query Failed: {str(e)}")
                
        if "active_sql_df" in st.session_state and st.session_state["active_sql_df"] is not None:
            df_sql = st.session_state["active_sql_df"]
            meta_sql = st.session_state.get("active_sql_meta", {})
            _render_profiling_and_configuration_flow(df_sql, source_name=f"SQL: {meta_sql.get('dbname', 'db')}", source_type="SQL Database")

def _render_profiling_and_configuration_flow(df_raw: pd.DataFrame, source_name: str, source_type: str):
    """Renders the complete 4-step generic data profiling, model configuration, and feasibility flow."""
    repo = DataRepository.get_instance()
    profiles = DataProfiler.profile_dataframe(df_raw)
    all_columns = list(df_raw.columns)
    
    # -------------------------------------------------------------------------
    # STEP 1: AUTOMATIC DATA PROFILING SUMMARY
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #0F172A;'>📋 Step 1: Automated Data Profiling & Structural Audit</h4>", unsafe_allow_html=True)
    st.caption("Automatic inspection of column data types, completeness, cardinality, sample values, and semantic roles:")
    
    profile_rows = []
    for p in profiles:
        sample_str = ", ".join(p["sample_values"][:3]) if p["sample_values"] else "—"
        profile_rows.append({
            "Column Name": p["column_name"],
            "Data Type": p["inferred_dtype"],
            "Null %": f"{p['null_pct']}% ({p['null_count']:,})",
            "Distinct Values": f"{p['unique_count']:,}",
            "Sample Values": sample_str,
            "Inferred Type": p["semantic_guess"],
            "Recommended Role": p["suggested_role"]
        })
    df_profile_display = pd.DataFrame(profile_rows)
    st.dataframe(df_profile_display, use_container_width=True, hide_index=True)
    
    with st.expander("👁️ View Raw Data Preview (First 10 Rows)", expanded=False):
        st.dataframe(df_raw.head(10), use_container_width=True)
        
    # -------------------------------------------------------------------------
    # STEP 2: CONFIGURE ANALYTICAL MODEL
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #0F172A;'>⚙️ Step 2: Configure Analytical Model & Field Roles</h4>", unsafe_allow_html=True)
    st.caption("Define the primary metric to investigate, analysis grain, dimensions to slice by, and explanatory drivers:")
    
    # Type-Filtered Column Lists
    valid_numeric_cols = DataProfiler.get_valid_numeric_columns(df_raw)
    valid_date_cols = DataProfiler.get_valid_date_columns(df_raw)
    
    # Defaults from Profiler
    def_date_col = next((p["column_name"] for p in profiles if p["suggested_role"] == "Date / Timestamp" and p["column_name"] in valid_date_cols), None)
    def_primary_col = next((p["column_name"] for p in profiles if p["suggested_role"] == "Primary Measure" and p["column_name"] in valid_numeric_cols), valid_numeric_cols[0] if valid_numeric_cols else (all_columns[0] if all_columns else ""))
    def_dims = [p["column_name"] for p in profiles if p["suggested_role"] in ["Dimension", "Category", "Geography", "Boolean"]]
    def_drivers = [p["column_name"] for p in profiles if p["suggested_role"] == "Numeric Driver" and p["column_name"] in valid_numeric_cols and p["column_name"] != def_primary_col]
    def_ids = [p["column_name"] for p in profiles if p["suggested_role"] in ["Identifier / Key", "Identifier"]]
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        dataset_name = st.text_input("Dataset / Investigation Title:", value=f"Analysis of {source_name}", key="cfg_dataset_name")
        grain_choice = st.selectbox(
            "Analysis Grain / Structure:",
            options=["Time Series (Historical Trend)", "Cross-Sectional Snapshot", "Record-Level Event Log"],
            index=0 if def_date_col else 1,
            key="cfg_grain_choice"
        )
        
        # Primary Measure (Filtered to genuinely numeric columns)
        measure_choices = valid_numeric_cols if valid_numeric_cols else all_columns
        pri_idx = measure_choices.index(def_primary_col) if def_primary_col in measure_choices else 0
        primary_measure = st.selectbox("Primary Measure to Investigate (*Numeric Required):", options=measure_choices, index=pri_idx, key="cfg_primary_measure")
        
        col_lbl, col_unit = st.columns(2)
        with col_lbl:
            primary_label = st.text_input("Measure Display Label:", value=primary_measure.replace("_", " ").title(), key="cfg_pri_label")
        with col_unit:
            unit_guess = "$" if any(kw in primary_measure.lower() for kw in ["rev", "sales", "cost", "spend", "amount", "price", "budget"]) else ("%" if "rate" in primary_measure.lower() or "pct" in primary_measure.lower() else "Units")
            primary_unit = st.text_input("Unit Symbol / Label:", value=unit_guess, key="cfg_pri_unit")
            
        agg_choice = st.selectbox(
            "Default Aggregation Function:",
            options=["Sum", "Average / Mean", "Count", "Distinct Count", "Minimum", "Maximum"],
            index=1 if any(kw in primary_measure.lower() for kw in ["rate", "pct", "score", "hours", "price", "avg"]) else 0,
            key="cfg_agg_choice"
        )
        
        distinct_entity_col = None
        if agg_choice == "Distinct Count":
            entity_choices = def_ids + [c for c in all_columns if c not in def_ids]
            distinct_entity_col = st.selectbox("Distinct Entity / ID Column to Count (*Required):", options=entity_choices, index=0, key="cfg_dist_entity")
            
        drop_invalid_rows = st.checkbox("Drop invalid / unparseable rows automatically (recommended)", value=True, key="cfg_drop_inv")
        
    with col_c2:
        date_options = ["None / No Date (Snapshot)"] + (valid_date_cols if valid_date_cols else all_columns)
        date_idx = date_options.index(def_date_col) if def_date_col in date_options else 0
        selected_date = st.selectbox("Date / Timestamp Field (Optional for Time Series):", options=date_options, index=date_idx, key="cfg_date_col")
        date_col_final = None if selected_date == "None / No Date (Snapshot)" else selected_date
        
        # Dimensions (Categorical, Geography, Boolean, Low-cardinality)
        dim_options = [c for c in all_columns if c != primary_measure and c != date_col_final]
        valid_def_dims = [d for d in def_dims if d in dim_options]
        selected_dims = st.multiselect("Category Dimensions to Slice By (Optional, any number):", options=dim_options, default=valid_def_dims, key="cfg_dims_sel")
        
        # Numeric Drivers (Filtered to valid numeric columns)
        driver_options = [c for c in valid_numeric_cols if c != primary_measure and c != date_col_final and c not in selected_dims]
        valid_def_drivers = [d for d in def_drivers if d in driver_options]
        selected_drivers = st.multiselect("Numeric Explanatory Drivers to Correlate (Optional, numeric only):", options=driver_options, default=valid_def_drivers, key="cfg_drivers_sel")
        
        # Identifiers
        id_options = [c for c in all_columns if c != primary_measure and c != date_col_final and c not in selected_dims and c not in selected_drivers]
        valid_def_ids = [i for i in def_ids if i in id_options]
        selected_ids = st.multiselect("Identifier / Entity Columns (Optional):", options=id_options, default=valid_def_ids, key="cfg_ids_sel")

    # Map Aggregation Type string
    agg_map = {
        "Sum": "sum",
        "Average / Mean": "mean",
        "Count": "count",
        "Distinct Count": "distinct_count",
        "Minimum": "min",
        "Maximum": "max"
    }
    final_agg_type = agg_map.get(agg_choice, "sum")

    # Build SemanticDataModel
    semantic_model = SemanticDataModel(
        dataset_name=dataset_name,
        analysis_grain=grain_choice,
        primary_measure=primary_measure,
        primary_measure_label=primary_label,
        primary_measure_unit=primary_unit,
        aggregation_type=final_agg_type,
        distinct_entity_column=distinct_entity_col,
        date_column=date_col_final,
        dimension_columns=selected_dims,
        driver_columns=selected_drivers,
        identifier_columns=selected_ids,
        is_demo=False
    )

    
    # -------------------------------------------------------------------------
    # STEP 3: REVIEW WHAT EDITH CAN ANALYZE
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #0F172A;'>🔍 Step 3: Analytical Capabilities Review</h4>", unsafe_allow_html=True)
    st.caption("Based on your configured field mappings, EDITH has verified which analytical methods are supported:")
    
    feasibility = AnalysisFeasibilityChecker.evaluate_feasibility(df_raw, semantic_model)
    
    # 2x4 grid for capabilities
    f_items = list(feasibility.items())
    for row_i in range(0, len(f_items), 4):
        cols = st.columns(4)
        for col_i, (k, f_info) in enumerate(f_items[row_i:row_i+4]):
            with cols[col_i]:
                is_avail = f_info["available"]
                card_border = "#BBF7D0" if is_avail else "#E2E8F0"
                card_bg = "#F0FDF4" if is_avail else "#F8FAFC"
                badge_bg = "#DCFCE7" if is_avail else "#F1F5F9"
                badge_color = "#166534" if is_avail else "#64748B"
                icon = "🟢" if is_avail else "⚪"
                
                st.markdown(
                    f"""
                    <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; padding: 12px; height: 130px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-size: 12px; font-weight: 800; color: #0F172A;">{f_info['name']}</span>
                            </div>
                            <div style="font-size: 11px; color: #475569; line-height: 1.4;">
                                {f_info['reason']}
                            </div>
                        </div>
                        <div style="text-align: right; margin-top: 6px;">
                            <span style="background: {badge_bg}; color: {badge_color}; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 4px;">
                                {icon} {f_info['status']}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # STEP 4: VALIDATE & LOAD DATASET
    # -------------------------------------------------------------------------
    if st.button("🚀 Confirm Configuration & Load Dataset for Investigation", key="btn_confirm_load_generic", type="primary", use_container_width=True):
        try:
            tables, feat_status, warnings = ColumnMapper.transform_generic_dataset(df_raw, semantic_model, drop_invalid_rows=drop_invalid_rows)
            
            source_info = {
                "source_type": source_type,
                "name": dataset_name,
                "is_demo": False,
                "row_count": len(tables["sales"]),
                "description": f"Custom dataset ({feat_status['date_range']}) with {len(semantic_model.dimension_columns)} dimension(s) and {len(semantic_model.driver_columns)} driver(s).",
                "feature_status": feat_status
            }
            
            repo.set_custom_data(tables, source_info, semantic_model=semantic_model)
            _reinitialize_analytics(kpi_name=semantic_model.primary_measure_label or semantic_model.primary_measure)
            
            st.success(f"✅ Successfully loaded {dataset_name}! {len(tables['sales']):,} rows ready for investigation.")
            if warnings:
                for w in warnings:
                    st.warning(f"⚠️ {w}")
            set_screen("overview")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Configuration Error: {str(e)}")

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

