"""Mathematical utilities used across modules."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def annualize_return(total_return: float, n_days: int) -> float:
    if n_days <= 0:
        return 0.0
    return (1 + total_return) ** (TRADING_DAYS / n_days) - 1


def annualize_vol(daily_vol: float) -> float:
    return daily_vol * np.sqrt(TRADING_DAYS)


def rolling_cumulative_return(
    returns: pd.DataFrame | pd.Series, window: int
) -> pd.DataFrame | pd.Series:
    return (1 + returns).rolling(window).apply(np.prod, raw=True) - 1


def expanding_cumulative_return(returns: pd.Series) -> pd.Series:
    return (1 + returns).cumprod() - 1


def zscore(series: pd.DataFrame | pd.Series, window: int = 252) -> pd.DataFrame | pd.Series:
    mean = series.rolling(window, min_periods=20).mean()
    std = series.rolling(window, min_periods=20).std()
    return (series - mean) / std.replace(0, np.nan)
