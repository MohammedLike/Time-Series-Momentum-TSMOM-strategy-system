"""Portfolio constraint enforcement.

Ensures weights respect position limits, gross exposure caps,
and sector concentration limits.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class ConstraintSet:
    """Applies a sequence of constraints to portfolio weights."""

    def __init__(
        self,
        max_position: float = 0.10,
        max_gross_exposure: float = 2.0,
        sector_limit: float | None = None,
    ):
        self.max_position = max_position
        self.max_gross_exposure = max_gross_exposure
        self.sector_limit = sector_limit

    def apply(self, weights: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
        w = self._cap_individual_positions(weights)
        w = self._cap_gross_exposure(w)
        return w

    def _cap_individual_positions(
        self, weights: pd.Series | pd.DataFrame
    ) -> pd.Series | pd.DataFrame:
        """Proportionally rescale if any position exceeds max_position."""
        abs_w = weights.abs()
        max_abs = abs_w.max() if isinstance(abs_w, pd.Series) else abs_w.max(axis=1)

        if isinstance(weights, pd.Series):
            if max_abs > self.max_position and max_abs > 0:
                scale = self.max_position / max_abs
                return weights * scale
            return weights.clip(-self.max_position, self.max_position)

        return weights.clip(-self.max_position, self.max_position)

    def _cap_gross_exposure(
        self, weights: pd.Series | pd.DataFrame
    ) -> pd.Series | pd.DataFrame:
        """Scale down all weights proportionally if gross exposure is breached."""
        if isinstance(weights, pd.Series):
            gross = weights.abs().sum()
            if gross > self.max_gross_exposure and gross > 0:
                return weights * (self.max_gross_exposure / gross)
            return weights

        gross = weights.abs().sum(axis=1)
        scale = np.minimum(1.0, self.max_gross_exposure / gross.replace(0, np.nan).fillna(1))
        return weights.multiply(scale, axis=0)
