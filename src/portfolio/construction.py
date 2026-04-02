"""Portfolio construction: signals → target weights.

Orchestrates position sizing, constraint enforcement,
and drawdown control into a single pipeline.
"""

from __future__ import annotations

import pandas as pd

from config.settings import AppSettings
from src.portfolio.constraints import ConstraintSet
from src.portfolio.position_sizing import volatility_target_weights
from src.risk.drawdown import DrawdownControlOverlay


class PortfolioConstructor:
    """Converts trading signals into constrained, risk-managed portfolio weights."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.constraints = ConstraintSet(
            max_position=settings.max_position_weight,
            max_gross_exposure=settings.max_gross_exposure,
        )
        self.drawdown_overlay = DrawdownControlOverlay(
            threshold=settings.drawdown_threshold,
            floor=settings.drawdown_scaling_floor,
        )

    def compute_weights(
        self,
        signals: pd.DataFrame,
        realized_vol: pd.DataFrame,
        portfolio_returns: pd.Series | None = None,
    ) -> pd.DataFrame:
        """Full pipeline: size → constrain → drawdown overlay.

        Args:
            signals: Trading signals, shape (T, N).
            realized_vol: Annualised vol estimates, shape (T, N).
            portfolio_returns: Running portfolio returns for drawdown calc.

        Returns:
            Target portfolio weights, shape (T, N).
        """
        raw_weights = volatility_target_weights(
            signals, realized_vol, self.settings.vol_target
        )

        constrained = self.constraints.apply(raw_weights)

        if portfolio_returns is not None:
            dd_scale = self.drawdown_overlay.compute_scale_series(portfolio_returns)
            constrained = constrained.multiply(dd_scale, axis=0)

        return constrained.fillna(0)


def compute_rebalance_mask(
    dates: pd.DatetimeIndex, frequency: str = "monthly"
) -> pd.Series:
    """Returns boolean mask: True on rebalance dates."""
    mask = pd.Series(False, index=dates)
    if frequency == "daily":
        mask[:] = True
    elif frequency == "weekly":
        mask[dates.weekday == 4] = True  # Fridays
    elif frequency == "monthly":
        month_ends = dates.to_series().groupby(dates.to_period("M")).tail(1).index
        mask[month_ends] = True
    return mask


def apply_rebalance_schedule(
    weights: pd.DataFrame, rebalance_mask: pd.Series
) -> pd.DataFrame:
    """Only update weights on rebalance dates; hold between."""
    rebalanced = weights.copy()
    rebalanced[~rebalance_mask] = pd.NA
    return rebalanced.ffill().fillna(0)
