"""Asset universe loader from YAML configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.utils.types import AssetMeta

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "universes.yaml"


def load_universes(path: Path = CONFIG_PATH) -> dict[str, list[AssetMeta]]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    universes: dict[str, list[AssetMeta]] = {}
    for universe_name, universe_data in raw.items():
        if universe_name == "strategy_presets":
            continue
        assets = []
        for a in universe_data["assets"]:
            assets.append(
                AssetMeta(
                    ticker=a["ticker"],
                    name=a["name"],
                    sector=a["sector"],
                    asset_class=universe_name,
                )
            )
        universes[universe_name] = assets
    return universes


def get_all_tickers(universes: dict[str, list[AssetMeta]] | None = None) -> list[str]:
    if universes is None:
        universes = load_universes()
    return [a.ticker for assets in universes.values() for a in assets]


def get_ticker_metadata(universes: dict[str, list[AssetMeta]] | None = None) -> dict[str, AssetMeta]:
    if universes is None:
        universes = load_universes()
    return {a.ticker: a for assets in universes.values() for a in assets}


def load_strategy_presets(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return raw.get("strategy_presets", {})
