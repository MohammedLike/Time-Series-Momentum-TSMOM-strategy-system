"""Data cleaning and return computation utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame, method: str = "simple") -> pd.DataFrame:
    if method == "log":
        return np.log(prices / prices.shift(1)).dropna(how="all")
    return prices.pct_change().dropna(how="all")


def winsorize_returns(returns: pd.DataFrame, std_multiple: float = 5.0) -> pd.DataFrame:
    mean = returns.mean()
    std = returns.std()
    lower = mean - std_multiple * std
    upper = mean + std_multiple * std
    return returns.clip(lower, upper, axis=1)


def forward_fill_with_limit(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    return df.ffill(limit=limit)


def drop_sparse_assets(df: pd.DataFrame, max_missing_pct: float = 0.10) -> pd.DataFrame:
    threshold = len(df) * max_missing_pct
    valid_cols = df.columns[df.isna().sum() <= threshold]
    return df[valid_cols]


def align_and_clean(prices: pd.DataFrame) -> pd.DataFrame:
    prices = forward_fill_with_limit(prices)
    prices = drop_sparse_assets(prices)
    prices = prices.dropna()
    return prices
