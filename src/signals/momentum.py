"""Core time-series momentum signal generators.

Implements the classic TSMOM signals from Moskowitz, Ooi & Pedersen (2012)
plus continuous and multi-horizon blended variants.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def tsmom_signal(returns: pd.DataFrame, lookback: int, skip: int = 1) -> pd.DataFrame:
    """Binary TSMOM: sign of cumulative return over [t-lookback-skip, t-skip].

    Args:
        returns: Daily returns, shape (T, N).
        lookback: Number of trading days for the lookback window.
        skip: Days to skip before signal date (avoids short-term reversal).

    Returns:
        DataFrame of {-1, 0, +1} signals.
    """
    cum_ret = returns.rolling(lookback).sum().shift(skip)
    return np.sign(cum_ret)


def continuous_tsmom_signal(
    returns: pd.DataFrame, lookback: int, skip: int = 1
) -> pd.DataFrame:
    """Continuous TSMOM: cumulative return normalised by realised volatility.

    Produces a signal proportional to risk-adjusted trend strength,
    typically in the range [-3, +3].
    """
    cum_ret = returns.rolling(lookback).sum().shift(skip)
    vol = returns.rolling(lookback).std() * np.sqrt(252)
    vol = vol.replace(0, np.nan)
    return cum_ret / vol


def multi_horizon_blend(
    returns: pd.DataFrame,
    lookbacks: list[int],
    weights: list[float] | None = None,
) -> pd.DataFrame:
    """Blends continuous TSMOM signals across multiple lookback windows.

    Default: equal-weight blend. Produces a smooth composite momentum signal.
    """
    if weights is None:
        weights = [1.0 / len(lookbacks)] * len(lookbacks)
    if len(weights) != len(lookbacks):
        raise ValueError("weights must match lookbacks in length")

    blended = pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
    for lb, w in zip(lookbacks, weights):
        sig = continuous_tsmom_signal(returns, lb)
        blended += w * sig.fillna(0)
    return blended


def macd_momentum_signal(
    prices: pd.DataFrame, fast: int = 12, slow: int = 26, signal_line: int = 9
) -> pd.DataFrame:
    """MACD-based momentum signal (alternative to pure return-based TSMOM).

    Returns the normalised MACD histogram as a continuous signal.
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_line, adjust=False).mean()
    histogram = macd - signal
    vol = histogram.rolling(252, min_periods=20).std()
    vol = vol.replace(0, np.nan)
    return histogram / vol
