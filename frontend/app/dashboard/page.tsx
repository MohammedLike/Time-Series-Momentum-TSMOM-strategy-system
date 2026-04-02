"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type BacktestRequest } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { KpiCard } from "@/components/ui/kpi-card";
import { EquityCurve } from "@/components/charts/equity-curve";
import { DrawdownChart } from "@/components/charts/drawdown-chart";
import { RollingMetrics } from "@/components/charts/rolling-metrics";
import { MonthlyHeatmap } from "@/components/charts/monthly-heatmap";
import { ExposureChart } from "@/components/charts/exposure-chart";
import { LoadingGrid, LoadingChart } from "@/components/ui/loading";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  Shield,
  Target,
  Percent,
  Clock,
} from "lucide-react";

const DEFAULT_REQUEST: BacktestRequest = {
  tickers: ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV"],
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
};

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-backtest"],
    queryFn: () => api.runBacktest(DEFAULT_REQUEST),
    staleTime: 5 * 60 * 1000,
  });

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-sm text-destructive mb-2">Failed to load dashboard data</p>
            <p className="text-xs text-muted-foreground">
              Ensure the backend is running at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const m = data?.metrics;

  return (
    <div className="space-y-6">
      <Header
        title="Strategy Dashboard"
        description="Time-Series Momentum — Multi-Asset, Regime-Aware, Volatility-Targeted"
        badge="Live"
      />

      {/* KPI Row */}
      {isLoading || !m ? (
        <LoadingGrid count={8} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
          <KpiCard
            title="CAGR"
            value={formatPercent(m.cagr)}
            icon={TrendingUp}
            trend={m.cagr > 0 ? "up" : "down"}
            delay={0}
          />
          <KpiCard
            title="Sharpe"
            value={formatNumber(m.sharpe_ratio)}
            icon={BarChart3}
            trend={m.sharpe_ratio > 0.5 ? "up" : m.sharpe_ratio < 0 ? "down" : "neutral"}
            delay={0.05}
          />
          <KpiCard
            title="Sortino"
            value={formatNumber(m.sortino_ratio)}
            icon={Activity}
            trend={m.sortino_ratio > 0.5 ? "up" : "down"}
            delay={0.1}
          />
          <KpiCard
            title="Max DD"
            value={formatPercent(m.max_drawdown)}
            icon={TrendingDown}
            trend="down"
            delay={0.15}
          />
          <KpiCard
            title="Calmar"
            value={formatNumber(m.calmar_ratio)}
            icon={Shield}
            trend={m.calmar_ratio > 0.3 ? "up" : "neutral"}
            delay={0.2}
          />
          <KpiCard
            title="Vol"
            value={formatPercent(m.annualized_vol)}
            icon={Percent}
            trend="neutral"
            delay={0.25}
          />
          <KpiCard
            title="Hit Rate"
            value={formatPercent(m.hit_rate_daily)}
            icon={Target}
            trend={m.hit_rate_daily > 0.5 ? "up" : "down"}
            delay={0.3}
          />
          <KpiCard
            title="Years"
            value={formatNumber(m.n_years, 1)}
            icon={Clock}
            trend="neutral"
            delay={0.35}
          />
        </div>
      )}

      {/* Equity Curve */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <EquityCurve
            equity={data.equity_curve}
            benchmark={data.benchmark_equity ?? undefined}
            regime={data.regime}
          />
        </motion.div>
      )}

      {/* Drawdown */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <DrawdownChart drawdown={data.drawdown} />
        </motion.div>
      )}

      {/* Rolling Metrics */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <RollingMetrics sharpe={data.rolling_sharpe} volatility={data.rolling_volatility} />
        </motion.div>
      )}

      {/* Exposure */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
          <ExposureChart
            gross={data.gross_exposure}
            net={data.net_exposure}
            long={data.long_exposure}
            short={data.short_exposure}
          />
        </motion.div>
      )}

      {/* Current Positions + Monthly Heatmap */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Current Positions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[400px] overflow-auto">
                  {data.positions
                    .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight))
                    .map((pos) => (
                      <div
                        key={pos.asset}
                        className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <Badge variant={pos.side === "LONG" ? "profit" : "loss"}>
                            {pos.side}
                          </Badge>
                          <span className="text-sm font-medium">{pos.asset}</span>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-mono">
                            {formatPercent(pos.weight)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            sig: {formatNumber(pos.signal)}
                          </p>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            className="xl:col-span-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.55 }}
          >
            <MonthlyHeatmap monthlyReturns={data.monthly_returns} />
          </motion.div>
        </div>
      )}

      {/* Stress Tests */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
          <Card>
            <CardHeader>
              <CardTitle>Historical Stress Tests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Scenario</th>
                      <th className="text-left py-2 px-3 text-muted-foreground font-medium">Period</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Return</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Max DD</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Worst Day</th>
                      <th className="text-right py-2 px-3 text-muted-foreground font-medium">Vol</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.stress_tests.map((st) => (
                      <tr key={st.scenario} className="border-b border-border/50 hover:bg-muted/50">
                        <td className="py-2 px-3 font-medium">{st.scenario}</td>
                        <td className="py-2 px-3 text-muted-foreground text-xs">{st.period}</td>
                        <td className={`py-2 px-3 text-right font-mono ${st.cumulative_return >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {formatPercent(st.cumulative_return)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-red-400">
                          {formatPercent(st.max_drawdown)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-red-400">
                          {formatPercent(st.worst_day)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono">
                          {formatPercent(st.annualized_vol)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
