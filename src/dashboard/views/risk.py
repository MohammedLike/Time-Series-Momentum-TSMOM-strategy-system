"""Risk page: drawdown, VaR, stress tests, correlations, distributions."""

from __future__ import annotations

import streamlit as st
import numpy as np

from src.dashboard.components.charts import (
    drawdown_chart,
    return_distribution_chart,
    correlation_heatmap,
    COLORS,
    _base_layout,
)
from src.risk.var import rolling_var, rolling_cvar
from src.risk.stress import run_stress_tests
from src.utils.types import BacktestResult
import plotly.graph_objects as go


def render_risk(result: BacktestResult) -> None:
    st.markdown("## Risk Management")

    ret = result.portfolio_returns

    # Risk KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    m = result.metrics
    with col1:
        st.metric("Ann. Vol", f"{m.get('annualized_vol', 0):.1%}")
    with col2:
        st.metric("Max Drawdown", f"{m.get('max_drawdown', 0):.1%}")
    with col3:
        st.metric("VaR (95%)", f"{m.get('var_95', 0):.2%}")
    with col4:
        st.metric("CVaR (95%)", f"{m.get('cvar_95', 0):.2%}")
    with col5:
        st.metric("DD Duration", f"{m.get('max_drawdown_duration_days', 0):.0f}d")

    st.markdown("---")

    # Drawdown Chart
    fig = drawdown_chart(ret)
    st.plotly_chart(fig, use_container_width=True, key="risk_drawdown")

    # Rolling VaR / CVaR
    st.markdown("### Rolling Risk Measures")
    col1, col2 = st.columns(2)
    with col1:
        r_var = rolling_var(ret, window=252, confidence=0.95)
        r_cvar = rolling_cvar(ret, window=252, confidence=0.95)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=r_var.index, y=r_var.values * 100,
            name="VaR (95%)", line=dict(color=COLORS["warning"]),
        ))
        fig.add_trace(go.Scatter(
            x=r_cvar.index, y=r_cvar.values * 100,
            name="CVaR (95%)", line=dict(color=COLORS["negative"]),
            fill="tonexty", fillcolor="rgba(239, 68, 68, 0.1)",
        ))
        fig.update_layout(**_base_layout("Rolling 252-Day VaR & CVaR", height=350))
        fig.update_yaxes(title="Daily Loss (%)", ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True, key="risk_rolling_var")

    with col2:
        fig = return_distribution_chart(ret)
        st.plotly_chart(fig, use_container_width=True, key="risk_return_dist")

    # Stress Tests
    st.markdown("---")
    st.markdown("### Historical Stress Tests")
    stress_results = run_stress_tests(ret)
    if not stress_results.empty:
        styled = stress_results.style.format({
            "cumulative_return": "{:.1%}",
            "max_drawdown": "{:.1%}",
            "worst_day": "{:.2%}",
            "best_day": "{:.2%}",
            "annualized_vol": "{:.1%}",
        }).background_gradient(
            subset=["cumulative_return"], cmap="RdYlGn", vmin=-0.3, vmax=0.1
        ).background_gradient(
            subset=["max_drawdown"], cmap="RdYlGn", vmin=-0.3, vmax=0
        )
        st.dataframe(styled, use_container_width=True)
    else:
        st.info("No stress test periods overlap with backtest data.")

    # Asset Correlation
    st.markdown("---")
    st.markdown("### Asset Correlations")
    col1, col2 = st.columns(2)
    with col1:
        if result.weights_history.shape[1] > 1:
            fig = correlation_heatmap(result.signals_history.dropna())
            st.plotly_chart(fig, use_container_width=True, key="risk_corr_full")
    with col2:
        if result.weights_history.shape[1] > 1:
            fig = correlation_heatmap(result.signals_history.dropna(), window=63)
            st.plotly_chart(fig, use_container_width=True, key="risk_corr_rolling")

    # Tail risk analysis
    st.markdown("---")
    st.markdown("### Tail Risk Analysis")
    col1, col2 = st.columns(2)
    with col1:
        # QQ plot
        from scipy import stats
        sorted_ret = np.sort(ret.dropna().values)
        theoretical = stats.norm.ppf(np.linspace(0.001, 0.999, len(sorted_ret)))
        fig = go.Figure()
        fig.add_trace(go.Scattergl(
            x=theoretical, y=sorted_ret * 100,
            mode="markers",
            marker=dict(size=2, color=COLORS["primary"], opacity=0.5),
            name="Returns",
        ))
        min_val = min(theoretical.min(), (sorted_ret * 100).min())
        max_val = max(theoretical.max(), (sorted_ret * 100).max())
        fig.add_trace(go.Scatter(
            x=[min_val, max_val], y=[min_val, max_val],
            mode="lines", line=dict(color=COLORS["negative"], dash="dash"),
            name="Normal",
        ))
        fig.update_layout(**_base_layout("Q-Q Plot vs Normal", height=400))
        fig.update_xaxes(title="Theoretical Quantiles")
        fig.update_yaxes(title="Sample Quantiles (%)")
        st.plotly_chart(fig, use_container_width=True, key="risk_qq_plot")

    with col2:
        from src.signals.volatility import ewma_volatility, simple_rolling_volatility
        ret_df = ret.to_frame("portfolio")
        ewma_vol = ewma_volatility(ret_df, halflife=20)
        roll_vol = simple_rolling_volatility(ret_df, window=21)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ewma_vol.index, y=ewma_vol.iloc[:, 0].values * 100,
            name="EWMA Vol (20d HL)",
            line=dict(color=COLORS["primary"]),
        ))
        fig.add_trace(go.Scatter(
            x=roll_vol.index, y=roll_vol.iloc[:, 0].values * 100,
            name="Rolling Vol (21d)",
            line=dict(color=COLORS["secondary"], dash="dash"),
        ))
        fig.update_layout(**_base_layout("Portfolio Volatility", height=400))
        fig.update_yaxes(title="Annualised Vol (%)", ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True, key="risk_vol_chart")
