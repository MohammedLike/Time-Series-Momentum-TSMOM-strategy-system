"""Data providers for fetching market data.

Supports yfinance with automatic retry and disk caching.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class YFinanceProvider:
    """Downloads adjusted OHLCV data from Yahoo Finance with retry logic."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def fetch_prices(
        self, tickers: list[str], start: str, end: str | None = None
    ) -> pd.DataFrame:
        logger.info("Fetching %d tickers from %s", len(tickers), start)
        data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError(f"No data returned for {tickers}")
        if len(tickers) == 1:
            data.columns = pd.MultiIndex.from_product([data.columns, tickers])
        return data


class CacheLayer:
    """Parquet-based disk cache to avoid re-downloading data."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, label: str) -> Path:
        return self.cache_dir / f"{label}.parquet"

    def get(self, label: str) -> pd.DataFrame | None:
        path = self._key(label)
        if path.exists():
            logger.info("Cache hit: %s", label)
            return pd.read_parquet(path)
        return None

    def put(self, label: str, df: pd.DataFrame) -> None:
        path = self._key(label)
        df.to_parquet(path)
        logger.info("Cached: %s", label)


class DataManager:
    """Orchestrates fetching, caching, and cleaning of market data."""

    def __init__(self, cache_dir: Path = Path("data/cache")):
        self.provider = YFinanceProvider()
        self.cache = CacheLayer(cache_dir)

    def get_prices(
        self, tickers: list[str], start: str, end: str | None = None
    ) -> pd.DataFrame:
        label = f"prices_{'_'.join(sorted(tickers))}_{start}"
        cached = self.cache.get(label)
        if cached is not None:
            return cached
        prices = self.provider.fetch_prices(tickers, start, end)
        self.cache.put(label, prices)
        return prices

    def get_close_prices(
        self, tickers: list[str], start: str, end: str | None = None
    ) -> pd.DataFrame:
        raw = self.get_prices(tickers, start, end)
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        else:
            close = raw.xs("Close", axis=1, level=0) if isinstance(raw.columns, pd.MultiIndex) else raw
        close = close[tickers] if all(t in close.columns for t in tickers) else close
        return close.dropna(how="all")
