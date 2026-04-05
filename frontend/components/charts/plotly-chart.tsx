"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import type { Data, Config } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export const COLORS = {
  primary: "#7c3aed",
  secondary: "#a855f7",
  profit: "#10b981",
  loss: "#ef4444",
  warning: "#f59e0b",
  blue: "#3b82f6",
  cyan: "#06b6d4",
  orange: "#f97316",
  pink: "#ec4899",
  slate: "#64748b",
  series: [
    "#7c3aed", "#3b82f6", "#06b6d4", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#a855f7", "#f97316", "#64748b",
    "#14b8a6", "#8b5cf6", "#f43f5e", "#0ea5e9", "#84cc16",
  ],
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type LooseLayout = Record<string, any>;

interface PlotlyChartProps {
  data: Data[];
  layout?: LooseLayout;
  config?: Partial<Config>;
  height?: number;
  className?: string;
}

export function PlotlyChart({
  data,
  layout = {},
  config = {},
  height = 350,
  className,
}: PlotlyChartProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const baseLayout: LooseLayout = {
    autosize: true,
    height,
    margin: { l: 50, r: 20, t: 10, b: 40 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: {
      family: "Inter, system-ui, sans-serif",
      size: 11,
      color: isDark ? "#94a3b8" : "#64748b",
    },
    xaxis: {
      gridcolor: isDark ? "rgba(148,163,184,0.06)" : "rgba(100,116,139,0.08)",
      zerolinecolor: isDark ? "rgba(148,163,184,0.1)" : "rgba(100,116,139,0.12)",
      showgrid: true,
      gridwidth: 1,
    },
    yaxis: {
      gridcolor: isDark ? "rgba(148,163,184,0.06)" : "rgba(100,116,139,0.08)",
      zerolinecolor: isDark ? "rgba(148,163,184,0.1)" : "rgba(100,116,139,0.12)",
      showgrid: true,
      gridwidth: 1,
    },
    legend: {
      bgcolor: "transparent",
      font: { size: 10, color: isDark ? "#94a3b8" : "#64748b" },
      orientation: "h",
      yanchor: "bottom",
      y: 1.02,
      xanchor: "right",
      x: 1,
    },
    hoverlabel: {
      bgcolor: isDark ? "rgba(15,23,42,0.95)" : "rgba(255,255,255,0.95)",
      bordercolor: isDark ? "rgba(124,58,237,0.3)" : "rgba(124,58,237,0.2)",
      font: { size: 11, color: isDark ? "#e2e8f0" : "#1e293b", family: "Inter" },
    },
    hovermode: "x unified",
    ...layout,
  };

  const baseConfig: Partial<Config> = {
    displayModeBar: false,
    responsive: true,
    ...config,
  };

  return (
    <div className={className}>
      <Plot
        data={data}
        layout={baseLayout}
        config={baseConfig}
        useResizeHandler
        style={{ width: "100%", height: `${height}px` }}
      />
    </div>
  );
}
