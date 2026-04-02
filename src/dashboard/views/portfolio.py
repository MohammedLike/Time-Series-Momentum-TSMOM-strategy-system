"""Portfolio page: weights, exposure, turnover, allocation breakdown."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.components.charts import (
    weights_area_chart,
    exposure_chart,
    turnover_chart,
    COLORS,
    _base_layout,
)
from src.utils.types import BacktestResult


def render_portfolio(result: BacktestResult) -> None:
    st.markdown("## Portfolio Construction")

    if result.weights_history.empty:
        st.info("No weight data available.")
        return

    # Exposure metrics
    weights = result.weights_history
    col1, col2, col3, col4 = st.columns(4)
    latest = weights.iloc[-1]
    with col1:
        st.metric("Gross Exposure", f"{latest.abs().sum():.2f}x")
    with col2:
        st.metric("Net Exposure", f"{latest.sum():.2f}x")
    with col3:
        st.metric("# Long", f"{(latest > 0.001).sum()}")
    with col4:
        st.metric("# Short", f"{(latest < -0.001).sum()}")

    st.markdown("---")

    # Weights over time
    fig = weights_area_chart(weights)
    st.plotly_chart(fig, use_container_width=True, key="portfolio_weights")

    # Exposure chart
    col1, col2 = st.columns(2)
    with col1:
        fig = exposure_chart(weights)
        st.plotly_chart(fig, use_container_width=True, key="portfolio_exposure")
    with col2:
        fig = turnover_chart(weights)
        st.plotly_chart(fig, use_container_width=True, key="portfolio_turnover")

    # Current allocation pie chart
    st.markdown("---")
    st.markdown("### Current Allocation")
    current = latest[latest.abs() > 0.001]
    if not current.empty:
        col1, col2 = st.columns(2)
        with col1:
            long_pos = current[current > 0].sort_values(ascending=False)
            if not long_pos.empty:
                fig = go.Figure(data=go.Pie(
                    labels=long_pos.index.tolist(),
                    values=long_pos.values,
                    hole=0.4,
                    marker=dict(colors=[COLORS["positive"], COLORS["primary"],
                                       COLORS["secondary"], COLORS["warning"]] * 10),
                ))
                fig.update_layout(**_base_layout("Long Positions", height=350))
                st.plotly_chart(fig, use_container_width=True, key="portfolio_long_pie")

        with col2:
            short_pos = current[current < 0].abs().sort_values(ascending=False)
            if not short_pos.empty:
                fig = go.Figure(data=go.Pie(
                    labels=short_pos.index.tolist(),
                    values=short_pos.values,
                    hole=0.4,
                    marker=dict(colors=[COLORS["negative"], COLORS["warning"],
                                       COLORS["neutral"]] * 10),
                ))
                fig.update_layout(**_base_layout("Short Positions", height=350))
                st.plotly_chart(fig, use_container_width=True, key="portfolio_short_pie")

    # Trade Blotter
    st.markdown("---")
    with st.expander("Recent Trades", expanded=False):
        if not result.trade_blotter.empty:
            recent = result.trade_blotter.tail(50).sort_values("date", ascending=False)
            st.dataframe(
                recent.style.format({"weight_change": "{:.4f}"}),
                use_container_width=True,
            )
        else:
            st.info("No trades recorded.")

    # Cumulative costs
    st.markdown("---")
    st.markdown("### Cumulative Transaction Costs")
    cum_costs = result.costs_history.cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cum_costs.index, y=cum_costs.values * 100,
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.2)",
        line=dict(color=COLORS["negative"], width=1.5),
    ))
    fig.update_layout(**_base_layout("Cumulative Cost Drag (%)", height=300))
    fig.update_yaxes(title="Cumulative Cost (%)", ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True, key="portfolio_costs")
