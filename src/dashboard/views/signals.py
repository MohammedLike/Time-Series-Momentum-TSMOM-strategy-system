"""Signals page: signal heatmap, per-asset signals, distributions."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.components.charts import signal_heatmap, COLORS, _base_layout
from src.utils.types import BacktestResult
from src.data.cleaning import compute_returns


def render_signals(result: BacktestResult, prices: pd.DataFrame) -> None:
    st.markdown("## Signal Analysis")

    if result.signals_history.empty:
        st.info("No signal data available.")
        return

    # Signal Heatmap
    fig = signal_heatmap(result.signals_history)
    st.plotly_chart(fig, use_container_width=True, key="signals_heatmap")

    st.markdown("---")

    # Per-asset signal time series
    st.markdown("### Individual Asset Signals")
    assets = result.signals_history.columns.tolist()
    selected = st.multiselect("Select assets", assets, default=assets[:4])

    if selected:
        fig = go.Figure()
        for asset in selected:
            fig.add_trace(go.Scatter(
                x=result.signals_history.index,
                y=result.signals_history[asset].values,
                name=asset,
                mode="lines",
            ))
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["neutral"])
        fig.update_layout(**_base_layout("Signal Strength Over Time", height=400))
        st.plotly_chart(fig, use_container_width=True, key="signals_per_asset")

    # Signal Distribution
    st.markdown("---")
    st.markdown("### Signal Distribution")
    col1, col2 = st.columns(2)

    with col1:
        flat_signals = result.signals_history.stack().dropna()
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=flat_signals.values,
            nbinsx=80,
            marker_color=COLORS["primary"],
            opacity=0.7,
        ))
        fig.update_layout(**_base_layout("Cross-Sectional Signal Distribution", height=350))
        fig.update_xaxes(title="Signal Value")
        st.plotly_chart(fig, use_container_width=True, key="signals_distribution")

    with col2:
        # Signal autocorrelation (persistence indicator)
        avg_signal = result.signals_history.mean(axis=1)
        autocorr = [avg_signal.autocorr(lag=i) for i in range(1, 31)]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(range(1, 31)),
            y=autocorr,
            marker_color=COLORS["secondary"],
        ))
        fig.update_layout(**_base_layout("Signal Autocorrelation (Persistence)", height=350))
        fig.update_xaxes(title="Lag (days)")
        fig.update_yaxes(title="Autocorrelation")
        st.plotly_chart(fig, use_container_width=True, key="signals_autocorr")

    # Signal vs Forward Returns scatter
    st.markdown("---")
    st.markdown("### Signal Predictive Power")
    returns = compute_returns(prices)
    fwd_5d = returns.rolling(5).sum().shift(-5)
    aligned_signals = result.signals_history.reindex(fwd_5d.index)

    avg_sig = aligned_signals.mean(axis=1).dropna()
    avg_fwd = fwd_5d.mean(axis=1).dropna()
    common = avg_sig.index.intersection(avg_fwd.index)

    if len(common) > 100:
        fig = go.Figure()
        fig.add_trace(go.Scattergl(
            x=avg_sig[common].values,
            y=avg_fwd[common].values * 100,
            mode="markers",
            marker=dict(color=COLORS["primary"], size=2, opacity=0.3),
        ))
        fig.update_layout(**_base_layout("Average Signal vs 5-Day Forward Return", height=400))
        fig.update_xaxes(title="Signal")
        fig.update_yaxes(title="5-Day Fwd Return (%)")
        st.plotly_chart(fig, use_container_width=True, key="signals_predictive")
