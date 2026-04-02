"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PlotlyChart, COLORS } from "@/components/charts/plotly-chart";
import { LoadingChart, LoadingGrid } from "@/components/ui/loading";
import { motion } from "framer-motion";
import type { Data } from "plotly.js";

const TICKERS = ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV"];

export default function SignalsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["signals"],
    queryFn: () => api.getSignals(TICKERS),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="space-y-6">
      <Header
        title="Signal Engine"
        description="Multi-horizon momentum signals with regime-aware scaling"
        badge="Signals"
      />

      {/* Current Signals */}
      {isLoading || !data ? (
        <LoadingGrid count={10} />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle>Current Signal State</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {Object.entries(data.current_signals)
                  .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                  .map(([asset, signal]) => (
                    <div
                      key={asset}
                      className="flex items-center justify-between p-3 rounded-md bg-muted/50"
                    >
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={signal > 0.1 ? "profit" : signal < -0.1 ? "loss" : "secondary"}
                        >
                          {signal > 0.1 ? "LONG" : signal < -0.1 ? "SHORT" : "FLAT"}
                        </Badge>
                        <span className="text-sm font-medium">{asset}</span>
                      </div>
                      <span
                        className={`font-mono text-sm ${signal > 0 ? "text-emerald-400" : signal < 0 ? "text-red-400" : "text-muted-foreground"}`}
                      >
                        {formatNumber(signal)}
                      </span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Signal Heatmap */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <CardTitle>Signal Heatmap — Last 12 Months (Weekly)</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    z: data.heatmap.map((row) =>
                      data.assets.map((a) => row.values[a] ?? 0)
                    ),
                    x: data.assets,
                    y: data.heatmap.map((row) => row.date),
                    type: "heatmap",
                    colorscale: [
                      [0, "#ef4444"],
                      [0.3, "#fca5a5"],
                      [0.5, "#f8fafc"],
                      [0.7, "#86efac"],
                      [1, "#10b981"],
                    ],
                    zmid: 0,
                    colorbar: {
                      title: { text: "Signal", font: { size: 10 } },
                      thickness: 12,
                      len: 0.8,
                    },
                    hovertemplate: "%{x} | %{y}<br>Signal: %{z:.2f}<extra></extra>",
                  } as Data,
                ]}
                height={450}
                layout={{
                  margin: { l: 80, r: 80, t: 10, b: 40 },
                  yaxis: { autorange: "reversed" },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Signal Components */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader>
              <CardTitle>Signal Pipeline Decomposition</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={Object.entries(data.signal_components).map(([name, points], i) => ({
                  x: points.map((p) => p.date),
                  y: points.map((p) => p.value),
                  type: "scatter" as const,
                  mode: "lines" as const,
                  name: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                  line: { color: COLORS.series[i % COLORS.series.length], width: 1.5 },
                }))}
                height={350}
                layout={{
                  yaxis: { title: "Signal Value" },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
