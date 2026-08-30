"""
core/data_reconciliation.py
Cross-file relationship discovery, join-key inference, and grain-aware table merging for EDITH.
"""
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np


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
            # Check overlap of unique values to ensure meaningful link
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
    join_keys: List[str]
) -> pd.DataFrame:
    """
    Performs a left join of a supporting table into a fact table on designated join keys,
    explicitly resolving grain mismatches (e.g. daily fact + weekly/monthly supporting)
    by forward/backward filling merged supporting values across finer-grain rows within groups.
    """
    if fact_df.empty or supporting_df.empty or not join_keys:
        return fact_df
        
    # Ensure join keys exist in both
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
        
    # Left merge
    merged = pd.merge(fact_df, supp_copy, on=valid_keys, how="left")
    
    # Handle grain mismatch: if supporting table had coarser grain or missing periods,
    # forward-fill and backward-fill within entity partitions so we don't leave NaNs
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
                
            # If still has NaNs (e.g. completely unmatched group), fill with safe fallback
            if merged[col].isnull().any():
                if pd.api.types.is_numeric_dtype(merged[col]):
                    fill_val = merged[col].dropna().median() if not merged[col].dropna().empty else 0.0
                    merged[col] = merged[col].fillna(fill_val)
                else:
                    merged[col] = merged[col].fillna("Unknown")
                    
    return merged
