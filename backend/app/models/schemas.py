"""Pydantic schemas for API request/response models."""

from __future__ import annotations
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    tickers: list[str] = Field(default=["SPY", "QQQ", "TLT", "GLD", "IEF"])
    start_date: str = "2005-01-01"
    end_date: str | None = None
    vol_target: float = 0.10
    momentum_lookbacks: list[int] = [21, 63, 126, 252]
    rebalance_frequency: str = "monthly"
    drawdown_threshold: float = 0.10
    drawdown_scaling_floor: float = 0.25
    max_position_weight: float = 0.10
    max_gross_exposure: float = 2.0
    slippage_bps: float = 5.0
    commission_bps: float = 1.0


class MetricsResponse(BaseModel):
    total_return: float = 0
    cagr: float = 0
    annualized_vol: float = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    calmar_ratio: float = 0
    max_drawdown: float = 0
    max_drawdown_duration_days: int = 0
    hit_rate_daily: float = 0
    skewness: float = 0
    kurtosis: float = 0
    best_day: float = 0
    worst_day: float = 0
    best_month: float = 0
    worst_month: float = 0
    var_95: float = 0
    var_99: float = 0
    cvar_95: float = 0
    cvar_99: float = 0
    n_trading_days: int = 0
    n_years: float = 0
    information_ratio: float | None = None
    tracking_error: float | None = None
    beta: float | None = None
    alpha_annual: float | None = None


class TimeSeriesPoint(BaseModel):
    date: str
    value: float


class AssetSignal(BaseModel):
    date: str
    asset: str
    signal: float


class RegimePoint(BaseModel):
    date: str
    regime_score: float
    trending_prob: float
    mean_reverting_prob: float


class StressTestResult(BaseModel):
    scenario: str
    period: str
    cumulative_return: float
    max_drawdown: float
    worst_day: float
    best_day: float
    annualized_vol: float
    n_days: int


class PositionInfo(BaseModel):
    asset: str
    weight: float
    signal: float
    side: str


class BacktestResponse(BaseModel):
    metrics: MetricsResponse
    equity_curve: list[TimeSeriesPoint]
    drawdown: list[TimeSeriesPoint]
    rolling_sharpe: list[TimeSeriesPoint]
    rolling_volatility: list[TimeSeriesPoint]
    weights: dict[str, list[TimeSeriesPoint]]
    signals: dict[str, list[TimeSeriesPoint]]
    monthly_returns: dict[str, dict[str, float | None]]
    stress_tests: list[StressTestResult]
    regime: list[RegimePoint]
    positions: list[PositionInfo]
    benchmark_equity: list[TimeSeriesPoint] | None = None
    cost_drag: list[TimeSeriesPoint]
    turnover: list[TimeSeriesPoint]
    gross_exposure: list[TimeSeriesPoint]
    net_exposure: list[TimeSeriesPoint]
    long_exposure: list[TimeSeriesPoint]
    short_exposure: list[TimeSeriesPoint]


class SignalHeatmapRow(BaseModel):
    date: str
    values: dict[str, float]


class SignalResponse(BaseModel):
    heatmap: list[SignalHeatmapRow]
    assets: list[str]
    current_signals: dict[str, float]
    signal_components: dict[str, list[TimeSeriesPoint]]


class RegimeResponse(BaseModel):
    regime_history: list[RegimePoint]
    current_regime: str
    current_probabilities: dict[str, float]
    regime_stats: dict[str, dict[str, float]]


class RiskResponse(BaseModel):
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    rolling_var: list[TimeSeriesPoint]
    rolling_cvar: list[TimeSeriesPoint]
    rolling_vol: list[TimeSeriesPoint]
    stress_tests: list[StressTestResult]
    risk_contributions: dict[str, float]
    drawdown_series: list[TimeSeriesPoint]
    drawdown_duration: list[TimeSeriesPoint]


class LiveUpdate(BaseModel):
    timestamp: str
    positions: list[PositionInfo]
    portfolio_value: float
    daily_pnl: float
    regime: str
    signals: dict[str, float]


class UniverseAsset(BaseModel):
    ticker: str
    name: str
    sector: str
    asset_class: str


class UniverseResponse(BaseModel):
    universes: dict[str, list[UniverseAsset]]
    presets: dict[str, dict]
