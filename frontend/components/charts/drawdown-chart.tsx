"use client";

import { PlotlyChart, COLORS } from "./plotly-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { TimeSeriesPoint } from "@/lib/api";
import type { Data } from "plotly.js";

interface DrawdownChartProps {
  drawdown: TimeSeriesPoint[];
  height?: number;
}

export function DrawdownChart({ drawdown, height = 250 }: DrawdownChartProps) {
  const traces: Data[] = [
    {
      x: drawdown.map((p) => p.date),
      y: drawdown.map((p) => p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Drawdown",
      line: { color: COLORS.loss, width: 1.5 },
      fill: "tozeroy",
      fillcolor: "rgba(239, 68, 68, 0.1)",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Drawdown</CardTitle>
      </CardHeader>
      <CardContent>
        <PlotlyChart
          data={traces}
          height={height}
          layout={{
            yaxis: {
              title: "Drawdown %",
              ticksuffix: "%",
              range: [
                Math.min(...drawdown.map((p) => p.value * 100)) * 1.1,
                1,
              ],
            },
          }}
        />
      </CardContent>
    </Card>
  );
}
