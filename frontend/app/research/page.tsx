"use client";

import { useEffect, useRef } from "react";
import { Header } from "@/components/layout/header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { motion } from "framer-motion";

function LaTeX({ math, display = false }: { math: string; display?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (ref.current) {
      import("katex").then((katex) => {
        katex.default.render(math, ref.current!, {
          throwOnError: false,
          displayMode: display,
        });
      });
    }
  }, [math, display]);

  return <span ref={ref} />;
}

function Section({
  title,
  children,
  delay = 0,
}: {
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm dark:prose-invert max-w-none">
          {children}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function ResearchPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <Header
        title="Research"
        description="Mathematical foundations and methodology of the TSMOM strategy"
        badge="Docs"
      />

      <Section title="1. What is Time-Series Momentum (TSMOM)?" delay={0}>
        <p>
          <strong>Time-Series Momentum (TSMOM)</strong> is a quantitative trading strategy that goes
          long assets with positive recent returns and short assets with negative recent returns.
          Unlike cross-sectional momentum (which ranks assets relative to each other), TSMOM uses
          each asset&apos;s <em>own past performance</em> as the signal.
        </p>
        <p>
          The foundational paper by <strong>Moskowitz, Ooi & Pedersen (2012)</strong> — &quot;Time
          Series Momentum&quot; published in the <em>Journal of Financial Economics</em> —
          demonstrated that TSMOM generates significant positive returns across 58 liquid instruments
          spanning equities, bonds, commodities, and currencies over multiple decades.
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <p className="text-xs text-muted-foreground mb-2">Core TSMOM Signal</p>
          <LaTeX
            math="s_{i,t} = \text{sign}\left(\sum_{\tau=t-k-1}^{t-1} r_{i,\tau}\right)"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            where <LaTeX math="r_{i,\tau}" /> is the return of asset <LaTeX math="i" /> at time{" "}
            <LaTeX math="\tau" />, and <LaTeX math="k" /> is the lookback window.
          </p>
        </div>
      </Section>

      <Section title="2. Why Does Momentum Work?" delay={0.05}>
        <p>Several explanations exist for why momentum persists across markets and time periods:</p>
        <ul>
          <li>
            <strong>Behavioral biases</strong>: Investors underreact to new information initially
            (anchoring, disposition effect) and then overreact as trends become obvious (herding,
            confirmation bias), creating persistent price trends.
          </li>
          <li>
            <strong>Market microstructure</strong>: Institutional investors often trade gradually
            (splitting large orders over days/weeks), causing delayed price adjustment.
          </li>
          <li>
            <strong>Risk compensation</strong>: Momentum may represent compensation for bearing
            &quot;crash risk&quot; — momentum strategies are vulnerable to sharp reversals (momentum
            crashes).
          </li>
          <li>
            <strong>Positive feedback loops</strong>: Risk management practices like stop-losses and
            portfolio insurance amplify trends, especially in volatile markets.
          </li>
        </ul>
      </Section>

      <Section title="3. Continuous TSMOM Signal" delay={0.1}>
        <p>
          Rather than a binary long/short signal, we use a <strong>continuous signal</strong> that
          scales position size by trend strength. This risk-adjusts the momentum by dividing by
          realized volatility:
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="s_{i,t}^{\text{cont}} = \frac{\sum_{\tau=t-k-1}^{t-1} r_{i,\tau}}{\sigma_{i,t} \cdot \sqrt{252}}"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            This produces a signal proportional to the Sharpe ratio of the asset over the lookback
            window.
          </p>
        </div>
      </Section>

      <Section title="4. Multi-Horizon Blending" delay={0.15}>
        <p>
          Different lookback windows capture different trend frequencies. We blend signals across
          multiple horizons using equal weights (or custom weights):
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="s_{i,t}^{\text{blend}} = \sum_{j=1}^{J} w_j \cdot s_{i,t}^{(k_j)}, \quad \text{where } \sum_{j} w_j = 1"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            Default lookbacks: <LaTeX math="k \in \{21, 63, 126, 252\}" /> trading days (approx.
            1M, 3M, 6M, 12M).
          </p>
        </div>
        <p>
          The blended signal is then passed through a post-processing pipeline:
        </p>
        <ol>
          <li>
            <strong>Exponential smoothing</strong> (halflife = 5 days) — reduces noise and turnover
          </li>
          <li>
            <strong>Z-score normalization</strong> (252-day rolling window) — standardizes signal
            scale
          </li>
          <li>
            <strong>Signal capping</strong> ([-2, +2]) — limits extreme bets
          </li>
        </ol>
      </Section>

      <Section title="5. Volatility-Targeting (Position Sizing)" delay={0.2}>
        <p>
          The Moskowitz-Ooi-Pedersen (MOP) volatility-targeting approach ensures each asset
          contributes roughly equal risk to the portfolio, regardless of its inherent volatility:
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="w_{i,t} = s_{i,t} \cdot \frac{\sigma_{\text{target}} / N}{\hat{\sigma}_{i,t}}"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            where <LaTeX math="\sigma_{\text{target}}" /> is the portfolio volatility target
            (default 10%), <LaTeX math="N" /> is the number of assets, and{" "}
            <LaTeX math="\hat{\sigma}_{i,t}" /> is the realized volatility estimate for asset{" "}
            <LaTeX math="i" />.
          </p>
        </div>
        <p>
          <strong>Intuition</strong>: A highly volatile asset (e.g., natural gas) gets a smaller
          position than a low-volatility asset (e.g., treasury bonds), so each contributes similar
          risk.
        </p>
      </Section>

      <Section title="6. Regime Detection (Hidden Markov Model)" delay={0.25}>
        <p>
          Academic research shows TSMOM alpha concentrates in <strong>trending regimes</strong> and
          can be negative in mean-reverting markets. We use a two-state Gaussian Hidden Markov Model
          (HMM) to classify the market:
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="r_t \mid S_t = k \sim \mathcal{N}(\mu_k, \sigma_k^2), \quad S_t \in \{0, 1\}"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            State transitions follow: <LaTeX math="P(S_t = j \mid S_{t-1} = i) = a_{ij}" />
          </p>
        </div>
        <ul>
          <li>
            <strong>State 0 (Trending)</strong>: Higher absolute mean returns. Momentum signals at
            full strength.
          </li>
          <li>
            <strong>State 1 (Mean-Reverting)</strong>: Lower absolute mean returns, choppy price
            action. Signals dampened to 30% strength.
          </li>
        </ul>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <p className="text-xs text-muted-foreground mb-2">Regime-Aware Signal Scaling</p>
          <LaTeX
            math="s_{i,t}^{\text{regime}} = s_{i,t}^{\text{blend}} \cdot (0.3 + 0.7 \cdot P(\text{trending} \mid r_{1:t}))"
            display
          />
        </div>
      </Section>

      <Section title="7. Drawdown Control Overlay" delay={0.3}>
        <p>
          The single most important production risk feature. Momentum strategies are vulnerable to
          <strong> momentum crashes</strong> — sharp, sudden trend reversals that can wipe months of
          gains. The drawdown control overlay dynamically reduces position sizes when the portfolio
          enters drawdown:
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="\text{scale}_t = \max\left(\text{floor}, \; 1 - \frac{|\text{DD}_t| - \theta}{\theta}\right)"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            where <LaTeX math="\text{DD}_t" /> is current drawdown,{" "}
            <LaTeX math="\theta = 10\%" /> is the threshold, and floor = 25% ensures we never
            fully exit.
          </p>
        </div>
        <ul>
          <li>Drawdown {"<"} 10%: No scaling, full positions</li>
          <li>Drawdown = 15%: Positions scaled to ~50%</li>
          <li>Drawdown = 20%+: Positions at floor (25%)</li>
        </ul>
      </Section>

      <Section title="8. Transaction Costs" delay={0.35}>
        <p>
          Many strategies that look profitable before costs are unprofitable after. We model
          realistic transaction costs:
        </p>
        <div className="bg-muted/50 rounded-lg p-4 my-4 text-center">
          <LaTeX
            math="\text{cost}_t = \sum_{i=1}^{N} |\Delta w_{i,t}| \cdot \frac{c_{\text{slip}} + c_{\text{comm}}}{10000}"
            display
          />
          <p className="text-xs text-muted-foreground mt-2">
            Default: 5 bps slippage + 1 bps commission = 6 bps per unit of turnover.
          </p>
        </div>
      </Section>

      <Section title="9. Risk Metrics" delay={0.4}>
        <p>
          The system computes 30+ risk/return metrics. Key definitions:
        </p>
        <div className="space-y-3">
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Sharpe Ratio (annualized)</p>
            <LaTeX math="\text{SR} = \frac{E[r - r_f]}{\sigma_r} \cdot \sqrt{252}" display />
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Sortino Ratio</p>
            <LaTeX
              math="\text{Sortino} = \frac{E[r - r_f]}{\sigma_{\text{downside}}} \cdot \sqrt{252}"
              display
            />
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Value-at-Risk (95%)</p>
            <LaTeX math="\text{VaR}_{0.95} = F^{-1}(0.05)" display />
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Conditional VaR (Expected Shortfall)</p>
            <LaTeX
              math="\text{CVaR}_{0.95} = E[r \mid r \leq \text{VaR}_{0.95}]"
              display
            />
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Calmar Ratio</p>
            <LaTeX math="\text{Calmar} = \frac{\text{CAGR}}{|\text{Max Drawdown}|}" display />
          </div>
        </div>
      </Section>

      <Section title="10. Glossary of Terms" delay={0.45}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            ["TSMOM", "Time-Series Momentum — trading based on an asset's own past return"],
            ["CAGR", "Compound Annual Growth Rate — annualized return accounting for compounding"],
            ["Sharpe Ratio", "Risk-adjusted return: excess return per unit of volatility"],
            ["Sortino Ratio", "Like Sharpe but only penalizes downside volatility"],
            ["Max Drawdown", "Largest peak-to-trough decline in portfolio value"],
            ["VaR", "Value-at-Risk — maximum expected loss at a confidence level"],
            ["CVaR", "Conditional VaR (Expected Shortfall) — average loss beyond VaR"],
            ["HMM", "Hidden Markov Model — probabilistic model for latent state detection"],
            ["Vol Target", "Target annualized portfolio volatility (e.g., 10%)"],
            ["Lookback", "Period of historical returns used to compute momentum signal"],
            ["Turnover", "Total absolute weight changes — drives transaction costs"],
            ["Gross Exposure", "Sum of absolute position weights — can exceed 100% with leverage"],
            ["Net Exposure", "Sum of signed positions — market directionality"],
            ["Regime", "Market state classification (trending vs mean-reverting)"],
            ["Drawdown Control", "Dynamic position scaling based on current portfolio drawdown"],
            ["Signal Capping", "Limiting signal magnitude to [-2, +2] to prevent extreme bets"],
          ].map(([term, def]) => (
            <div key={term} className="p-3 rounded-md bg-muted/50">
              <p className="text-xs font-semibold text-primary">{term}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{def}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="11. References" delay={0.5}>
        <ol className="text-xs space-y-2">
          <li>
            Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time Series Momentum.{" "}
            <em>Journal of Financial Economics</em>, 104(2), 228-250.
          </li>
          <li>
            Baltas, A. N., & Kosowski, R. (2013). Momentum Strategies in Futures Markets and
            Trend-Following Funds. Working Paper.
          </li>
          <li>
            Barroso, P., & Santa-Clara, P. (2015). Momentum Has Its Moments.{" "}
            <em>Journal of Financial Economics</em>, 116(1), 111-120.
          </li>
          <li>
            Daniel, K., & Moskowitz, T. J. (2016). Momentum Crashes.{" "}
            <em>Journal of Financial Economics</em>, 122(2), 221-247.
          </li>
          <li>
            Kim, A. Y., Tse, Y., & Wald, J. K. (2016). Time Series Momentum and Volatility
            Scaling. <em>Journal of Financial Markets</em>, 30, 103-124.
          </li>
        </ol>
      </Section>
    </div>
  );
}
