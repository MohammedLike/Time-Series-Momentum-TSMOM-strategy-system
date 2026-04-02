"""API routes — all endpoints for the TSMOM platform."""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BacktestRequest, BacktestResponse,
    SignalResponse, RegimeResponse, RiskResponse,
    LiveUpdate, UniverseResponse,
)
from app.services.engine import (
    run_backtest, get_signals, get_regime, get_risk,
    get_live_update, get_universe,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run-backtest", response_model=BacktestResponse)
async def api_run_backtest(req: BacktestRequest):
    """Run a full backtest with custom parameters."""
    try:
        return run_backtest(req)
    except Exception as e:
        logger.exception("Backtest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-signals", response_model=SignalResponse)
async def api_get_signals(
    tickers: str = "SPY,QQQ,TLT,GLD,IEF",
    start_date: str = "2005-01-01",
    lookbacks: str = "21,63,126,252",
):
    """Get momentum signals for specified assets."""
    try:
        ticker_list = [t.strip() for t in tickers.split(",")]
        lb_list = [int(x.strip()) for x in lookbacks.split(",")]
        return get_signals(ticker_list, start_date, lb_list)
    except Exception as e:
        logger.exception("Signal generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-regime", response_model=RegimeResponse)
async def api_get_regime(
    tickers: str = "SPY,QQQ,TLT,GLD,IEF",
    start_date: str = "2005-01-01",
):
    """Get market regime detection results."""
    try:
        ticker_list = [t.strip() for t in tickers.split(",")]
        return get_regime(ticker_list, start_date)
    except Exception as e:
        logger.exception("Regime detection failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-risk", response_model=RiskResponse)
async def api_get_risk(
    tickers: str = "SPY,QQQ,TLT,GLD,IEF",
    start_date: str = "2005-01-01",
    vol_target: float = 0.10,
):
    """Get risk analysis for the strategy."""
    try:
        ticker_list = [t.strip() for t in tickers.split(",")]
        return get_risk(ticker_list, start_date, vol_target)
    except Exception as e:
        logger.exception("Risk analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-update", response_model=LiveUpdate)
async def api_live_update(
    tickers: str = "SPY,QQQ,TLT,GLD,IEF,XLF,XLE,XLK",
):
    """Get a simulated live trading snapshot."""
    try:
        ticker_list = [t.strip() for t in tickers.split(",")]
        return get_live_update(ticker_list)
    except Exception as e:
        logger.exception("Live update failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-performance")
async def api_get_performance(
    tickers: str = "SPY,QQQ,TLT,GLD,IEF",
    start_date: str = "2005-01-01",
):
    """Quick performance summary without full backtest detail."""
    try:
        req = BacktestRequest(
            tickers=[t.strip() for t in tickers.split(",")],
            start_date=start_date,
        )
        result = run_backtest(req)
        return {
            "metrics": result.metrics,
            "equity_curve": result.equity_curve,
            "benchmark_equity": result.benchmark_equity,
        }
    except Exception as e:
        logger.exception("Performance fetch failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universe", response_model=UniverseResponse)
async def api_get_universe():
    """Get available asset universes and strategy presets."""
    return get_universe()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "tsmom-api"}
