"use client";

import { PlotlyChart } from "./plotly-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { Data } from "plotly.js";

interface MonthlyHeatmapProps {
  monthlyReturns: Record<string, Record<string, number | null>>;
  height?: number;
}

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function MonthlyHeatmap({ monthlyReturns, height = 400 }: MonthlyHeatmapProps) {
  const years = Object.keys(monthlyReturns).sort();
  const z: (number | null)[][] = [];
  const text: string[][] = [];

  for (const year of years) {
    const row: (number | null)[] = [];
    const textRow: string[] = [];
    for (let m = 1; m <= 12; m++) {
      const val = monthlyReturns[year]?.[String(m)] ?? null;
      row.push(val !== null ? val * 100 : null);
      textRow.push(val !== null ? `${(val * 100).toFixed(2)}%` : "");
    }
    z.push(row);
    text.push(textRow);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const traces: any[] = [
    {
      z,
      x: MONTH_LABELS,
      y: years,
      type: "heatmap",
      colorscale: [
        [0, "#ef4444"],
        [0.35, "#fca5a5"],
        [0.5, "#f8fafc"],
        [0.65, "#86efac"],
        [1, "#10b981"],
      ],
      text,
      texttemplate: "%{text}",
      textfont: { size: 9 },
      hovertemplate: "%{y} %{x}: %{text}<extra></extra>",
      showscale: true,
      colorbar: {
        title: { text: "Return %", font: { size: 10 } },
        ticksuffix: "%",
        thickness: 12,
        len: 0.8,
      },
      zmid: 0,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Returns Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <PlotlyChart
          data={traces}
          height={height}
          layout={{
            margin: { l: 50, r: 80, t: 10, b: 40 },
            yaxis: { autorange: "reversed" },
          }}
        />
      </CardContent>
    </Card>
  );
}
