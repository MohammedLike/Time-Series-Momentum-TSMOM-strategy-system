"""Drawdown analysis and drawdown-control overlay.

The DrawdownControlOverlay is the single most important production risk
feature for momentum strategies, protecting against "momentum crashes"
— sharp trend reversals that can wipe months of gains.
"""

from __future__ import annotations

import pandas as pd


def drawdown_series(returns: pd.Series) -> pd.DataFrame:
    """Compute cumulative return, running max, drawdown, and duration."""
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    dd = cum / running_max - 1

    is_dd = dd < 0
    dd_groups = (~is_dd).cumsum()
    duration = is_dd.groupby(dd_groups).cumsum()

    return pd.DataFrame({
        "cumulative": cum,
        "running_max": running_max,
        "drawdown": dd,
        "drawdown_duration": duration,
    })


class DrawdownControlOverlay:
    """Dynamically reduces exposure when portfolio is in drawdown.

    When drawdown exceeds `threshold`, positions are scaled down
    proportionally. At the `floor`, positions are at minimum size.

    scale = max(floor, 1 - (|current_dd| - threshold) / threshold)

    This prevents the classic momentum crash from compounding losses.
    """

    def __init__(self, threshold: float = 0.10, floor: float = 0.25):
        self.threshold = threshold
        self.floor = floor

    def compute_scale(self, current_drawdown: float) -> float:
        """Single-point scale factor given current drawdown (negative number)."""
        dd = abs(current_drawdown)
        if dd <= self.threshold:
            return 1.0
        scale = 1.0 - (dd - self.threshold) / self.threshold
        return max(self.floor, scale)

    def compute_scale_series(self, returns: pd.Series) -> pd.Series:
        """Vectorised scale factor series from return stream."""
        cum = (1 + returns).cumprod()
        running_max = cum.cummax()
        dd = cum / running_max - 1  # negative values

        dd_abs = dd.abs()
        scale = 1.0 - (dd_abs - self.threshold).clip(lower=0) / self.threshold
        return scale.clip(lower=self.floor, upper=1.0)
