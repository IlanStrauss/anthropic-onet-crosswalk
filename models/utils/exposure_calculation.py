"""
Shared Exposure Calculation Utilities
======================================

Common functions for calculating AI exposure with task importance weighting.

Author: Ilan Strauss | AI Disclosures Project
Date: January 2026
"""

import numpy as np
import pandas as pd


def first_nonnull(x):
    """Get first non-null value to avoid false missingness from 'first'."""
    x = x.dropna()
    return x.iloc[0] if len(x) else np.nan


def calculate_importance_weighted_exposure(crosswalk_df, onet_dir=None):
    """
    Calculate occupation-level AI exposure using task importance weights.

    IMPORTANT: The crosswalk only contains tasks WITH Claude usage. To get proper
    exposure, we need the FULL O*NET task universe to compute:
    exposure = (importance of AI-touched tasks) / (total importance of ALL tasks)

    Parameters
    ----------
    crosswalk_df : pd.DataFrame
        Task-level crosswalk with Claude usage
    onet_dir : Path, optional
        Path to O*NET database directory. If None, uses default location.

    Returns
    -------
    pd.DataFrame
        Occupation-level data with ai_exposure in [0,1]
    """
    from pathlib import Path

    # Load full O*NET task ratings to get ALL tasks (not just Claude-touched ones)
    if onet_dir is None:
        onet_dir = Path(__file__).parent.parent.parent / "data" / "onet" / "db_30_1_excel"

    task_ratings_file = onet_dir / "Task Ratings.xlsx"

    print("  Loading full O*NET task universe...")
    task_ratings = pd.read_excel(task_ratings_file)

    # Filter for Importance scale
    importance = task_ratings[task_ratings['Scale ID'] == 'IM'].copy()
    importance = importance[[
        'O*NET-SOC Code',
        'Task ID',
        'Data Value'
    ]].rename(columns={
        'O*NET-SOC Code': 'onet_soc_code',
        'Task ID': 'onet_task_id',
        'Data Value': 'task_importance'
    })

    print(f"  Full task universe: {len(importance):,} (occ, task) pairs")

    # Get Claude usage from crosswalk (only has tasks WITH usage)
    claude_usage = crosswalk_df[[
        'onet_soc_code',
        'onet_task_id',
        'api_usage_count',
        'TOT_EMP',
        'A_MEAN',
        'A_MEDIAN',
        'onet_occupation_title',
        'job_zone' if 'job_zone' in crosswalk_df.columns else 'Job Zone'
    ]].copy()

    # Rename job_zone if needed
    if 'Job Zone' in claude_usage.columns:
        claude_usage = claude_usage.rename(columns={'Job Zone': 'job_zone'})

    # Merge full task universe with Claude usage (left join on importance)
    # Tasks without Claude usage will have api_usage_count = NaN
    full_tasks = importance.merge(
        claude_usage,
        on=['onet_soc_code', 'onet_task_id'],
        how='left'
    )

    # Fill missing usage with 0
    full_tasks['api_usage_count'] = full_tasks['api_usage_count'].fillna(0)

    # Binary indicator: does this task have Claude usage?
    full_tasks['has_claude_usage'] = (full_tasks['api_usage_count'] > 0).astype(float)

    # Importance of AI-touched tasks
    full_tasks['ai_task_importance'] = full_tasks['task_importance'] * full_tasks['has_claude_usage']

    print(f"  Tasks with Claude usage: {full_tasks['has_claude_usage'].sum():,.0f}")

    # Aggregate to occupation level
    occ = full_tasks.groupby("onet_soc_code").agg(
        total_task_importance=("task_importance", "sum"),
        ai_task_importance=("ai_task_importance", "sum"),
        api_usage_count=("api_usage_count", "sum"),
        A_MEAN=("A_MEAN", first_nonnull),
        A_MEDIAN=("A_MEDIAN", first_nonnull),
        TOT_EMP=("TOT_EMP", first_nonnull),
        onet_occupation_title=("onet_occupation_title", first_nonnull),
        job_zone=("job_zone", first_nonnull)
    ).reset_index()

    # Drop rows missing employment/wage data (not in BLS)
    occ = occ[
        occ["A_MEAN"].notna() &
        occ["TOT_EMP"].notna() &
        (occ["TOT_EMP"] > 0) &
        (occ["total_task_importance"] > 0)
    ].copy()

    print(f"  Occupations with wage data: {len(occ):,}")

    # IMPORTANCE-WEIGHTED EXPOSURE
    # What fraction of high-importance work in this occupation is AI-exposed?
    occ["ai_exposure"] = occ["ai_task_importance"] / occ["total_task_importance"]

    # Ensure [0,1] bounds
    occ["ai_exposure"] = occ["ai_exposure"].clip(0, 1)

    # Also compute simple usage_per_worker for comparison
    occ["usage_per_worker"] = occ["api_usage_count"] / occ["TOT_EMP"]

    print(f"  Exposure range: {occ['ai_exposure'].min():.4f} to {occ['ai_exposure'].max():.4f}")
    print(f"  Mean exposure: {occ['ai_exposure'].mean():.4f}")

    return occ


def calculate_simple_usage_intensity(df):
    """
    Calculate occupation-level AI exposure using simple per-worker intensity.

    This is the fallback method when task_importance is unavailable.
    Scales usage_per_worker to [0,1] via max-scaling.

    Parameters
    ----------
    df : pd.DataFrame
        Task-level crosswalk

    Returns
    -------
    pd.DataFrame
        Occupation-level data with ai_exposure in [0,1]
    """
    df = df.copy()

    # Occupation-level totals
    occ = df.groupby("onet_soc_code").agg(
        api_usage_count=("api_usage_count", "sum"),
        A_MEAN=("A_MEAN", first_nonnull),
        A_MEDIAN=("A_MEDIAN", first_nonnull),
        TOT_EMP=("TOT_EMP", first_nonnull),
        onet_occupation_title=("onet_occupation_title", first_nonnull),
        job_zone=("job_zone", first_nonnull) if "job_zone" in df.columns else ("Job Zone", first_nonnull)
    ).reset_index()

    # Drop rows missing key denominators
    occ = occ[occ["A_MEAN"].notna() & occ["TOT_EMP"].notna() & (occ["TOT_EMP"] > 0)].copy()

    # Usage intensity per worker, normalized to [0,1]
    occ["usage_per_worker"] = occ["api_usage_count"] / occ["TOT_EMP"]
    occ["ai_exposure"] = occ["usage_per_worker"] / occ["usage_per_worker"].max()

    return occ
