"""Walk-forward validation for honest out-of-sample performance estimation.

Without walk-forward, any backtest result is suspect — you don't know
how much is genuine alpha vs overfitting to the training period.
"""

from __future__ import annotations

import logging

import pandas as pd

from config.settings import AppSettings
from src.backtest.engine import BacktestEngine
from src.utils.types import BacktestResult

logger = logging.getLogger(__name__)


def walk_forward_backtest(
    prices: pd.DataFrame,
    settings: AppSettings | None = None,
    train_window: int = 756,   # ~3 years
    test_window: int = 252,    # ~1 year
    step: int = 126,           # ~6 months
) -> list[BacktestResult]:
    """Walk-forward out-of-sample validation.

    Slides a train/test window through time:
    - Train on [t, t+train_window) to fit regime model
    - Test on [t+train_window, t+train_window+test_window)
    - Step forward by `step` days

    Returns list of BacktestResults, one per fold.
    """
    settings = settings or AppSettings()
    dates = prices.index
    n = len(dates)
    folds = []

    fold_idx = 0
    start = 0
    while start + train_window + test_window <= n:
        train_end = start + train_window
        test_end = min(train_end + test_window, n)

        train_prices = prices.iloc[start:train_end]
        test_prices = prices.iloc[train_end:test_end]

        logger.info(
            "Fold %d: train %s→%s, test %s→%s",
            fold_idx,
            dates[start].strftime("%Y-%m-%d"),
            dates[train_end - 1].strftime("%Y-%m-%d"),
            dates[train_end].strftime("%Y-%m-%d"),
            dates[test_end - 1].strftime("%Y-%m-%d"),
        )

        engine = BacktestEngine(settings)
        # Fit signals on full history up to test start
        full_prices = prices.iloc[:test_end]
        result = engine.run(full_prices)

        # Extract only the test-period returns
        test_dates = test_prices.index
        oos_result = BacktestResult(
            portfolio_returns=result.portfolio_returns.reindex(test_dates).dropna(),
            benchmark_returns=None,
            weights_history=result.weights_history.reindex(test_dates).dropna(),
            signals_history=result.signals_history.reindex(test_dates).dropna(),
            costs_history=result.costs_history.reindex(test_dates).dropna(),
            trade_blotter=result.trade_blotter[
                result.trade_blotter["date"].isin(test_dates)
            ] if len(result.trade_blotter) > 0 else result.trade_blotter,
            metrics=result.metrics,
            settings_snapshot=result.settings_snapshot,
        )
        folds.append(oos_result)

        start += step
        fold_idx += 1

    logger.info("Walk-forward complete: %d folds", len(folds))
    return folds


def combine_walk_forward_results(folds: list[BacktestResult]) -> pd.Series:
    """Stitch together out-of-sample returns from walk-forward folds."""
    all_returns = pd.concat([f.portfolio_returns for f in folds])
    return all_returns.sort_index()[~all_returns.sort_index().index.duplicated(keep="first")]
