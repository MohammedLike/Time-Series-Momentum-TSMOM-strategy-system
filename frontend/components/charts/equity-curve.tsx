"use client";

import { PlotlyChart, COLORS } from "./plotly-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { TimeSeriesPoint, RegimePoint } from "@/lib/api";
import type { Data } from "plotly.js";

interface EquityCurveProps {
  equity: TimeSeriesPoint[];
  benchmark?: TimeSeriesPoint[];
  regime?: RegimePoint[];
  height?: number;
}

export function EquityCurve({ equity, benchmark, regime, height = 400 }: EquityCurveProps) {
  const traces: Data[] = [
    {
      x: equity.map((p) => p.date),
      y: equity.map((p) => p.value),
      type: "scatter",
      mode: "lines",
      name: "TSMOM Strategy",
      line: { color: COLORS.primary, width: 2 },
      fill: "tozeroy",
      fillcolor: "rgba(99, 102, 241, 0.05)",
    },
  ];

  if (benchmark?.length) {
    traces.push({
      x: benchmark.map((p) => p.date),
      y: benchmark.map((p) => p.value),
      type: "scatter",
      mode: "lines",
      name: "S&P 500 (Benchmark)",
      line: { color: COLORS.slate, width: 1.5, dash: "dot" },
    });
  }

  // Regime overlay as background shapes
  const shapes: Array<Record<string, unknown>> = [];
  if (regime?.length) {
    let currentRegime = regime[0].regime_score > 0.5;
    let startDate = regime[0].date;

    for (let i = 1; i < regime.length; i++) {
      const isTrending = regime[i].regime_score > 0.5;
      if (isTrending !== currentRegime || i === regime.length - 1) {
        if (!currentRegime) {
          shapes.push({
            type: "rect",
            xref: "x",
            yref: "paper",
            x0: startDate,
            x1: regime[i].date,
            y0: 0,
            y1: 1,
            fillcolor: "rgba(239, 68, 68, 0.04)",
            line: { width: 0 },
            layer: "below",
          });
        }
        currentRegime = isTrending;
        startDate = regime[i].date;
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Equity Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <PlotlyChart
          data={traces}
          height={height}
          layout={{
            yaxis: { title: "Cumulative Return", tickformat: ".2f" },
            shapes: shapes as never[],
          }}
        />
      </CardContent>
    </Card>
  );
}
