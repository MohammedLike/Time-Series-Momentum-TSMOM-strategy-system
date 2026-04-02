"""Transaction cost modelling.

Models slippage and commission costs that erode gross returns.
Essential for realistic backtesting — many strategies that look
profitable before costs are unprofitable after.
"""

from __future__ import annotations

import pandas as pd


class TransactionCostModel:
    """Computes round-trip transaction costs from weight changes."""

    def __init__(self, slippage_bps: float = 5.0, commission_bps: float = 1.0):
        self.total_cost_bps = slippage_bps + commission_bps

    def compute_costs(self, weight_changes: pd.DataFrame) -> pd.Series:
        """Daily transaction costs as a fraction of portfolio value.

        cost_t = sum(|Δw_i,t|) × total_cost_bps / 10_000
        """
        turnover = weight_changes.abs().sum(axis=1)
        return turnover * self.total_cost_bps / 10_000

    def net_returns(
        self, gross_returns: pd.Series, costs: pd.Series
    ) -> pd.Series:
        """Gross returns minus transaction costs."""
        aligned_costs = costs.reindex(gross_returns.index, fill_value=0)
        return gross_returns - aligned_costs
