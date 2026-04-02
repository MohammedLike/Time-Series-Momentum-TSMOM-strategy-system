"""Data contracts shared across the TSMOM system."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class BacktestResult:
    """Immutable container for a single backtest run."""

    portfolio_returns: pd.Series
    benchmark_returns: pd.Series | None
    weights_history: pd.DataFrame
    signals_history: pd.DataFrame
    costs_history: pd.Series
    trade_blotter: pd.DataFrame
    metrics: dict[str, float]
    settings_snapshot: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AssetMeta:
    """Metadata for a single tradeable instrument."""

    ticker: str
    name: str
    sector: str
    asset_class: str = "equities"
