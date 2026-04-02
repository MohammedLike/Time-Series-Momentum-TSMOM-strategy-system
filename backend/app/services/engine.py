"""Core service layer — wraps existing quant engine for API consumption.

Bridges the existing TSMOM system with the FastAPI layer by converting
pandas DataFrames/Series into JSON-serializable structures.
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path
from functools import lru_cache

import numpy as np
import pandas as pd

# Add project root to path so we can import existing modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import AppSettings
from src.backtest.engine import BacktestEngine
from src.data.provider import DataManager
from src.data.cleaning import compute_returns, winsorize_returns, align_and_clean
from src.data.universe import load_universes, load_strategy_presets, get_ticker_metadata
from src.signals.composite import CompositeSignalGenerator
from src.signals.volatility import ewma_volatility
from src.signals.regime import HMMRegimeDetector
from src.risk.metrics import compute_all_metrics, rolling_sharpe, monthly_returns_table
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


@lru_cache(maxsize=1)
def _get_data_manager() -> DataManager:
    return DataManager(cache_dir=PROJECT_ROOT / "data" / "cache")


def run_backtest(req: BacktestRequest) -> BacktestResponse:
    """Execute a full backtest and return structured results."""
    settings = _build_settings(req)
    dm = _get_data_manager()

    prices = dm.get_close_prices(req.tickers, req.start_date, req.end_date)
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
            spy = dm.get_close_prices(["SPY"], req.start_date, req.end_date)
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

    return BacktestResponse(
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


def get_signals(tickers: list[str], start_date: str, lookbacks: list[int] | None = None) -> SignalResponse:
    """Get current signal state for all assets."""
    dm = _get_data_manager()
    settings = AppSettings()
    if lookbacks:
        settings.momentum_lookbacks = lookbacks

    prices = dm.get_close_prices(tickers, start_date)
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

    return SignalResponse(
        heatmap=heatmap,
        assets=list(final.columns),
        current_signals=current_signals,
        signal_components=signal_components,
    )


def get_regime(tickers: list[str], start_date: str) -> RegimeResponse:
    """Get regime detection analysis."""
    dm = _get_data_manager()
    prices = dm.get_close_prices(tickers, start_date)
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

    return RegimeResponse(
        regime_history=regime_history,
        current_regime=current_regime,
        current_probabilities={
            "trending": round(float(regime_probs.iloc[-1].iloc[0]), 4),
            "mean_reverting": round(float(regime_probs.iloc[-1].iloc[1]), 4),
        },
        regime_stats=regime_stats,
    )


def get_risk(tickers: list[str], start_date: str, vol_target: float = 0.10) -> RiskResponse:
    """Get risk analysis data."""
    dm = _get_data_manager()
    settings = AppSettings(vol_target=vol_target)
    prices = dm.get_close_prices(tickers, start_date)
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

    return RiskResponse(
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


def get_live_update(tickers: list[str]) -> LiveUpdate:
    """Simulate a live trading snapshot."""
    dm = _get_data_manager()
    settings = AppSettings()

    prices = dm.get_close_prices(tickers, "2020-01-01")
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
