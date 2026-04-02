"""Asset detail page: drill down into individual asset performance."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.components.charts import COLORS, _base_layout
from src.utils.types import BacktestResult
from src.data.cleaning import compute_returns
from src.risk.metrics import compute_all_metrics


def render_asset_detail(result: BacktestResult, prices: pd.DataFrame) -> None:
    st.markdown("## Asset Detail")

    assets = result.weights_history.columns.tolist()
    if not assets:
        st.info("No assets in portfolio.")
        return

    selected = st.selectbox("Select Asset", assets)
    if selected is None:
        return

    returns = compute_returns(prices)

    # ── Multi-panel chart: Price + Signal + Weight ──────────────────
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.35, 0.20, 0.20, 0.25],
        subplot_titles=("Price", "Momentum Signal", "Portfolio Weight", "PnL Contribution"),
    )

    # Price
    if selected in prices.columns:
        fig.add_trace(go.Scatter(
            x=prices.index, y=prices[selected].values,
            name="Price", line=dict(color=COLORS["primary"], width=1.5),
        ), row=1, col=1)

    # Signal
    if selected in result.signals_history.columns:
        sig = result.signals_history[selected]
        colors = [COLORS["positive"] if v > 0 else COLORS["negative"] for v in sig.values]
        fig.add_trace(go.Bar(
            x=sig.index, y=sig.values,
            name="Signal", marker_color=colors, opacity=0.6,
        ), row=2, col=1)

    # Weight
    if selected in result.weights_history.columns:
        w = result.weights_history[selected]
        fig.add_trace(go.Scatter(
            x=w.index, y=w.values,
            name="Weight", fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.2)",
            line=dict(color=COLORS["primary"], width=1),
        ), row=3, col=1)

    # PnL Contribution
    if selected in returns.columns and selected in result.weights_history.columns:
        contrib = result.weights_history[selected].shift(1) * returns[selected]
        cum_contrib = contrib.cumsum()
        fig.add_trace(go.Scatter(
            x=cum_contrib.index, y=cum_contrib.values * 100,
            name="Cum. PnL", fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.2)",
            line=dict(color=COLORS["positive"], width=1.5),
        ), row=4, col=1)

    fig.update_layout(
        height=900,
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        showlegend=False,
        margin=dict(l=50, r=30, t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True, key="asset_detail_multipanel")

    # ── Asset-level Metrics ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### {selected} Performance Metrics")

    if selected in returns.columns and selected in result.weights_history.columns:
        asset_contrib = result.weights_history[selected].shift(1) * returns[selected]
        asset_contrib = asset_contrib.dropna()
        if len(asset_contrib) > 10:
            asset_metrics = compute_all_metrics(asset_contrib)

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Contribution", f"{asset_metrics.get('total_return', 0):.1%}")
            with col2:
                st.metric("Sharpe", f"{asset_metrics.get('sharpe_ratio', 0):.2f}")
            with col3:
                st.metric("Hit Rate", f"{asset_metrics.get('hit_rate_daily', 0):.1%}")
            with col4:
                st.metric("Max DD", f"{asset_metrics.get('max_drawdown', 0):.1%}")
            with col5:
                st.metric("Avg Weight", f"{result.weights_history[selected].mean():.3f}")

    # ── Trade history for this asset ────────────────────────────────
    st.markdown("---")
    with st.expander(f"Trade History for {selected}", expanded=False):
        if not result.trade_blotter.empty:
            asset_trades = result.trade_blotter[result.trade_blotter["asset"] == selected]
            if not asset_trades.empty:
                st.dataframe(
                    asset_trades.tail(30).sort_values("date", ascending=False),
                    use_container_width=True,
                )
            else:
                st.info(f"No trades for {selected}.")
        else:
            st.info("No trade data.")
