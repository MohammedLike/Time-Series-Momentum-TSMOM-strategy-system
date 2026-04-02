"""Signal post-processing: smoothing, normalisation, and capping."""

from __future__ import annotations

import numpy as np
import pandas as pd


def smooth_signal(signal: pd.DataFrame, halflife: int = 5) -> pd.DataFrame:
    """Exponential smoothing to reduce signal noise and turnover."""
    return signal.ewm(halflife=halflife).mean()


def zscore_normalize(signal: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """Cross-sectional z-score normalisation within a rolling window."""
    mean = signal.rolling(window, min_periods=20).mean()
    std = signal.rolling(window, min_periods=20).std().replace(0, np.nan)
    return (signal - mean) / std


def cap_signal(signal: pd.DataFrame, cap: float = 2.0) -> pd.DataFrame:
    """Clip signal values to [-cap, +cap] to limit extreme bets."""
    return signal.clip(-cap, cap)


def apply_signal_pipeline(
    raw_signal: pd.DataFrame,
    smooth_halflife: int = 5,
    zscore_window: int = 252,
    cap: float = 2.0,
) -> pd.DataFrame:
    """Full post-processing pipeline: smooth → normalise → cap."""
    sig = smooth_signal(raw_signal, smooth_halflife)
    sig = zscore_normalize(sig, zscore_window)
    sig = cap_signal(sig, cap)
    return sig
