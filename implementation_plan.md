# TSMOM Full-Stack Platform — Implementation Plan

## Goal

Transform the existing Streamlit-based TSMOM dashboard into an **institutional-quality web platform** using FastAPI (backend) + Next.js (frontend). The result should feel like a Bloomberg/AQR internal tool — minimal, data-dense, and visually refined.

---

## User Review Required

> [!IMPORTANT]
> ### Design Direction: Light Minimal (Zara) vs Dark Terminal (Bloomberg)?
> Your spec mentions both "white background, black typography" (Zara) AND Bloomberg Terminal. These are opposite aesthetics. **My plan**: Default to the **clean white/light** design with a **dark mode toggle** so both are available. The light mode will be Zara-minimal, the dark mode will be terminal-grade. Agree?

> [!IMPORTANT]  
> ### Chart Library: Lightweight Recharts vs Full-Featured Plotly?
> - **Recharts**: Native React, fast renders, great for time series & bar charts, but weak on heatmaps/QQ plots  
> - **Plotly (react-plotly.js)**: Heavy bundle (~1MB), but supports every chart type (heatmaps, QQ, subplots)
> 
> **My recommendation**: Use **Lightweight Charts** (TradingView) for the equity/price curves (professional financial look), **Recharts** for most analytics charts, and a **custom canvas heatmap** for the monthly returns. This avoids Plotly's bundle weight while covering all chart types. Agree?

> [!WARNING]
> ### Python Version
> Your system has Python 3.10.11. The existing `pyproject.toml` requires `>=3.11` (for `list[int]` syntax in type hints). The existing code uses `list[int]` and `X | Y` union syntax. I'll add `from __future__ import annotations` where needed and adjust the requirement to `>=3.10`. This won't affect functionality.

---

## Architecture Overview

```
d:\claude projects\time series momentum\
├── backend/                    # NEW — FastAPI server
│   ├── main.py                 # App entry, CORS, lifespan
│   ├── api/
│   │   ├── routes/
│   │   │   ├── backtest.py     # POST /run-backtest
│   │   │   ├── signals.py      # GET /signals
│   │   │   ├── portfolio.py    # GET /portfolio
│   │   │   ├── risk.py         # GET /risk
│   │   │   ├── assets.py       # GET /asset/{ticker}
│   │   │   └── health.py       # GET /health
│   │   └── schemas.py          # Pydantic request/response models
│   ├── core/
│   │   ├── engine.py           # Backtest orchestrator (wraps existing src/)
│   │   └── state.py            # In-memory result cache (last backtest)
│   └── requirements.txt
│
├── frontend/                   # NEW — Next.js app
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx      # Root layout, fonts, theme provider
│   │   │   ├── page.tsx        # Overview dashboard
│   │   │   ├── signals/page.tsx
│   │   │   ├── portfolio/page.tsx
│   │   │   ├── risk/page.tsx
│   │   │   └── assets/page.tsx
│   │   ├── components/
│   │   │   ├── ui/             # ShadCN components
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   ├── header.tsx
│   │   │   │   └── theme-provider.tsx
│   │   │   ├── charts/
│   │   │   │   ├── equity-curve.tsx
│   │   │   │   ├── drawdown-chart.tsx
│   │   │   │   ├── rolling-sharpe.tsx
│   │   │   │   ├── monthly-heatmap.tsx
│   │   │   │   ├── signal-heatmap.tsx
│   │   │   │   ├── weights-area.tsx
│   │   │   │   ├── exposure-chart.tsx
│   │   │   │   ├── var-chart.tsx
│   │   │   │   ├── qq-plot.tsx
│   │   │   │   ├── stress-table.tsx
│   │   │   │   └── asset-detail-panels.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── kpi-card.tsx
│   │   │   │   ├── insights-panel.tsx
│   │   │   │   └── control-panel.tsx
│   │   │   └── shared/
│   │   │       ├── loading-skeleton.tsx
│   │   │       └── error-boundary.tsx
│   │   ├── lib/
│   │   │   ├── api.ts           # API client (fetch wrapper)
│   │   │   ├── types.ts         # TypeScript interfaces
│   │   │   ├── utils.ts         # Formatting helpers
│   │   │   └── constants.ts     # Colors, config
│   │   └── hooks/
│   │       ├── use-backtest.ts   # Data fetching hook
│   │       └── use-theme.ts
│   ├── tailwind.config.ts
│   ├── package.json
│   └── next.config.ts
│
├── src/                        # EXISTING — quant logic (untouched)
├── config/                     # EXISTING — settings & universes
└── README.md                   # UPDATED — full setup guide
```

---

## Proposed Changes

### Backend — FastAPI Server

#### [NEW] [main.py](file:///d:/claude%20projects/time%20series%20momentum/backend/main.py)
- FastAPI app with CORS middleware (allow `localhost:3000` + production origins)
- Lifespan handler for startup/shutdown
- Mount all route modules

#### [NEW] [api/schemas.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/schemas.py)
- `BacktestRequest`: asset_universes, vol_target, lookbacks, rebalance_freq, drawdown_threshold, costs, regime_enabled, preset
- `BacktestResponse`: equity_curve, returns, drawdowns, weights, signals, costs, metrics, insights
- `SignalResponse`, `PortfolioResponse`, `RiskResponse`, `AssetDetailResponse`
- All using Pydantic v2 with proper serialization for DataFrames → JSON

#### [NEW] [api/routes/backtest.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/routes/backtest.py)
- `POST /run-backtest`: Accepts `BacktestRequest`, runs engine, caches result, returns `BacktestResponse`
- Wraps existing `BacktestEngine.run()` with proper error handling
- Converts pandas objects to JSON-serializable dicts

#### [NEW] [api/routes/signals.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/routes/signals.py)
- `GET /signals`: Returns signal matrix, autocorrelation data, predictive stats from cached result

#### [NEW] [api/routes/portfolio.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/routes/portfolio.py)
- `GET /portfolio`: Returns weights, exposure, turnover, cost drag, allocation breakdown

#### [NEW] [api/routes/risk.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/routes/risk.py)
- `GET /risk`: Returns drawdown, rolling VaR/CVaR, stress tests, QQ data, vol data

#### [NEW] [api/routes/assets.py](file:///d:/claude%20projects/time%20series%20momentum/backend/api/routes/assets.py)
- `GET /asset/{ticker}`: Returns price, signal, weight, PnL contribution, trade history for one asset

#### [NEW] [core/engine.py](file:///d:/claude%20projects/time%20series%20momentum/backend/core/engine.py)
- Thin wrapper that imports from `src/` and `config/`, runs backtest, computes all derived data
- Generates auto-insights (e.g., "Strategy underperforms in mean-reverting regimes")

#### [NEW] [core/state.py](file:///d:/claude%20projects/time%20series%20momentum/backend/core/state.py)
- In-memory singleton storing last `BacktestResult` + derived data
- Avoids re-running the engine for every GET endpoint

---

### Frontend — Next.js Application

#### Foundation Layer

#### [NEW] Next.js project scaffolding
- `create-next-app` with TypeScript, Tailwind CSS, App Router, ESLint
- ShadCN UI initialization
- Dependencies: `framer-motion`, `recharts`, `lightweight-charts`, `lucide-react`, `next-themes`

#### [NEW] [layout.tsx](file:///d:/claude%20projects/time%20series%20momentum/frontend/src/app/layout.tsx)
- Root layout with Inter font, ThemeProvider (light/dark), sidebar navigation
- Persistent sidebar with nav links: Overview, Signals, Portfolio, Risk, Assets
- Dark mode toggle in header

#### [NEW] Design System
- Tailwind config with custom palette: slate-950 (dark bg), white (light bg), indigo-500 (accent)
- ShadCN components: Card, Button, Select, Slider, Tabs, Badge, Skeleton, Sheet
- Consistent spacing system, typography scale

---

#### Pages

#### [NEW] Overview Page (/)
- **Control Panel** (top): Strategy preset select, vol target slider, rebalance frequency, run backtest button
- **KPI Cards Row**: CAGR, Sharpe, Sortino, Max DD, Calmar — animated count-up on load
- **Equity Curve**: TradingView Lightweight Charts — strategy vs benchmark
- **2-column**: Rolling Sharpe (Recharts area) + Drawdown (Recharts area, red fill)
- **Monthly Heatmap**: Custom canvas component — green/red cells with values
- **Insights Panel**: Auto-generated text based on metrics

#### [NEW] Signals Page (/signals)
- **Signal Heatmap**: Canvas-based heatmap of signals across assets × time
- **Signal Distribution**: Recharts histogram
- **Autocorrelation Chart**: Recharts bar chart (30 lags)
- **Predictive Power**: Recharts scatter plot (signal vs 5d forward return)

#### [NEW] Portfolio Page (/portfolio)
- **Exposure KPIs**: Gross, Net, # Long, # Short
- **Weights Area Chart**: Recharts stacked area
- **Exposure Chart**: Recharts dual-line (gross + net)
- **Turnover Bar Chart**: Monthly turnover bars
- **Allocation Donut**: Recharts pie chart (long/short split)
- **Cost Drag**: Recharts cumulative area
- **Trade Blotter**: ShadCN Table with sorting

#### [NEW] Risk Page (/risk)
- **Risk KPIs**: Vol, Max DD, VaR, CVaR, DD Duration
- **Drawdown Chart**: Red-filled area chart
- **Rolling VaR/CVaR**: Dual-line area chart
- **Return Distribution**: Histogram with VaR line
- **Stress Test Table**: ShadCN Table with color-coded returns
- **QQ Plot**: Recharts scatter with normal reference line
- **Volatility Chart**: EWMA vs Rolling vol comparison

#### [NEW] Asset Detail Page (/assets)
- **Asset Selector**: ShadCN Select dropdown
- **4-panel Chart**: Price, Signal (bar), Weight (area), Cumulative PnL — stacked vertically
- **Asset Metrics**: Mini KPI cards
- **Trade History**: Filtered blotter table

---

#### Shared Components

#### [NEW] Control Panel
- Strategy presets: Conservative / Balanced / Aggressive / Custom
- Universe selection: multi-select with asset class groups
- Parameter sliders: vol target, DD threshold, max exposure
- Rebalance frequency dropdown
- Transaction cost inputs
- **Run Backtest** button with loading state
- **Download CSV** button

#### [NEW] KPI Card
- Framer Motion entrance animation (fade + slide up)
- Value with formatting (percentage / ratio / days)
- Subtle border, icon

#### [NEW] Insights Panel
- Auto-generated bullet points based on metrics
- Rules engine: if Sharpe > 1 → "Strong risk-adjusted returns", if max_dd > 20% → "Significant drawdown risk", etc.

#### [NEW] Loading Skeleton
- Skeleton cards, skeleton charts matching layout shape
- Appears during backtest run

#### [NEW] Theme Provider
- `next-themes` for light/dark toggle
- Chart colors adapt to theme

---

## Open Questions

> [!IMPORTANT]
> ### Data Freshness
> Should the backend auto-download fresh data on each backtest run, or should it use cached Parquet data if available (with a "Refresh Data" button)? **My recommendation**: Use cache by default with a "Refresh Data" toggle — backtests are faster and don't hit API rate limits.

---

## Verification Plan

### Automated Tests
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Hit `GET /health` — expect `{"status": "ok"}`
3. `POST /run-backtest` with default params — expect valid JSON with metrics
4. Start frontend: `cd frontend && npm run dev`
5. Open browser, verify all 5 pages render with charts

### Manual Verification
1. Run a backtest from the UI with "Balanced" preset
2. Verify KPI cards show realistic values (Sharpe ~0.5-1.5, CAGR ~5-15%)
3. Toggle dark mode — all charts and text should adapt
4. Click through all 5 pages — no crashes, all charts populated
5. Download CSV — verify file contains returns data
6. Select an individual asset — verify detail panel loads
