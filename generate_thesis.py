"""Generate comprehensive thesis-level PDF documentation for the TSMOM project."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image, KeepTogether, HRFlowable, ListFlowable, ListItem,
)
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import datetime

# ─── Colors ──────────────────────────────────────────────────────────
PRIMARY = HexColor("#1e293b")
ACCENT = HexColor("#6366f1")
LIGHT_BG = HexColor("#f8fafc")
BORDER = HexColor("#e2e8f0")
MUTED = HexColor("#64748b")
PROFIT = HexColor("#10b981")
LOSS = HexColor("#ef4444")
WHITE = white
BLACK = black

W, H = A4

# ─── Custom Styles ───────────────────────────────────────────────────
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="ThesisTitle",
    fontName="Helvetica-Bold",
    fontSize=28,
    leading=34,
    textColor=PRIMARY,
    alignment=TA_CENTER,
    spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="ThesisSubtitle",
    fontName="Helvetica",
    fontSize=14,
    leading=18,
    textColor=MUTED,
    alignment=TA_CENTER,
    spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="ChapterTitle",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=26,
    textColor=PRIMARY,
    spaceBefore=20,
    spaceAfter=14,
    borderWidth=0,
    borderColor=ACCENT,
    borderPadding=0,
))
styles.add(ParagraphStyle(
    name="SectionTitle",
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    textColor=PRIMARY,
    spaceBefore=16,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="SubSection",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=HexColor("#334155"),
    spaceBefore=12,
    spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Body",
    fontName="Helvetica",
    fontSize=10,
    leading=15,
    textColor=HexColor("#1e293b"),
    alignment=TA_JUSTIFY,
    spaceAfter=8,
    firstLineIndent=0,
))
styles.add(ParagraphStyle(
    name="BodyIndent",
    parent=styles["Body"],
    leftIndent=20,
))
styles.add(ParagraphStyle(
    name="Equation",
    fontName="Courier",
    fontSize=10,
    leading=14,
    textColor=HexColor("#1e293b"),
    alignment=TA_CENTER,
    spaceBefore=10,
    spaceAfter=10,
    backColor=LIGHT_BG,
    borderWidth=0.5,
    borderColor=BORDER,
    borderPadding=8,
))
styles.add(ParagraphStyle(
    name="CodeBlock",
    fontName="Courier",
    fontSize=8.5,
    leading=12,
    textColor=HexColor("#1e293b"),
    backColor=LIGHT_BG,
    borderWidth=0.5,
    borderColor=BORDER,
    borderPadding=8,
    spaceBefore=6,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Caption",
    fontName="Helvetica-Oblique",
    fontSize=9,
    leading=12,
    textColor=MUTED,
    alignment=TA_CENTER,
    spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="TOCEntry",
    fontName="Helvetica",
    fontSize=11,
    leading=20,
    textColor=PRIMARY,
    leftIndent=10,
))
styles.add(ParagraphStyle(
    name="TOCSubEntry",
    fontName="Helvetica",
    fontSize=10,
    leading=18,
    textColor=MUTED,
    leftIndent=30,
))
styles.add(ParagraphStyle(
    name="Footer",
    fontName="Helvetica",
    fontSize=8,
    textColor=MUTED,
    alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name="BulletBody",
    parent=styles["Body"],
    leftIndent=24,
    bulletIndent=12,
    spaceBefore=2,
    spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="TableCell",
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    textColor=PRIMARY,
))
styles.add(ParagraphStyle(
    name="TableHeader",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=WHITE,
))
styles.add(ParagraphStyle(
    name="Note",
    fontName="Helvetica-Oblique",
    fontSize=9,
    leading=13,
    textColor=MUTED,
    leftIndent=20,
    rightIndent=20,
    spaceBefore=8,
    spaceAfter=8,
    backColor=HexColor("#f1f5f9"),
    borderWidth=0.5,
    borderColor=BORDER,
    borderPadding=8,
))


def heading_line():
    return HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=2, spaceAfter=12)


def thin_line():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=6, spaceAfter=6)


def bullet(text):
    return Paragraph(f"<bullet>&bull;</bullet> {text}", styles["BulletBody"])


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    h = [[Paragraph(h, styles["TableHeader"]) for h in headers]]
    r = [[Paragraph(str(c), styles["TableCell"]) for c in row] for row in rows]
    data = h + r

    w = col_widths or [None] * len(headers)
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]))
    return t


# ─── Page Templates ──────────────────────────────────────────────────
def on_page(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(MUTED)
    canvas_obj.drawString(doc.leftMargin, 25, "TSMOM Quantitative Strategy Platform")
    canvas_obj.drawRightString(W - doc.rightMargin, 25, f"Page {doc.page}")
    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.line(doc.leftMargin, 38, W - doc.rightMargin, 38)
    canvas_obj.restoreState()


def on_first_page(canvas_obj, doc):
    pass  # No header/footer on cover page


# ─── Build Document ──────────────────────────────────────────────────
def build_thesis():
    output_path = "D:/claude projects/time series momentum/TSMOM_Thesis_Documentation.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
    )

    story = []

    # ═══════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.5 * inch))
    story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=20))
    story.append(Paragraph("Time-Series Momentum", styles["ThesisTitle"]))
    story.append(Paragraph("Quantitative Strategy Platform", styles["ThesisTitle"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=20))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Comprehensive Technical Documentation &amp; Research Thesis", styles["ThesisSubtitle"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("A Production-Grade, Institutional-Quality System for", styles["ThesisSubtitle"]))
    story.append(Paragraph("Multi-Asset Momentum Trading with Regime Detection", styles["ThesisSubtitle"]))
    story.append(Spacer(1, 1.2 * inch))

    cover_info = [
        ["Platform", "TSMOM Quant Platform v1.0"],
        ["Architecture", "FastAPI + Next.js + Python Quant Engine"],
        ["Assets", "27 ETFs across Equities, Commodities, Fixed Income, FX"],
        ["Framework", "Moskowitz, Ooi &amp; Pedersen (2012)"],
        ["Date", datetime.datetime.now().strftime("%B %d, %Y")],
    ]
    cover_table = Table(cover_info, colWidths=[1.5 * inch, 3.5 * inch])
    cover_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("RIGHTPADDING", (0, 0), (0, -1), 12),
    ]))
    story.append(cover_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("Table of Contents", styles["ChapterTitle"]))
    story.append(heading_line())

    toc_entries = [
        ("1", "Introduction &amp; Motivation"),
        ("2", "Theoretical Foundations"),
        ("  2.1", "Time-Series Momentum (TSMOM)"),
        ("  2.2", "Why Momentum Works"),
        ("  2.3", "Momentum Crashes &amp; Risk"),
        ("3", "Signal Generation Pipeline"),
        ("  3.1", "Binary TSMOM Signal"),
        ("  3.2", "Continuous TSMOM Signal"),
        ("  3.3", "Multi-Horizon Blending"),
        ("  3.4", "Signal Post-Processing"),
        ("4", "Regime Detection"),
        ("  4.1", "Hidden Markov Model (HMM)"),
        ("  4.2", "Regime-Aware Signal Scaling"),
        ("5", "Volatility Estimation"),
        ("6", "Portfolio Construction"),
        ("  6.1", "Volatility Targeting (MOP)"),
        ("  6.2", "Constraint Enforcement"),
        ("  6.3", "Rebalance Scheduling"),
        ("7", "Risk Management"),
        ("  7.1", "Drawdown Control Overlay"),
        ("  7.2", "Value-at-Risk &amp; CVaR"),
        ("  7.3", "Historical Stress Testing"),
        ("8", "Backtesting Engine"),
        ("  8.1", "Vectorized Architecture"),
        ("  8.2", "Walk-Forward Validation"),
        ("  8.3", "Transaction Cost Modeling"),
        ("9", "System Architecture"),
        ("  9.1", "Backend (FastAPI)"),
        ("  9.2", "Frontend (Next.js)"),
        ("  9.3", "Data Pipeline"),
        ("10", "Web Application Features"),
        ("  10.1", "Strategy Dashboard"),
        ("  10.2", "Signal Engine Visualization"),
        ("  10.3", "Regime Detection Panel"),
        ("  10.4", "Risk Management Module"),
        ("  10.5", "Backtest Laboratory"),
        ("  10.6", "Research &amp; Documentation"),
        ("  10.7", "Live Trading Simulation"),
        ("11", "Installation &amp; Setup Guide"),
        ("12", "Configuration Reference"),
        ("13", "Deployment"),
        ("14", "Asset Universe"),
        ("15", "Performance Metrics Reference"),
        ("16", "Charts &amp; Visualizations Guide"),
        ("17", "Glossary of Terms"),
        ("18", "References"),
    ]
    for num, title in toc_entries:
        style = styles["TOCSubEntry"] if num.startswith("  ") else styles["TOCEntry"]
        story.append(Paragraph(f"<b>{num.strip()}</b>&nbsp;&nbsp;&nbsp;{title}", style))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 1: INTRODUCTION
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Introduction &amp; Motivation", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph(
        "This document presents a comprehensive technical thesis on the <b>Time-Series Momentum (TSMOM) "
        "Quantitative Strategy Platform</b> -- a production-grade, institutional-quality system designed for "
        "systematic trend-following across multiple asset classes. The platform encompasses the full lifecycle "
        "of quantitative strategy development: from data ingestion and signal generation, through portfolio "
        "construction and risk management, to interactive visualization and live trading simulation.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The system is built on the foundational research of <b>Moskowitz, Ooi &amp; Pedersen (2012)</b>, "
        "published in the <i>Journal of Financial Economics</i>, which demonstrated that time-series momentum "
        "-- the tendency for an asset's recent performance to persist -- generates significant positive returns "
        "across 58 liquid instruments spanning equities, bonds, commodities, and currencies over multiple decades. "
        "This anomaly is one of the most robust findings in quantitative finance.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "Unlike simple academic implementations, this platform incorporates <b>production-critical enhancements</b> "
        "that separate real-world trading systems from toy models: regime detection via Hidden Markov Models, "
        "drawdown control overlays for crash protection, volatility-targeting position sizing, walk-forward "
        "out-of-sample validation, and realistic transaction cost modeling.",
        styles["Body"]
    ))

    story.append(Paragraph("1.1 Project Scope", styles["SectionTitle"]))
    story.append(Paragraph("The platform consists of three major components:", styles["Body"]))
    story.append(bullet("<b>Quant Engine (Python)</b> -- Core strategy logic: signals, portfolio construction, risk management, backtesting"))
    story.append(bullet("<b>REST API (FastAPI)</b> -- Exposes the engine as async HTTP endpoints for the web application"))
    story.append(bullet("<b>Web Dashboard (Next.js)</b> -- Institutional-quality interactive frontend with 7 pages of analytics"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The system trades <b>27 ETFs</b> across 4 asset classes (equities, commodities, fixed income, FX), "
        "uses <b>20+ years of daily data</b> (2005-present), and computes <b>30+ risk/return metrics</b> "
        "per backtest run. The entire backtest pipeline executes in under 30 seconds using vectorized NumPy/Pandas operations.",
        styles["Body"]
    ))

    story.append(Paragraph("1.2 Technology Stack", styles["SectionTitle"]))
    tech_data = [
        ["Layer", "Technology", "Purpose"],
        ["Quant Engine", "Python 3.11+, Pandas, NumPy, SciPy", "Signal generation, backtesting, risk analytics"],
        ["ML / Regime", "scikit-learn, hmmlearn", "Hidden Markov Model regime detection"],
        ["Backend API", "FastAPI, Uvicorn, SQLAlchemy", "Async REST API, database ORM"],
        ["Frontend", "Next.js 15, React 19, TypeScript", "Server-side rendered web application"],
        ["UI Framework", "Tailwind CSS, Radix UI, Framer Motion", "Styling, components, animations"],
        ["Charts", "Plotly.js", "Interactive financial visualizations"],
        ["Data", "yfinance, PyArrow (Parquet)", "Market data fetching and caching"],
        ["Config", "Pydantic, YAML", "Type-safe settings management"],
        ["DevOps", "Docker, GitHub Actions", "Containerization and CI/CD"],
    ]
    story.append(make_table(tech_data[0], tech_data[1:], [1.0*inch, 2.2*inch, 2.8*inch]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 2: THEORETICAL FOUNDATIONS
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Theoretical Foundations", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("2.1 Time-Series Momentum (TSMOM)", styles["SectionTitle"]))
    story.append(Paragraph(
        "Time-Series Momentum is a quantitative trading strategy that takes positions based on each asset's "
        "own recent performance. If an asset has had positive returns over a lookback period, the strategy "
        "goes long; if returns were negative, it goes short. This is distinct from <b>cross-sectional momentum</b> "
        "(which ranks assets relative to each other) -- TSMOM uses each asset's absolute return as the signal.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The core insight: <i>assets that have been going up tend to continue going up, and assets that have "
        "been going down tend to continue going down</i>. This persistence exists across virtually all tradeable "
        "markets and has been documented across centuries of data.",
        styles["Body"]
    ))
    story.append(Paragraph("The binary TSMOM signal:", styles["Body"]))
    story.append(Paragraph(
        "s(i,t) = sign( SUM[tau = t-k-1 to t-1] r(i,tau) )",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "where r(i,tau) is the return of asset i at time tau, and k is the lookback window in trading days. "
        "The skip parameter (default 1 day) avoids short-term mean-reversion at the daily frequency.",
        styles["Body"]
    ))

    story.append(Paragraph("2.2 Why Momentum Works", styles["SectionTitle"]))
    story.append(Paragraph(
        "Multiple theoretical frameworks explain why momentum persists across markets and time periods, "
        "despite being well-documented for decades:",
        styles["Body"]
    ))
    story.append(bullet(
        "<b>Behavioral Biases</b>: Investors underreact to new information initially (anchoring, "
        "disposition effect) and then overreact as trends become obvious (herding, confirmation bias). "
        "This creates a delayed price adjustment pattern that manifests as persistent trends."
    ))
    story.append(bullet(
        "<b>Market Microstructure</b>: Institutional investors often split large orders over days or weeks, "
        "causing gradual price adjustment rather than immediate jumps. This mechanical effect creates "
        "exploitable autocorrelation in returns."
    ))
    story.append(bullet(
        "<b>Risk Premium</b>: Momentum may represent compensation for bearing 'crash risk'. Momentum "
        "strategies are vulnerable to sharp reversals (momentum crashes), and the positive expected "
        "return compensates investors for this tail risk."
    ))
    story.append(bullet(
        "<b>Positive Feedback Loops</b>: Risk management practices like stop-losses, margin calls, and "
        "portfolio insurance create forced selling/buying that amplifies price trends, especially during "
        "volatile periods."
    ))

    story.append(Paragraph("2.3 Momentum Crashes &amp; Risk", styles["SectionTitle"]))
    story.append(Paragraph(
        "The most critical risk of momentum strategies is the <b>momentum crash</b> -- a sudden, violent "
        "reversal of trends that can wipe out months of gains in days. Famous examples include the March 2009 "
        "reversal (when beaten-down financials surged 50%+ while momentum leaders collapsed) and the COVID "
        "recovery rally of April 2020.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "Daniel &amp; Moskowitz (2016) documented that momentum crashes are <b>predictable</b> -- they tend to "
        "occur after extended periods of high volatility and large dispersion between winners and losers. "
        "This motivates our drawdown control overlay (Chapter 7.1), which dynamically reduces exposure when "
        "the portfolio enters drawdown.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 3: SIGNAL GENERATION
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Signal Generation Pipeline", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "The signal generation pipeline is the intellectual core of the system. It transforms raw price data "
        "into trading signals through a multi-stage process: momentum computation, regime-aware scaling, "
        "and post-processing for noise reduction.",
        styles["Body"]
    ))

    story.append(Paragraph("3.1 Binary TSMOM Signal", styles["SectionTitle"]))
    story.append(Paragraph(
        "The simplest signal: the sign of cumulative returns over a lookback window. Produces +1 (long), "
        "-1 (short), or 0 (flat). Implemented in <font face='Courier'>src/signals/momentum.py</font>.",
        styles["Body"]
    ))
    story.append(Paragraph("s(i,t) = sign( r(i, t-k..t-1) )", styles["Equation"]))

    story.append(Paragraph("3.2 Continuous TSMOM Signal", styles["SectionTitle"]))
    story.append(Paragraph(
        "Rather than a binary long/short, the continuous signal scales position size by risk-adjusted trend "
        "strength. This is the cumulative return divided by realized volatility:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "s_cont(i,t) = SUM(r(i, t-k..t-1)) / ( sigma(i,t) * sqrt(252) )",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "This produces a signal proportional to the Sharpe ratio of the asset over the lookback window. "
        "A value of +2.0 means the asset has been trending up at 2 standard deviations; -1.5 means a "
        "moderate downtrend. The continuous signal allows for proportional position sizing -- stronger trends "
        "get larger positions.",
        styles["Body"]
    ))

    story.append(Paragraph("3.3 Multi-Horizon Blending", styles["SectionTitle"]))
    story.append(Paragraph(
        "Different lookback windows capture different trend frequencies. Short lookbacks (21 days / 1 month) "
        "react quickly but produce more noise and turnover. Long lookbacks (252 days / 12 months) are smoother "
        "but slower to respond. The system blends signals across multiple horizons:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "s_blend(i,t) = SUM[j=1..J]( w_j * s_cont(i,t,k_j) ),    where SUM(w_j) = 1",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "Default lookbacks: k = {21, 63, 126, 252} trading days (approximately 1, 3, 6, and 12 months). "
        "Default weights: equal (1/4 each). This diversification across horizons reduces variance and "
        "improves consistency.",
        styles["Body"]
    ))

    story.append(Paragraph("3.4 Signal Post-Processing", styles["SectionTitle"]))
    story.append(Paragraph(
        "Raw momentum signals are noisy and can produce excessive turnover. The post-processing pipeline "
        "applies three transformations in sequence:",
        styles["Body"]
    ))
    story.append(bullet(
        "<b>Exponential Smoothing</b> (halflife = 5 days): Reduces day-to-day signal noise. "
        "The exponentially-weighted moving average gives recent observations more weight while smoothing "
        "out random fluctuations. This significantly reduces portfolio turnover."
    ))
    story.append(bullet(
        "<b>Z-Score Normalization</b> (252-day rolling window): Standardizes signal magnitude across time. "
        "A raw momentum signal of 0.5 means different things in a low-vol environment vs high-vol. "
        "Z-scoring ensures signals are always relative to recent history."
    ))
    story.append(bullet(
        "<b>Signal Capping</b> ([-2, +2]): Limits extreme bets. Without capping, a single asset with "
        "an outsized momentum signal could dominate the portfolio. Capping at +/- 2 ensures no signal "
        "can produce an unreasonably large position."
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 4: REGIME DETECTION
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Regime Detection", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "Regime detection is what separates production-grade TSMOM from academic toy models. Research shows "
        "that TSMOM alpha <b>concentrates in trending regimes</b> and can be negative in mean-reverting markets. "
        "Our system uses a Hidden Markov Model (HMM) to classify the market into two regimes in real-time.",
        styles["Body"]
    ))

    story.append(Paragraph("4.1 Hidden Markov Model (HMM)", styles["SectionTitle"]))
    story.append(Paragraph(
        "A two-state Gaussian HMM models market returns as generated by one of two latent (hidden) states, "
        "each with its own mean and variance:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "r(t) | S(t) = k  ~  Normal(mu_k, sigma_k^2),    S(t) in {0, 1}",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "State transitions follow a Markov chain: P(S(t) = j | S(t-1) = i) = a(i,j). "
        "The model is trained using the Baum-Welch algorithm (Expectation-Maximization) on historical market "
        "returns. The state with higher absolute mean returns is labeled 'trending' (momentum works), "
        "while the other is labeled 'mean-reverting' (momentum is dangerous).",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The HMM produces posterior probabilities for each state at each point in time, enabling smooth "
        "transitions rather than binary switching. The system uses the <b>hmmlearn</b> library with a "
        "fallback to a simple trend-strength heuristic if HMM fitting fails.",
        styles["Body"]
    ))

    story.append(Paragraph("4.2 Regime-Aware Signal Scaling", styles["SectionTitle"]))
    story.append(Paragraph(
        "Once the regime is identified, signals are scaled by regime confidence. In trending regimes, "
        "signals operate at full strength. In mean-reverting regimes, signals are dampened to 30% -- "
        "enough to maintain some exposure but insufficient to generate large losses from whipsaws:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "s_regime(i,t) = s_blend(i,t) * (0.3 + 0.7 * P(trending | r(1:t)))",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "This mapping ensures the multiplier ranges from 0.3 (fully mean-reverting) to 1.0 (fully trending). "
        "The floor of 0.3 prevents complete exit from the market, which would miss sudden trend resumptions.",
        styles["Body"]
    ))

    story.append(Paragraph("Trend Strength Indicator (Fallback)", styles["SubSection"]))
    story.append(Paragraph(
        "When the HMM fails to converge (e.g., insufficient data), the system falls back to a simple "
        "heuristic: the fraction of sub-periods with positive returns over a 252-day rolling window. "
        "Values near 1.0 indicate strong uptrend, near 0.0 strong downtrend, and near 0.5 no trend "
        "(likely mean-reverting). This provides a robust alternative that requires no model fitting.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 5: VOLATILITY ESTIMATION
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Volatility Estimation", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "Accurate volatility estimation is critical for position sizing, risk management, and signal quality. "
        "The system implements four volatility estimators, each with different trade-offs:",
        styles["Body"]
    ))

    vol_data = [
        ["Estimator", "Formula / Method", "Use Case"],
        ["EWMA (default)", "Exponentially-weighted variance, halflife=20 days, annualized", "Primary estimator. Reacts quickly to vol spikes."],
        ["Yang-Zhang", "Combines overnight, open-to-close, and Rogers-Satchell components using OHLC data", "More efficient than close-to-close for same window size."],
        ["Garman-Klass", "Uses log(H/L) and log(C/O) from OHLC data", "Robust OHLC alternative, handles gaps."],
        ["Simple Rolling", "21-day rolling standard deviation, annualized", "Classic baseline. Simple but slow to react."],
    ]
    story.append(make_table(vol_data[0], vol_data[1:], [1.1*inch, 2.6*inch, 2.3*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The EWMA estimator is used by default throughout the system. Its exponential weighting (halflife of "
        "20 trading days) means recent observations receive more weight, allowing the estimator to adapt "
        "quickly when volatility spikes (e.g., during market crashes). All estimators annualize their output "
        "by multiplying by sqrt(252).",
        styles["Body"]
    ))

    story.append(Paragraph("Volatility Regime Indicator", styles["SubSection"]))
    story.append(Paragraph(
        "A binary high-volatility indicator flags when current volatility exceeds its rolling 75th percentile "
        "over the past year. This can be used as an additional signal filter -- dampening positions during "
        "extreme volatility environments when trend signals are less reliable.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 6: PORTFOLIO CONSTRUCTION
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Portfolio Construction", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("6.1 Volatility Targeting (MOP Framework)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The Moskowitz-Ooi-Pedersen (MOP) volatility-targeting approach is the industry standard for TSMOM "
        "position sizing. Each asset receives an equal risk budget, and positions are scaled inversely by "
        "the asset's realized volatility:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "w(i,t) = s(i,t) * ( sigma_target / N ) / sigma_hat(i,t)",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "where sigma_target is the portfolio volatility target (default 10% annualized), N is the number of "
        "assets, and sigma_hat(i,t) is the realized volatility estimate for asset i.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "<b>Intuition</b>: A highly volatile asset (e.g., natural gas with 40% annual vol) gets a position "
        "roughly 4x smaller than a low-volatility asset (e.g., treasury bonds with 10% annual vol). This "
        "ensures each position contributes approximately equal risk to the portfolio, regardless of the "
        "asset's inherent volatility.",
        styles["Body"]
    ))

    story.append(Paragraph("6.2 Constraint Enforcement", styles["SectionTitle"]))
    story.append(Paragraph("The constraint system prevents dangerous portfolio configurations:", styles["Body"]))
    story.append(bullet(
        "<b>Per-Position Cap</b> (default 10%): No single asset can exceed 10% of portfolio weight. "
        "Prevents concentration risk."
    ))
    story.append(bullet(
        "<b>Gross Exposure Cap</b> (default 200%): The sum of absolute weights cannot exceed 2.0x. "
        "Prevents excessive leverage. When breached, all weights are proportionally scaled down."
    ))
    story.append(Paragraph(
        "Constraints are applied proportionally (not by clipping), preserving the relative ranking of positions. "
        "This means if gross exposure needs to be scaled from 250% to 200%, all positions are multiplied "
        "by 200/250 = 0.8, maintaining relative allocations.",
        styles["Body"]
    ))

    story.append(Paragraph("6.3 Rebalance Scheduling", styles["SectionTitle"]))
    story.append(Paragraph(
        "The system supports three rebalance frequencies: <b>daily</b>, <b>weekly</b> (Fridays), and "
        "<b>monthly</b> (last trading day). Between rebalance dates, weights are held constant (not updated). "
        "Monthly rebalancing is the default -- it reduces turnover and transaction costs while maintaining "
        "the core trend-following exposure.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 7: RISK MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("7. Risk Management", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("7.1 Drawdown Control Overlay", styles["SectionTitle"]))
    story.append(Paragraph(
        "The drawdown control overlay is the <b>single most important production risk feature</b> for momentum "
        "strategies. It protects against momentum crashes by dynamically reducing position sizes when the "
        "portfolio enters drawdown:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "scale(t) = max( floor, 1 - (|DD(t)| - theta) / theta )",
        styles["Equation"]
    ))
    story.append(Paragraph(
        "where DD(t) is the current drawdown (negative number), theta = 10% is the threshold at which "
        "scaling begins, and floor = 25% is the minimum exposure (never fully exit).",
        styles["Body"]
    ))
    story.append(Paragraph("Behavior at different drawdown levels:", styles["Body"]))

    dd_data = [
        ["Drawdown", "Scale Factor", "Effect"],
        ["0% to -10%", "1.00 (100%)", "No scaling -- full positions maintained"],
        ["-10% to -15%", "0.50 to 1.00", "Partial scaling -- positions progressively reduced"],
        ["-15% to -20%", "0.25 to 0.50", "Heavy scaling -- positions at 25-50%"],
        ["Beyond -20%", "0.25 (floor)", "Floor reached -- minimum 25% exposure maintained"],
    ]
    story.append(make_table(dd_data[0], dd_data[1:], [1.0*inch, 1.3*inch, 3.2*inch]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The floor of 25% is critical: completely exiting during a drawdown would mean missing the recovery "
        "rally if the trend resumes. The floor maintains enough exposure to participate in recoveries.",
        styles["Body"]
    ))

    story.append(Paragraph("7.2 Value-at-Risk &amp; Conditional VaR", styles["SectionTitle"]))
    story.append(Paragraph(
        "The system computes both parametric (Gaussian) and historical (non-parametric) VaR and CVaR at "
        "95% and 99% confidence levels:",
        styles["Body"]
    ))
    story.append(bullet("<b>VaR(95%)</b>: Maximum expected daily loss that should not be exceeded 95% of the time."))
    story.append(bullet("<b>CVaR(95%)</b> (Expected Shortfall): The average loss in the worst 5% of days. "
        "More informative than VaR because it measures the severity of tail events, not just their threshold."))
    story.append(bullet("<b>Rolling VaR/CVaR</b>: 252-day rolling estimates for time-series visualization."))

    story.append(Paragraph("7.3 Historical Stress Testing", styles["SectionTitle"]))
    story.append(Paragraph(
        "The system evaluates portfolio performance during 8 pre-defined historical crisis periods:",
        styles["Body"]
    ))
    stress_data = [
        ["Scenario", "Period", "Description"],
        ["Global Financial Crisis", "Sep 2008 - Mar 2009", "Lehman collapse, credit freeze, equity drawdown -55%"],
        ["European Debt Crisis", "Jul 2011 - Nov 2011", "Greek/Italian sovereign debt fears, bank contagion"],
        ["Taper Tantrum", "May 2013 - Sep 2013", "Fed signals QE tapering, bond market sell-off"],
        ["China Deval / Oil Crash", "Aug 2015 - Feb 2016", "Yuan devaluation, oil below $30"],
        ["Volmageddon", "Jan 2018 - Mar 2018", "VIX spike from 10 to 50, short-vol products wiped out"],
        ["COVID-19 Crash", "Feb 2020 - Apr 2020", "Pandemic lockdowns, fastest bear market in history"],
        ["2022 Rate Shock", "Jan 2022 - Jun 2022", "Fed hiking cycle, bond/equity simultaneous sell-off"],
        ["SVB Banking Crisis", "Mar 2023", "Silicon Valley Bank collapse, regional bank contagion"],
    ]
    story.append(make_table(stress_data[0], stress_data[1:], [1.5*inch, 1.5*inch, 3.0*inch]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 8: BACKTESTING ENGINE
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("8. Backtesting Engine", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("8.1 Vectorized Architecture", styles["SectionTitle"]))
    story.append(Paragraph(
        "The backtesting engine uses a <b>vectorized (not event-driven)</b> architecture. All operations "
        "are expressed as NumPy/Pandas array operations rather than Python loops over individual time steps. "
        "This design choice provides a 100-1000x speedup over event-driven backtesting frameworks, enabling "
        "a full 20-year backtest with 30 assets to complete in seconds.",
        styles["Body"]
    ))
    story.append(Paragraph("The engine pipeline executes 8 steps:", styles["Body"]))
    story.append(bullet("<b>Step 1</b>: Compute returns and EWMA volatility from prices"))
    story.append(bullet("<b>Step 2</b>: Generate composite momentum signals (regime-aware, multi-horizon)"))
    story.append(bullet("<b>Step 3</b>: Compute raw position weights via volatility targeting"))
    story.append(bullet("<b>Step 4</b>: Apply rebalance schedule (hold between rebalance dates)"))
    story.append(bullet("<b>Step 5</b>: Apply drawdown control overlay (path-dependent, iterative)"))
    story.append(bullet("<b>Step 6</b>: Calculate gross returns, transaction costs, and net returns"))
    story.append(bullet("<b>Step 7</b>: Build trade blotter (what was bought/sold each day)"))
    story.append(bullet("<b>Step 8</b>: Compute 30+ risk/return metrics"))

    story.append(Paragraph("8.2 Walk-Forward Validation", styles["SectionTitle"]))
    story.append(Paragraph(
        "Walk-forward validation is the gold standard for out-of-sample testing in quantitative finance. "
        "Without it, any backtest result is suspect -- you cannot distinguish genuine alpha from overfitting "
        "to the training period.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The walk-forward procedure slides a train/test window through time: train on [t, t+3y) to fit the "
        "regime model, test on [t+3y, t+4y), then step forward by 6 months. Default configuration:",
        styles["Body"]
    ))
    story.append(bullet("<b>Train window</b>: 756 trading days (~3 years)"))
    story.append(bullet("<b>Test window</b>: 252 trading days (~1 year)"))
    story.append(bullet("<b>Step size</b>: 126 trading days (~6 months)"))
    story.append(Paragraph(
        "The out-of-sample returns from all folds are stitched together to produce an honest assessment "
        "of the strategy's true generalization performance.",
        styles["Body"]
    ))

    story.append(Paragraph("8.3 Transaction Cost Modeling", styles["SectionTitle"]))
    story.append(Paragraph(
        "Realistic cost modeling is essential -- many strategies that appear profitable before costs are "
        "unprofitable after. The system models two cost components:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "cost(t) = SUM_i( |delta_w(i,t)| ) * (c_slip + c_comm) / 10000",
        styles["Equation"]
    ))
    story.append(bullet("<b>Slippage</b> (default 5 bps): Market impact cost of executing trades"))
    story.append(bullet("<b>Commission</b> (default 1 bps): Broker fees"))
    story.append(Paragraph(
        "Total cost: 6 bps per unit of turnover. Monthly rebalancing produces lower costs than daily/weekly.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 9: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("9. System Architecture", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("9.1 Backend Architecture (FastAPI)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The backend wraps the existing Python quant engine in a modern async REST API. Key design decisions:",
        styles["Body"]
    ))
    story.append(bullet(
        "<b>asyncio.to_thread</b>: All heavy computation (backtests, signal generation) runs in a thread pool "
        "via asyncio.to_thread(), preventing the event loop from blocking. This allows health checks and other "
        "requests to remain responsive during long-running backtests."
    ))
    story.append(bullet(
        "<b>Cache-aware data loading</b>: The _get_prices() function first attempts an exact cache match, "
        "then falls back to finding cached superset files. This avoids network downloads when the requested "
        "tickers are a subset of a previously-cached universe."
    ))
    story.append(bullet("<b>CORS middleware</b>: Allows frontend requests from any origin during development."))

    story.append(Paragraph("API Endpoints", styles["SubSection"]))
    api_data = [
        ["Method", "Endpoint", "Description"],
        ["POST", "/api/run-backtest", "Full backtest with custom parameters (tickers, vol target, lookbacks, etc.)"],
        ["GET", "/api/get-signals", "Momentum signal heatmap, current state, pipeline decomposition"],
        ["GET", "/api/get-regime", "HMM regime probabilities, history, statistics per regime"],
        ["GET", "/api/get-risk", "VaR, CVaR, stress tests, risk contributions, drawdown"],
        ["GET", "/api/live-update", "Simulated live trading snapshot with noise-perturbed signals"],
        ["GET", "/api/universe", "Available asset universes and strategy presets"],
        ["GET", "/api/health", "Health check endpoint"],
    ]
    story.append(make_table(api_data[0], api_data[1:], [0.6*inch, 1.5*inch, 3.9*inch]))

    story.append(Paragraph("Backend Directory Structure", styles["SubSection"]))
    story.append(Paragraph(
        "backend/<br/>"
        "&nbsp;&nbsp;main.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# FastAPI app entry point<br/>"
        "&nbsp;&nbsp;app/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;api/routes.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# All REST endpoints<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;core/config.py &nbsp;&nbsp;&nbsp;&nbsp;# Pydantic settings<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;core/database.py &nbsp;&nbsp;# SQLAlchemy async engine<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;models/schemas.py &nbsp;# 20+ request/response models<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;services/engine.py # Service layer wrapping quant modules",
        styles["CodeBlock"]
    ))

    story.append(Paragraph("9.2 Frontend Architecture (Next.js)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The frontend is a Next.js 15 application using the App Router. It features server-side rendering, "
        "TypeScript type safety, and a component architecture optimized for financial data visualization.",
        styles["Body"]
    ))
    story.append(bullet("<b>Styling</b>: Tailwind CSS with a custom design system (CSS variables for dark/light themes)"))
    story.append(bullet("<b>Components</b>: Radix UI primitives (tabs, tooltips, badges) with CVA variant system"))
    story.append(bullet("<b>Charts</b>: Plotly.js via react-plotly.js with dynamic import (no SSR)"))
    story.append(bullet("<b>State</b>: TanStack React Query for server state management and caching"))
    story.append(bullet("<b>Animations</b>: Framer Motion for smooth page transitions and loading states"))

    story.append(Paragraph("9.3 Data Pipeline", styles["SectionTitle"]))
    story.append(Paragraph(
        "Market data flows through a multi-layer pipeline: yfinance (Yahoo Finance API) with exponential "
        "backoff retry logic (tenacity library), disk-based Parquet caching (PyArrow), and a cleaning stage "
        "that forward-fills gaps, drops sparse assets, and winsorizes extreme returns at 5 standard deviations.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 10: WEB APPLICATION FEATURES
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("10. Web Application Features", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("10.1 Strategy Dashboard (/dashboard)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The main dashboard is the landing page of the application. It displays a comprehensive overview of "
        "the TSMOM strategy performance with the following components:",
        styles["Body"]
    ))
    story.append(bullet("<b>KPI Row</b>: 8 key metrics (CAGR, Sharpe, Sortino, Max DD, Calmar, Vol, Hit Rate, Years) "
        "displayed as animated cards with color-coded trend indicators."))
    story.append(bullet("<b>Equity Curve</b>: Interactive Plotly chart showing cumulative returns of the strategy "
        "vs S&amp;P 500 benchmark, with regime overlay (red shading for mean-reverting periods)."))
    story.append(bullet("<b>Drawdown Chart</b>: Area chart showing portfolio drawdown over time, highlighting "
        "the magnitude and duration of each drawdown episode."))
    story.append(bullet("<b>Rolling Sharpe &amp; Volatility</b>: Dual charts showing 1-year rolling Sharpe ratio "
        "and 63-day rolling annualized volatility."))
    story.append(bullet("<b>Portfolio Exposure</b>: Stacked chart showing long, short, gross, and net exposure over time."))
    story.append(bullet("<b>Current Positions</b>: Table of active positions with weight, signal strength, and direction."))
    story.append(bullet("<b>Monthly Returns Heatmap</b>: Year x Month matrix with color-coded returns."))
    story.append(bullet("<b>Stress Test Table</b>: Performance during 8 historical crisis periods."))

    story.append(Paragraph("10.2 Signal Engine (/dashboard/signals)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The signal page provides deep analysis of the momentum signal generation process:",
        styles["Body"]
    ))
    story.append(bullet("<b>Current Signal State</b>: Grid showing each asset's signal value with LONG/SHORT/FLAT badges."))
    story.append(bullet("<b>Signal Heatmap</b>: Assets x Time heatmap showing signal evolution over the last 12 months (weekly)."))
    story.append(bullet("<b>Pipeline Decomposition</b>: Line chart showing raw momentum, regime score, volatility, "
        "and final signal components over time."))

    story.append(Paragraph("10.3 Regime Detection (/dashboard/regime)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The regime page visualizes the HMM regime detection system:",
        styles["Body"]
    ))
    story.append(bullet("<b>KPIs</b>: Current regime, trending probability, time spent in each regime."))
    story.append(bullet("<b>Regime Score History</b>: Time series showing the regime classification over the full sample."))
    story.append(bullet("<b>Probability Chart</b>: P(Trending) and P(Mean-Reverting) over time."))
    story.append(bullet("<b>Regime Statistics</b>: Side-by-side comparison of trending vs mean-reverting periods "
        "(days, return, volatility)."))

    story.append(Paragraph("10.4 Risk Management (/dashboard/risk)", styles["SectionTitle"]))
    story.append(bullet("<b>VaR/CVaR Cards</b>: Daily Value-at-Risk and Expected Shortfall at 95% and 99% confidence."))
    story.append(bullet("<b>Rolling VaR/CVaR</b>: 252-day rolling estimates with filled area between VaR and CVaR."))
    story.append(bullet("<b>Risk Contribution Pie Chart</b>: Breakdown of portfolio risk by asset."))
    story.append(bullet("<b>Drawdown Series</b>: Full drawdown time series with duration tracking."))
    story.append(bullet("<b>Rolling Volatility</b>: 63-day rolling annualized volatility with area fill."))

    story.append(Paragraph("10.5 Backtest Laboratory (/backtest)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The Backtest Lab is the most interactive page -- it allows users to configure and run custom backtests "
        "with full parameter control:",
        styles["Body"]
    ))
    story.append(bullet("<b>Strategy Presets</b>: One-click buttons for Conservative, Balanced, Aggressive configurations."))
    story.append(bullet("<b>Asset Selection</b>: Toggle individual assets on/off from the 27-asset universe, "
        "organized by asset class."))
    story.append(bullet("<b>Parameter Controls</b>: Numeric inputs for vol target, drawdown threshold, max position weight, "
        "gross exposure cap, slippage, commission. Dropdown for rebalance frequency."))
    story.append(bullet("<b>Lookback Selection</b>: Toggle momentum lookback horizons (1M, 3M, 6M, 12M)."))
    story.append(bullet("<b>Instant Results</b>: Full KPI row, equity curve, drawdown, rolling metrics, exposure, "
        "and monthly heatmap update immediately after the backtest completes."))
    story.append(bullet("<b>CSV Export</b>: Download backtest equity curve as CSV for further analysis."))

    story.append(Paragraph("10.6 Research (/research)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The Research page provides educational content with LaTeX-rendered mathematical equations, covering: "
        "TSMOM concept, continuous signals, multi-horizon blending, volatility targeting, regime detection, "
        "drawdown control, transaction costs, risk metrics, a complete glossary of 16 key terms, and "
        "academic references.",
        styles["Body"]
    ))

    story.append(Paragraph("10.7 Live Trading Simulation (/live)", styles["SectionTitle"]))
    story.append(Paragraph(
        "The Live Trading page simulates real-time portfolio management with auto-refreshing data every 5 seconds. "
        "Signals are perturbed with small Gaussian noise to simulate market movement. Features include: "
        "animated position cards, portfolio value history chart, live signal bar chart, and real-time regime indicator.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 11: INSTALLATION & SETUP
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("11. Installation &amp; Setup Guide", styles["ChapterTitle"]))
    story.append(heading_line())

    story.append(Paragraph("11.1 Prerequisites", styles["SectionTitle"]))
    story.append(bullet("<b>Python 3.10+</b> (3.11 recommended)"))
    story.append(bullet("<b>Node.js 20+</b> with npm"))
    story.append(bullet("<b>Git</b> for version control"))

    story.append(Paragraph("11.2 Backend Setup", styles["SectionTitle"]))
    story.append(Paragraph(
        "# Clone the repository<br/>"
        "git clone &lt;repository-url&gt;<br/>"
        "cd time-series-momentum<br/><br/>"
        "# Install Python dependencies<br/>"
        "pip install -r backend/requirements.txt<br/><br/>"
        "# Start the backend API server<br/>"
        "python start_backend.py<br/><br/>"
        "# The API will be available at http://localhost:8000<br/>"
        "# API docs at http://localhost:8000/docs",
        styles["CodeBlock"]
    ))

    story.append(Paragraph("11.3 Frontend Setup", styles["SectionTitle"]))
    story.append(Paragraph(
        "# Navigate to frontend directory<br/>"
        "cd frontend<br/><br/>"
        "# Install Node.js dependencies<br/>"
        "npm install<br/><br/>"
        "# Start the development server<br/>"
        "npm run dev<br/><br/>"
        "# The dashboard will be available at http://localhost:3000",
        styles["CodeBlock"]
    ))

    story.append(Paragraph("11.4 Running Both Servers", styles["SectionTitle"]))
    story.append(Paragraph(
        "Open two terminal windows. In the first, start the backend. In the second, start the frontend. "
        "The frontend calls the backend API at http://localhost:8000/api by default (configurable via "
        "the NEXT_PUBLIC_API_URL environment variable in frontend/.env.local).",
        styles["Body"]
    ))

    story.append(Paragraph("11.5 Docker Deployment", styles["SectionTitle"]))
    story.append(Paragraph(
        "# Build and start all services<br/>"
        "docker-compose up --build<br/><br/>"
        "# This starts:<br/>"
        "#   Backend on port 8000<br/>"
        "#   Frontend on port 3000",
        styles["CodeBlock"]
    ))

    story.append(Paragraph("11.6 Running the Quant Engine Directly", styles["SectionTitle"]))
    story.append(Paragraph(
        "The quant engine can be used without the web application:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "# Quick CLI backtest<br/>"
        "python run.py<br/><br/>"
        "# Streamlit interactive dashboard<br/>"
        "streamlit run src/dashboard/app.py<br/><br/>"
        "# Programmatic access<br/>"
        "from config.settings import AppSettings<br/>"
        "from src.backtest.engine import BacktestEngine<br/>"
        "from src.data.provider import DataManager<br/><br/>"
        "dm = DataManager()<br/>"
        "prices = dm.get_close_prices(['SPY','QQQ','TLT'], '2020-01-01')<br/>"
        "engine = BacktestEngine(AppSettings())<br/>"
        "result = engine.run(prices)<br/>"
        "print(result.metrics['sharpe_ratio'])",
        styles["CodeBlock"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 12: CONFIGURATION REFERENCE
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("12. Configuration Reference", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "All parameters are defined in config/settings.py using Pydantic. They can be overridden via "
        "environment variables with the TSMOM_ prefix (e.g., TSMOM_VOL_TARGET=0.15).",
        styles["Body"]
    ))

    config_data = [
        ["Parameter", "Default", "Description"],
        ["vol_target", "0.10", "Portfolio annualized volatility target (10%)"],
        ["momentum_lookbacks", "[21,63,126,252]", "Lookback windows in trading days"],
        ["signal_cap", "2.0", "Maximum signal magnitude"],
        ["max_position_weight", "0.10", "Per-asset weight cap (10%)"],
        ["max_gross_exposure", "2.0", "Maximum total absolute weight (200%)"],
        ["rebalance_frequency", "monthly", "Options: daily, weekly, monthly"],
        ["drawdown_threshold", "0.10", "DD level where scaling begins (10%)"],
        ["drawdown_scaling_floor", "0.25", "Minimum exposure at max DD (25%)"],
        ["default_slippage_bps", "5.0", "Market impact cost per trade"],
        ["commission_bps", "1.0", "Broker commission per trade"],
        ["risk_free_rate", "0.0", "Risk-free rate for Sharpe calculation"],
        ["default_start_date", "2005-01-01", "Default backtest start date"],
    ]
    story.append(make_table(config_data[0], config_data[1:], [1.6*inch, 1.2*inch, 3.2*inch]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Strategy Presets", styles["SubSection"]))
    preset_data = [
        ["Preset", "Vol Target", "Lookbacks", "Rebalance", "DD Threshold"],
        ["Conservative", "8%", "[126, 252]", "Monthly", "8%"],
        ["Balanced", "10%", "[21, 63, 126, 252]", "Monthly", "10%"],
        ["Aggressive", "15%", "[21, 63]", "Weekly", "15%"],
    ]
    story.append(make_table(preset_data[0], preset_data[1:]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 13: DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("13. Deployment", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "The system is designed for cloud deployment with the following recommended infrastructure:",
        styles["Body"]
    ))

    deploy_data = [
        ["Component", "Recommended Platform", "Alternative"],
        ["Frontend", "Vercel (automatic Next.js deployment)", "Netlify, AWS Amplify"],
        ["Backend", "Railway or Render (Docker-based)", "AWS EC2, DigitalOcean"],
        ["Database", "NeonDB or Supabase (PostgreSQL)", "SQLite (dev only)"],
        ["CI/CD", "GitHub Actions (included)", "GitLab CI, CircleCI"],
    ]
    story.append(make_table(deploy_data[0], deploy_data[1:], [1.2*inch, 2.5*inch, 2.3*inch]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("CI/CD Pipeline", styles["SubSection"]))
    story.append(Paragraph(
        "The included GitHub Actions workflow (.github/workflows/ci.yml) runs on every push to main:",
        styles["Body"]
    ))
    story.append(bullet("<b>Backend Lint</b>: ruff (linter) and mypy (type checker) on src/ and backend/"))
    story.append(bullet("<b>Backend Tests</b>: pytest on the test suite"))
    story.append(bullet("<b>Frontend Build</b>: npm install + npm run build"))
    story.append(bullet("<b>Docker Build</b>: docker-compose build (runs after lint and build pass)"))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 14: ASSET UNIVERSE
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("14. Asset Universe", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "The system trades 27 liquid ETFs across 4 asset classes, defined in config/universes.yaml. "
        "ETFs are used as proxies for underlying markets (e.g., GLD proxies gold futures).",
        styles["Body"]
    ))

    asset_data = [
        ["Ticker", "Name", "Asset Class", "Sector"],
        ["SPY", "S&P 500", "Equities", "Broad Market"],
        ["QQQ", "Nasdaq 100", "Equities", "Technology"],
        ["IWM", "Russell 2000", "Equities", "Small Cap"],
        ["XLF", "Financials SPDR", "Equities", "Financials"],
        ["XLE", "Energy SPDR", "Equities", "Energy"],
        ["XLV", "Healthcare SPDR", "Equities", "Healthcare"],
        ["XLK", "Technology SPDR", "Equities", "Technology"],
        ["XLI", "Industrials SPDR", "Equities", "Industrials"],
        ["XLP", "Consumer Staples", "Equities", "Staples"],
        ["XLY", "Consumer Disc.", "Equities", "Discretionary"],
        ["XLU", "Utilities SPDR", "Equities", "Utilities"],
        ["XLRE", "Real Estate SPDR", "Equities", "Real Estate"],
        ["GLD", "Gold ETF", "Commodities", "Precious Metals"],
        ["SLV", "Silver ETF", "Commodities", "Precious Metals"],
        ["USO", "Crude Oil ETF", "Commodities", "Energy"],
        ["UNG", "Natural Gas ETF", "Commodities", "Energy"],
        ["DBA", "Agriculture ETF", "Commodities", "Agriculture"],
        ["TLT", "20+ Year Treasury", "Fixed Income", "Long Duration"],
        ["IEF", "7-10 Year Treasury", "Fixed Income", "Mid Duration"],
        ["SHY", "1-3 Year Treasury", "Fixed Income", "Short Duration"],
        ["LQD", "Inv. Grade Corp.", "Fixed Income", "Credit"],
        ["HYG", "High Yield Corp.", "Fixed Income", "High Yield"],
        ["UUP", "US Dollar Index", "FX", "Dollar"],
        ["FXE", "Euro ETF", "FX", "Major"],
        ["FXY", "Japanese Yen ETF", "FX", "Major"],
        ["FXB", "British Pound ETF", "FX", "Major"],
        ["FXA", "Australian Dollar", "FX", "Commodity FX"],
    ]
    story.append(make_table(asset_data[0], asset_data[1:], [0.7*inch, 1.5*inch, 1.1*inch, 1.2*inch]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 15: PERFORMANCE METRICS
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("15. Performance Metrics Reference", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "The system computes 30+ metrics in a single pass through the return series. "
        "All metrics are computed in src/risk/metrics.py.",
        styles["Body"]
    ))

    metrics_data = [
        ["Metric", "Formula / Description", "Interpretation"],
        ["Total Return", "(1+r1)(1+r2)...(1+rn) - 1", "Cumulative compounded return"],
        ["CAGR", "(1+total)^(1/years) - 1", "Annualized compound growth rate"],
        ["Annualized Vol", "std(r) * sqrt(252)", "Annualized standard deviation of returns"],
        ["Sharpe Ratio", "E[r-rf] / std(r) * sqrt(252)", "Risk-adjusted return per unit of total risk"],
        ["Sortino Ratio", "E[r-rf] / downside_std * sqrt(252)", "Like Sharpe but only penalizes downside"],
        ["Calmar Ratio", "CAGR / |Max Drawdown|", "Return per unit of worst drawdown"],
        ["Max Drawdown", "min(cumulative / peak - 1)", "Largest peak-to-trough decline"],
        ["Hit Rate", "P(r > 0)", "Fraction of positive-return days"],
        ["VaR 95%", "5th percentile of returns", "Max daily loss at 95% confidence"],
        ["CVaR 95%", "E[r | r <= VaR95]", "Average loss beyond VaR threshold"],
        ["Skewness", "3rd standardized moment", "Asymmetry of return distribution"],
        ["Kurtosis", "4th standardized moment - 3", "Fat-tailedness of returns"],
        ["Info Ratio", "E[r-rb] / std(r-rb) * sqrt(252)", "Active return per tracking error"],
        ["Beta", "cov(r,rb) / var(rb)", "Sensitivity to benchmark returns"],
        ["Alpha", "Intercept of regression r vs rb", "Return unexplained by benchmark"],
    ]
    story.append(make_table(metrics_data[0], metrics_data[1:], [1.1*inch, 2.3*inch, 2.6*inch]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 16: CHARTS & VISUALIZATIONS
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("16. Charts &amp; Visualizations Guide", styles["ChapterTitle"]))
    story.append(heading_line())
    story.append(Paragraph(
        "All charts use Plotly.js with a custom institutional theme (dark/light mode support). "
        "The chart wrapper component (plotly-chart.tsx) provides consistent styling across all visualizations.",
        styles["Body"]
    ))

    chart_data = [
        ["Chart Type", "Page", "Data Source", "Purpose"],
        ["Equity Curve", "Dashboard", "Cumulative portfolio returns", "Primary performance visualization with benchmark overlay"],
        ["Drawdown", "Dashboard, Risk", "Peak-to-trough decline", "Visualize loss episodes and recovery times"],
        ["Rolling Sharpe", "Dashboard", "252-day rolling Sharpe ratio", "Track risk-adjusted performance stability over time"],
        ["Rolling Volatility", "Dashboard, Risk", "63-day rolling annualized vol", "Monitor portfolio risk through time"],
        ["Exposure Chart", "Dashboard", "Long/short/gross/net weights", "Portfolio directionality and leverage tracking"],
        ["Monthly Heatmap", "Dashboard", "Monthly compounded returns", "Seasonal patterns and year-by-year consistency"],
        ["Signal Heatmap", "Signals", "Weekly signal values per asset", "Cross-asset momentum patterns over time"],
        ["Signal Components", "Signals", "Raw, regime, vol, final signal", "Pipeline decomposition for debugging"],
        ["Regime Score", "Regime", "HMM posterior probability", "Trending vs mean-reverting classification"],
        ["Regime Probs", "Regime", "State probabilities", "Confidence in regime classification"],
        ["Rolling VaR/CVaR", "Risk", "252-day rolling tail risk", "Dynamic tail risk monitoring"],
        ["Risk Contribution", "Risk", "Weight * asset vol", "Pie chart of risk by asset"],
        ["Live Signals", "Live Trading", "Perturbed real-time signals", "Horizontal bar chart of signal strength"],
        ["Portfolio Value", "Live Trading", "Simulated portfolio NAV", "Session-level P&L tracking"],
    ]
    story.append(make_table(chart_data[0], chart_data[1:], [1.2*inch, 0.8*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Color Palette", styles["SubSection"]))
    story.append(Paragraph(
        "The platform uses an institutional color palette designed for financial applications: "
        "Primary (#6366f1 indigo), Profit (#10b981 emerald), Loss (#ef4444 red), Warning (#f59e0b amber), "
        "Slate (#64748b) for secondary elements. Dark mode uses a deep navy background (#0a0e1a) with "
        "muted foregrounds for reduced eye strain during extended analysis sessions.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 17: GLOSSARY
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("17. Glossary of Terms", styles["ChapterTitle"]))
    story.append(heading_line())

    glossary = [
        ["Term", "Definition"],
        ["TSMOM", "Time-Series Momentum -- trading based on an asset's own past return, not relative to peers"],
        ["CAGR", "Compound Annual Growth Rate -- annualized return accounting for compounding effects"],
        ["Sharpe Ratio", "Risk-adjusted return: excess return (above risk-free rate) per unit of volatility"],
        ["Sortino Ratio", "Like Sharpe but only penalizes downside (negative) volatility, ignoring upside variance"],
        ["Max Drawdown", "Largest peak-to-trough percentage decline in portfolio value"],
        ["Calmar Ratio", "CAGR divided by the absolute value of maximum drawdown"],
        ["VaR", "Value-at-Risk -- maximum expected loss at a given confidence level (e.g., 95%)"],
        ["CVaR", "Conditional VaR (Expected Shortfall) -- average loss in the worst tail beyond VaR"],
        ["HMM", "Hidden Markov Model -- probabilistic model for detecting latent regime states"],
        ["Vol Target", "Target annualized portfolio volatility, used for position sizing (e.g., 10%)"],
        ["Lookback", "Period of historical returns used to compute the momentum signal (in trading days)"],
        ["Turnover", "Total absolute weight changes per period -- determines transaction cost drag"],
        ["Gross Exposure", "Sum of absolute position weights -- exceeds 100% when using leverage or shorting"],
        ["Net Exposure", "Sum of signed position weights -- indicates overall market directionality"],
        ["Regime", "Market state classification: trending (momentum works) vs mean-reverting (momentum fails)"],
        ["Drawdown Control", "Dynamic position scaling based on current portfolio drawdown to limit crash losses"],
        ["Signal Capping", "Limiting signal magnitude to [-2, +2] to prevent extreme position sizing"],
        ["Volatility Targeting", "Position sizing inversely proportional to asset volatility for equal risk contribution"],
        ["Walk-Forward", "Out-of-sample validation method using rolling train/test windows through time"],
        ["Winsorization", "Clipping extreme returns at N standard deviations to reduce outlier impact"],
        ["Rebalance", "Periodic portfolio weight adjustment (daily, weekly, or monthly)"],
        ["Slippage", "Market impact cost of trade execution (measured in basis points)"],
        ["ETF", "Exchange-Traded Fund -- used as liquid proxies for asset class exposure"],
        ["MOP", "Moskowitz-Ooi-Pedersen framework -- the standard TSMOM volatility-targeting approach"],
        ["Basis Point", "One hundredth of one percent (0.01%). 5 bps = 0.05%"],
    ]
    story.append(make_table(glossary[0], glossary[1:], [1.4*inch, 4.6*inch]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════
    # CHAPTER 18: REFERENCES
    # ═══════════════════════════════════════════════════════════════════
    story.append(Paragraph("18. References", styles["ChapterTitle"]))
    story.append(heading_line())

    refs = [
        "Moskowitz, T. J., Ooi, Y. H., &amp; Pedersen, L. H. (2012). Time Series Momentum. "
        "<i>Journal of Financial Economics</i>, 104(2), 228-250.",

        "Baltas, A. N., &amp; Kosowski, R. (2013). Momentum Strategies in Futures Markets and "
        "Trend-Following Funds. Working Paper, Imperial College London.",

        "Barroso, P., &amp; Santa-Clara, P. (2015). Momentum Has Its Moments. "
        "<i>Journal of Financial Economics</i>, 116(1), 111-120.",

        "Daniel, K., &amp; Moskowitz, T. J. (2016). Momentum Crashes. "
        "<i>Journal of Financial Economics</i>, 122(2), 221-247.",

        "Kim, A. Y., Tse, Y., &amp; Wald, J. K. (2016). Time Series Momentum and Volatility "
        "Scaling. <i>Journal of Financial Markets</i>, 30, 103-124.",

        "Jegadeesh, N., &amp; Titman, S. (1993). Returns to Buying Winners and Selling Losers: "
        "Implications for Stock Market Efficiency. <i>Journal of Finance</i>, 48(1), 65-91.",

        "Asness, C. S., Moskowitz, T. J., &amp; Pedersen, L. H. (2013). Value and Momentum "
        "Everywhere. <i>Journal of Finance</i>, 68(3), 929-985.",

        "Hamilton, J. D. (1989). A New Approach to the Economic Analysis of Nonstationary Time "
        "Series and the Business Cycle. <i>Econometrica</i>, 57(2), 357-384.",

        "Hurst, B., Ooi, Y. H., &amp; Pedersen, L. H. (2017). A Century of Evidence on "
        "Trend-Following Investing. <i>The Journal of Portfolio Management</i>, 44(1), 15-29.",

        "Garman, M. B., &amp; Klass, M. J. (1980). On the Estimation of Security Price "
        "Volatilities from Historical Data. <i>Journal of Business</i>, 53(1), 67-78.",

        "Yang, D., &amp; Zhang, Q. (2000). Drift-Independent Volatility Estimation Based on "
        "High, Low, Open, and Close Prices. <i>Journal of Business</i>, 73(3), 477-492.",
    ]

    for i, ref in enumerate(refs, 1):
        story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{ref}", styles["Body"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 30))
    story.append(thin_line())
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<i>This document was generated as part of the TSMOM Quantitative Strategy Platform project. "
        "The system represents a production-grade implementation of the Moskowitz-Ooi-Pedersen (2012) "
        "framework with modern enhancements for regime detection, drawdown protection, and interactive "
        "web-based analytics.</i>",
        styles["Note"]
    ))

    # ─── Build ────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print(f"\nThesis generated: {output_path}")
    print(f"Total pages: ~20")


if __name__ == "__main__":
    build_thesis()
