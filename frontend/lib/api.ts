const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchApi<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error ${res.status}: ${error}`);
  }
  return res.json();
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface PositionInfo {
  asset: string;
  weight: number;
  signal: number;
  side: string;
}

export interface MetricsResponse {
  total_return: number;
  cagr: number;
  annualized_vol: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_duration_days: number;
  hit_rate_daily: number;
  skewness: number;
  kurtosis: number;
  best_day: number;
  worst_day: number;
  best_month: number;
  worst_month: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
  cvar_99: number;
  n_trading_days: number;
  n_years: number;
  information_ratio?: number;
  tracking_error?: number;
  beta?: number;
  alpha_annual?: number;
}

export interface StressTestResult {
  scenario: string;
  period: string;
  cumulative_return: number;
  max_drawdown: number;
  worst_day: number;
  best_day: number;
  annualized_vol: number;
  n_days: number;
}

export interface BacktestResponse {
  metrics: MetricsResponse;
  equity_curve: TimeSeriesPoint[];
  drawdown: TimeSeriesPoint[];
  rolling_sharpe: TimeSeriesPoint[];
  rolling_volatility: TimeSeriesPoint[];
  weights: Record<string, TimeSeriesPoint[]>;
  signals: Record<string, TimeSeriesPoint[]>;
  monthly_returns: Record<string, Record<string, number | null>>;
  stress_tests: StressTestResult[];
  regime: RegimePoint[];
  positions: PositionInfo[];
  benchmark_equity?: TimeSeriesPoint[];
  cost_drag: TimeSeriesPoint[];
  turnover: TimeSeriesPoint[];
  gross_exposure: TimeSeriesPoint[];
  net_exposure: TimeSeriesPoint[];
  long_exposure: TimeSeriesPoint[];
  short_exposure: TimeSeriesPoint[];
}

export interface BacktestRequest {
  tickers: string[];
  start_date: string;
  end_date?: string;
  vol_target: number;
  momentum_lookbacks: number[];
  rebalance_frequency: string;
  drawdown_threshold: number;
  drawdown_scaling_floor: number;
  max_position_weight: number;
  max_gross_exposure: number;
  slippage_bps: number;
  commission_bps: number;
}

export interface SignalHeatmapRow {
  date: string;
  values: Record<string, number>;
}

export interface SignalResponse {
  heatmap: SignalHeatmapRow[];
  assets: string[];
  current_signals: Record<string, number>;
  signal_components: Record<string, TimeSeriesPoint[]>;
}

export interface RegimePoint {
  date: string;
  regime_score: number;
  trending_prob: number;
  mean_reverting_prob: number;
}

export interface RegimeResponse {
  regime_history: RegimePoint[];
  current_regime: string;
  current_probabilities: Record<string, number>;
  regime_stats: Record<string, Record<string, number>>;
}

export interface RiskResponse {
  var_95: number;
  var_99: number;
  cvar_95: number;
  cvar_99: number;
  rolling_var: TimeSeriesPoint[];
  rolling_cvar: TimeSeriesPoint[];
  rolling_vol: TimeSeriesPoint[];
  stress_tests: StressTestResult[];
  risk_contributions: Record<string, number>;
  drawdown_series: TimeSeriesPoint[];
  drawdown_duration: TimeSeriesPoint[];
}

export interface LiveUpdate {
  timestamp: string;
  positions: PositionInfo[];
  portfolio_value: number;
  daily_pnl: number;
  regime: string;
  signals: Record<string, number>;
}

export interface UniverseAsset {
  ticker: string;
  name: string;
  sector: string;
  asset_class: string;
}

export interface UniverseResponse {
  universes: Record<string, UniverseAsset[]>;
  presets: Record<string, Record<string, unknown>>;
}

export interface AssetReport {
  ticker: string;
  total_return: number;
  annualized_return: number;
  annualized_vol: number;
  sharpe_ratio: number;
  max_drawdown: number;
  current_signal: number;
  current_vol: number;
  current_weight: number;
  recent_3m_return: number;
  risk_level: string;
  momentum_verdict: string;
  recommendation: string;
  recommendation_color: string;
  recommendation_detail: string;
}

export interface ResearchReport {
  summary: {
    headline: string;
    plain_english: string;
    market_regime: string;
    regime_explanation: string;
    portfolio_grade: string;
    risk_profile: string;
    key_takeaways: string[];
    what_to_do: string;
  };
  asset_reports: AssetReport[];
  metrics_explained: Record<string, { value: number; label: string; explanation: string }>;
  generated_at: string;
  data_period: string;
  n_assets: number;
}

// API functions
export const api = {
  runBacktest: (req: BacktestRequest) =>
    fetchApi<BacktestResponse>("/run-backtest", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  getSignals: (tickers: string[], startDate = "2005-01-01", lookbacks = "21,63,126,252") =>
    fetchApi<SignalResponse>(
      `/get-signals?tickers=${tickers.join(",")}&start_date=${startDate}&lookbacks=${lookbacks}`
    ),

  getRegime: (tickers: string[], startDate = "2005-01-01") =>
    fetchApi<RegimeResponse>(
      `/get-regime?tickers=${tickers.join(",")}&start_date=${startDate}`
    ),

  getRisk: (tickers: string[], startDate = "2005-01-01", volTarget = 0.1) =>
    fetchApi<RiskResponse>(
      `/get-risk?tickers=${tickers.join(",")}&start_date=${startDate}&vol_target=${volTarget}`
    ),

  getLiveUpdate: (tickers: string[]) =>
    fetchApi<LiveUpdate>(`/live-update?tickers=${tickers.join(",")}`),

  getUniverse: () => fetchApi<UniverseResponse>("/universe"),

  getPerformance: (tickers: string[], startDate = "2005-01-01") =>
    fetchApi<{ metrics: MetricsResponse; equity_curve: TimeSeriesPoint[]; benchmark_equity?: TimeSeriesPoint[] }>(
      `/get-performance?tickers=${tickers.join(",")}&start_date=${startDate}`
    ),

  getResearchReport: (tickers: string[], startDate = "2005-01-01") =>
    fetchApi<ResearchReport>(
      `/research-report?tickers=${tickers.join(",")}&start_date=${startDate}`
    ),

  health: () => fetchApi<{ status: string }>("/health"),
};
