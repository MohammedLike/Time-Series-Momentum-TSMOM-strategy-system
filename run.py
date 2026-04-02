"""Quick-start script: run backtest from command line and print results.

Usage: python run.py
Dashboard: streamlit run src/dashboard/app.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.settings import AppSettings
from src.data.provider import DataManager
from src.data.universe import load_universes, get_all_tickers
from src.data.cleaning import align_and_clean, compute_returns
from src.backtest.engine import BacktestEngine


def main():
    print("=" * 70)
    print("  TSMOM — Time-Series Momentum Backtest Engine")
    print("=" * 70)

    settings = AppSettings()
    universes = load_universes()
    tickers = get_all_tickers(universes)

    print(f"\n  Universe: {len(tickers)} assets across {len(universes)} classes")
    print(f"  Start date: {settings.default_start_date}")
    print(f"  Vol target: {settings.vol_target:.0%}")
    print(f"  Rebalance: {settings.rebalance_frequency}")
    print(f"  DD threshold: {settings.drawdown_threshold:.0%}")
    print(f"  Costs: {settings.default_slippage_bps + settings.commission_bps:.0f} bps round-trip")

    print("\n  Downloading data...")
    dm = DataManager(settings.data_cache_dir)
    prices = dm.get_close_prices(tickers, settings.default_start_date)
    prices = align_and_clean(prices)
    print(f"  Got {prices.shape[0]} days × {prices.shape[1]} assets")

    # Benchmark: equal-weight buy-and-hold
    returns = compute_returns(prices)
    benchmark = returns.mean(axis=1)

    print("\n  Running backtest...")
    engine = BacktestEngine(settings)
    result = engine.run(prices, benchmark_returns=benchmark)

    # Print results
    m = result.metrics
    print("\n" + "=" * 70)
    print("  BACKTEST RESULTS")
    print("=" * 70)
    print(f"""
  RETURNS
    Total Return:     {m.get('total_return', 0):>10.1%}
    CAGR:             {m.get('cagr', 0):>10.1%}
    Best Day:         {m.get('best_day', 0):>10.2%}
    Worst Day:        {m.get('worst_day', 0):>10.2%}
    Best Month:       {m.get('best_month', 0):>10.1%}
    Worst Month:      {m.get('worst_month', 0):>10.1%}

  RISK
    Annualised Vol:   {m.get('annualized_vol', 0):>10.1%}
    Max Drawdown:     {m.get('max_drawdown', 0):>10.1%}
    DD Duration:      {m.get('max_drawdown_duration_days', 0):>10.0f} days
    VaR (95%):        {m.get('var_95', 0):>10.2%}
    CVaR (95%):       {m.get('cvar_95', 0):>10.2%}

  RISK-ADJUSTED
    Sharpe Ratio:     {m.get('sharpe_ratio', 0):>10.2f}
    Sortino Ratio:    {m.get('sortino_ratio', 0):>10.2f}
    Calmar Ratio:     {m.get('calmar_ratio', 0):>10.2f}
    Hit Rate (Daily): {m.get('hit_rate_daily', 0):>10.1%}

  DISTRIBUTION
    Skewness:         {m.get('skewness', 0):>10.2f}
    Kurtosis:         {m.get('kurtosis', 0):>10.2f}
    Trading Days:     {m.get('n_trading_days', 0):>10.0f}
    Years:            {m.get('n_years', 0):>10.1f}
""")

    if "information_ratio" in m:
        print(f"  VS BENCHMARK")
        print(f"    Info Ratio:       {m.get('information_ratio', 0):>10.2f}")
        print(f"    Tracking Error:   {m.get('tracking_error', 0):>10.1%}")
        print(f"    Beta:             {m.get('beta', 0):>10.2f}")
        print(f"    Alpha (annual):   {m.get('alpha_annual', 0):>10.2%}")

    print("\n" + "=" * 70)
    print("  Launch dashboard:  streamlit run src/dashboard/app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
