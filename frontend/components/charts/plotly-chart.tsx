"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import type { Data, Layout, Config } from "plotly.js";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

// Institutional color palette
export const COLORS = {
  primary: "#6366f1",
  secondary: "#8b5cf6",
  profit: "#10b981",
  loss: "#ef4444",
  warning: "#f59e0b",
  blue: "#3b82f6",
  cyan: "#06b6d4",
  orange: "#f97316",
  pink: "#ec4899",
  slate: "#64748b",
  series: [
    "#6366f1", "#3b82f6", "#06b6d4", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#8b5cf6", "#f97316", "#64748b",
    "#14b8a6", "#a855f7", "#f43f5e", "#0ea5e9", "#84cc16",
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
      gridcolor: isDark ? "#1e293b" : "#f1f5f9",
      zerolinecolor: isDark ? "#334155" : "#e2e8f0",
      showgrid: true,
      gridwidth: 1,
    },
    yaxis: {
      gridcolor: isDark ? "#1e293b" : "#f1f5f9",
      zerolinecolor: isDark ? "#334155" : "#e2e8f0",
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
      bgcolor: isDark ? "#1e293b" : "#ffffff",
      bordercolor: isDark ? "#334155" : "#e2e8f0",
      font: { size: 11, color: isDark ? "#e2e8f0" : "#1e293b" },
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
