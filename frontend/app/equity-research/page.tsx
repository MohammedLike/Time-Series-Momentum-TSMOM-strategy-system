"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type AssetReport } from "@/lib/api";
import { formatPercent, formatNumber, formatCurrency, cn } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading";
import { PlotlyChart, COLORS } from "@/components/charts/plotly-chart";
import { motion, AnimatePresence } from "framer-motion";
import type { Data } from "plotly.js";
import {
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Target,
  Activity,
  Brain,
} from "lucide-react";

const ALL_TICKERS = [
  "SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV",
  "XLP", "XLU", "XLY", "XLI", "XLRE", "SLV", "DBA", "USO", "UNG", "HYG",
  "LQD", "SHY", "UUP", "FXA", "FXB", "FXE", "FXY",
];

const PRESETS: Record<string, string[]> = {
  "Core Portfolio": ["SPY", "QQQ", "TLT", "GLD", "IEF"],
  "Growth Focus": ["SPY", "QQQ", "IWM", "XLK", "XLV", "XLY"],
  "Income & Safety": ["TLT", "IEF", "HYG", "LQD", "SHY", "XLU", "XLP"],
  "Commodities": ["GLD", "SLV", "USO", "UNG", "DBA"],
  "All Assets": ALL_TICKERS,
};

function RecommendationIcon({ rec }: { rec: string }) {
  if (rec === "Favorable") return <CheckCircle className="w-5 h-5 text-emerald-400" />;
  if (rec === "Unfavorable") return <XCircle className="w-5 h-5 text-red-400" />;
  return <Minus className="w-5 h-5 text-yellow-400" />;
}

function SignalBar({ value }: { value: number }) {
  const pct = Math.min(Math.abs(value) / 2, 1) * 100;
  const isPositive = value > 0;
  return (
    <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
      <div
        className={cn(
          "h-full rounded-full transition-all duration-700",
          isPositive ? "bg-emerald-500" : "bg-red-500"
        )}
        style={{
          width: `${pct}%`,
          marginLeft: isPositive ? "50%" : `${50 - pct}%`,
        }}
      />
    </div>
  );
}

function AssetCard({ asset, index }: { asset: AssetReport; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, type: "spring", stiffness: 100 }}
    >
      <Card
        className={cn(
          "overflow-hidden transition-all duration-300 cursor-pointer",
          asset.recommendation === "Favorable" && "border-emerald-500/20 glow-profit",
          asset.recommendation === "Unfavorable" && "border-red-500/20 glow-loss"
        )}
        onClick={() => setExpanded(!expanded)}
      >
        <CardContent className="p-5">
          {/* Header row */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <RecommendationIcon rec={asset.recommendation} />
              <div>
                <span className="text-lg font-bold font-mono">{asset.ticker}</span>
                <Badge
                  className="ml-2 text-[9px]"
                  variant={
                    asset.recommendation === "Favorable"
                      ? "profit"
                      : asset.recommendation === "Unfavorable"
                        ? "loss"
                        : "secondary"
                  }
                >
                  {asset.recommendation}
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className={cn(
                  "text-lg font-bold font-mono",
                  asset.annualized_return > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {formatPercent(asset.annualized_return)}
                </p>
                <p className="text-[10px] text-muted-foreground">Annual Return</p>
              </div>
              {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
            </div>
          </div>

          {/* Signal bar */}
          <div className="mb-3">
            <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
              <span>Bearish</span>
              <span>Signal: {formatNumber(asset.current_signal)}</span>
              <span>Bullish</span>
            </div>
            <SignalBar value={asset.current_signal} />
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xs text-muted-foreground">Sharpe</p>
              <p className="text-sm font-mono font-semibold">{formatNumber(asset.sharpe_ratio)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Risk</p>
              <p className={cn("text-sm font-semibold",
                asset.risk_level === "Low" || asset.risk_level === "Very Low" ? "text-emerald-400" :
                asset.risk_level === "High" || asset.risk_level === "Very High" ? "text-red-400" : "text-yellow-400"
              )}>{asset.risk_level}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Max DD</p>
              <p className="text-sm font-mono font-semibold text-red-400">{formatPercent(asset.max_drawdown)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">3M Return</p>
              <p className={cn("text-sm font-mono font-semibold",
                asset.recent_3m_return > 0 ? "text-emerald-400" : "text-red-400"
              )}>{formatPercent(asset.recent_3m_return)}</p>
            </div>
          </div>

          {/* Expanded details */}
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="mt-4 pt-4 border-t border-border/30 space-y-3">
                  <div className="flex items-start gap-2 p-3 rounded-xl bg-muted/30">
                    <Info className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium mb-1">Momentum Analysis</p>
                      <p className="text-sm text-muted-foreground">{asset.momentum_verdict}</p>
                    </div>
                  </div>
                  <div className={cn(
                    "flex items-start gap-2 p-3 rounded-xl",
                    asset.recommendation === "Favorable" ? "bg-emerald-500/5" :
                    asset.recommendation === "Unfavorable" ? "bg-red-500/5" : "bg-yellow-500/5"
                  )}>
                    <Target className="w-4 h-4 mt-0.5 flex-shrink-0 text-primary" />
                    <div>
                      <p className="text-sm font-medium mb-1">Recommendation</p>
                      <p className="text-sm text-muted-foreground">{asset.recommendation_detail}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground">Volatility</p>
                      <p className="text-sm font-mono">{formatPercent(asset.current_vol)}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground">Total Return</p>
                      <p className="text-sm font-mono">{formatPercent(asset.total_return)}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-muted/30">
                      <p className="text-[10px] text-muted-foreground">Current Weight</p>
                      <p className="text-sm font-mono">{formatPercent(asset.current_weight)}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function EquityResearchPage() {
  const [selectedPreset, setSelectedPreset] = useState("Core Portfolio");
  const tickers = PRESETS[selectedPreset];

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["research-report", selectedPreset],
    queryFn: () => api.getResearchReport(tickers),
    staleTime: 10 * 60 * 1000,
  });

  return (
    <div className="space-y-6 max-w-6xl">
      <Header
        title="Equity Research Report"
        description="Plain-English investment analysis — no jargon, just clear insights"
        badge="AI-Powered"
      />

      {/* Preset selector */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-muted-foreground font-medium mr-1">Portfolio:</span>
            {Object.keys(PRESETS).map((preset) => (
              <Button
                key={preset}
                variant={selectedPreset === preset ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedPreset(preset)}
                className="text-xs"
              >
                {preset}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <div className="py-16">
          <LoadingSpinner />
          <p className="text-center text-sm text-muted-foreground mt-4">
            Analyzing {tickers.length} assets across {new Date().getFullYear() - 2005}+ years of data...
          </p>
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="p-8 text-center">
            <AlertTriangle className="w-10 h-10 text-destructive mx-auto mb-3" />
            <p className="text-sm text-destructive mb-2">Failed to generate report</p>
            <p className="text-xs text-muted-foreground mb-4">
              Make sure the backend is running at localhost:8000
            </p>
            <Button size="sm" onClick={() => refetch()}>Retry</Button>
          </CardContent>
        </Card>
      )}

      {data && (
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Executive Summary */}
          <Card className="border-gradient">
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <CardTitle>Executive Summary</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <h2 className="text-xl font-bold text-gradient">
                {data.summary.headline}
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {data.summary.plain_english}
              </p>

              {/* Grade cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <div className="p-3 rounded-xl bg-muted/30 text-center">
                  <BarChart3 className="w-5 h-5 mx-auto mb-1.5 text-primary" />
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Portfolio Grade</p>
                  <p className={cn("text-lg font-bold",
                    data.summary.portfolio_grade === "Excellent" ? "text-emerald-400" :
                    data.summary.portfolio_grade === "Good" ? "text-emerald-300" :
                    data.summary.portfolio_grade === "Fair" ? "text-yellow-400" : "text-red-400"
                  )}>{data.summary.portfolio_grade}</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/30 text-center">
                  <Shield className="w-5 h-5 mx-auto mb-1.5 text-primary" />
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Risk Profile</p>
                  <p className="text-lg font-bold">{data.summary.risk_profile}</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/30 text-center">
                  <Zap className="w-5 h-5 mx-auto mb-1.5 text-primary" />
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Market Regime</p>
                  <p className={cn("text-lg font-bold",
                    data.summary.market_regime === "Trending" ? "text-emerald-400" : "text-yellow-400"
                  )}>{data.summary.market_regime}</p>
                </div>
                <div className="p-3 rounded-xl bg-muted/30 text-center">
                  <Activity className="w-5 h-5 mx-auto mb-1.5 text-primary" />
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Assets Analyzed</p>
                  <p className="text-lg font-bold">{data.n_assets}</p>
                </div>
              </div>

              {/* Regime explanation */}
              <div className={cn(
                "flex items-start gap-3 p-4 rounded-xl mt-2",
                data.summary.market_regime === "Trending"
                  ? "bg-emerald-500/5 border border-emerald-500/20"
                  : "bg-yellow-500/5 border border-yellow-500/20"
              )}>
                <Brain className={cn("w-5 h-5 mt-0.5 flex-shrink-0",
                  data.summary.market_regime === "Trending" ? "text-emerald-400" : "text-yellow-400"
                )} />
                <p className="text-sm text-muted-foreground">{data.summary.regime_explanation}</p>
              </div>
            </CardContent>
          </Card>

          {/* Key Takeaways */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-primary" />
                <CardTitle>Key Takeaways</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {data.summary.key_takeaways.map((takeaway, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-2.5 p-3 rounded-xl bg-muted/30"
                  >
                    <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-[10px] font-bold text-primary">{i + 1}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{takeaway}</p>
                  </motion.div>
                ))}
              </div>
              <div className="mt-4 p-4 rounded-xl bg-primary/5 border border-primary/10">
                <p className="text-sm font-medium mb-1 flex items-center gap-2">
                  <Info className="w-4 h-4 text-primary" />
                  What should I do?
                </p>
                <p className="text-sm text-muted-foreground">{data.summary.what_to_do}</p>
              </div>
            </CardContent>
          </Card>

          {/* Metrics Explained */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                <CardTitle>Your Numbers — Explained Simply</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(data.metrics_explained).map(([key, metric], i) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-4 rounded-xl bg-muted/30 space-y-1.5"
                  >
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{metric.label}</p>
                    <p className="text-xl font-bold font-mono">
                      {key.includes("return") || key.includes("drawdown") || key.includes("vol") || key.includes("hit")
                        ? formatPercent(metric.value)
                        : formatNumber(metric.value)}
                    </p>
                    <p className="text-xs text-muted-foreground leading-relaxed">{metric.explanation}</p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Signal Overview Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                <CardTitle>Current Momentum Signals</CardTitle>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Green = upward momentum (bullish), Red = downward momentum (bearish)
              </p>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    type: "bar",
                    x: data.asset_reports.map((a) => a.current_signal),
                    y: data.asset_reports.map((a) => a.ticker),
                    orientation: "h",
                    marker: {
                      color: data.asset_reports.map((a) =>
                        a.current_signal > 0.1 ? COLORS.profit :
                        a.current_signal < -0.1 ? COLORS.loss : COLORS.slate
                      ),
                      line: { width: 0 },
                    },
                    hovertemplate: "%{y}: %{x:.2f}<extra></extra>",
                  } as Data,
                ]}
                height={Math.max(250, data.asset_reports.length * 32)}
                layout={{
                  margin: { l: 55, r: 20, t: 10, b: 30 },
                  xaxis: { title: "Signal Strength", range: [-2.5, 2.5] },
                  yaxis: { autorange: "reversed" },
                  shapes: [{
                    type: "line",
                    x0: 0, x1: 0,
                    y0: -0.5, y1: data.asset_reports.length - 0.5,
                    line: { color: "rgba(100,116,139,0.3)", width: 1, dash: "dash" },
                  }],
                }}
              />
            </CardContent>
          </Card>

          {/* Individual Asset Reports */}
          <div>
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Individual Asset Analysis
              <span className="text-xs text-muted-foreground font-normal ml-2">
                Click any card for details
              </span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.asset_reports.map((asset, i) => (
                <AssetCard key={asset.ticker} asset={asset} index={i} />
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="text-center py-6 text-xs text-muted-foreground/60 space-y-1">
            <p>Report generated: {data.generated_at} | Data period: {data.data_period}</p>
            <p>This is a quantitative model output, not financial advice. Past performance does not guarantee future results.</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
