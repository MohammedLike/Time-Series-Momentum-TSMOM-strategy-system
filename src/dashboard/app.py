"""TSMOM Dashboard — Streamlit entry point.

Launch with: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np

from config.settings import AppSettings
from src.data.provider import DataManager
from src.data.universe import load_universes, get_all_tickers, load_strategy_presets
from src.data.cleaning import align_and_clean
from src.backtest.engine import BacktestEngine
from src.utils.types import BacktestResult


st.set_page_config(
    page_title="TSMOM | Time-Series Momentum",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for dark, professional look ────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #0f172a;
        font-family: 'Inter', sans-serif;
    }
    .stSidebar {
        background-color: #1e293b;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stMetric label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    h1, h2, h3 {
        color: #e2e8f0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }
    div[data-testid="stExpander"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar Configuration ────────────────────────────────────────────
def sidebar_config() -> tuple[AppSettings, list[str], str]:
    with st.sidebar:
        st.markdown("# ⚙️ Configuration")
        st.markdown("---")

        # Universe selection
        universes = load_universes()
        universe_names = list(universes.keys())
        selected_universes = st.multiselect(
            "Asset Universes",
            universe_names,
            default=universe_names[:2],
        )

        tickers = []
        for u in selected_universes:
            tickers.extend([a.ticker for a in universes[u]])

        # Strategy preset
        presets = load_strategy_presets()
        preset_name = st.selectbox(
            "Strategy Preset",
            ["Custom"] + list(presets.keys()),
            index=2,  # balanced
        )

        st.markdown("---")
        st.markdown("### Strategy Parameters")

        settings = AppSettings()
        if preset_name != "Custom" and preset_name in presets:
            p = presets[preset_name]
            settings.vol_target = p.get("vol_target", settings.vol_target)
            settings.momentum_lookbacks = p.get("lookbacks", settings.momentum_lookbacks)
            settings.rebalance_frequency = p.get("rebalance_frequency", settings.rebalance_frequency)
            settings.drawdown_threshold = p.get("drawdown_threshold", settings.drawdown_threshold)

        settings.vol_target = st.slider(
            "Volatility Target",
            0.03, 0.25, float(settings.vol_target), 0.01,
            format="%.0f%%",
            help="Annualised portfolio volatility target",
        )
        settings.rebalance_frequency = st.selectbox(
            "Rebalance Frequency",
            ["daily", "weekly", "monthly"],
            index=["daily", "weekly", "monthly"].index(settings.rebalance_frequency),
        )
        settings.drawdown_threshold = st.slider(
            "Drawdown Control Threshold",
            0.05, 0.25, float(settings.drawdown_threshold), 0.01,
            format="%.0f%%",
            help="Start reducing exposure when drawdown exceeds this",
        )
        settings.max_gross_exposure = st.slider(
            "Max Gross Exposure",
            0.5, 3.0, float(settings.max_gross_exposure), 0.1,
            format="%.1fx",
        )

        st.markdown("---")
        st.markdown("### Data Range")
        start_date = st.text_input("Start Date", settings.default_start_date)
        settings.default_start_date = start_date

        st.markdown("---")
        st.markdown("### Transaction Costs")
        settings.default_slippage_bps = st.number_input(
            "Slippage (bps)", 0.0, 50.0, float(settings.default_slippage_bps), 1.0
        )
        settings.commission_bps = st.number_input(
            "Commission (bps)", 0.0, 20.0, float(settings.commission_bps), 0.5
        )

    return settings, tickers, start_date


# ── Data Loading & Backtest ──────────────────────────────────────────
@st.cache_resource(ttl=3600, show_spinner="Downloading market data...")
def load_data(tickers: tuple[str, ...], start: str) -> pd.DataFrame:
    dm = DataManager()
    prices = dm.get_close_prices(list(tickers), start)
    return align_and_clean(prices)


@st.cache_resource(
    ttl=3600,
    show_spinner="Running backtest engine...",
    hash_funcs={AppSettings: lambda s: hash(str(s.model_dump()))},
)
def run_backtest(
    _prices: pd.DataFrame, settings: AppSettings
) -> BacktestResult:
    engine = BacktestEngine(settings)
    return engine.run(_prices)


# ── Main App ─────────────────────────────────────────────────────────
def main():
    settings, tickers, start_date = sidebar_config()

    st.markdown("# 📊 Time-Series Momentum Strategy")
    st.markdown(
        "*Production-grade multi-asset TSMOM with regime detection, "
        "volatility targeting, and drawdown control*"
    )

    if not tickers:
        st.warning("Select at least one asset universe from the sidebar.")
        return

    try:
        prices = load_data(tuple(sorted(tickers)), start_date)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    if prices.empty or prices.shape[1] < 2:
        st.error("Not enough data. Try different tickers or date range.")
        return

    result = run_backtest(prices, settings)

    # ── Tabs ─────────────────────────────────────────────────────────
    from src.dashboard.views.overview import render_overview
    from src.dashboard.views.signals import render_signals
    from src.dashboard.views.portfolio import render_portfolio
    from src.dashboard.views.risk import render_risk
    from src.dashboard.views.asset_detail import render_asset_detail

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "🎯 Signals",
        "💼 Portfolio",
        "🛡️ Risk",
        "🔍 Asset Detail",
    ])

    with tab1:
        render_overview(result, prices)
    with tab2:
        render_signals(result, prices)
    with tab3:
        render_portfolio(result)
    with tab4:
        render_risk(result)
    with tab5:
        render_asset_detail(result, prices)


if __name__ == "__main__":
    main()
