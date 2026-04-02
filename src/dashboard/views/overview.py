"""Overview page: KPIs, equity curve, rolling Sharpe, monthly heatmap."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.dashboard.components.kpi_cards import render_kpi_row, render_extended_metrics
from src.dashboard.components.charts import (
    equity_curve_chart,
    drawdown_chart,
    rolling_sharpe_chart,
    monthly_heatmap,
)
from src.utils.types import BacktestResult
from src.data.cleaning import compute_returns


def render_overview(result: BacktestResult, prices: pd.DataFrame) -> None:
    st.markdown("## Performance Overview")

    # KPI Cards
    render_kpi_row(result.metrics)

    st.markdown("---")

    # Equity Curve
    benchmark_ret = compute_returns(prices).mean(axis=1) if prices.shape[1] > 1 else None
    fig_equity = equity_curve_chart(result.portfolio_returns, benchmark_ret)
    st.plotly_chart(fig_equity, use_container_width=True, key="overview_equity")

    # Two-column: Rolling Sharpe + Drawdown
    col1, col2 = st.columns(2)
    with col1:
        fig_sharpe = rolling_sharpe_chart(result.portfolio_returns)
        st.plotly_chart(fig_sharpe, use_container_width=True, key="overview_sharpe")
    with col2:
        fig_dd = drawdown_chart(result.portfolio_returns)
        st.plotly_chart(fig_dd, use_container_width=True, key="overview_drawdown")

    # Monthly Returns Heatmap
    st.markdown("---")
    fig_heatmap = monthly_heatmap(result.portfolio_returns)
    st.plotly_chart(fig_heatmap, use_container_width=True, key="overview_heatmap")

    # Extended Metrics
    with st.expander("Detailed Metrics", expanded=False):
        render_extended_metrics(result.metrics)
