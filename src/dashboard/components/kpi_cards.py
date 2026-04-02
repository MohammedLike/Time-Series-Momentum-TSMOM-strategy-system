"""KPI card rendering for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


def render_kpi_row(metrics: dict[str, float]) -> None:
    """Render a row of KPI metric cards."""
    cols = st.columns(5)

    kpis = [
        ("CAGR", metrics.get("cagr", 0), "{:.1%}", None),
        ("Sharpe Ratio", metrics.get("sharpe_ratio", 0), "{:.2f}", None),
        ("Sortino Ratio", metrics.get("sortino_ratio", 0), "{:.2f}", None),
        ("Max Drawdown", metrics.get("max_drawdown", 0), "{:.1%}", None),
        ("Calmar Ratio", metrics.get("calmar_ratio", 0), "{:.2f}", None),
    ]

    for col, (label, value, fmt, delta) in zip(cols, kpis):
        with col:
            st.metric(
                label=label,
                value=fmt.format(value),
                delta=delta,
            )


def render_extended_metrics(metrics: dict[str, float]) -> None:
    """Render extended metrics in two columns."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Returns**")
        st.write(f"Total Return: **{metrics.get('total_return', 0):.1%}**")
        st.write(f"CAGR: **{metrics.get('cagr', 0):.1%}**")
        st.write(f"Best Day: **{metrics.get('best_day', 0):.2%}**")
        st.write(f"Worst Day: **{metrics.get('worst_day', 0):.2%}**")
        st.write(f"Best Month: **{metrics.get('best_month', 0):.1%}**")
        st.write(f"Worst Month: **{metrics.get('worst_month', 0):.1%}**")

    with col2:
        st.markdown("**Risk**")
        st.write(f"Annual Vol: **{metrics.get('annualized_vol', 0):.1%}**")
        st.write(f"Max DD: **{metrics.get('max_drawdown', 0):.1%}**")
        st.write(f"DD Duration: **{metrics.get('max_drawdown_duration_days', 0):.0f} days**")
        st.write(f"VaR (95%): **{metrics.get('var_95', 0):.2%}**")
        st.write(f"CVaR (95%): **{metrics.get('cvar_95', 0):.2%}**")

    with col3:
        st.markdown("**Quality**")
        st.write(f"Sharpe: **{metrics.get('sharpe_ratio', 0):.2f}**")
        st.write(f"Sortino: **{metrics.get('sortino_ratio', 0):.2f}**")
        st.write(f"Calmar: **{metrics.get('calmar_ratio', 0):.2f}**")
        st.write(f"Hit Rate: **{metrics.get('hit_rate_daily', 0):.1%}**")
        st.write(f"Skewness: **{metrics.get('skewness', 0):.2f}**")
        st.write(f"Kurtosis: **{metrics.get('kurtosis', 0):.2f}**")
