"""Realised volatility estimators.

Multiple estimators serve different purposes:
- EWMA reacts quickly to vol spikes (good for fast risk reduction).
- Yang-Zhang uses OHLC data with better statistical efficiency.
- Garman-Klass is a robust OHLC alternative.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def ewma_volatility(returns: pd.DataFrame, halflife: int = 20) -> pd.DataFrame:
    """Exponentially-weighted realised volatility, annualised."""
    var = returns.ewm(halflife=halflife).var()
    return np.sqrt(var * 252)


def simple_rolling_volatility(
    returns: pd.DataFrame, window: int = 21
) -> pd.DataFrame:
    """Simple rolling standard deviation, annualised."""
    return returns.rolling(window).std() * np.sqrt(252)


def yang_zhang_volatility(
    open_: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    window: int = 20,
) -> pd.DataFrame:
    """Yang-Zhang OHLC volatility estimator.

    Combines overnight, open-to-close, and Rogers-Satchell components.
    More efficient than close-to-close for the same window size.
    """
    log_ho = np.log(high / open_)
    log_lo = np.log(low / open_)
    log_co = np.log(close / open_)
    log_oc = np.log(open_ / close.shift(1))

    close_vol = log_oc.rolling(window).var()
    open_vol = log_co.rolling(window).var()
    rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window).mean()

    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    yz_var = close_vol + k * open_vol + (1 - k) * rs

    return np.sqrt(yz_var.clip(lower=0) * 252)


def garman_klass_volatility(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    open_: pd.DataFrame,
    window: int = 20,
) -> pd.DataFrame:
    """Garman-Klass OHLC volatility estimator."""
    log_hl = np.log(high / low) ** 2
    log_co = np.log(close / open_) ** 2

    gk_var = (0.5 * log_hl - (2 * np.log(2) - 1) * log_co).rolling(window).mean()
    return np.sqrt(gk_var.clip(lower=0) * 252)
