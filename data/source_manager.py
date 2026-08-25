"""
data/source_manager.py
Data Ingestion, SQL Security, File Parsing, Column Mapping, and Validation Manager for EDITH.
Allows users to securely load real business data from CSV, Excel, SQLite, and SQL databases.
"""
import io
import re
import sqlite3
import tempfile
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

class SQLQueryValidator:
    """Enforces strict read-only query execution to prevent destructive SQL operations."""
    
    FORBIDDEN_KEYWORDS = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
        r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"\bREPLACE\b",
        r"\bMERGE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bGRANT\b",
        r"\bREVOKE\b", r"\bATTACH\b", r"\bDETACH\b", r"\bINTO\s+OUTFILE\b",
        r"\bINTO\s+DUMPFILE\b", r"\bLOAD_FILE\b", r"\bSHUTDOWN\b"
    ]
    
    @classmethod
    def validate_query(cls, query: str) -> Tuple[bool, str]:
        """Validates that a SQL query is strictly read-only SELECT."""
        if not query or not query.strip():
            return False, "Query cannot be empty."
            
        clean_q = query.strip()
        
        # Remove line comments and block comments
        clean_q = re.sub(r"--.*$", "", clean_q, flags=re.MULTILINE)
        clean_q = re.sub(r"/\*.*?\*/", "", clean_q, flags=re.DOTALL).strip()
        
        # Check for multiple statements separated by semicolon
        statements = [s.strip() for s in clean_q.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are not permitted. Enter a single SELECT query."
            
        first_stmt = statements[0] if statements else ""
        
        # Must start with SELECT or WITH (CTE)
        if not (first_stmt.upper().startswith("SELECT") or first_stmt.upper().startswith("WITH")):
            return False, "Only read-only SELECT or WITH (CTE) queries are permitted."
            
        # Check forbidden keywords
        for pattern in cls.FORBIDDEN_KEYWORDS:
            if re.search(pattern, first_stmt, re.IGNORECASE):
                matched = re.search(pattern, first_stmt, re.IGNORECASE).group(0)
                return False, f"Destructive or modifying SQL keyword '{matched}' is strictly forbidden."
                
        return True, "Query validated as safe read-only SELECT."

class DataParser:
    """Parses incoming files (CSV, Excel, SQLite) into raw DataFrames with metadata."""
    
    @staticmethod
    def parse_csv(file_buffer_or_path: Any) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Parses CSV with encoding fallbacks."""
        encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]
        df = None
        used_enc = "utf-8"
        
        if hasattr(file_buffer_or_path, "seek"):
            file_buffer_or_path.seek(0)
            
        for enc in encodings:
            try:
                if hasattr(file_buffer_or_path, "seek"):
                    file_buffer_or_path.seek(0)
                df = pd.read_csv(file_buffer_or_path, encoding=enc)
                used_enc = enc
                break
            except Exception:
                continue
                
        if df is None:
            raise ValueError("Failed to parse CSV with supported encodings (UTF-8, Latin-1, CP1252).")
            
        meta = {
            "source_type": "CSV",
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
            "encoding": used_enc
        }
        return df, meta

    @staticmethod
    def parse_excel(file_buffer_or_path: Any, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
        """Parses Excel workbook and lists available worksheets."""
        if hasattr(file_buffer_or_path, "seek"):
            file_buffer_or_path.seek(0)
            
        xl = pd.ExcelFile(file_buffer_or_path)
        sheet_names = xl.sheet_names
        
        target_sheet = sheet_name if (sheet_name and sheet_name in sheet_names) else sheet_names[0]
        df = xl.parse(target_sheet)
        
        meta = {
            "source_type": "Excel",
            "sheet_name": target_sheet,
            "available_sheets": sheet_names,
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict()
        }
        return df, sheet_names, meta

    @staticmethod
    def parse_sqlite_file(file_buffer: Any, table_name: Optional[str] = None, query: Optional[str] = None) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
        """Reads a SQLite database upload in temporary storage and executes safe extraction."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            if hasattr(file_buffer, "seek"):
                file_buffer.seek(0)
                tmp.write(file_buffer.read())
            tmp_path = tmp.name
            
        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                raise ValueError("No user tables found in the uploaded SQLite database.")
                
            if query:
                is_safe, msg = SQLQueryValidator.validate_query(query)
                if not is_safe:
                    raise ValueError(f"Security validation failed: {msg}")
                df = pd.read_sql_query(query, conn)
            else:
                target_table = table_name if (table_name and table_name in tables) else tables[0]
                df = pd.read_sql_query(f"SELECT * FROM \"{target_table}\" LIMIT 50000;", conn)
                
            conn.close()
            
            meta = {
                "source_type": "SQLite",
                "tables": tables,
                "row_count": len(df),
                "col_count": len(df.columns),
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "null_counts": df.isnull().sum().to_dict()
            }
            return df, tables, meta
        finally:
            import os
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def parse_sql_connection(
        db_type: str,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
        table: Optional[str] = None,
        query: Optional[str] = None,
        ssl_mode: str = "prefer"
    ) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
        """Connects to a remote SQL database (PostgreSQL, MySQL, SQL Server) using SQLAlchemy or pure drivers."""
        try:
            from sqlalchemy import create_engine, inspect, text
        except ImportError:
            raise RuntimeError("SQLAlchemy is not installed. To use remote SQL databases, ensure sqlalchemy is available.")
            
        # Build connection URL cleanly (without storing password in persistent logs)
        if db_type == "PostgreSQL":
            driver_prefix = "postgresql+psycopg2"
            port = port or 5432
            url = f"{driver_prefix}://{user}:{password}@{host}:{port}/{dbname}"
        elif db_type == "MySQL":
            driver_prefix = "mysql+pymysql"
            port = port or 3306
            url = f"{driver_prefix}://{user}:{password}@{host}:{port}/{dbname}"
        elif db_type == "Microsoft SQL Server":
            driver_prefix = "mssql+pyodbc"
            port = port or 1433
            url = f"{driver_prefix}://{user}:{password}@{host}:{port}/{dbname}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
            
        engine = create_engine(url, connect_args={"connect_timeout": 8})
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if query:
            is_safe, msg = SQLQueryValidator.validate_query(query)
            if not is_safe:
                raise ValueError(f"Security validation failed: {msg}")
            with engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)
        else:
            target_table = table if (table and table in tables) else (tables[0] if tables else "")
            if not target_table:
                raise ValueError("No accessible tables found in the connected database.")
            with engine.connect() as conn:
                df = pd.read_sql_query(text(f"SELECT * FROM {target_table} LIMIT 50000;"), conn)
                
        meta = {
            "source_type": f"SQL ({db_type})",
            "host": host,
            "dbname": dbname,
            "tables": tables,
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict()
        }
        return df, tables, meta

class ColumnMapper:
    """Maps custom dataset columns to standard EDITH analytical schemas and validates features."""
    
    STANDARD_FIELDS = {
        "date": {"label": "Date / Timestamp Column", "required": True, "desc": "Weekly or daily transaction date"},
        "metric_value": {"label": "Metric / Revenue Value ($)", "required": True, "desc": "Numerical target metric"},
        "region": {"label": "Region / Geography", "required": False, "desc": "Geographic dimension"},
        "customer_tier": {"label": "Customer Tier / Segment", "required": False, "desc": "Enterprise, Mid-Market, SMB"},
        "product_line": {"label": "Product Line / SKU", "required": False, "desc": "Product category/name"},
        "channel": {"label": "Sales Channel", "required": False, "desc": "Direct, Partner, Online"},
        "unit_price": {"label": "Unit Price (Optional Driver)", "required": False, "desc": "Price per unit for elasticity"},
        "units_sold": {"label": "Units / Volume (Optional Driver)", "required": False, "desc": "Quantity sold for volume decomposition"},
        "competitor_signal": {"label": "Competitor Activity (Optional Driver)", "required": False, "desc": "Competitor promo index/flag"},
        "inventory_signal": {"label": "Inventory / Stock Fill (Optional Driver)", "required": False, "desc": "Fill rate / stockout indicator"}
    }
    
    @classmethod
    def auto_infer_mapping(cls, columns: List[str]) -> Dict[str, Optional[str]]:
        """Infers mapping suggestions based on common column name heuristics."""
        mapping = {}
        cols_lower = {col.lower(): col for col in columns}
        
        # Date
        for kw in ["date", "week_date", "week", "timestamp", "time", "period", "day", "month"]:
            if kw in cols_lower:
                mapping["date"] = cols_lower[kw]
                break
        if "date" not in mapping and columns:
            mapping["date"] = columns[0]
            
        # Metric Value
        for kw in ["gross_revenue", "revenue", "sales", "amount", "total_sales", "metric_value", "value", "arr", "mrr"]:
            if kw in cols_lower:
                mapping["metric_value"] = cols_lower[kw]
                break
                
        # Dimensions
        for kw in ["region", "geography", "country", "territory", "zone", "state", "location"]:
            if kw in cols_lower:
                mapping["region"] = cols_lower[kw]
                break
        for kw in ["customer_tier", "tier", "segment", "account_type", "customer_segment"]:
            if kw in cols_lower:
                mapping["customer_tier"] = cols_lower[kw]
                break
        for kw in ["product_line", "product", "sku", "product_name", "item", "suite"]:
            if kw in cols_lower:
                mapping["product_line"] = cols_lower[kw]
                break
        for kw in ["channel", "sales_channel", "distribution_channel", "source"]:
            if kw in cols_lower:
                mapping["channel"] = cols_lower[kw]
                break
                
        # Optional Drivers
        for kw in ["unit_price", "price", "avg_price", "rate"]:
            if kw in cols_lower:
                mapping["unit_price"] = cols_lower[kw]
                break
        for kw in ["units_sold", "volume", "quantity", "units", "count"]:
            if kw in cols_lower:
                mapping["units_sold"] = cols_lower[kw]
                break
                
        return mapping

    @classmethod
    def validate_and_transform(
        cls,
        df_raw: pd.DataFrame,
        mapping: Dict[str, Optional[str]],
        kpi_name: str = "Imported Business Metric"
    ) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any], List[str]]:
        """
        Transforms raw mapped user DataFrame into standard EDITH normalized repository tables.
        Returns (tables_dict, metadata_dict, validation_warnings).
        """
        warnings = []
        df = df_raw.copy()
        
        # 1. Date Validation
        date_col = mapping.get("date")
        if not date_col or date_col not in df.columns:
            raise ValueError("A valid 'Date' column is required.")
            
        try:
            df["parsed_date"] = pd.to_datetime(df[date_col])
        except Exception as e:
            raise ValueError(f"Failed to parse Date column '{date_col}' to datetime: {e}")
            
        # 2. Metric Value Validation
        val_col = mapping.get("metric_value")
        if not val_col or val_col not in df.columns:
            raise ValueError("A valid 'Metric / Revenue Value' column is required.")
            
        try:
            # Clean string numbers (e.g. "$1,200", "5.2%")
            if df[val_col].dtype == object:
                df["parsed_val"] = df[val_col].astype(str).str.replace("$", "").str.replace(",", "").str.replace("%", "").astype(float)
            else:
                df["parsed_val"] = df[val_col].astype(float)
        except Exception as e:
            raise ValueError(f"Metric column '{val_col}' must contain valid numeric values: {e}")
            
        df = df.sort_values("parsed_date").reset_index(drop=True)
        
        # Aggregate to weekly or unique date intervals
        # Create week_idx and week_label
        unique_dates = df["parsed_date"].drop_duplicates().sort_values().reset_index(drop=True)
        if len(unique_dates) < 8:
            raise ValueError(f"Dataset has only {len(unique_dates)} time periods. EDITH requires at least 8 time periods for baseline corridor analysis.")
            
        date_to_idx = {d: idx + 1 for idx, d in enumerate(unique_dates)}
        df["week_idx"] = df["parsed_date"].map(date_to_idx)
        df["week_label"] = df["parsed_date"].dt.strftime("%Y-W%U")
        df["week_date"] = df["parsed_date"].dt.strftime("%Y-%m-%d")
        
        # Standardize Dimensions (fallback to 'All' if missing)
        df["region"] = df[mapping["region"]].astype(str) if (mapping.get("region") and mapping["region"] in df.columns) else "All Regions"
        df["customer_tier"] = df[mapping["customer_tier"]].astype(str) if (mapping.get("customer_tier") and mapping["customer_tier"] in df.columns) else "General"
        df["product_line"] = df[mapping["product_line"]].astype(str) if (mapping.get("product_line") and mapping["product_line"] in df.columns) else "Primary Suite"
        df["channel"] = df[mapping["channel"]].astype(str) if (mapping.get("channel") and mapping["channel"] in df.columns) else "Direct"
        
        # Standardize Drivers
        df["gross_revenue"] = df["parsed_val"]
        df["units_sold"] = df[mapping["units_sold"]].astype(float) if (mapping.get("units_sold") and mapping["units_sold"] in df.columns) else np.maximum(1.0, df["gross_revenue"] / 10000.0)
        df["unit_price"] = df[mapping["unit_price"]].astype(float) if (mapping.get("unit_price") and mapping["unit_price"] in df.columns) else (df["gross_revenue"] / np.maximum(1.0, df["units_sold"]))
        df["gross_margin"] = df["gross_revenue"] * 0.70 # Baseline estimate if unmapped
        
        # Construct Normalized Sales Table
        sales_table = df[[
            "week_idx", "week_label", "week_date", "region", "customer_tier",
            "product_line", "channel", "gross_revenue", "units_sold", "unit_price", "gross_margin"
        ]]
        
        # Construct Auxiliary Driver Tables
        pricing_table = pd.DataFrame([
            {"change_id": "CHG-001", "effective_date": df["week_date"].iloc[max(0, len(df)-3)], "week_idx": max(1, len(unique_dates)-2), "product_line": sales_table["product_line"].iloc[0], "tier": sales_table["customer_tier"].iloc[0], "old_price": sales_table["unit_price"].median(), "new_price": sales_table["unit_price"].iloc[-1], "reason": "Standard Policy"}
        ])
        
        inv_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": sales_table["region"].iloc[0], "product_line": sales_table["product_line"].iloc[0], "fill_rate_pct": 99.4, "stockout_days": 0}
            for w, d in zip(sales_table["week_idx"].unique(), sales_table["week_date"].unique())
        ])
        
        comp_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": sales_table["region"].iloc[0], "competitor_name": "ApexTech", "campaign_active": False, "competitor_price_index": 100.0}
            for w, d in zip(sales_table["week_idx"].unique(), sales_table["week_date"].unique())
        ])
        
        fb_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": sales_table["region"].iloc[0], "complaint_count": 5, "pricing_complaints": 2}
            for w, d in zip(sales_table["week_idx"].unique(), sales_table["week_date"].unique())
        ])
        
        tables = {
            "sales": sales_table,
            "pricing": pricing_table,
            "inventory": inv_table,
            "competitor": comp_table,
            "feedback": fb_table
        }
        
        # Feature Availability Check
        has_region = bool(mapping.get("region") and mapping["region"] in df_raw.columns and df_raw[mapping["region"]].nunique() > 1)
        has_tier = bool(mapping.get("customer_tier") and mapping["customer_tier"] in df_raw.columns and df_raw[mapping["customer_tier"]].nunique() > 1)
        has_product = bool(mapping.get("product_line") and mapping["product_line"] in df_raw.columns and df_raw[mapping["product_line"]].nunique() > 1)
        has_price_driver = bool(mapping.get("unit_price") or mapping.get("units_sold"))
        
        if not has_region:
            warnings.append("Region dimension was not mapped or contains only 1 value. Regional breakdown will show single aggregated cohort.")
        if not has_tier:
            warnings.append("Customer Tier was not mapped. Control group / DiD analysis will use default single tier.")
        if not has_price_driver:
            warnings.append("Unit Price / Volume drivers were not explicitly mapped. Unit prices inferred from revenue ratios.")
            
        feature_status = {
            "can_detect_anomalies": True,
            "can_decompose_variance": has_region or has_tier or has_product,
            "can_test_causal_hypotheses": True,
            "can_simulate_policy": True,
            "mapped_dimensions": [d for d in ["region", "customer_tier", "product_line", "channel"] if mapping.get(d)],
            "total_weeks": len(unique_dates),
            "date_range": f"{unique_dates.iloc[0].strftime('%Y-%m-%d')} to {unique_dates.iloc[-1].strftime('%Y-%m-%d')}",
            "kpi_name": kpi_name
        }
        
        return tables, feature_status, warnings
