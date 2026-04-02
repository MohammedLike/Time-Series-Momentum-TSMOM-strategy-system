# TSMOM — Production-Grade Time-Series Momentum System

A comprehensive, multi-asset time-series momentum strategy with regime-aware signal generation, volatility targeting, drawdown control, and an interactive analytics dashboard.

## What This Solves

Real-world portfolio management challenges that basic momentum strategies ignore:

- **Momentum Crashes**: Drawdown-control overlay automatically reduces exposure during sharp reversals
- **Regime Blindness**: HMM-based regime detection dampens signals in mean-reverting markets
- **Naive Position Sizing**: Volatility-targeting ensures equal risk contribution across assets
- **Transaction Cost Ignorance**: Full cost modeling with slippage and commission
- **Overfitting**: Walk-forward validation for honest out-of-sample performance
- **Single-Asset Tunnel Vision**: Tracks 30+ instruments across equities, commodities, bonds, and FX

## Architecture

```
config/             → Centralized settings (Pydantic), asset universes (YAML)
src/
├── data/           → Data providers (yfinance), caching (Parquet), cleaning
├── signals/        → Momentum signals, volatility estimators, regime detection
├── portfolio/      → Position sizing, constraints, rebalancing
├── risk/           → Metrics, drawdown control, VaR/CVaR, stress testing
├── costs/          → Transaction cost modeling
├── backtest/       → Vectorised backtest engine, walk-forward validation
└── dashboard/      → Streamlit app with 5 interactive pages
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Run Backtest (CLI)

```bash
python run.py
```

### 3. Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

## Dashboard Pages

| Page | What You See |
|------|-------------|
| **Overview** | KPI cards, equity curve vs benchmark, rolling Sharpe, monthly heatmap, drawdown |
| **Signals** | Signal heatmap across assets, per-asset signals, autocorrelation, predictive power |
| **Portfolio** | Weight allocation over time, exposure, turnover, long/short breakdown, cost drag |
| **Risk** | Drawdown chart, rolling VaR/CVaR, stress tests (GFC, COVID, etc.), Q-Q plot, vol |
| **Asset Detail** | Drill into any asset: price, signal, weight, PnL contribution, trade history |

## Key Features

### Signal Generation
- Multi-horizon momentum (1m, 3m, 6m, 12m) with equal-weight or custom blending
- MACD-based alternative signals
- Regime-aware scaling via Hidden Markov Model
- Signal smoothing, z-score normalization, and capping

### Volatility Estimators
- EWMA (fast-reacting)
- Yang-Zhang (OHLC-efficient)
- Garman-Klass (OHLC-robust)
- Simple rolling

### Portfolio Construction
- Volatility-targeting (Moskowitz/Ooi/Pedersen approach)
- Per-position and gross exposure constraints
- Configurable rebalance frequency (daily/weekly/monthly)
- Turnover-aware rebalancing

### Risk Management
- Drawdown control overlay with configurable threshold and floor
- Full metrics suite: Sharpe, Sortino, Calmar, VaR, CVaR, skewness, kurtosis
- Historical stress testing (GFC, COVID, Taper Tantrum, etc.)
- Walk-forward out-of-sample validation

### Configuration
All parameters configurable via:
- `config/settings.py` (code defaults)
- `.env` file (environment overrides)
- Dashboard sidebar (interactive)
- Strategy presets: Conservative, Balanced, Aggressive

## Asset Universe

| Class | Instruments | Examples |
|-------|------------|---------|
| Equities | 12 ETFs | SPY, QQQ, XLF, XLE, XLV |
| Commodities | 5 ETFs | GLD, SLV, USO, UNG, DBA |
| Fixed Income | 5 ETFs | TLT, IEF, SHY, LQD, HYG |
| FX | 5 ETFs | UUP, FXE, FXY, FXB, FXA |

## Technology

- **Python 3.11+** with type hints
- **pandas / numpy / scipy** for computation
- **yfinance** for market data
- **hmmlearn** for regime detection (HMM)
- **Streamlit** for interactive dashboard
- **Plotly** for professional charts
- **Pydantic** for validated configuration
- **Parquet** for efficient data caching
