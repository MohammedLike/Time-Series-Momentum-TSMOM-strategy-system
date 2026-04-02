"""Composite signal generator — the intellectual core of the system.

Blends multi-horizon momentum signals with regime awareness
to produce the final trading signal for each asset.
"""

from __future__ import annotations

import pandas as pd

from config.settings import AppSettings
from src.signals.filters import apply_signal_pipeline
from src.signals.momentum import multi_horizon_blend
from src.signals.regime import HMMRegimeDetector, trend_strength_indicator
from src.signals.volatility import ewma_volatility


class CompositeSignalGenerator:
    """Generates regime-aware, multi-horizon momentum signals.

    Pipeline:
        1. Compute blended momentum signal across lookback windows
        2. Detect market regime (trending vs mean-reverting)
        3. Scale signal by regime confidence (dampen in mean-reverting)
        4. Apply smoothing, z-score normalisation, and capping
    """

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.regime_detector = HMMRegimeDetector(n_regimes=2)

    def generate(self, returns: pd.DataFrame) -> pd.DataFrame:
        raw_signal = multi_horizon_blend(returns, self.settings.momentum_lookbacks)

        # Regime overlay: use a broad market proxy (mean of all assets)
        market_returns = returns.mean(axis=1)
        try:
            regime_score = self.regime_detector.fit_predict(market_returns)
        except Exception:
            regime_score = trend_strength_indicator(
                market_returns.to_frame(), lookback=252
            ).iloc[:, 0]

        # Scale: trending regime → full signal; mean-reverting → dampened
        # regime_score ∈ [0, 1]; we map to [0.3, 1.0] to never fully zero out
        regime_multiplier = 0.3 + 0.7 * regime_score
        scaled_signal = raw_signal.multiply(regime_multiplier, axis=0)

        final_signal = apply_signal_pipeline(
            scaled_signal,
            smooth_halflife=5,
            zscore_window=252,
            cap=self.settings.signal_cap,
        )
        return final_signal

    def generate_components(self, returns: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Returns individual signal components for dashboard analysis."""
        raw_signal = multi_horizon_blend(returns, self.settings.momentum_lookbacks)
        market_returns = returns.mean(axis=1)
        vol = ewma_volatility(returns)

        try:
            regime_score = self.regime_detector.fit_predict(market_returns)
        except Exception:
            regime_score = trend_strength_indicator(
                market_returns.to_frame(), lookback=252
            ).iloc[:, 0]

        return {
            "raw_momentum": raw_signal,
            "regime_score": regime_score,
            "volatility": vol,
            "final_signal": self.generate(returns),
        }
