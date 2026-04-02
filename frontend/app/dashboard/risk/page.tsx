"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { KpiCard } from "@/components/ui/kpi-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PlotlyChart, COLORS } from "@/components/charts/plotly-chart";
import { LoadingChart, LoadingGrid } from "@/components/ui/loading";
import { motion } from "framer-motion";
import { ShieldAlert, TrendingDown, BarChart3, AlertTriangle } from "lucide-react";
import type { Data } from "plotly.js";

const TICKERS = ["SPY", "QQQ", "IWM", "TLT", "IEF", "GLD", "XLF", "XLE", "XLK", "XLV"];

export default function RiskPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["risk"],
    queryFn: () => api.getRisk(TICKERS),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="space-y-6">
      <Header
        title="Risk Management"
        description="VaR, CVaR, stress testing, drawdown control, and risk decomposition"
        badge="Risk"
      />

      {/* KPIs */}
      {isLoading || !data ? (
        <LoadingGrid count={4} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard
            title="VaR 95%"
            value={formatPercent(data.var_95)}
            subtitle="Daily"
            icon={ShieldAlert}
            trend="down"
            delay={0}
          />
          <KpiCard
            title="CVaR 95%"
            value={formatPercent(data.cvar_95)}
            subtitle="Expected Shortfall"
            icon={AlertTriangle}
            trend="down"
            delay={0.05}
          />
          <KpiCard
            title="VaR 99%"
            value={formatPercent(data.var_99)}
            subtitle="Daily"
            icon={TrendingDown}
            trend="down"
            delay={0.1}
          />
          <KpiCard
            title="CVaR 99%"
            value={formatPercent(data.cvar_99)}
            subtitle="Extreme Tail"
            icon={BarChart3}
            trend="down"
            delay={0.15}
          />
        </div>
      )}

      {/* Rolling VaR / CVaR */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardHeader>
              <CardTitle>Rolling VaR & CVaR (252-day window, 95% confidence)</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.rolling_var.map((p) => p.date),
                    y: data.rolling_var.map((p) => p.value * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "VaR 95%",
                    line: { color: COLORS.warning, width: 1.5 },
                  } as Data,
                  {
                    x: data.rolling_cvar.map((p) => p.date),
                    y: data.rolling_cvar.map((p) => p.value * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "CVaR 95%",
                    line: { color: COLORS.loss, width: 1.5 },
                    fill: "tonexty",
                    fillcolor: "rgba(239, 68, 68, 0.05)",
                  } as Data,
                ]}
                height={300}
                layout={{
                  yaxis: { title: "Daily Loss %", ticksuffix: "%" },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Drawdown */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader>
              <CardTitle>Drawdown & Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.drawdown_series.map((p) => p.date),
                    y: data.drawdown_series.map((p) => p.value * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "Drawdown",
                    line: { color: COLORS.loss, width: 1.5 },
                    fill: "tozeroy",
                    fillcolor: "rgba(239, 68, 68, 0.1)",
                  } as Data,
                ]}
                height={280}
                layout={{
                  yaxis: { title: "Drawdown %", ticksuffix: "%" },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Risk Contributions */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Risk Contribution by Asset</CardTitle>
              </CardHeader>
              <CardContent>
                <PlotlyChart
                  data={[
                    {
                      labels: Object.keys(data.risk_contributions),
                      values: Object.values(data.risk_contributions).map((v) => v * 100),
                      type: "pie",
                      hole: 0.55,
                      marker: {
                        colors: COLORS.series.slice(0, Object.keys(data.risk_contributions).length),
                      },
                      textinfo: "label+percent",
                      textfont: { size: 10 },
                      hovertemplate: "%{label}: %{value:.1f}%<extra></extra>",
                    } as Data,
                  ]}
                  height={320}
                  layout={{
                    margin: { l: 10, r: 10, t: 10, b: 10 },
                    showlegend: false,
                  }}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Stress Test Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[320px] overflow-auto">
                  {data.stress_tests.map((st) => (
                    <div
                      key={st.scenario}
                      className="flex items-center justify-between p-3 rounded-md bg-muted/50"
                    >
                      <div>
                        <p className="text-sm font-medium">{st.scenario}</p>
                        <p className="text-[10px] text-muted-foreground">{st.period}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-sm font-mono ${st.cumulative_return >= 0 ? "text-emerald-400" : "text-red-400"}`}
                        >
                          {formatPercent(st.cumulative_return)}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          DD: {formatPercent(st.max_drawdown)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      )}

      {/* Rolling Volatility */}
      {isLoading || !data ? (
        <LoadingChart />
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <Card>
            <CardHeader>
              <CardTitle>Rolling Volatility (63-day)</CardTitle>
            </CardHeader>
            <CardContent>
              <PlotlyChart
                data={[
                  {
                    x: data.rolling_vol.map((p) => p.date),
                    y: data.rolling_vol.map((p) => p.value * 100),
                    type: "scatter",
                    mode: "lines",
                    name: "Rolling Vol",
                    line: { color: COLORS.warning, width: 1.5 },
                    fill: "tozeroy",
                    fillcolor: "rgba(245, 158, 11, 0.06)",
                  } as Data,
                ]}
                height={280}
                layout={{
                  yaxis: { title: "Annualized Vol %", ticksuffix: "%" },
                }}
              />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
