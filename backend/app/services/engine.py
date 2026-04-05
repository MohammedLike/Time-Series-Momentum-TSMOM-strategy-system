"""Core service layer — wraps existing quant engine for API consumption.

Bridges the existing TSMOM system with the FastAPI layer by converting
pandas DataFrames/Series into JSON-serializable structures.
"""

from __future__ import annotations

import sys
import time
import hashlib
import json
import logging
from pathlib import Path
from functools import lru_cache
from threading import Lock

import numpy as np
import pandas as pd

# Add project root to path so we can import existing modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import AppSettings
from src.backtest.engine import BacktestEngine
from src.data.provider import DataManager
from src.data.cleaning import compute_returns, winsorize_returns, align_and_clean
from src.data.universe import load_universes, load_strategy_presets
from src.signals.composite import CompositeSignalGenerator
from src.signals.volatility import ewma_volatility
from src.signals.regime import HMMRegimeDetector
from src.risk.metrics import rolling_sharpe, monthly_returns_table
from src.risk.stress import run_stress_tests
from src.risk.drawdown import drawdown_series
from src.risk.var import rolling_var, rolling_cvar
from app.models.schemas import (
    BacktestRequest, BacktestResponse, MetricsResponse,
    TimeSeriesPoint, StressTestResult, RegimePoint, PositionInfo,
    SignalResponse, SignalHeatmapRow,
    RegimeResponse, RiskResponse, LiveUpdate,
    UniverseResponse, UniverseAsset,
)

logger = logging.getLogger(__name__)

# ── In-memory result cache ──────────────────────────────────────────
# Caches expensive computation results for 10 minutes.
_cache: dict[str, tuple[float, object]] = {}
_cache_lock = Lock()
CACHE_TTL = 600  # 10 minutes


def _cache_key(*args) -> str:
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_get(key: str):
    with _cache_lock:
        if key in _cache:
            ts, val = _cache[key]
            if time.time() - ts < CACHE_TTL:
                logger.info("Cache hit: %s", key[:12])
                return val
            del _cache[key]
    return None


def _cache_set(key: str, val):
    with _cache_lock:
        _cache[key] = (time.time(), val)
        # Evict old entries if cache grows too large
        if len(_cache) > 50:
            oldest = min(_cache, key=lambda k: _cache[k][0])
            del _cache[oldest]


# Downsample large time series to keep API responses fast
MAX_POINTS = 2000


def _downsample(series: pd.Series, max_points: int = MAX_POINTS) -> pd.Series:
    if len(series) <= max_points:
        return series
    step = max(1, len(series) // max_points)
    return series.iloc[::step]


def _series_to_points(series: pd.Series, max_points: int = MAX_POINTS) -> list[TimeSeriesPoint]:
    s = _downsample(series.dropna(), max_points)
    return [
        TimeSeriesPoint(date=d.strftime("%Y-%m-%d"), value=round(float(v), 6))
        for d, v in s.items()
    ]


def _build_settings(req: BacktestRequest) -> AppSettings:
    return AppSettings(
        vol_target=req.vol_target,
        momentum_lookbacks=req.momentum_lookbacks,
        rebalance_frequency=req.rebalance_frequency,
        drawdown_threshold=req.drawdown_threshold,
        drawdown_scaling_floor=req.drawdown_scaling_floor,
        max_position_weight=req.max_position_weight,
        max_gross_exposure=req.max_gross_exposure,
        default_slippage_bps=req.slippage_bps,
        commission_bps=req.commission_bps,
    )


CACHE_DIR = PROJECT_ROOT / "data" / "cache"


@lru_cache(maxsize=1)
def _get_data_manager() -> DataManager:
    return DataManager(cache_dir=CACHE_DIR)


def _get_prices(tickers: list[str], start_date: str, end_date: str | None = None) -> pd.DataFrame:
    """Load prices, using cached superset files when exact cache key is missing.

    The DataManager caches by exact sorted ticker list. If the user requests
    a subset of a previously-cached universe, we load the superset from cache
    and filter columns, avoiding a network call.
    """
    dm = _get_data_manager()
    try:
        return dm.get_close_prices(tickers, start_date, end_date)
    except Exception:
        # Exact cache miss and network failed — try to find a cached superset
        requested = set(tickers)
        for parquet_file in sorted(CACHE_DIR.glob("prices_*.parquet"), key=lambda p: -p.stat().st_size):
            try:
                df = pd.read_parquet(parquet_file)
                # Handle MultiIndex columns (yfinance format)
                if isinstance(df.columns, pd.MultiIndex):
                    if "Close" in df.columns.get_level_values(0):
                        close = df["Close"]
                    else:
                        close = df.xs("Close", axis=1, level=0)
                else:
                    close = df

                available = set(close.columns)
                if requested.issubset(available):
                    logger.info("Using cached superset from %s", parquet_file.name)
                    result = close[tickers].dropna(how="all")
                    if start_date:
                        result = result[result.index >= start_date]
                    if end_date:
                        result = result[result.index <= end_date]
                    return result
            except Exception:
                continue

        raise ValueError(
            f"No cached data found containing {tickers}. "
            "Network download also failed. Check your internet connection or cache."
        )


def run_backtest(req: BacktestRequest) -> BacktestResponse:
    """Execute a full backtest and return structured results."""
    key = _cache_key("backtest", req.model_dump())
    cached = _cache_get(key)
    if cached is not None:
        return cached

    settings = _build_settings(req)

    prices = _get_prices(req.tickers, req.start_date, req.end_date)
    prices = align_and_clean(prices)

    # Run engine
    engine = BacktestEngine(settings)

    # Get benchmark (SPY)
    benchmark_returns = None
    benchmark_equity = None
    if "SPY" in prices.columns:
        spy_prices = prices["SPY"]
        benchmark_returns = spy_prices.pct_change().dropna()
    else:
        try:
            spy = _get_prices(["SPY"], req.start_date, req.end_date)
            benchmark_returns = spy["SPY"].pct_change().dropna()
        except Exception:
            pass

    result = engine.run(prices, benchmark_returns)

    # Equity curve
    equity = (1 + result.portfolio_returns).cumprod()

    # Benchmark equity
    if benchmark_returns is not None:
        bench_eq = (1 + benchmark_returns).cumprod()
        benchmark_equity = _series_to_points(bench_eq)

    # Drawdown
    dd_data = drawdown_series(result.portfolio_returns)

    # Rolling metrics
    r_sharpe = rolling_sharpe(result.portfolio_returns, window=252)
    r_vol = result.portfolio_returns.rolling(63).std() * np.sqrt(252)

    # Weights per asset
    weights_dict = {}
    for col in result.weights_history.columns:
        weights_dict[col] = _series_to_points(result.weights_history[col])

    # Signals per asset
    signals_dict = {}
    for col in result.signals_history.columns:
        signals_dict[col] = _series_to_points(result.signals_history[col])

    # Monthly returns
    monthly_table = monthly_returns_table(result.portfolio_returns)
    monthly_dict = {}
    for year in monthly_table.index:
        monthly_dict[str(year)] = {
            str(m): round(float(v), 4) if pd.notna(v) else None
            for m, v in monthly_table.loc[year].items()
        }

    # Stress tests
    stress = run_stress_tests(result.portfolio_returns)
    stress_results = []
    for scenario, row in stress.iterrows():
        stress_results.append(StressTestResult(
            scenario=str(scenario),
            period=row.get("period", ""),
            cumulative_return=round(float(row.get("cumulative_return", 0)), 4),
            max_drawdown=round(float(row.get("max_drawdown", 0)), 4),
            worst_day=round(float(row.get("worst_day", 0)), 4),
            best_day=round(float(row.get("best_day", 0)), 4),
            annualized_vol=round(float(row.get("annualized_vol", 0)), 4),
            n_days=int(row.get("n_days", 0)),
        ))

    # Regime
    returns = compute_returns(prices)
    returns = winsorize_returns(returns)
    market_returns = returns.mean(axis=1)
    detector = HMMRegimeDetector(n_regimes=2)
    try:
        regime_score = detector.fit_predict(market_returns)
        regime_probs = detector.regime_probability(market_returns)
    except Exception:
        regime_score = pd.Series(0.5, index=market_returns.index)
        regime_probs = pd.DataFrame(
            {"regime_0": 0.5, "regime_1": 0.5}, index=market_returns.index
        )

    regime_points = []
    sampled_regime = _downsample(regime_score)
    for d in sampled_regime.index:
        probs = regime_probs.loc[d] if d in regime_probs.index else pd.Series({"regime_0": 0.5, "regime_1": 0.5})
        prob_vals = probs.values if hasattr(probs, 'values') else [0.5, 0.5]
        regime_points.append(RegimePoint(
            date=d.strftime("%Y-%m-%d"),
            regime_score=round(float(regime_score.get(d, 0.5)), 4),
            trending_prob=round(float(prob_vals[0]) if len(prob_vals) > 0 else 0.5, 4),
            mean_reverting_prob=round(float(prob_vals[1]) if len(prob_vals) > 1 else 0.5, 4),
        ))

    # Current positions
    last_weights = result.weights_history.iloc[-1]
    last_signals = result.signals_history.iloc[-1]
    positions = []
    for asset in last_weights.index:
        w = float(last_weights[asset])
        s = float(last_signals.get(asset, 0))
        if abs(w) > 1e-6:
            positions.append(PositionInfo(
                asset=asset,
                weight=round(w, 4),
                signal=round(s, 4),
                side="LONG" if w > 0 else "SHORT",
            ))

    # Cost drag
    cost_cum = result.costs_history.cumsum()

    # Turnover
    weight_changes = result.weights_history.diff().fillna(0)
    turnover = weight_changes.abs().sum(axis=1)

    # Exposure
    gross_exp = result.weights_history.abs().sum(axis=1)
    net_exp = result.weights_history.sum(axis=1)
    long_exp = result.weights_history.clip(lower=0).sum(axis=1)
    short_exp = result.weights_history.clip(upper=0).sum(axis=1).abs()

    # Metrics
    m = result.metrics
    metrics = MetricsResponse(**{k: m.get(k, 0) for k in MetricsResponse.model_fields if k in m})

    result_response = BacktestResponse(
        metrics=metrics,
        equity_curve=_series_to_points(equity),
        drawdown=_series_to_points(dd_data["drawdown"]),
        rolling_sharpe=_series_to_points(r_sharpe),
        rolling_volatility=_series_to_points(r_vol),
        weights=weights_dict,
        signals=signals_dict,
        monthly_returns=monthly_dict,
        stress_tests=stress_results,
        regime=regime_points,
        positions=positions,
        benchmark_equity=benchmark_equity,
        cost_drag=_series_to_points(cost_cum),
        turnover=_series_to_points(turnover),
        gross_exposure=_series_to_points(gross_exp),
        net_exposure=_series_to_points(net_exp),
        long_exposure=_series_to_points(long_exp),
        short_exposure=_series_to_points(short_exp),
    )
    _cache_set(key, result_response)
    return result_response


def get_signals(tickers: list[str], start_date: str, lookbacks: list[int] | None = None) -> SignalResponse:
    """Get current signal state for all assets."""
    key = _cache_key("signals", sorted(tickers), start_date, lookbacks)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    settings = AppSettings()
    if lookbacks:
        settings.momentum_lookbacks = lookbacks

    prices = _get_prices(tickers, start_date)
    prices = align_and_clean(prices)
    returns = compute_returns(prices)
    returns = winsorize_returns(returns)

    gen = CompositeSignalGenerator(settings)
    components = gen.generate_components(returns)
    final = components["final_signal"]

    # Heatmap (last 252 trading days, downsampled to weekly)
    heatmap_data = final.tail(252).resample("W").last().dropna(how="all")
    heatmap = []
    for d, row in heatmap_data.iterrows():
        heatmap.append(SignalHeatmapRow(
            date=d.strftime("%Y-%m-%d"),
            values={col: round(float(v), 4) for col, v in row.items() if pd.notna(v)},
        ))

    # Current signals
    current = final.iloc[-1]
    current_signals = {col: round(float(v), 4) for col, v in current.items() if pd.notna(v)}

    # Signal components
    signal_components = {}
    for comp_name, comp_data in components.items():
        if isinstance(comp_data, pd.DataFrame):
            # Average across assets for summary
            avg = comp_data.mean(axis=1)
            signal_components[comp_name] = _series_to_points(avg)
        elif isinstance(comp_data, pd.Series):
            signal_components[comp_name] = _series_to_points(comp_data)

    result = SignalResponse(
        heatmap=heatmap,
        assets=list(final.columns),
        current_signals=current_signals,
        signal_components=signal_components,
    )
    _cache_set(key, result)
    return result


def get_regime(tickers: list[str], start_date: str) -> RegimeResponse:
    """Get regime detection analysis."""
    key = _cache_key("regime", sorted(tickers), start_date)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    prices = _get_prices(tickers, start_date)
    prices = align_and_clean(prices)
    returns = compute_returns(prices)
    returns = winsorize_returns(returns)
    market_returns = returns.mean(axis=1)

    detector = HMMRegimeDetector(n_regimes=2)
    try:
        regime_score = detector.fit_predict(market_returns)
        regime_probs = detector.regime_probability(market_returns)
    except Exception:
        regime_score = pd.Series(0.5, index=market_returns.index)
        regime_probs = pd.DataFrame(
            {"regime_0": 0.5, "regime_1": 0.5}, index=market_returns.index
        )

    # Regime history
    regime_history = []
    sampled = _downsample(regime_score)
    for d in sampled.index:
        probs = regime_probs.loc[d] if d in regime_probs.index else pd.Series({"regime_0": 0.5, "regime_1": 0.5})
        prob_vals = probs.values if hasattr(probs, 'values') else [0.5, 0.5]
        regime_history.append(RegimePoint(
            date=d.strftime("%Y-%m-%d"),
            regime_score=round(float(regime_score.get(d, 0.5)), 4),
            trending_prob=round(float(prob_vals[0]) if len(prob_vals) > 0 else 0.5, 4),
            mean_reverting_prob=round(float(prob_vals[1]) if len(prob_vals) > 1 else 0.5, 4),
        ))

    # Current regime
    last_score = float(regime_score.iloc[-1])
    current_regime = "Trending" if last_score > 0.5 else "Mean-Reverting"

    # Regime statistics
    trending_mask = regime_score > 0.5
    mr_mask = regime_score <= 0.5

    trending_rets = market_returns[trending_mask]
    mr_rets = market_returns[mr_mask]

    regime_stats = {
        "trending": {
            "count_days": int(trending_mask.sum()),
            "pct_time": round(float(trending_mask.mean()), 4),
            "avg_return": round(float(trending_rets.mean() * 252), 4) if len(trending_rets) > 0 else 0,
            "volatility": round(float(trending_rets.std() * np.sqrt(252)), 4) if len(trending_rets) > 0 else 0,
        },
        "mean_reverting": {
            "count_days": int(mr_mask.sum()),
            "pct_time": round(float(mr_mask.mean()), 4),
            "avg_return": round(float(mr_rets.mean() * 252), 4) if len(mr_rets) > 0 else 0,
            "volatility": round(float(mr_rets.std() * np.sqrt(252)), 4) if len(mr_rets) > 0 else 0,
        },
    }

    result = RegimeResponse(
        regime_history=regime_history,
        current_regime=current_regime,
        current_probabilities={
            "trending": round(float(regime_probs.iloc[-1].iloc[0]), 4),
            "mean_reverting": round(float(regime_probs.iloc[-1].iloc[1]), 4),
        },
        regime_stats=regime_stats,
    )
    _cache_set(key, result)
    return result


def get_risk(tickers: list[str], start_date: str, vol_target: float = 0.10) -> RiskResponse:
    """Get risk analysis data."""
    key = _cache_key("risk", sorted(tickers), start_date, vol_target)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    settings = AppSettings(vol_target=vol_target)
    prices = _get_prices(tickers, start_date)
    prices = align_and_clean(prices)

    engine = BacktestEngine(settings)
    result = engine.run(prices)
    rets = result.portfolio_returns

    # Rolling risk
    r_var = rolling_var(rets, window=252, confidence=0.95)
    r_cvar = rolling_cvar(rets, window=252, confidence=0.95)
    r_vol = rets.rolling(63).std() * np.sqrt(252)

    # Drawdown
    dd_data = drawdown_series(rets)

    # Stress tests
    stress = run_stress_tests(rets)
    stress_results = []
    for scenario, row in stress.iterrows():
        stress_results.append(StressTestResult(
            scenario=str(scenario),
            period=row.get("period", ""),
            cumulative_return=round(float(row.get("cumulative_return", 0)), 4),
            max_drawdown=round(float(row.get("max_drawdown", 0)), 4),
            worst_day=round(float(row.get("worst_day", 0)), 4),
            best_day=round(float(row.get("best_day", 0)), 4),
            annualized_vol=round(float(row.get("annualized_vol", 0)), 4),
            n_days=int(row.get("n_days", 0)),
        ))

    # Risk contributions per asset
    weights_last = result.weights_history.iloc[-1]
    returns_data = compute_returns(prices)
    asset_vols = returns_data.std() * np.sqrt(252)
    risk_contrib = {}
    total_risk = 0
    for asset in weights_last.index:
        rc = abs(float(weights_last[asset])) * float(asset_vols.get(asset, 0))
        risk_contrib[asset] = round(rc, 4)
        total_risk += rc
    # Normalize
    if total_risk > 0:
        risk_contrib = {k: round(v / total_risk, 4) for k, v in risk_contrib.items()}

    risk_result = RiskResponse(
        var_95=round(float(result.metrics.get("var_95", 0)), 6),
        var_99=round(float(result.metrics.get("var_99", 0)), 6),
        cvar_95=round(float(result.metrics.get("cvar_95", 0)), 6),
        cvar_99=round(float(result.metrics.get("cvar_99", 0)), 6),
        rolling_var=_series_to_points(r_var),
        rolling_cvar=_series_to_points(r_cvar),
        rolling_vol=_series_to_points(r_vol),
        stress_tests=stress_results,
        risk_contributions=risk_contrib,
        drawdown_series=_series_to_points(dd_data["drawdown"]),
        drawdown_duration=_series_to_points(dd_data["drawdown_duration"]),
    )
    _cache_set(key, risk_result)
    return risk_result


def get_live_update(tickers: list[str]) -> LiveUpdate:
    """Simulate a live trading snapshot."""
    settings = AppSettings()

    prices = _get_prices(tickers, "2020-01-01")
    prices = align_and_clean(prices)
    returns = compute_returns(prices)
    returns = winsorize_returns(returns)

    gen = CompositeSignalGenerator(settings)
    signals = gen.generate(returns)
    vol = ewma_volatility(returns)

    # Latest signals with noise for simulation effect
    latest_signals = signals.iloc[-1]
    noise = pd.Series(
        np.random.normal(0, 0.05, len(latest_signals)),
        index=latest_signals.index,
    )
    simulated_signals = (latest_signals + noise).clip(-2, 2)

    # Position sizing
    n_assets = len(tickers)
    per_asset_budget = settings.vol_target / n_assets
    latest_vol = vol.iloc[-1]
    safe_vol = latest_vol.clip(lower=0.01)
    weights = simulated_signals * per_asset_budget / safe_vol
    weights = weights.clip(-settings.max_position_weight, settings.max_position_weight)

    positions = []
    for asset in weights.index:
        w = float(weights[asset])
        if abs(w) > 1e-4:
            positions.append(PositionInfo(
                asset=asset,
                weight=round(w, 4),
                signal=round(float(simulated_signals[asset]), 4),
                side="LONG" if w > 0 else "SHORT",
            ))

    # Regime
    market_returns = returns.mean(axis=1)
    detector = HMMRegimeDetector(n_regimes=2)
    try:
        regime_score = detector.fit_predict(market_returns)
        current_regime = "Trending" if float(regime_score.iloc[-1]) > 0.5 else "Mean-Reverting"
    except Exception:
        current_regime = "Unknown"

    return LiveUpdate(
        timestamp=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        positions=positions,
        portfolio_value=round(1_000_000 * (1 + float(returns.mean(axis=1).tail(252).sum())), 2),
        daily_pnl=round(float(returns.mean(axis=1).iloc[-1]) * 1_000_000, 2),
        regime=current_regime,
        signals={asset: round(float(v), 4) for asset, v in simulated_signals.items()},
    )


def get_universe() -> UniverseResponse:
    """Get available asset universes and strategy presets."""
    universes = load_universes()
    presets = load_strategy_presets()

    universe_dict = {}
    for name, assets in universes.items():
        universe_dict[name] = [
            UniverseAsset(
                ticker=a.ticker,
                name=a.name,
                sector=a.sector,
                asset_class=a.asset_class,
            )
            for a in assets
        ]

    return UniverseResponse(universes=universe_dict, presets=presets)


def _grade(val: float, thresholds: list[tuple[float, str]]) -> str:
    for t, label in thresholds:
        if val >= t:
            return label
    return thresholds[-1][1]


def _signal_verdict(signal: float) -> str:
    if signal > 0.5:
        return "Strong upward momentum — the trend is clearly in your favor."
    if signal > 0.1:
        return "Mild positive momentum — a gentle tailwind, not a strong trend."
    if signal > -0.1:
        return "Neutral — no clear direction right now. Best to stay patient."
    if signal > -0.5:
        return "Mild negative momentum — the wind is turning against this asset."
    return "Strong downward momentum — this asset is in a clear downtrend."


def generate_research_report(tickers: list[str], start_date: str = "2005-01-01") -> dict:
    """Generate a plain-English equity research report for non-technical investors."""
    key = _cache_key("research", sorted(tickers), start_date)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    settings = AppSettings()
    prices = _get_prices(tickers, start_date)
    prices = align_and_clean(prices)
    returns = compute_returns(prices)
    returns = winsorize_returns(returns)

    # Run backtest
    engine = BacktestEngine(settings)
    benchmark_returns = None
    if "SPY" in prices.columns:
        benchmark_returns = prices["SPY"].pct_change().dropna()
    result = engine.run(prices, benchmark_returns)
    m = result.metrics

    # Signals
    gen = CompositeSignalGenerator(settings)
    signals = gen.generate(returns)
    latest_signals = signals.iloc[-1]

    # Volatility
    vol = ewma_volatility(returns)
    latest_vol = vol.iloc[-1]

    # Regime
    market_returns = returns.mean(axis=1)
    detector = HMMRegimeDetector(n_regimes=2)
    try:
        regime_score = detector.fit_predict(market_returns)
        regime = "Trending" if float(regime_score.iloc[-1]) > 0.5 else "Mean-Reverting"
    except Exception:
        regime = "Unknown"

    # Per-asset analysis
    asset_reports = []
    for ticker in tickers:
        if ticker not in returns.columns:
            continue
        asset_ret = returns[ticker]
        total_ret = float((1 + asset_ret).prod() - 1)
        ann_ret = float((1 + total_ret) ** (252 / max(len(asset_ret), 1)) - 1)
        ann_vol = float(asset_ret.std() * np.sqrt(252))
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        max_dd = float((asset_ret.cumsum() - asset_ret.cumsum().cummax()).min())
        sig = float(latest_signals.get(ticker, 0))
        cur_vol = float(latest_vol.get(ticker, 0)) * np.sqrt(252)
        last_weight = float(result.weights_history[ticker].iloc[-1]) if ticker in result.weights_history.columns else 0

        # Recent performance (last 3 months)
        recent_ret = float(asset_ret.tail(63).sum()) if len(asset_ret) >= 63 else float(asset_ret.sum())

        # Risk level
        risk_level = _grade(cur_vol, [(0.30, "Very High"), (0.20, "High"), (0.12, "Moderate"), (0.05, "Low"), (0, "Very Low")])

        # Momentum verdict
        momentum = _signal_verdict(sig)

        # Overall recommendation
        if sig > 0.3 and sharpe > 0.3:
            recommendation = "Favorable"
            rec_color = "green"
            rec_detail = f"{ticker} shows positive momentum with decent risk-adjusted returns. The strategy is currently allocating {abs(last_weight)*100:.1f}% to this position."
        elif sig < -0.3:
            recommendation = "Unfavorable"
            rec_color = "red"
            rec_detail = f"{ticker} is in a downtrend. The model suggests reducing or avoiding exposure. Current signal: {sig:.2f}."
        else:
            recommendation = "Neutral"
            rec_color = "yellow"
            rec_detail = f"{ticker} is not showing a strong trend in either direction. Consider holding current positions but don't add more."

        asset_reports.append({
            "ticker": ticker,
            "total_return": round(total_ret, 4),
            "annualized_return": round(ann_ret, 4),
            "annualized_vol": round(ann_vol, 4),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_dd, 4),
            "current_signal": round(sig, 4),
            "current_vol": round(cur_vol, 4),
            "current_weight": round(last_weight, 4),
            "recent_3m_return": round(recent_ret, 4),
            "risk_level": risk_level,
            "momentum_verdict": momentum,
            "recommendation": recommendation,
            "recommendation_color": rec_color,
            "recommendation_detail": rec_detail,
        })

    # Sort by recommendation: Favorable first
    order = {"Favorable": 0, "Neutral": 1, "Unfavorable": 2}
    asset_reports.sort(key=lambda x: order.get(x["recommendation"], 1))

    # Portfolio summary in plain English
    cagr = m.get("cagr", 0)
    sharpe = m.get("sharpe_ratio", 0)
    max_dd = m.get("max_drawdown", 0)
    vol = m.get("annualized_vol", 0)

    portfolio_grade = _grade(sharpe, [(1.0, "Excellent"), (0.5, "Good"), (0.2, "Fair"), (0, "Poor"), (-999, "Very Poor")])
    risk_grade = _grade(-abs(max_dd), [(-0.05, "Conservative"), (-0.10, "Moderate"), (-0.20, "Aggressive"), (-999, "Very Aggressive")])

    n_favorable = sum(1 for a in asset_reports if a["recommendation"] == "Favorable")
    n_unfavorable = sum(1 for a in asset_reports if a["recommendation"] == "Unfavorable")

    summary = {
        "headline": f"Portfolio returned {cagr*100:.1f}% per year with a Sharpe ratio of {sharpe:.2f}",
        "plain_english": (
            f"If you had invested $10,000 using this strategy since {start_date}, "
            f"it would have grown at roughly {cagr*100:.1f}% per year. "
            f"The worst drop from peak was {abs(max_dd)*100:.1f}%, "
            f"meaning your portfolio would have temporarily lost that much before recovering. "
            f"Overall volatility (how much your portfolio swings day to day) is {vol*100:.1f}% annually."
        ),
        "market_regime": regime,
        "regime_explanation": (
            "The market is currently in a TRENDING phase — momentum strategies tend to perform well."
            if regime == "Trending"
            else "The market is currently in a MEAN-REVERTING phase — momentum may underperform. Consider reducing position sizes."
        ),
        "portfolio_grade": portfolio_grade,
        "risk_profile": risk_grade,
        "key_takeaways": [
            f"{n_favorable} out of {len(asset_reports)} assets show favorable momentum right now."
            if n_favorable > 0
            else "No assets are showing strong favorable momentum — patience is key.",
            f"Watch out: {n_unfavorable} assets are in a downtrend."
            if n_unfavorable > 0
            else "Good news: no assets are in a significant downtrend.",
            f"Your portfolio risk is {risk_grade.lower()} — the strategy targets {settings.vol_target*100:.0f}% annual volatility.",
            f"The drawdown protection kicks in at {settings.drawdown_threshold*100:.0f}% loss, automatically reducing exposure.",
        ],
        "what_to_do": (
            "The strategy is fully automated — it adjusts positions based on momentum signals and volatility targets. "
            "You don't need to do anything. The model rebalances monthly and cuts exposure during drawdowns."
        ),
    }

    metrics_explained = {
        "cagr": {"value": round(cagr, 4), "label": "Annual Return", "explanation": f"The strategy earns about {cagr*100:.1f}% per year on average."},
        "sharpe_ratio": {"value": round(sharpe, 2), "label": "Risk-Adjusted Return", "explanation": f"For every unit of risk taken, you earn {sharpe:.2f} units of return. Above 1.0 is excellent, above 0.5 is good."},
        "max_drawdown": {"value": round(max_dd, 4), "label": "Worst Drop", "explanation": f"The biggest peak-to-trough decline was {abs(max_dd)*100:.1f}%. This is the worst period you'd have experienced."},
        "annualized_vol": {"value": round(vol, 4), "label": "Volatility", "explanation": f"Your portfolio value swings about {vol*100:.1f}% per year. Lower is smoother."},
        "hit_rate": {"value": round(m.get("hit_rate_daily", 0), 4), "label": "Win Rate", "explanation": f"The strategy is profitable on {m.get('hit_rate_daily', 0)*100:.1f}% of trading days."},
        "calmar_ratio": {"value": round(m.get("calmar_ratio", 0), 2), "label": "Return per Drawdown", "explanation": "How much return you get per unit of worst-case loss. Higher is better."},
    }

    report = {
        "summary": summary,
        "asset_reports": asset_reports,
        "metrics_explained": metrics_explained,
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_period": f"{start_date} to present",
        "n_assets": len(asset_reports),
    }
    _cache_set(key, report)
    return report
