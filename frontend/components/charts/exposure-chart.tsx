"use client";

import { PlotlyChart, COLORS } from "./plotly-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { TimeSeriesPoint } from "@/lib/api";
import type { Data } from "plotly.js";

interface ExposureChartProps {
  gross: TimeSeriesPoint[];
  net: TimeSeriesPoint[];
  long: TimeSeriesPoint[];
  short: TimeSeriesPoint[];
  height?: number;
}

export function ExposureChart({ gross, net, long, short, height = 280 }: ExposureChartProps) {
  const traces: Data[] = [
    {
      x: long.map((p) => p.date),
      y: long.map((p) => p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Long",
      line: { color: COLORS.profit, width: 1.5 },
      fill: "tozeroy",
      fillcolor: "rgba(16, 185, 129, 0.08)",
    },
    {
      x: short.map((p) => p.date),
      y: short.map((p) => -p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Short",
      line: { color: COLORS.loss, width: 1.5 },
      fill: "tozeroy",
      fillcolor: "rgba(239, 68, 68, 0.08)",
    },
    {
      x: gross.map((p) => p.date),
      y: gross.map((p) => p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Gross",
      line: { color: COLORS.warning, width: 1, dash: "dot" },
    },
    {
      x: net.map((p) => p.date),
      y: net.map((p) => p.value * 100),
      type: "scatter",
      mode: "lines",
      name: "Net",
      line: { color: COLORS.blue, width: 1, dash: "dash" },
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Exposure</CardTitle>
      </CardHeader>
      <CardContent>
        <PlotlyChart
          data={traces}
          height={height}
          layout={{
            yaxis: { title: "Exposure %", ticksuffix: "%" },
          }}
        />
      </CardContent>
    </Card>
  );
}
