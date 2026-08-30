"""
data/source_manager.py
Data Ingestion, SQL Security, File Parsing, Column Mapping, and Validation Manager for EDITH.
Allows users to securely load real business data from CSV, Excel, SQLite, and SQL databases.
"""
import io
import re
import sqlite3
import tempfile
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class SemanticDataModel:
    """User-defined or inferred analytical semantic model for any business dataset."""
    dataset_name: str = "Business Dataset"
    analysis_grain: str = "Time Series"  # "Time Series", "Cross-Sectional Snapshot", "Record-Level Event Log"
    primary_measure: str = ""            # Column name of the metric to investigate
    primary_measure_label: str = ""      # Human display name (e.g. "Defect Rate", "Turnover", "Actual Cost")
    primary_measure_unit: str = ""       # Unit symbol (e.g. "$", "%", "Units", "Hours", "Tickets", "Headcount")
    aggregation_type: str = "sum"        # "sum", "mean", "count", "min", "max", "distinct_count"
    distinct_entity_column: Optional[str] = None # Column to distinct-count when aggregation_type == "distinct_count"
    date_column: Optional[str] = None
    dimension_columns: List[str] = field(default_factory=list)  # Any number of categorical dimensions
    driver_columns: List[str] = field(default_factory=list)     # Any number of numeric explanatory drivers
    identifier_columns: List[str] = field(default_factory=list) # Record IDs, ticket IDs, employee IDs
    target_column: Optional[str] = None
    is_demo: bool = False
    drop_invalid_rows: bool = True

    @property
    def is_temporal(self) -> bool:
        return bool(self.date_column and self.date_column != "None (Snapshot)")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "analysis_grain": self.analysis_grain,
            "primary_measure": self.primary_measure,
            "primary_measure_label": self.primary_measure_label or self.primary_measure,
            "primary_measure_unit": self.primary_measure_unit,
            "aggregation_type": self.aggregation_type,
            "distinct_entity_column": self.distinct_entity_column,
            "date_column": self.date_column,
            "dimension_columns": self.dimension_columns,
            "driver_columns": self.driver_columns,
            "identifier_columns": self.identifier_columns,
            "target_column": self.target_column,
            "is_demo": self.is_demo,
            "is_temporal": self.is_temporal,
            "drop_invalid_rows": self.drop_invalid_rows
        }

class DataProfiler:
    """Generic data profiler inspecting every column in raw structured business datasets."""

    STRONG_KPI_KEYWORDS = {
        "revenue", "sales", "mrr", "arr", "churn_rate", "churn", "retention_rate",
        "retention", "gross_margin", "yield_pct", "yield", "profit", "net_income",
        "conversion_rate", "nps", "ltv", "gmv", "bookings", "ebitda"
    }
    DRIVER_KEYWORDS = {
        "spend", "cost", "budget", "clicks", "impressions", "cpl", "cac", "discount",
        "hours", "headcount", "salary", "wage", "reopen_count", "inventory_count",
        "tickets", "downtime", "duration", "delay"
    }
    NEUTRAL_KPI_KEYWORDS = {
        "amount", "value", "volume", "units", "rate", "score", "variance", "total",
        "count", "quantity"
    }

    @staticmethod
    def is_reliably_numeric(series: pd.Series) -> Tuple[bool, int, float]:
        """
        Tests whether a series is genuinely numeric or reliably parseable as numeric/currency/percent.
        Returns (is_numeric, invalid_count, invalid_pct).
        Rejects arbitrary text or categories.
        """
        if series.empty:
            return False, 0, 0.0
            
        if pd.api.types.is_numeric_dtype(series):
            null_cnt = int(series.isnull().sum())
            return True, null_cnt, round((null_cnt / len(series)) * 100.0, 1)
            
        # Clean formatting (currency $, commas, percentage signs)
        clean = series.astype(str).str.replace(r"[\$,%]", "", regex=True).str.replace(",", "").str.strip()
        clean = clean.replace({"": np.nan, "none": np.nan, "nan": np.nan, "null": np.nan, "n/a": np.nan, "-": np.nan})
        
        parsed = pd.to_numeric(clean, errors="coerce")
        valid_cnt = int(parsed.notnull().sum())
        non_null_raw = int(series.dropna().count())
        
        if non_null_raw == 0:
            return False, len(series), 100.0
            
        invalid_cnt = non_null_raw - valid_cnt
        invalid_pct = round((invalid_cnt / max(1, len(series))) * 100.0, 1)
        
        # Must parse at least 80% of non-null values cleanly to be considered a numeric column
        is_num = (valid_cnt / non_null_raw >= 0.8) and (valid_cnt >= 1)
        return is_num, invalid_cnt, invalid_pct

    @staticmethod
    def is_reliably_datetime(series: pd.Series) -> Tuple[bool, int, float]:
        """
        Tests whether a series can be reliably parsed as datetime/timestamps.
        Returns (is_datetime, invalid_count, invalid_pct).
        """
        if series.empty:
            return False, 0, 0.0
        if pd.api.types.is_datetime64_any_dtype(series):
            null_cnt = int(series.isnull().sum())
            return True, null_cnt, round((null_cnt / len(series)) * 100.0, 1)
            
        valid_raw = series.dropna()
        if valid_raw.empty:
            return False, len(series), 100.0
            
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Quick check first 10 rows
            sample = valid_raw.iloc[:min(10, len(valid_raw))]
            try:
                try:
                    pd.to_datetime(sample, errors="raise", format="mixed")
                except (TypeError, ValueError):
                    pd.to_datetime(sample, errors="raise")
            except Exception:
                return False, len(series), 100.0
                
            try:
                parsed = pd.to_datetime(valid_raw, errors="coerce", format="mixed")
            except (TypeError, ValueError):
                parsed = pd.to_datetime(valid_raw, errors="coerce")
                
            valid_cnt = int(parsed.notnull().sum())
            invalid_cnt = len(valid_raw) - valid_cnt
            invalid_pct = round((invalid_cnt / max(1, len(series))) * 100.0, 1)
            
            is_dt = (valid_cnt / len(valid_raw) >= 0.8) and (valid_cnt >= 1)
            return is_dt, invalid_cnt, invalid_pct



    @classmethod
    def clean_numeric_series(cls, series: pd.Series) -> pd.Series:
        """
        Converts strings with currency, commas, and percentage signs to clean float series.
        Unparseable text becomes NaN (not silently coerced to 0.0).
        """
        if pd.api.types.is_numeric_dtype(series):
            return series.astype(float)
        clean = series.astype(str).str.replace(r"[\$,%]", "", regex=True).str.replace(",", "").str.strip()
        clean = clean.replace({"": np.nan, "none": np.nan, "nan": np.nan, "null": np.nan, "n/a": np.nan, "-": np.nan})
        return pd.to_numeric(clean, errors="coerce")

    @classmethod
    def get_valid_numeric_columns(cls, df: pd.DataFrame) -> List[str]:
        """Returns all columns that are genuinely numeric or reliably parseable as numeric."""
        valid_cols = []
        for col in df.columns:
            is_num, _, _ = cls.is_reliably_numeric(df[col])
            if is_num:
                valid_cols.append(col)
        return valid_cols

    @classmethod
    def get_valid_date_columns(cls, df: pd.DataFrame) -> List[str]:
        """Returns all columns that can be reliably parsed as dates/timestamps."""
        valid_cols = []
        for col in df.columns:
            is_dt, _, _ = cls.is_reliably_datetime(df[col])
            if is_dt:
                valid_cols.append(col)
        return valid_cols

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Inspects every column and calculates full structural, statistical, and semantic profile."""
        profiles = []
        n_rows = len(df)
        
        for col in df.columns:
            series = df[col]
            null_cnt = int(series.isnull().sum())
            null_pct = round((null_cnt / max(1, n_rows)) * 100.0, 1)
            valid_series = series.dropna()
            uniq_cnt = int(valid_series.nunique())
            
            sample_vals = [str(x) for x in valid_series.unique()[:3]]
            inferred_type = str(series.dtype)
            stats = {}
            semantic_guess = "TEXT"
            suggested_role = "Dimension"
            
            col_lower = str(col).lower().strip()
            
            is_num, num_inv_cnt, _ = cls.is_reliably_numeric(series)
            is_dt, dt_inv_cnt, _ = cls.is_reliably_datetime(series)
            
            # 1. Date / Timestamp Heuristic
            if is_dt and not is_num:
                semantic_guess = "DATE"
                suggested_role = "Date / Timestamp"
                try:
                    dt_series = pd.to_datetime(valid_series, errors="coerce").dropna()
                    stats = {
                        "min_date": dt_series.min().strftime("%Y-%m-%d") if not dt_series.empty else "",
                        "max_date": dt_series.max().strftime("%Y-%m-%d") if not dt_series.empty else "",
                        "date_span_days": int((dt_series.max() - dt_series.min()).days) if not dt_series.empty else 0
                    }
                except Exception:
                    stats = {"format": "Datetime"}
            
            # 2. Numeric / Continuous / Measures / Drivers
            elif is_num:
                num_series = cls.clean_numeric_series(valid_series).dropna()
                
                # Check for Boolean flag (0/1)
                if uniq_cnt <= 2 and set(num_series.unique()).issubset({0, 1, 0.0, 1.0}):
                    semantic_guess = "BOOLEAN"
                    suggested_role = "Dimension"
                    stats = {"true_pct": round(float((num_series == 1).mean() * 100.0), 1)}
                # Check for ID (pure integer unique code or ID column name)
                elif any(kw in col_lower for kw in ["_id", "id", "code", "key", "number", "num", "ssn"]) and uniq_cnt > 0.8 * n_rows:
                    semantic_guess = "IDENTIFIER"
                    suggested_role = "Identifier / Key"
                    stats = {"unique_ratio": round(uniq_cnt / max(1, n_rows), 3)}
                else:
                    semantic_guess = "NUMERIC_MEASURE"
                    tokens = set(t for t in re.sub(r'[^a-zA-Z0-9_]', '_', col_lower).split('_') if t)
                    matched_strong = [kw for kw in cls.STRONG_KPI_KEYWORDS if kw in tokens or f"_{kw}_" in f"_{col_lower}_" or col_lower.startswith(f"{kw}_") or col_lower.endswith(f"_{kw}")]
                    matched_driver = [kw for kw in cls.DRIVER_KEYWORDS if kw in tokens or f"_{kw}_" in f"_{col_lower}_" or col_lower.startswith(f"{kw}_") or col_lower.endswith(f"_{kw}")]
                    
                    if matched_strong:
                        suggested_role = "Primary Measure"
                    elif matched_driver:
                        suggested_role = "Numeric Driver"
                    elif any(kw in col_lower for kw in cls.NEUTRAL_KPI_KEYWORDS):
                        suggested_role = "Primary Measure"
                    else:
                        suggested_role = "Numeric Driver"
                        
                    stats = {
                        "min": round(float(num_series.min()), 2) if not num_series.empty else 0.0,
                        "max": round(float(num_series.max()), 2) if not num_series.empty else 0.0,
                        "mean": round(float(num_series.mean()), 2) if not num_series.empty else 0.0,
                        "median": round(float(num_series.median()), 2) if not num_series.empty else 0.0,
                        "std": round(float(num_series.std()), 2) if (len(num_series) > 1 and not num_series.empty) else 0.0
                    }
                    
            # 3. Boolean Text Flags
            elif set(str(x).lower() for x in valid_series.unique()).issubset({"true", "false", "yes", "no", "t", "f", "y", "n"}):
                semantic_guess = "BOOLEAN"
                suggested_role = "Dimension"
                stats = {"unique_values": sample_vals}
                
            # 4. Geography, Identifiers, Text, and Categories
            else:
                if any(kw in col_lower for kw in ["region", "country", "city", "state", "territory", "zone", "location", "geo", "plant", "site"]):
                    semantic_guess = "GEOGRAPHY"
                    suggested_role = "Dimension"
                elif any(kw in col_lower for kw in ["_id", "id", "guid", "uuid", "key", "code", "ticket", "employee", "order_id"]):
                    semantic_guess = "IDENTIFIER"
                    suggested_role = "Identifier / Key"
                elif uniq_cnt > 0.6 * n_rows and n_rows > 20:
                    semantic_guess = "TEXT"
                    suggested_role = "Identifier / Key"
                else:
                    semantic_guess = "CATEGORY"
                    suggested_role = "Dimension"
                    
                top_cats = valid_series.value_counts().head(3).to_dict()
                stats = {"top_frequencies": {str(k): int(v) for k, v in top_cats.items()}}
                
            profiles.append({
                "column_name": col,
                "inferred_dtype": inferred_type,
                "null_count": null_cnt,
                "null_pct": null_pct,
                "unique_count": uniq_cnt,
                "sample_values": sample_vals,
                "semantic_guess": semantic_guess,
                "suggested_role": suggested_role,
                "stats": stats
            })
            
        return profiles

    @classmethod
    def rank_kpi_candidates(
        cls,
        profiles: List[Dict[str, Any]],
        dataset_name: str = "",
        df: Optional[pd.DataFrame] = None,
        valid_date_columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate primary measures using a multi-signal explainable scoring model:
        1. Tiered keyword matching (strong KPI vs neutral vs driver penalties)
        2. Dataset name token overlap
        3. Row null coverage
        4. Time-series lag-1 autocorrelation coherence (when date column is present)
        5. Scale magnitude tiebreaker
        """
        candidates = []
        import re
        ds_tokens = set(re.findall(r'[a-zA-Z0-9]+', dataset_name.lower())) - {
            'data', 'dataset', 'table', 'file', 'csv', 'xlsx', 'performance', 'report', 'analytics'
        } if dataset_name else set()
        
        for p in profiles:
            if p.get("semantic_guess") != "NUMERIC_MEASURE":
                continue
            col = p["column_name"]
            col_clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(col).lower())
            tokens = set(t for t in col_clean.split('_') if t)
            
            score = 0.0
            rationale_parts = []
            
            # 1. Tiered keyword match
            matched_strong = [kw for kw in cls.STRONG_KPI_KEYWORDS if kw in tokens or f"_{kw}_" in f"_{col_clean}_" or col_clean.startswith(f"{kw}_") or col_clean.endswith(f"_{kw}")]
            matched_driver = [kw for kw in cls.DRIVER_KEYWORDS if kw in tokens or f"_{kw}_" in f"_{col_clean}_" or col_clean.startswith(f"{kw}_") or col_clean.endswith(f"_{kw}")]
            matched_neutral = [kw for kw in cls.NEUTRAL_KPI_KEYWORDS if kw in tokens or f"_{kw}_" in f"_{col_clean}_" or col_clean.startswith(f"{kw}_") or col_clean.endswith(f"_{kw}")]
            
            if matched_strong:
                score += 50.0
                rationale_parts.append(f"Strong KPI keyword match ({matched_strong[0]})")
            elif matched_driver:
                score -= 30.0
                rationale_parts.append(f"Driver/input keyword match ({matched_driver[0]})")
            elif matched_neutral:
                score += 15.0
                rationale_parts.append(f"General measure keyword ({matched_neutral[0]})")
                
            # 2. Dataset name token overlap
            if ds_tokens:
                overlap = tokens.intersection(ds_tokens)
                if overlap:
                    score += 25.0 * len(overlap)
                    rationale_parts.append(f"Matches dataset name ({', '.join(sorted(overlap))})")
                    
            # 3. Null coverage
            null_pct = float(p.get("null_pct", 0.0))
            coverage_score = round((1.0 - (null_pct / 100.0)) * 15.0, 2)
            score += coverage_score
            if null_pct < 5.0:
                rationale_parts.append(f"{100.0 - null_pct:.1f}% row coverage")
            elif null_pct > 20.0:
                rationale_parts.append(f"{null_pct:.1f}% null rate penalty")
                
            # 4. Time-series coherence (lag-1 autocorrelation)
            if df is not None and valid_date_columns and len(valid_date_columns) > 0:
                date_col = valid_date_columns[0]
                if date_col in df.columns and col in df.columns:
                    try:
                        temp = df[[date_col, col]].dropna()
                        if len(temp) >= 5:
                            temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                            temp = temp.dropna().sort_values(date_col)
                            num_s = cls.clean_numeric_series(temp[col]).dropna()
                            if len(num_s) >= 5:
                                ac = float(num_s.autocorr(lag=1))
                                if not np.isnan(ac) and ac > 0.0:
                                    coherence_score = round(ac * 15.0, 2)
                                    score += coherence_score
                                    if ac >= 0.4:
                                        rationale_parts.append(f"Smooth temporal trend (lag-1 r={ac:.2f})")
                                    else:
                                        rationale_parts.append(f"Temporal trend (lag-1 r={ac:.2f})")
                    except Exception:
                        pass
                        
            # 5. Scale / Magnitude tiebreaker
            stats = p.get("stats", {})
            magnitude = float(stats.get("median", stats.get("mean", 0.0)))
            
            rationale = "; ".join(rationale_parts) if rationale_parts else "Standard numeric measure"
            candidates.append({
                "column_name": col,
                "score": score,
                "magnitude": magnitude,
                "rationale": rationale
            })
            
        candidates.sort(key=lambda c: (round(c["score"] / 2.0) * 2.0, c["score"], c["magnitude"]), reverse=True)
        return [
            {
                "column_name": c["column_name"],
                "score": round(c["score"], 1),
                "rationale": c["rationale"]
            }
            for c in candidates[:3]
        ]

    @classmethod
    def profile_dataset(cls, df: pd.DataFrame, dataset_name: str = "") -> Dict[str, Any]:
        """Inspects and returns a complete structural and statistical profile of a dataset."""
        profiles = cls.profile_dataframe(df)
        valid_num = cls.get_valid_numeric_columns(df)
        valid_dates = cls.get_valid_date_columns(df)
        valid_dims = [
            p["column_name"] for p in profiles 
            if p["column_name"] not in valid_num and p["column_name"] not in valid_dates
        ]
        kpi_candidates = cls.rank_kpi_candidates(
            profiles=profiles,
            dataset_name=dataset_name,
            df=df,
            valid_date_columns=valid_dates
        )
        return {
            "profiles": profiles,
            "valid_numeric_columns": valid_num,
            "valid_date_columns": valid_dates,
            "valid_dimension_columns": valid_dims,
            "kpi_candidates": kpi_candidates,
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }


class AnalysisFeasibilityChecker:
    """Evaluates data requirements for each analytical mode and determines suitability."""

    @classmethod
    def evaluate_feasibility(cls, df: pd.DataFrame, model: SemanticDataModel) -> Dict[str, Dict[str, Any]]:
        has_primary = bool(model.primary_measure and model.primary_measure in df.columns)
        has_date = bool(model.date_column and model.date_column in df.columns)
        
        unique_dates = df[model.date_column].dropna().nunique() if has_date else 0
        has_enough_dates = unique_dates >= 8
        
        has_dims = len(model.dimension_columns) > 0 and any(d in df.columns for d in model.dimension_columns)
        has_drivers = len(model.driver_columns) > 0 and any(d in df.columns for d in model.driver_columns)
        
        return {
            "time_series_investigation": {
                "name": "Time-Series Anomaly Detection",
                "available": has_primary and has_date and has_enough_dates,
                "status": "Available" if (has_primary and has_date and has_enough_dates) else "Unavailable",
                "reason": f"Active with {unique_dates} time periods." if (has_date and has_enough_dates) else ("Requires Date/Time field with at least 8 distinct periods." if (has_date and not has_enough_dates) else "Date/Time field not selected.")
            },
            "dimensional_breakdown": {
                "name": "Dimensional Variance Localization",
                "available": has_primary and has_dims,
                "status": "Available" if (has_primary and has_dims) else "Unavailable",
                "reason": f"Active with {len(model.dimension_columns)} mapped dimension(s): {', '.join(model.dimension_columns)}." if has_dims else "Requires at least 1 categorical dimension."
            },
            "driver_correlation": {
                "name": "Correlation & Driver Analysis",
                "available": has_primary and has_drivers,
                "status": "Available" if (has_primary and has_drivers) else "Unavailable",
                "reason": f"Active with {len(model.driver_columns)} numeric driver(s): {', '.join(model.driver_columns)}." if has_drivers else "Requires at least 1 numeric explanatory driver."
            },
            "distribution_outlier": {
                "name": "Distribution & Outlier Analysis",
                "available": has_primary,
                "status": "Available" if has_primary else "Unavailable",
                "reason": f"Active for primary measure '{model.primary_measure_label or model.primary_measure}'." if has_primary else "Primary measure required."
            },
            "cohort_comparison": {
                "name": "Cohort & Group Comparison",
                "available": has_primary and has_dims,
                "status": "Available" if (has_primary and has_dims) else "Unavailable",
                "reason": f"Active for comparing cohorts across dimensions." if has_dims else "Requires at least 1 categorical dimension."
            },
            "data_quality_audit": {
                "name": "Data Quality & Null Audit",
                "available": True,
                "status": "Available",
                "reason": "Always available across all columns."
            },
            "snapshot_analysis": {
                "name": "Cross-Sectional Snapshot Analysis",
                "available": has_primary,
                "status": "Available",
                "reason": "Evaluates distribution, variance concentration, and cohort statistics without requiring time series ordering."
            },
            "counterfactual_simulation": {
                "name": "Counterfactual Policy Simulation",
                "available": model.is_demo,
                "status": "Available (Demo Mode)" if model.is_demo else "Unavailable",
                "reason": "Standard structural econometric model active for B2B SaaS demo." if model.is_demo else "Simulations require explicit structural econometric parameters (price elasticity, response coefficients). Deferring counterfactual simulation for custom datasets."
            }
        }


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

    @classmethod
    def transform_generic_dataset(
        cls,
        df_raw: pd.DataFrame,
        model: SemanticDataModel,
        drop_invalid_rows: bool = True
    ) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any], List[str]]:

        """
        Transforms any structured business dataset (HR, Operations, Finance, Support, Marketing, etc.)
        into normalized EDITH repository tables driven by user's SemanticDataModel.
        Enforces strict field type validation and avoids fabricating sequential dates for snapshot datasets.
        """
        warnings = []
        df = df_raw.copy()
        
        # 1. Primary Measure Validation & Type Checking
        val_col = model.primary_measure
        if not val_col or val_col not in df.columns:
            raise ValueError(f"A valid Primary Measure column is required (received '{val_col}').")
            
        is_num, inv_cnt, inv_pct = DataProfiler.is_reliably_numeric(df[val_col])
        if not is_num:
            raise ValueError(f"Primary measure '{val_col}' contains non-numeric text and cannot be evaluated as a quantitative measure ({inv_cnt} invalid text values found, {inv_pct}%).")
            
        parsed_vals = DataProfiler.clean_numeric_series(df[val_col])
        inv_mask = parsed_vals.isnull()
        if inv_mask.any():
            num_inv = int(inv_mask.sum())
            pct_inv = round((num_inv / max(1, len(df))) * 100.0, 1)
            if drop_invalid_rows:
                warnings.append(f"Dropped {num_inv} row(s) ({pct_inv}%) containing unparseable/null values in Primary Measure '{val_col}'.")
                df = df[~inv_mask].copy()
                parsed_vals = parsed_vals[~inv_mask]
            else:
                raise ValueError(f"Primary measure '{val_col}' contains {num_inv} unparseable or missing rows ({pct_inv}%). Please clean data or enable 'Drop invalid rows'.")
                
        df["parsed_val"] = parsed_vals

        # 2. Distinct Count Aggregation Entity Validation
        if model.aggregation_type == "distinct_count":
            entity_col = model.distinct_entity_column or (model.identifier_columns[0] if model.identifier_columns else model.primary_measure)
            if not entity_col or entity_col not in df.columns:
                raise ValueError("Distinct Count aggregation requires a valid Entity / Identifier column to count distinct values.")
            model.distinct_entity_column = entity_col

        # 3. Numeric Drivers Validation & Type Checking
        for drv in model.driver_columns:
            if drv in df.columns:
                is_drv_num, drv_inv_cnt, drv_inv_pct = DataProfiler.is_reliably_numeric(df[drv])
                if not is_drv_num:
                    raise ValueError(f"Numeric driver '{drv}' contains non-numeric text and cannot be evaluated as a quantitative driver ({drv_inv_cnt} invalid text values found, {drv_inv_pct}%).")
                parsed_drv = DataProfiler.clean_numeric_series(df[drv])
                df[drv] = parsed_drv.fillna(parsed_drv.median() if not parsed_drv.dropna().empty else 0.0)

        # 4. Analysis Grain & Temporal Date Handling
        grain_lower = model.analysis_grain.lower()
        is_snapshot_grain = any(kw in grain_lower for kw in ["snapshot", "cross-sectional", "record", "event"])
        has_date = bool(model.date_column and model.date_column in df.columns and not is_snapshot_grain)
        unique_dates = []
        
        if has_date:
            is_dt, dt_inv_cnt, dt_inv_pct = DataProfiler.is_reliably_datetime(df[model.date_column])
            if not is_dt:
                warnings.append(f"Date column '{model.date_column}' could not be reliably parsed as datetime ({dt_inv_cnt} invalid values, {dt_inv_pct}%). Operating in Cross-Sectional Snapshot mode.")
                has_date = False
            else:
                try:
                    df["parsed_date"] = pd.to_datetime(df[model.date_column], errors="coerce")
                    valid_date_mask = df["parsed_date"].notnull()
                    if not valid_date_mask.all():
                        num_inv = int((~valid_date_mask).sum())
                        pct_inv = round((num_inv / max(1, len(df))) * 100.0, 1)
                        if drop_invalid_rows:
                            warnings.append(f"Dropped {num_inv} row(s) ({pct_inv}%) with unparseable dates in '{model.date_column}'.")
                            df = df[valid_date_mask].copy()
                        else:
                            raise ValueError(f"Date column '{model.date_column}' contains {num_inv} unparseable date values ({pct_inv}%).")
                            
                    df = df.sort_values("parsed_date").reset_index(drop=True)
                    unique_dates = df["parsed_date"].drop_duplicates().sort_values().reset_index(drop=True)
                    if len(unique_dates) < 2:
                        has_date = False
                        warnings.append(f"Date column '{model.date_column}' contains only 1 unique timestamp. Operating in Snapshot mode.")
                    else:
                        date_to_idx = {d: idx + 1 for idx, d in enumerate(unique_dates)}
                        df["week_idx"] = df["parsed_date"].map(date_to_idx)
                        df["week_label"] = df["parsed_date"].dt.strftime("%Y-W%U")
                        df["week_date"] = df["parsed_date"].dt.strftime("%Y-%m-%d")
                except Exception as e:
                    warnings.append(f"Failed to parse date column '{model.date_column}' ({e}). Operating in Snapshot mode.")
                    has_date = False

        is_temporal = has_date and not is_snapshot_grain
        if not is_temporal:
            # DO NOT fabricate sequential weeks/dates for snapshot / record-level datasets
            df["week_idx"] = 1
            df["week_label"] = "Snapshot" if "snapshot" in grain_lower else "Record-Level"
            df["week_date"] = "Snapshot"
            unique_dates = []

        # 5. Standardize Primary Metric Column name
        df["gross_revenue"] = df["parsed_val"]  # Standard internal measure alias
        df["gross_margin"] = df["parsed_val"] * 0.70  # Fallback margin alias

        # 6. Standardize Dimensions
        for dim in model.dimension_columns:
            if dim in df.columns:
                df[dim] = df[dim].fillna("Unknown").astype(str)

        # Standardize dimension aliases for backward-compatible views
        if model.dimension_columns:
            df["region"] = df[model.dimension_columns[0]]
            df["customer_tier"] = df[model.dimension_columns[1]] if len(model.dimension_columns) > 1 else "General"
            df["product_line"] = df[model.dimension_columns[2]] if len(model.dimension_columns) > 2 else "Primary"
            df["channel"] = df[model.dimension_columns[3]] if len(model.dimension_columns) > 3 else "Direct"
        else:
            df["region"] = "All"
            df["customer_tier"] = "General"
            df["product_line"] = "Primary"
            df["channel"] = "Direct"

        # Aliases for volume and price drivers
        if "units_sold" not in df.columns:
            df["units_sold"] = df[model.driver_columns[0]] if model.driver_columns else np.maximum(1.0, df["parsed_val"])
        if "unit_price" not in df.columns:
            df["unit_price"] = df[model.driver_columns[1]] if len(model.driver_columns) > 1 else 1.0

        # Construct Auxiliary Tables for Causal / Diagnostic compatibility
        unique_w = df["week_idx"].unique()
        unique_d = df["week_date"].unique()

        pricing_table = pd.DataFrame([
            {"change_id": "CHG-001", "effective_date": df["week_date"].iloc[max(0, len(df)-3)], "week_idx": max(1, len(unique_w)-2), "product_line": df["product_line"].iloc[0], "tier": df["customer_tier"].iloc[0], "old_price": float(df["parsed_val"].median() if not df.empty else 0.0), "new_price": float(df["parsed_val"].iloc[-1] if not df.empty else 0.0), "reason": "Standard Observation"}
        ])
        inv_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": df["region"].iloc[0], "product_line": df["product_line"].iloc[0], "fill_rate_pct": 99.4, "stockout_days": 0}
            for w, d in zip(unique_w, unique_d)
        ])
        comp_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": df["region"].iloc[0], "competitor_name": "Industry Baseline", "campaign_active": False, "competitor_price_index": 100.0}
            for w, d in zip(unique_w, unique_d)
        ])
        fb_table = pd.DataFrame([
            {"week_idx": w, "week_date": d, "region": df["region"].iloc[0], "complaint_count": 0, "pricing_complaints": 0}
            for w, d in zip(unique_w, unique_d)
        ])

        tables = {
            "sales": df,
            "raw": df_raw,
            "pricing": pricing_table,
            "inventory": inv_table,
            "competitor": comp_table,
            "feedback": fb_table
        }

        # Feasibility check
        feasibility = AnalysisFeasibilityChecker.evaluate_feasibility(df_raw, model)

        feature_status = {
            "is_temporal": is_temporal,
            "analysis_grain": model.analysis_grain,
            "can_detect_anomalies": is_temporal and feasibility["time_series_investigation"]["available"],
            "can_decompose_variance": feasibility["dimensional_breakdown"]["available"],
            "can_test_causal_hypotheses": model.is_demo,
            "can_simulate_policy": model.is_demo,
            "mapped_dimensions": model.dimension_columns,
            "mapped_drivers": model.driver_columns,
            "identifier_columns": model.identifier_columns,
            "distinct_entity_column": model.distinct_entity_column,
            "total_records": len(df),
            "total_periods": len(unique_dates) if is_temporal else 1,
            "date_range": f"{unique_dates.iloc[0].strftime('%Y-%m-%d')} to {unique_dates.iloc[-1].strftime('%Y-%m-%d')}" if (is_temporal and len(unique_dates) > 0) else f"{model.analysis_grain} (Non-Temporal)",
            "kpi_name": model.primary_measure_label or model.primary_measure,
            "kpi_unit": model.primary_measure_unit,
            "aggregation_type": model.aggregation_type,
            "feasibility": feasibility
        }

        return tables, feature_status, warnings


