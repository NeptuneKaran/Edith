"""
core/data_reconciliation.py
Cross-file relationship discovery, join-key inference, and grain-aware table merging for EDITH.
"""
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from data.source_manager import DataProfiler


def find_date_column(df: pd.DataFrame) -> Optional[str]:
    """Finds the most likely datetime column in a DataFrame."""
    if df is None or df.empty:
        return None
    # 1. Look for obvious column names first
    candidate_names = [
        "date", "week_date", "week_start", "timestamp", "period", "time", "month",
        "fiscal_week", "iso_week", "day", "order_date", "transaction_date", "log_date"
    ]
    cols_lower = {str(c).lower(): c for c in df.columns}
    for kw in candidate_names:
        if kw in cols_lower:
            c = cols_lower[kw]
            is_dt, _, _ = DataProfiler.is_reliably_datetime(df[c])
            if is_dt or pd.api.types.is_datetime64_any_dtype(df[c]):
                return c
                
    # 2. Check any datetime dtype column
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
            
    # 3. Test other columns with is_reliably_datetime
    for c in df.columns:
        is_dt, _, _ = DataProfiler.is_reliably_datetime(df[c])
        if is_dt:
            return c
            
    return None


def detect_join_keys(df1: pd.DataFrame, df2: pd.DataFrame) -> List[str]:
    """
    Identifies valid shared join-key columns between two DataFrames.
    Checks that columns exist in both DataFrames, have compatible data types,
    and contain non-null values.
    """
    if df1 is None or df2 is None or df1.empty or df2.empty:
        return []
        
    shared_cols = [c for c in df1.columns if c in df2.columns]
    join_keys = []
    
    for col in shared_cols:
        s1 = df1[col].dropna()
        s2 = df2[col].dropna()
        
        if s1.empty or s2.empty:
            continue
            
        t1 = str(df1[col].dtype)
        t2 = str(df2[col].dtype)
        
        # 1. Both numeric
        is_num1 = pd.api.types.is_numeric_dtype(df1[col])
        is_num2 = pd.api.types.is_numeric_dtype(df2[col])
        if is_num1 and is_num2:
            join_keys.append(col)
            continue
            
        # 2. Both datetime
        is_dt1 = pd.api.types.is_datetime64_any_dtype(df1[col])
        is_dt2 = pd.api.types.is_datetime64_any_dtype(df2[col])
        if is_dt1 and is_dt2:
            join_keys.append(col)
            continue
            
        # 3. Both object/string/categorical
        is_str1 = pd.api.types.is_string_dtype(df1[col]) or pd.api.types.is_object_dtype(df1[col]) or pd.api.types.is_categorical_dtype(df1[col])
        is_str2 = pd.api.types.is_string_dtype(df2[col]) or pd.api.types.is_object_dtype(df2[col]) or pd.api.types.is_categorical_dtype(df2[col])
        if is_str1 and is_str2:
            overlap = set(s1.astype(str).unique()).intersection(set(s2.astype(str).unique()))
            if len(overlap) > 0:
                join_keys.append(col)
                continue
                
        # 4. Exact dtype match fallback
        if t1 == t2:
            join_keys.append(col)
            
    return join_keys


def merge_tables_with_grain(
    fact_df: pd.DataFrame,
    supporting_df: pd.DataFrame,
    join_keys: List[str],
    fact_date_col: Optional[str] = None,
    supp_date_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Performs a left join / as-of join of a supporting table into a fact table on designated join keys.
    Guarantees that the fact table's row count is never duplicated or changed (assert len(merged) == len(fact_df)).
    
    Handles:
    - Grain mismatch (e.g. daily fact vs weekly/monthly supporting table) using pd.merge_asof
    - Differently named date columns (e.g. date vs week_start or fiscal_week)
    - Duplicate key prevention via as-of date alignment or deterministic deduplication
    - Missing period values via partition-aware forward/backward filling
    """
    if fact_df.empty or supporting_df.empty or not join_keys:
        return fact_df
        
    valid_keys = [k for k in join_keys if k in fact_df.columns and k in supporting_df.columns]
    if not valid_keys:
        return fact_df
        
    supp_copy = supporting_df.copy()
    
    # Handle column collisions for non-key columns
    non_key_cols = [c for c in supp_copy.columns if c not in valid_keys]
    rename_map = {}
    for c in non_key_cols:
        if c in fact_df.columns:
            rename_map[c] = f"{c}_supp"
    if rename_map:
        supp_copy.rename(columns=rename_map, inplace=True)
        non_key_cols = [rename_map.get(c, c) for c in non_key_cols]
        
    has_duplicates = supp_copy.duplicated(subset=valid_keys).any()
    
    d_fact = fact_date_col or find_date_column(fact_df)
    d_supp = supp_date_col or find_date_column(supp_copy)
    
    # If supporting has duplicates on the join keys AND both have recognizable date columns -> AS-OF JOIN
    if has_duplicates and d_fact and d_supp and d_fact in fact_df.columns and d_supp in supp_copy.columns:
        try:
            fact_work = fact_df.copy()
            supp_work = supp_copy.copy()
            
            fact_work["_asof_date_fact"] = pd.to_datetime(fact_work[d_fact])
            supp_work["_asof_date_supp"] = pd.to_datetime(supp_work[d_supp])
            
            # by keys are any valid categorical join keys other than the date columns
            by_keys = [k for k in valid_keys if k != d_fact and k != d_supp]
            for k in by_keys:
                fact_work[k] = fact_work[k].astype(str)
                supp_work[k] = supp_work[k].astype(str)
                
            fact_work["_orig_order_idx"] = np.arange(len(fact_work))
            fact_sorted = fact_work.sort_values("_asof_date_fact").reset_index(drop=True)
            supp_sorted = supp_work.sort_values("_asof_date_supp").reset_index(drop=True)
            
            if by_keys:
                merged_sorted = pd.merge_asof(
                    fact_sorted,
                    supp_sorted,
                    left_on="_asof_date_fact",
                    right_on="_asof_date_supp",
                    by=by_keys,
                    direction="backward"
                )
            else:
                merged_sorted = pd.merge_asof(
                    fact_sorted,
                    supp_sorted,
                    left_on="_asof_date_fact",
                    right_on="_asof_date_supp",
                    direction="backward"
                )
                
            # Handle forward/backward fill for earlier dates within groups
            for col in non_key_cols:
                if col in merged_sorted.columns and merged_sorted[col].isnull().any():
                    if by_keys:
                        try:
                            merged_sorted[col] = merged_sorted.groupby(by_keys)[col].transform(lambda g: g.ffill().bfill())
                        except Exception:
                            merged_sorted[col] = merged_sorted[col].ffill().bfill()
                    else:
                        merged_sorted[col] = merged_sorted[col].ffill().bfill()
                        
                    if merged_sorted[col].isnull().any():
                        if pd.api.types.is_numeric_dtype(merged_sorted[col]):
                            fill_val = merged_sorted[col].dropna().median() if not merged_sorted[col].dropna().empty else 0.0
                            merged_sorted[col] = merged_sorted[col].fillna(fill_val)
                        else:
                            merged_sorted[col] = merged_sorted[col].fillna("Unknown")
                            
            merged = merged_sorted.sort_values("_orig_order_idx").reset_index(drop=True)
            cols_to_drop = ["_orig_order_idx", "_asof_date_fact", "_asof_date_supp"]
            merged.drop(columns=[c for c in cols_to_drop if c in merged.columns], inplace=True)
            
        except Exception:
            # Fallback to deduplication if as-of join encounters unexpected formatting
            supp_dedup = supp_copy.drop_duplicates(subset=valid_keys, keep="last")
            merged = pd.merge(fact_df, supp_dedup, on=valid_keys, how="left")
            group_keys = [k for k in valid_keys if k not in ["date", "parsed_date", "week_date", "timestamp"]]
            for col in non_key_cols:
                if col in merged.columns and merged[col].isnull().any():
                    if group_keys:
                        try:
                            merged[col] = merged.groupby(group_keys)[col].transform(lambda g: g.ffill().bfill())
                        except Exception:
                            merged[col] = merged[col].ffill().bfill()
                    else:
                        merged[col] = merged[col].ffill().bfill()
                    if merged[col].isnull().any():
                        if pd.api.types.is_numeric_dtype(merged[col]):
                            fill_val = merged[col].dropna().median() if not merged[col].dropna().empty else 0.0
                            merged[col] = merged[col].fillna(fill_val)
                        else:
                            merged[col] = merged[col].fillna("Unknown")
    elif has_duplicates:
        # Non-temporal duplicates in supporting table -> deduplicate
        supp_dedup = supp_copy.drop_duplicates(subset=valid_keys, keep="last")
        merged = pd.merge(fact_df, supp_dedup, on=valid_keys, how="left")
        group_keys = [k for k in valid_keys if k not in ["date", "parsed_date", "week_date", "timestamp"]]
        for col in non_key_cols:
            if col in merged.columns and merged[col].isnull().any():
                if group_keys:
                    try:
                        merged[col] = merged.groupby(group_keys)[col].transform(lambda g: g.ffill().bfill())
                    except Exception:
                        merged[col] = merged[col].ffill().bfill()
                else:
                    merged[col] = merged[col].ffill().bfill()
                if merged[col].isnull().any():
                    if pd.api.types.is_numeric_dtype(merged[col]):
                        fill_val = merged[col].dropna().median() if not merged[col].dropna().empty else 0.0
                        merged[col] = merged[col].fillna(fill_val)
                    else:
                        merged[col] = merged[col].fillna("Unknown")
    else:
        # Unique keys -> standard left merge
        merged = pd.merge(fact_df, supp_copy, on=valid_keys, how="left")
        group_keys = [k for k in valid_keys if k not in ["date", "parsed_date", "week_date", "timestamp"]]
        for col in non_key_cols:
            if col in merged.columns and merged[col].isnull().any():
                if group_keys:
                    try:
                        merged[col] = merged.groupby(group_keys)[col].transform(lambda g: g.ffill().bfill())
                    except Exception:
                        merged[col] = merged[col].ffill().bfill()
                else:
                    merged[col] = merged[col].ffill().bfill()
                if merged[col].isnull().any():
                    if pd.api.types.is_numeric_dtype(merged[col]):
                        fill_val = merged[col].dropna().median() if not merged[col].dropna().empty else 0.0
                        merged[col] = merged[col].fillna(fill_val)
                    else:
                        merged[col] = merged[col].fillna("Unknown")
                        
    # Assert correctness invariant: fact row count must be preserved exactly
    assert len(merged) == len(fact_df), f"Row count invariant violated: fact table has {len(fact_df)} rows, merged table has {len(merged)} rows"
    
    return merged
