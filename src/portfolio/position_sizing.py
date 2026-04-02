"""Position sizing methods.

Implements the Moskowitz/Ooi/Pedersen volatility-targeting approach
plus Kelly criterion and risk-parity alternatives.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def volatility_target_weights(
    signals: pd.DataFrame,
    realized_vol: pd.DataFrame,
    vol_target: float = 0.10,
) -> pd.DataFrame:
    """Volatility-targeting position sizing (the TSMOM standard).

    Each asset gets an equal risk budget of vol_target / N.
    Weight_i = signal_i × (vol_target / N) / realized_vol_i

    This ensures each position contributes roughly equally to
    portfolio risk regardless of the asset's inherent volatility.
    """
    n_assets = signals.shape[1]
    per_asset_budget = vol_target / n_assets
    safe_vol = realized_vol.replace(0, np.nan).clip(lower=0.01)
    weights = signals * per_asset_budget / safe_vol
    return weights


def inverse_vol_weights(
    signals: pd.DataFrame, realized_vol: pd.DataFrame
) -> pd.DataFrame:
    """Weight inversely proportional to volatility, scaled by signal direction."""
    inv_vol = 1.0 / realized_vol.replace(0, np.nan).clip(lower=0.01)
    inv_vol_sum = inv_vol.sum(axis=1)
    normalized = inv_vol.div(inv_vol_sum, axis=0)
    return normalized * np.sign(signals)


def equal_weight_signals(signals: pd.DataFrame) -> pd.DataFrame:
    """Equal weight per asset, direction from signal."""
    n = signals.shape[1]
    return np.sign(signals) / n
