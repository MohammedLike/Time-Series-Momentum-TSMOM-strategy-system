"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type BacktestRequest, type BacktestResponse } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { KpiCard } from "@/components/ui/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EquityCurve } from "@/components/charts/equity-curve";
import { DrawdownChart } from "@/components/charts/drawdown-chart";
import { RollingMetrics } from "@/components/charts/rolling-metrics";
import { MonthlyHeatmap } from "@/components/charts/monthly-heatmap";
import { ExposureChart } from "@/components/charts/exposure-chart";
import { LoadingSpinner } from "@/components/ui/loading";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, BarChart3, Activity,
  Shield, Play, RotateCcw, Download,
} from "lucide-react";

const ALL_TICKERS = [
  "SPY", "QQQ", "IWM", "XLF", "XLE", "XLV", "XLK", "XLI", "XLP", "XLY", "XLU", "XLRE",
  "GLD", "SLV", "USO", "UNG", "DBA",
  "TLT", "IEF", "SHY", "LQD", "HYG",
  "UUP", "FXE", "FXY", "FXB", "FXA",
];

const ASSET_CLASSES: Record<string, string[]> = {
  Equities: ["SPY", "QQQ", "IWM", "XLF", "XLE", "XLV", "XLK", "XLI", "XLP", "XLY", "XLU", "XLRE"],
  Commodities: ["GLD", "SLV", "USO", "UNG", "DBA"],
  "Fixed Income": ["TLT", "IEF", "SHY", "LQD", "HYG"],
  FX: ["UUP", "FXE", "FXY", "FXB", "FXA"],
};

export default function BacktestPage() {
  const [params, setParams] = useState<BacktestRequest>({
    tickers: ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE"],
    start_date: "2005-01-01",
    vol_target: 0.10,
    momentum_lookbacks: [21, 63, 126, 252],
    rebalance_frequency: "monthly",
    drawdown_threshold: 0.10,
    drawdown_scaling_floor: 0.25,
    max_position_weight: 0.10,
    max_gross_exposure: 2.0,
    slippage_bps: 5.0,
    commission_bps: 1.0,
  });

  const mutation = useMutation({
    mutationFn: (req: BacktestRequest) => api.runBacktest(req),
  });

  const data = mutation.data;
  const m = data?.metrics;

  const toggleTicker = (ticker: string) => {
    setParams((prev) => ({
      ...prev,
      tickers: prev.tickers.includes(ticker)
        ? prev.tickers.filter((t) => t !== ticker)
        : [...prev.tickers, ticker],
    }));
  };

  const toggleLookback = (lb: number) => {
    setParams((prev) => ({
      ...prev,
      momentum_lookbacks: prev.momentum_lookbacks.includes(lb)
        ? prev.momentum_lookbacks.filter((l) => l !== lb)
        : [...prev.momentum_lookbacks, lb].sort(),
    }));
  };

  const applyPreset = (preset: "conservative" | "balanced" | "aggressive") => {
    const presets = {
      conservative: { vol_target: 0.08, momentum_lookbacks: [126, 252], rebalance_frequency: "monthly", drawdown_threshold: 0.08 },
      balanced: { vol_target: 0.10, momentum_lookbacks: [21, 63, 126, 252], rebalance_frequency: "monthly", drawdown_threshold: 0.10 },
      aggressive: { vol_target: 0.15, momentum_lookbacks: [21, 63], rebalance_frequency: "weekly", drawdown_threshold: 0.15 },
    };
    setParams((prev) => ({ ...prev, ...presets[preset] }));
  };

  const handleExportCSV = () => {
    if (!data) return;
    const rows = [["Date", "Value"]];
    data.equity_curve.forEach((p) => rows.push([p.date, String(p.value)]));
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tsmom_backtest.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Header
        title="Backtest Laboratory"
        description="Configure and run custom backtests with real-time parameter tuning"
        badge="Lab"
      >
        {data && (
          <Button variant="outline" size="sm" onClick={handleExportCSV}>
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export CSV
          </Button>
        )}
      </Header>

      {/* Parameter Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Presets */}
          <div>
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">Strategy Presets</p>
            <div className="flex gap-2">
              {(["conservative", "balanced", "aggressive"] as const).map((preset) => (
                <Button
                  key={preset}
                  variant="outline"
                  size="sm"
                  onClick={() => applyPreset(preset)}
                  className="capitalize"
                >
                  {preset}
                </Button>
              ))}
            </div>
          </div>

          {/* Asset Selection */}
          <div>
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">Asset Universe</p>
            {Object.entries(ASSET_CLASSES).map(([cls, tickers]) => (
              <div key={cls} className="mb-3">
                <p className="text-xs font-medium mb-1.5">{cls}</p>
                <div className="flex flex-wrap gap-1.5">
                  {tickers.map((ticker) => (
                    <button
                      key={ticker}
                      onClick={() => toggleTicker(ticker)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                        params.tickers.includes(ticker)
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      {ticker}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Parameters Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                Vol Target
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="0.5"
                value={params.vol_target}
                onChange={(e) => setParams((p) => ({ ...p, vol_target: Number(e.target.value) }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                DD Threshold
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="0.5"
                value={params.drawdown_threshold}
                onChange={(e) => setParams((p) => ({ ...p, drawdown_threshold: Number(e.target.value) }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                Max Position
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="1"
                value={params.max_position_weight}
                onChange={(e) => setParams((p) => ({ ...p, max_position_weight: Number(e.target.value) }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                Gross Exposure
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="5"
                value={params.max_gross_exposure}
                onChange={(e) => setParams((p) => ({ ...p, max_gross_exposure: Number(e.target.value) }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                Slippage (bps)
              </label>
              <input
                type="number"
                step="1"
                min="0"
                max="50"
                value={params.slippage_bps}
                onChange={(e) => setParams((p) => ({ ...p, slippage_bps: Number(e.target.value) }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                Rebalance
              </label>
              <select
                value={params.rebalance_frequency}
                onChange={(e) => setParams((p) => ({ ...p, rebalance_frequency: e.target.value }))}
                className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          {/* Lookback Selection */}
          <div>
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">
              Momentum Lookbacks (trading days)
            </p>
            <div className="flex gap-2">
              {[21, 63, 126, 252].map((lb) => (
                <button
                  key={lb}
                  onClick={() => toggleLookback(lb)}
                  className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                    params.momentum_lookbacks.includes(lb)
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {lb === 21 ? "1M" : lb === 63 ? "3M" : lb === 126 ? "6M" : "12M"} ({lb}d)
                </button>
              ))}
            </div>
          </div>

          {/* Run Button */}
          <div className="flex gap-3">
            <Button
              onClick={() => mutation.mutate(params)}
              disabled={mutation.isPending || params.tickers.length === 0}
              className="min-w-[160px]"
            >
              {mutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-primary-foreground/20 border-t-primary-foreground rounded-full animate-spin mr-2" />
                  Running Backtest...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Backtest
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                setParams({
                  tickers: ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE"],
                  start_date: "2005-01-01",
                  vol_target: 0.1,
                  momentum_lookbacks: [21, 63, 126, 252],
                  rebalance_frequency: "monthly",
                  drawdown_threshold: 0.1,
                  drawdown_scaling_floor: 0.25,
                  max_position_weight: 0.1,
                  max_gross_exposure: 2.0,
                  slippage_bps: 5.0,
                  commission_bps: 1.0,
                })
              }
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {mutation.isPending && (
        <Card>
          <CardContent className="py-16">
            <LoadingSpinner />
            <p className="text-center text-sm text-muted-foreground mt-4">
              Running backtest with {params.tickers.length} assets...
            </p>
          </CardContent>
        </Card>
      )}

      {mutation.isError && (
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-destructive">
              Backtest failed: {(mutation.error as Error).message}
            </p>
          </CardContent>
        </Card>
      )}

      {data && m && (
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
            <KpiCard title="CAGR" value={formatPercent(m.cagr)} icon={TrendingUp} trend={m.cagr > 0 ? "up" : "down"} />
            <KpiCard title="Sharpe" value={formatNumber(m.sharpe_ratio)} icon={BarChart3} trend={m.sharpe_ratio > 0.5 ? "up" : "neutral"} />
            <KpiCard title="Sortino" value={formatNumber(m.sortino_ratio)} icon={Activity} trend={m.sortino_ratio > 1 ? "up" : "neutral"} />
            <KpiCard title="Max DD" value={formatPercent(m.max_drawdown)} icon={TrendingDown} trend="down" />
            <KpiCard title="Calmar" value={formatNumber(m.calmar_ratio)} icon={Shield} trend={m.calmar_ratio > 0.3 ? "up" : "neutral"} />
            <KpiCard title="Vol" value={formatPercent(m.annualized_vol)} trend="neutral" />
            <KpiCard title="VaR 95" value={formatPercent(m.var_95)} trend="down" />
            <KpiCard title="Total Return" value={formatPercent(m.total_return)} trend={m.total_return > 0 ? "up" : "down"} />
          </div>

          <EquityCurve equity={data.equity_curve} benchmark={data.benchmark_equity ?? undefined} regime={data.regime} />
          <DrawdownChart drawdown={data.drawdown} />
          <RollingMetrics sharpe={data.rolling_sharpe} volatility={data.rolling_volatility} />
          <ExposureChart
            gross={data.gross_exposure}
            net={data.net_exposure}
            long={data.long_exposure}
            short={data.short_exposure}
          />
          <MonthlyHeatmap monthlyReturns={data.monthly_returns} />
        </motion.div>
      )}
    </div>
  );
}
