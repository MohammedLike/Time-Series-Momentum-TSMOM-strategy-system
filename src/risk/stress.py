"""Historical stress testing.

Evaluates strategy performance during known crisis periods.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

HISTORICAL_SCENARIOS: dict[str, tuple[str, str]] = {
    "Global Financial Crisis": ("2008-09-01", "2009-03-31"),
    "European Debt Crisis": ("2011-07-01", "2011-11-30"),
    "Taper Tantrum": ("2013-05-01", "2013-09-30"),
    "China Deval / Oil Crash": ("2015-08-01", "2016-02-29"),
    "Volmageddon Feb 2018": ("2018-01-26", "2018-03-31"),
    "COVID-19 Crash": ("2020-02-15", "2020-04-15"),
    "2022 Rate Shock": ("2022-01-01", "2022-06-30"),
    "SVB Banking Crisis": ("2023-03-01", "2023-03-31"),
}


def run_stress_tests(
    portfolio_returns: pd.Series,
    scenarios: dict[str, tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """Evaluate portfolio performance during historical stress periods.

    Returns a DataFrame with one row per scenario:
    cumulative_return, max_drawdown, worst_day, annualized_vol, n_days.
    """
    if scenarios is None:
        scenarios = HISTORICAL_SCENARIOS

    results = []
    for name, (start, end) in scenarios.items():
        mask = (portfolio_returns.index >= start) & (portfolio_returns.index <= end)
        period_returns = portfolio_returns[mask]
        if len(period_returns) < 2:
            continue

        cum = (1 + period_returns).prod() - 1
        running_max = (1 + period_returns).cumprod().cummax()
        dd = (1 + period_returns).cumprod() / running_max - 1
        max_dd = dd.min()

        results.append({
            "scenario": name,
            "period": f"{start} → {end}",
            "cumulative_return": cum,
            "max_drawdown": max_dd,
            "worst_day": period_returns.min(),
            "best_day": period_returns.max(),
            "annualized_vol": period_returns.std() * np.sqrt(252),
            "n_days": len(period_returns),
        })

    return pd.DataFrame(results).set_index("scenario") if results else pd.DataFrame()
