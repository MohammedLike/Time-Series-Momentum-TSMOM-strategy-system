"""Reusable Plotly chart builders for the TSMOM dashboard.

All charts use a consistent dark theme for professional appearance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

COLORS = {
    "primary": "#6366f1",
    "secondary": "#22d3ee",
    "positive": "#10b981",
    "negative": "#ef4444",
    "warning": "#f59e0b",
    "neutral": "#94a3b8",
    "bg": "#0f172a",
    "card": "#1e293b",
    "text": "#e2e8f0",
}

TEMPLATE = "plotly_dark"


def _base_layout(title: str = "", height: int = 400) -> dict:
    return dict(
        template=TEMPLATE,
        title=dict(text=title, font=dict(size=16, color=COLORS["text"])),
        height=height,
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], size=12),
        margin=dict(l=50, r=30, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )


def equity_curve_chart(
    returns: pd.Series,
    benchmark: pd.Series | None = None,
    title: str = "Equity Curve (Growth of $1)",
) -> go.Figure:
    fig = go.Figure()
    cum = (1 + returns).cumprod()
    fig.add_trace(go.Scatter(
        x=cum.index, y=cum.values,
        name="TSMOM Strategy",
        line=dict(color=COLORS["primary"], width=2),
        fill="tozeroy",
        fillcolor="rgba(99, 102, 241, 0.1)",
    ))
    if benchmark is not None:
        bench_cum = (1 + benchmark).cumprod()
        fig.add_trace(go.Scatter(
            x=bench_cum.index, y=bench_cum.values,
            name="Benchmark",
            line=dict(color=COLORS["neutral"], width=1.5, dash="dash"),
        ))
    fig.update_layout(**_base_layout(title, height=450))
    fig.update_yaxes(title="Portfolio Value ($)")
    return fig


def drawdown_chart(returns: pd.Series, threshold: float = -0.10) -> go.Figure:
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    dd = cum / running_max - 1

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd.index, y=dd.values * 100,
        name="Drawdown",
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.3)",
        line=dict(color=COLORS["negative"], width=1),
    ))
    fig.add_hline(
        y=threshold * 100, line_dash="dash",
        line_color=COLORS["warning"],
        annotation_text=f"DD Control Threshold ({threshold:.0%})",
    )
    fig.update_layout(**_base_layout("Underwater Chart (Drawdown)", height=350))
    fig.update_yaxes(title="Drawdown (%)", ticksuffix="%")
    return fig


def rolling_sharpe_chart(returns: pd.Series, window: int = 252) -> go.Figure:
    roll_mean = returns.rolling(window).mean()
    roll_std = returns.rolling(window).std()
    rolling_sr = (roll_mean / roll_std) * np.sqrt(252)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rolling_sr.index, y=rolling_sr.values,
        name=f"Rolling {window}d Sharpe",
        line=dict(color=COLORS["secondary"], width=1.5),
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["neutral"])
    fig.add_hline(y=1, line_dash="dot", line_color=COLORS["positive"], annotation_text="SR = 1.0")
    fig.update_layout(**_base_layout(f"Rolling {window}-Day Sharpe Ratio", height=350))
    return fig


def monthly_heatmap(returns: pd.Series) -> go.Figure:
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    df = pd.DataFrame({
        "year": monthly.index.year,
        "month": monthly.index.month,
        "return": monthly.values * 100,
    })
    pivot = df.pivot(index="year", columns="month", values="return")
    pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0, COLORS["negative"]],
            [0.5, COLORS["bg"]],
            [1, COLORS["positive"]],
        ],
        text=np.where(np.isnan(pivot.values), "", np.round(pivot.values, 1).astype(str)),
        texttemplate="%{text}%",
        textfont=dict(size=10),
        hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="Return (%)"),
        zmid=0,
    ))
    fig.update_layout(**_base_layout("Monthly Returns Heatmap (%)", height=500))
    return fig


def weights_area_chart(weights: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in weights.columns:
        fig.add_trace(go.Scatter(
            x=weights.index, y=weights[col].values,
            name=col,
            mode="lines",
            stackgroup="weights",
        ))
    fig.update_layout(**_base_layout("Portfolio Weights Over Time", height=450))
    fig.update_yaxes(title="Weight")
    return fig


def signal_heatmap(signals: pd.DataFrame) -> go.Figure:
    # Resample to weekly for readability
    weekly_signals = signals.resample("W").last()
    fig = go.Figure(data=go.Heatmap(
        z=weekly_signals.T.values,
        x=weekly_signals.index,
        y=weekly_signals.columns.tolist(),
        colorscale=[
            [0, COLORS["negative"]],
            [0.5, "#1e293b"],
            [1, COLORS["positive"]],
        ],
        zmid=0,
        colorbar=dict(title="Signal"),
    ))
    fig.update_layout(**_base_layout("Signal Heatmap (Weekly)", height=500))
    return fig


def exposure_chart(weights: pd.DataFrame) -> go.Figure:
    gross = weights.abs().sum(axis=1)
    net = weights.sum(axis=1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=gross.index, y=gross.values,
        name="Gross Exposure",
        line=dict(color=COLORS["warning"], width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=net.index, y=net.values,
        name="Net Exposure",
        line=dict(color=COLORS["primary"], width=1.5),
    ))
    fig.update_layout(**_base_layout("Portfolio Exposure", height=350))
    fig.update_yaxes(title="Exposure (x)")
    return fig


def return_distribution_chart(returns: pd.Series) -> go.Figure:
    var_95 = np.percentile(returns.dropna(), 5)
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=returns.values * 100,
        nbinsx=100,
        marker_color=COLORS["primary"],
        opacity=0.7,
        name="Daily Returns",
    ))
    fig.add_vline(x=var_95 * 100, line_dash="dash", line_color=COLORS["negative"],
                  annotation_text=f"VaR 95% ({var_95:.2%})")
    fig.update_layout(**_base_layout("Return Distribution", height=350))
    fig.update_xaxes(title="Daily Return (%)")
    fig.update_yaxes(title="Frequency")
    return fig


def correlation_heatmap(returns: pd.DataFrame, window: int | None = None) -> go.Figure:
    if window:
        corr = returns.tail(window).corr()
        title = f"Asset Correlation (Last {window} Days)"
    else:
        corr = returns.corr()
        title = "Asset Correlation (Full Period)"

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=9),
        colorbar=dict(title="Corr"),
    ))
    fig.update_layout(**_base_layout(title, height=500))
    return fig


def turnover_chart(weights: pd.DataFrame) -> go.Figure:
    daily_turnover = weights.diff().abs().sum(axis=1)
    monthly_turnover = daily_turnover.resample("ME").sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_turnover.index,
        y=monthly_turnover.values,
        marker_color=COLORS["secondary"],
        opacity=0.7,
        name="Monthly Turnover",
    ))
    fig.update_layout(**_base_layout("Monthly Portfolio Turnover", height=350))
    fig.update_yaxes(title="Total |ΔWeight|")
    return fig
