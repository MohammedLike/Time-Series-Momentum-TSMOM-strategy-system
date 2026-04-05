"""Vectorised backtest engine.

Core of the TSMOM system — transforms raw prices into a fully
attributed backtest with signals, weights, costs, and metrics.

Design choice: vectorised (not event-driven) for speed. On daily bars
with < 50 assets, this runs in seconds, not minutes.
"""

from __future__ import annotations

import logging

import pandas as pd

from config.settings import AppSettings
from src.costs.transaction_costs import TransactionCostModel
from src.data.cleaning import compute_returns, winsorize_returns
from src.portfolio.construction import (
    PortfolioConstructor,
    apply_rebalance_schedule,
    compute_rebalance_mask,
)
from src.risk.drawdown import DrawdownControlOverlay
from src.risk.metrics import compute_all_metrics
from src.signals.composite import CompositeSignalGenerator
from src.signals.volatility import ewma_volatility
from src.utils.types import BacktestResult

logger = logging.getLogger(__name__)


class BacktestEngine:
    """End-to-end backtest: prices → signals → weights → PnL → metrics.

    The engine:
    1. Computes returns and volatility from prices
    2. Generates composite momentum signals (regime-aware)
    3. Sizes positions via vol-targeting with constraints
    4. Applies rebalance schedule and drawdown control
    5. Accounts for transaction costs
    6. Produces full attribution and risk metrics
    """

    def __init__(self, settings: AppSettings | None = None):
        self.settings = settings or AppSettings()
        self.signal_generator = CompositeSignalGenerator(self.settings)
        self.portfolio_constructor = PortfolioConstructor(self.settings)
        self.cost_model = TransactionCostModel(
            slippage_bps=self.settings.default_slippage_bps,
            commission_bps=self.settings.commission_bps,
        )
        self.drawdown_overlay = DrawdownControlOverlay(
            threshold=self.settings.drawdown_threshold,
            floor=self.settings.drawdown_scaling_floor,
        )

    def run(
        self,
        prices: pd.DataFrame,
        benchmark_returns: pd.Series | None = None,
    ) -> BacktestResult:
        logger.info("Starting backtest with %d assets, %d days", prices.shape[1], prices.shape[0])

        # ── Step 1: Returns & volatility ─────────────────────────────
        returns = compute_returns(prices)
        returns = winsorize_returns(returns)
        vol = ewma_volatility(returns, halflife=20)

        # ── Step 2: Signal generation ────────────────────────────────
        signals = self.signal_generator.generate(returns)

        # ── Step 3: Raw position sizing ──────────────────────────────
        raw_weights = self.portfolio_constructor.compute_weights(signals, vol)

        # ── Step 4: Rebalance schedule ───────────────────────────────
        rebal_mask = compute_rebalance_mask(
            returns.index, self.settings.rebalance_frequency
        )
        weights = apply_rebalance_schedule(raw_weights, rebal_mask)

        # ── Step 5: Drawdown control (iterative for path dependency) ─
        weights = self._apply_drawdown_control(weights, returns)

        # ── Step 6: Portfolio returns & costs ────────────────────────
        weight_changes = weights.diff().fillna(0)
        gross_returns = (weights.shift(1) * returns).sum(axis=1)
        costs = self.cost_model.compute_costs(weight_changes)
        net_returns = self.cost_model.net_returns(gross_returns, costs)

        # ── Step 7: Trade blotter ────────────────────────────────────
        blotter = self._build_blotter(weight_changes)

        # ── Step 8: Metrics ──────────────────────────────────────────
        metrics = compute_all_metrics(net_returns, self.settings.risk_free_rate, benchmark_returns)

        logger.info(
            "Backtest complete. Sharpe=%.2f, CAGR=%.1f%%, MaxDD=%.1f%%",
            metrics.get("sharpe_ratio", 0),
            metrics.get("cagr", 0) * 100,
            metrics.get("max_drawdown", 0) * 100,
        )

        return BacktestResult(
            portfolio_returns=net_returns,
            benchmark_returns=benchmark_returns,
            weights_history=weights,
            signals_history=signals,
            costs_history=costs,
            trade_blotter=blotter,
            metrics=metrics,
            settings_snapshot=self.settings.model_dump(),
        )

    def _apply_drawdown_control(
        self, weights: pd.DataFrame, returns: pd.DataFrame
    ) -> pd.DataFrame:
        """Apply drawdown overlay using running portfolio PnL."""
        controlled = weights.copy()
        port_ret = (weights.shift(1) * returns).sum(axis=1)
        cum = (1 + port_ret).cumprod()
        running_max = cum.cummax()
        dd = cum / running_max - 1

        scale = self.drawdown_overlay.compute_scale_series(port_ret)
        controlled = controlled.multiply(scale, axis=0)
        return controlled

    def _build_blotter(self, weight_changes: pd.DataFrame) -> pd.DataFrame:
        """Build a trade blotter from weight changes."""
        records = []
        for date in weight_changes.index:
            row = weight_changes.loc[date]
            trades = row[row.abs() > 1e-6]
            for asset, delta in trades.items():
                records.append({
                    "date": date,
                    "asset": asset,
                    "side": "BUY" if delta > 0 else "SELL",
                    "weight_change": delta,
                })
        return pd.DataFrame(records) if records else pd.DataFrame(
            columns=["date", "asset", "side", "weight_change"]
        )
