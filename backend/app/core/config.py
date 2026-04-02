"""Backend configuration — mirrors the quant engine settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TSMOM_")

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    database_url: str = "sqlite+aiosqlite:///./tsmom.db"

    # Quant engine defaults
    data_cache_dir: Path = Path("../data/cache")
    default_start_date: str = "2005-01-01"
    risk_free_rate: float = 0.0
    trading_days_per_year: int = 252
    momentum_lookbacks: list[int] = [21, 63, 126, 252]
    signal_combination_method: str = "equal_weight"
    signal_cap: float = 2.0
    vol_target: float = 0.10
    max_position_weight: float = 0.10
    max_gross_exposure: float = 2.0
    rebalance_frequency: str = "monthly"
    drawdown_threshold: float = 0.10
    drawdown_scaling_floor: float = 0.25
    default_slippage_bps: float = 5.0
    commission_bps: float = 1.0


settings = Settings()
