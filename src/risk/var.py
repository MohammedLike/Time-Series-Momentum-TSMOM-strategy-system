"""Value-at-Risk and Expected Shortfall (CVaR) estimators."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def parametric_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Gaussian (parametric) VaR."""
    z = stats.norm.ppf(1 - confidence)
    return float(returns.mean() + z * returns.std())


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Non-parametric VaR from empirical quantile."""
    return float(np.percentile(returns.dropna(), (1 - confidence) * 100))


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Expected Shortfall (CVaR): mean of returns beyond VaR threshold."""
    var = historical_var(returns, confidence)
    tail = returns[returns <= var]
    return float(tail.mean()) if len(tail) > 0 else var


def rolling_var(
    returns: pd.Series, window: int = 252, confidence: float = 0.95
) -> pd.Series:
    """Rolling historical VaR for time-series visualization."""
    return returns.rolling(window, min_periods=60).quantile((1 - confidence))


def rolling_cvar(
    returns: pd.Series, window: int = 252, confidence: float = 0.95
) -> pd.Series:
    """Rolling CVaR (Expected Shortfall)."""
    quantile_level = 1 - confidence

    def _cvar(x):
        threshold = np.percentile(x, quantile_level * 100)
        tail = x[x <= threshold]
        return tail.mean() if len(tail) > 0 else threshold

    return returns.rolling(window, min_periods=60).apply(_cvar, raw=True)
