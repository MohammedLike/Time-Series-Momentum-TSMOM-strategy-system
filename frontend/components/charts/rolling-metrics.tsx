"use client";

import { PlotlyChart, COLORS } from "./plotly-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { TimeSeriesPoint } from "@/lib/api";
import type { Data } from "plotly.js";

interface RollingMetricsProps {
  sharpe: TimeSeriesPoint[];
  volatility: TimeSeriesPoint[];
  height?: number;
}

export function RollingMetrics({ sharpe, volatility, height = 280 }: RollingMetricsProps) {
  const sharpeTraces: Data[] = [
    {
      x: sharpe.map((p) => p.date),
      y: sharpe.map((p) => p.value),
      type: "scatter",
      mode: "lines",
      name: "Rolling Sharpe (1Y)",
      line: { color: COLORS.primary, width: 1.5 },
    },
    {
      x: sharpe.map((p) => p.date),
      y: Array(sharpe.length).fill(0),
      type: "scatter",
      mode: "lines",
      name: "Zero Line",
      line: { color: COLORS.slate, width: 1, dash: "dash" },
      showlegend: false,
    },
  ];

  const volTraces: Data[] = [
    {
      x: volatility.map((p) => p.date),
      y: volatility.map((p) => p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Rolling Vol (63d)",
      line: { color: COLORS.warning, width: 1.5 },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Rolling Sharpe Ratio</CardTitle>
        </CardHeader>
        <CardContent>
          <PlotlyChart data={sharpeTraces} height={height} layout={{
            yaxis: { title: "Sharpe Ratio" },
          }} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Rolling Volatility</CardTitle>
        </CardHeader>
        <CardContent>
          <PlotlyChart data={volTraces} height={height} layout={{
            yaxis: { title: "Annualized Vol %", ticksuffix: "%" },
          }} />
        </CardContent>
      </Card>
    </div>
  );
}
