"""Central configuration for the TSMOM system.

Every tunable parameter lives here, overridable via environment variables
with the TSMOM_ prefix (e.g., TSMOM_VOL_TARGET=0.15).
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TSMOM_")

    # ── Data ──────────────────────────────────────────────────────────
    data_cache_dir: Path = Path("data/cache")
    default_start_date: str = "2005-01-01"
    risk_free_rate: float = 0.0
    trading_days_per_year: int = 252

    # ── Signal ────────────────────────────────────────────────────────
    momentum_lookbacks: list[int] = [21, 63, 126, 252]
    signal_combination_method: str = "equal_weight"
    signal_cap: float = 2.0

    # ── Portfolio ─────────────────────────────────────────────────────
    vol_target: float = 0.10
    max_position_weight: float = 0.10
    max_gross_exposure: float = 2.0
    rebalance_frequency: str = "monthly"

    # ── Risk ──────────────────────────────────────────────────────────
    drawdown_threshold: float = 0.10
    drawdown_scaling_floor: float = 0.25

    # ── Costs ─────────────────────────────────────────────────────────
    default_slippage_bps: float = 5.0
    commission_bps: float = 1.0
