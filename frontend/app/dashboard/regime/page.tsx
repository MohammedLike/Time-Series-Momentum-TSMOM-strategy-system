"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { KpiCard } from "@/components/ui/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PlotlyChart, COLORS } from "@/components/charts/plotly-chart";
import { LoadingChart, LoadingGrid } from "@/components/ui/loading";
import { motion } from "framer-motion";
import { Brain, TrendingUp, Repeat, Clock } from "lucide-react";
import type { Data } from "plotly.js";

const TICKERS = ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV"];

export default function RegimePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["regime"],
    queryFn: () => api.getRegime(TICKERS),
    staleTime: 5 * 60 * 1000,
  });

  const trending = data?.regime_stats?.trending;
  const meanRev = data?.regime_stats?.mean_reverting;

  return (
    <div className="space-y-6">
      <Header
        title="Regime Detection"
        description="Hidden Markov Model classifying trending vs mean-reverting market regimes"
        badge="HMM"
      />

      {/* KPIs */}
      {isLoading || !data ? (
        <LoadingGrid count={4} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard
            title="Current Regime"
            value={data.current_regime}
            icon={Brain}
            trend={data.current_regime === "Trending" ? "up" : "down"}
            delay={0}
          />
          <KpiCard
            title="Trending Prob"
            value={formatPercent(data.current_probabilities.trending)}
            icon={TrendingUp}
            trend={data.current_probabilities.trending > 0.5 ? "up" : "neutral"}
            delay={0.05}
          />
          <KpiCard
            title="Time in Trend"
            value={formatPercent(trending?.pct_time ?? 0)}
            icon={Clock}
            trend="neutral"
            delay={0.1}
          />
          <KpiCard
            title="Time Mean-Rev"
            value={formatPercent(meanRev?.pct_time ?? 0)}
            icon={Repeat}
            trend="neutral"
            delay={0.15}
          />
        </div>
      )}

      {/* Regime Score Over Time */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <CardTitle>Regime Score History</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.regime_history.map((p) => p.date),
                    y: data.regime_history.map((p) => p.regime_score),
                    type: "scatter",
                    mode: "lines",
                    name: "Regime Score",
                    line: { color: COLORS.primary, width: 2 },
                    fill: "tozeroy",
                    fillcolor: "rgba(99, 102, 241, 0.08)",
                  } as Data,
                  {
                    x: data.regime_history.map((p) => p.date),
                    y: Array(data.regime_history.length).fill(0.5),
                    type: "scatter",
                    mode: "lines",
                    name: "Threshold",
                    line: { color: COLORS.slate, width: 1, dash: "dash" },
                    showlegend: false,
                  } as Data,
                ]}
                height={300}
                layout={{
                  yaxis: {
                    title: "Score (>0.5 = Trending)",
                    range: [0, 1.05],
                  },
                  annotations: [
                    {
                      x: 0.02, y: 0.95,
                      xref: "paper", yref: "paper",
                      text: "TRENDING",
                      showarrow: false,
                      font: { size: 10, color: COLORS.profit },
                    },
                    {
                      x: 0.02, y: 0.15,
                      xref: "paper", yref: "paper",
                      text: "MEAN-REVERTING",
                      showarrow: false,
                      font: { size: 10, color: COLORS.loss },
                    },
                  ],
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Regime Probabilities */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader>
              <CardTitle>Regime Probabilities Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.regime_history.map((p) => p.date),
                    y: data.regime_history.map((p) => p.trending_prob * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "P(Trending)",
                    line: { color: COLORS.profit, width: 1.5 },
                    fill: "tozeroy",
                    fillcolor: "rgba(16, 185, 129, 0.1)",
                  } as Data,
                  {
                    x: data.regime_history.map((p) => p.date),
                    y: data.regime_history.map((p) => p.mean_reverting_prob * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "P(Mean-Reverting)",
                    line: { color: COLORS.loss, width: 1.5 },
                    fill: "tozeroy",
                    fillcolor: "rgba(239, 68, 68, 0.1)",
                  } as Data,
                ]}
                height={300}
                layout={{
                  yaxis: { title: "Probability %", ticksuffix: "%", range: [0, 105] },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Regime Statistics Comparison */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle>Trending Regime</CardTitle>
                  <Badge variant="profit">MOMENTUM WORKS</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  In trending regimes, momentum signals are at full strength. The HMM identifies
                  periods where assets exhibit persistent directional moves — the condition under
                  which TSMOM generates alpha.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Days</p>
                    <p className="text-lg font-mono font-bold">{trending?.count_days?.toLocaleString()}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">% of Time</p>
                    <p className="text-lg font-mono font-bold">{formatPercent(trending?.pct_time ?? 0)}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Avg Ann. Return</p>
                    <p className="text-lg font-mono font-bold text-emerald-400">{formatPercent(trending?.avg_return ?? 0)}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Ann. Volatility</p>
                    <p className="text-lg font-mono font-bold">{formatPercent(trending?.volatility ?? 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle>Mean-Reverting Regime</CardTitle>
                  <Badge variant="loss">SIGNALS DAMPENED</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  In mean-reverting regimes, momentum signals are scaled down to 30% strength.
                  These periods feature choppy, range-bound markets where trend-following
                  generates whipsaws and losses.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Days</p>
                    <p className="text-lg font-mono font-bold">{meanRev?.count_days?.toLocaleString()}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">% of Time</p>
                    <p className="text-lg font-mono font-bold">{formatPercent(meanRev?.pct_time ?? 0)}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Avg Ann. Return</p>
                    <p className="text-lg font-mono font-bold">{formatPercent(meanRev?.avg_return ?? 0)}</p>
                  </div>
                  <div className="p-3 rounded-md bg-muted/50">
                    <p className="text-[10px] text-muted-foreground uppercase">Ann. Volatility</p>
                    <p className="text-lg font-mono font-bold">{formatPercent(meanRev?.volatility ?? 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      )}
    </div>
  );
}
