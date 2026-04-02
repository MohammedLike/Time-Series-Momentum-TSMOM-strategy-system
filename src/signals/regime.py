"""Market regime detection.

Identifies trending vs mean-reverting regimes using:
1. Hidden Markov Model (HMM) — probabilistic regime classification
2. Trend strength indicator — simple heuristic
3. Volatility regime indicator — high/low vol classification

Regime awareness is what separates toy TSMOM from production-grade:
academic research shows TSMOM alpha concentrates in trending regimes.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HMMRegimeDetector:
    """Two-state Gaussian HMM for regime detection.

    States are labelled as 'trending' (momentum works) vs 'mean-reverting'
    (momentum is dangerous) based on which state has higher mean |return|.
    """

    def __init__(self, n_regimes: int = 2):
        self.n_regimes = n_regimes
        self.model = None

    def fit_predict(self, returns: pd.Series) -> pd.Series:
        try:
            from hmmlearn.hmm import GaussianHMM
        except ImportError:
            logger.warning("hmmlearn not installed; falling back to trend strength")
            return trend_strength_indicator(returns.to_frame(), lookback=252).iloc[:, 0]

        clean = returns.dropna().values.reshape(-1, 1)
        model = GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="full",
            n_iter=200,
            random_state=42,
        )
        model.fit(clean)
        self.model = model

        states = model.predict(clean)
        state_series = pd.Series(states, index=returns.dropna().index, name="regime")

        means = model.means_.flatten()
        trending_state = int(np.argmax(np.abs(means)))
        state_series = state_series.map(
            lambda s: 1.0 if s == trending_state else 0.0
        )
        return state_series.reindex(returns.index).ffill().fillna(0.5)

    def regime_probability(self, returns: pd.Series) -> pd.DataFrame:
        if self.model is None:
            self.fit_predict(returns)
        if self.model is None:
            return pd.DataFrame(
                {"trending": 0.5, "mean_reverting": 0.5}, index=returns.index
            )
        clean = returns.dropna().values.reshape(-1, 1)
        probs = self.model.predict_proba(clean)
        df = pd.DataFrame(
            probs,
            index=returns.dropna().index,
            columns=[f"regime_{i}" for i in range(self.n_regimes)],
        )
        return df.reindex(returns.index).ffill().fillna(0.5)


def trend_strength_indicator(
    returns: pd.DataFrame, lookback: int = 252
) -> pd.DataFrame:
    """Fraction of sub-periods with positive return.

    Values near 1.0 = strong uptrend, near 0.0 = strong downtrend,
    near 0.5 = no trend (likely mean-reverting).
    """
    positive = (returns > 0).astype(float)
    return positive.rolling(lookback, min_periods=20).mean()


def vol_regime_indicator(
    vol_series: pd.DataFrame, threshold_percentile: float = 0.75
) -> pd.DataFrame:
    """Binary high-vol indicator.

    Returns 1.0 when current vol exceeds its rolling 75th percentile
    (or custom threshold). Used to dampen signals in extreme volatility.
    """
    rolling_quantile = vol_series.rolling(252, min_periods=60).quantile(threshold_percentile)
    return (vol_series > rolling_quantile).astype(float)
