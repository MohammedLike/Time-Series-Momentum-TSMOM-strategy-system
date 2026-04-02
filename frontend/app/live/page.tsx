"use client";

import { useState, useEffect, useCallback } from "react";
import { api, type LiveUpdate } from "@/lib/api";
import { formatPercent, formatNumber, formatCurrency } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { KpiCard } from "@/components/ui/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PlotlyChart, COLORS } from "@/components/charts/plotly-chart";
import { LoadingSpinner } from "@/components/ui/loading";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radio,
  DollarSign,
  TrendingUp,
  Brain,
  Activity,
  Pause,
  Play,
  RefreshCw,
} from "lucide-react";
import type { Data } from "plotly.js";

const TICKERS = ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV"];

export default function LivePage() {
  const [isLive, setIsLive] = useState(false);
  const [data, setData] = useState<LiveUpdate | null>(null);
  const [history, setHistory] = useState<{ timestamp: string; value: number }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchUpdate = useCallback(async () => {
    try {
      setLoading(true);
      const update = await api.getLiveUpdate(TICKERS);
      setData(update);
      setHistory((prev) => [
        ...prev.slice(-100),
        { timestamp: update.timestamp, value: update.portfolio_value },
      ]);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isLive) {
      fetchUpdate();
      const interval = setInterval(fetchUpdate, 5000);
      return () => clearInterval(interval);
    }
  }, [isLive, fetchUpdate]);

  return (
    <div className="space-y-6">
      <Header
        title="Live Trading Simulation"
        description="Real-time signal updates with simulated portfolio positions"
        badge={isLive ? "LIVE" : "PAUSED"}
      >
        <div className="flex items-center gap-2">
          {isLive && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle" />
              Auto-updating every 5s
            </div>
          )}
          <Button
            variant={isLive ? "destructive" : "default"}
            size="sm"
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? (
              <>
                <Pause className="w-3.5 h-3.5 mr-1.5" /> Stop
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 mr-1.5" /> Start Live
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchUpdate}
            disabled={loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </Header>

      {error && (
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-destructive">Connection error: {error}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Ensure the backend is running. Retrying automatically...
            </p>
          </CardContent>
        </Card>
      )}

      {!data && !loading && !error && (
        <Card>
          <CardContent className="py-16 text-center">
            <Radio className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-lg font-medium mb-2">Live Trading Simulation</p>
            <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
              Click &quot;Start Live&quot; to begin receiving simulated real-time trading signals
              and portfolio updates. Signals refresh every 5 seconds with small perturbations
              to simulate market movement.
            </p>
            <Button onClick={() => setIsLive(true)}>
              <Play className="w-4 h-4 mr-2" /> Start Simulation
            </Button>
          </CardContent>
        </Card>
      )}

      {loading && !data && <LoadingSpinner />}

      {data && (
        <AnimatePresence mode="wait">
          <motion.div
            key="live-data"
            className="space-y-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiCard
                title="Portfolio Value"
                value={formatCurrency(data.portfolio_value)}
                icon={DollarSign}
                trend={data.daily_pnl >= 0 ? "up" : "down"}
              />
              <KpiCard
                title="Daily P&L"
                value={formatCurrency(data.daily_pnl)}
                icon={TrendingUp}
                trend={data.daily_pnl >= 0 ? "up" : "down"}
              />
              <KpiCard
                title="Regime"
                value={data.regime}
                icon={Brain}
                trend={data.regime === "Trending" ? "up" : "down"}
              />
              <KpiCard
                title="Active Positions"
                value={String(data.positions.length)}
                icon={Activity}
                trend="neutral"
              />
            </div>

            {/* Portfolio Value History */}
            {history.length > 1 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Portfolio Value (Session)</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      Last update: {data.timestamp}
                    </p>
                  </div>
                </CardHeader>
                <CardContent>
                  <PlotlyChart
                    data={[
                      {
                        x: history.map((h) => h.timestamp),
                        y: history.map((h) => h.value),
                        type: "scatter",
                        mode: "lines+markers",
                        name: "Portfolio",
                        line: { color: COLORS.primary, width: 2 },
                        marker: { size: 4 },
                      } as Data,
                    ]}
                    height={250}
                    layout={{
                      yaxis: { title: "Value ($)", tickprefix: "$" },
                    }}
                  />
                </CardContent>
              </Card>
            )}

            {/* Positions & Signals Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Current Positions */}
              <Card>
                <CardHeader>
                  <CardTitle>Current Positions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <AnimatePresence>
                      {data.positions
                        .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight))
                        .map((pos) => (
                          <motion.div
                            key={pos.asset}
                            layout
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className="flex items-center justify-between p-3 rounded-md bg-muted/50"
                          >
                            <div className="flex items-center gap-3">
                              <Badge variant={pos.side === "LONG" ? "profit" : "loss"}>
                                {pos.side}
                              </Badge>
                              <span className="text-sm font-medium">{pos.asset}</span>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-mono">{formatPercent(pos.weight)}</p>
                              <p className="text-xs text-muted-foreground">
                                sig: {formatNumber(pos.signal)}
                              </p>
                            </div>
                          </motion.div>
                        ))}
                    </AnimatePresence>
                  </div>
                </CardContent>
              </Card>

              {/* Signal Gauge */}
              <Card>
                <CardHeader>
                  <CardTitle>Live Signals</CardTitle>
                </CardHeader>
                <CardContent>
                  <PlotlyChart
                    data={[
                      {
                        type: "bar",
                        x: Object.values(data.signals),
                        y: Object.keys(data.signals),
                        orientation: "h",
                        marker: {
                          color: Object.values(data.signals).map((v) =>
                            v > 0.1
                              ? COLORS.profit
                              : v < -0.1
                                ? COLORS.loss
                                : COLORS.slate
                          ),
                        },
                        hovertemplate: "%{y}: %{x:.2f}<extra></extra>",
                      } as Data,
                    ]}
                    height={350}
                    layout={{
                      margin: { l: 50, r: 20, t: 10, b: 30 },
                      xaxis: { title: "Signal Strength", range: [-2.5, 2.5] },
                      yaxis: { autorange: "reversed" },
                      shapes: [
                        {
                          type: "line",
                          x0: 0,
                          x1: 0,
                          y0: -0.5,
                          y1: Object.keys(data.signals).length - 0.5,
                          line: { color: "rgba(100,116,139,0.5)", width: 1, dash: "dash" },
                        },
                      ],
                    }}
                  />
                </CardContent>
              </Card>
            </div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
