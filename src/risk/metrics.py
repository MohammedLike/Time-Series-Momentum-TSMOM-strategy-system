"""Comprehensive performance and risk metrics.

Computes all standard quantitative finance metrics in one pass.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

TRADING_DAYS = 252


def compute_all_metrics(
    returns: pd.Series, risk_free_rate: float = 0.0, benchmark: pd.Series | None = None
) -> dict[str, float]:
    """Compute a complete set of risk/return metrics."""
    n = len(returns)
    if n < 2:
        return {}

    total_return = (1 + returns).prod() - 1
    n_years = n / TRADING_DAYS
    cagr = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1

    daily_rf = risk_free_rate / TRADING_DAYS
    excess = returns - daily_rf

    ann_vol = returns.std() * np.sqrt(TRADING_DAYS)
    sharpe = excess.mean() / returns.std() * np.sqrt(TRADING_DAYS) if returns.std() > 0 else 0

    downside = returns[returns < 0].std()
    sortino = excess.mean() / downside * np.sqrt(TRADING_DAYS) if downside > 0 else 0

    # Drawdown
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    drawdown = cum / running_max - 1
    max_dd = drawdown.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    # Drawdown duration
    is_dd = drawdown < 0
    dd_groups = (~is_dd).cumsum()
    dd_durations = is_dd.groupby(dd_groups).sum()
    max_dd_duration = int(dd_durations.max()) if len(dd_durations) > 0 else 0

    # Hit rate
    hit_rate = (returns > 0).mean()

    # Distribution
    skew = float(returns.skew())
    kurt = float(returns.kurtosis())

    # VaR & CVaR
    var_95 = float(np.percentile(returns, 5))
    var_99 = float(np.percentile(returns, 1))
    cvar_95 = float(returns[returns <= var_95].mean()) if (returns <= var_95).any() else var_95
    cvar_99 = float(returns[returns <= var_99].mean()) if (returns <= var_99).any() else var_99

    # Monthly stats
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    best_month = float(monthly.max()) if len(monthly) > 0 else 0
    worst_month = float(monthly.min()) if len(monthly) > 0 else 0

    metrics = {
        "total_return": total_return,
        "cagr": cagr,
        "annualized_vol": ann_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown": max_dd,
        "max_drawdown_duration_days": max_dd_duration,
        "hit_rate_daily": hit_rate,
        "skewness": skew,
        "kurtosis": kurt,
        "best_day": float(returns.max()),
        "worst_day": float(returns.min()),
        "best_month": best_month,
        "worst_month": worst_month,
        "var_95": var_95,
        "var_99": var_99,
        "cvar_95": cvar_95,
        "cvar_99": cvar_99,
        "n_trading_days": n,
        "n_years": round(n_years, 1),
    }

    if benchmark is not None:
        aligned = pd.concat([returns, benchmark], axis=1).dropna()
        if len(aligned) > 10:
            active = aligned.iloc[:, 0] - aligned.iloc[:, 1]
            te = active.std() * np.sqrt(TRADING_DAYS)
            ir = active.mean() / active.std() * np.sqrt(TRADING_DAYS) if active.std() > 0 else 0
            beta, alpha, _, _, _ = stats.linregress(aligned.iloc[:, 1], aligned.iloc[:, 0])
            metrics["information_ratio"] = ir
            metrics["tracking_error"] = te
            metrics["beta"] = beta
            metrics["alpha_annual"] = alpha * TRADING_DAYS

    return metrics


def rolling_sharpe(returns: pd.Series, window: int = 252) -> pd.Series:
    """Rolling annualised Sharpe ratio."""
    roll_mean = returns.rolling(window).mean()
    roll_std = returns.rolling(window).std()
    return (roll_mean / roll_std) * np.sqrt(TRADING_DAYS)


def monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
    """Pivot table of monthly returns: rows=year, columns=month."""
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    table = pd.DataFrame({
        "year": monthly.index.year,
        "month": monthly.index.month,
        "return": monthly.values,
    })
    return table.pivot(index="year", columns="month", values="return")
