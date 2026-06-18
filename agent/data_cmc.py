"""CoinMarketCap Agent Hub data client.

Reads the signals the strategy trades on. Uses the CMC API key from the
environment (os.getenv — never hardcoded, never read from a dotfile). Each call
is the unit we later meter through x402.

Surface used: Fear & Greed index + listings quotes. Extended in Phase 2 to
funding rates + derivatives positioning (the regime inputs).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import requests

CMC_BASE = "https://pro-api.coinmarketcap.com"


class MissingCMCKey(RuntimeError):
    pass


@dataclass(frozen=True)
class Signal:
    """One decision input pulled from CMC."""

    name: str
    value: float
    classification: str  # e.g. "Fear", "Greed", "Neutral"
    fresh: bool = True    # set False by the x402 trust-gate when stale


def _key() -> str:
    k = os.getenv("CMC_API_KEY")
    if not k:
        raise MissingCMCKey(
            "CMC_API_KEY is not set. Get a free key at coinmarketcap.com/api "
            "and export CMC_API_KEY."
        )
    return k


def fear_greed() -> Signal:
    """Latest CMC Fear & Greed index (0-100) + its classification."""
    r = requests.get(
        f"{CMC_BASE}/v3/fear-and-greed/latest",
        headers={"X-CMC_PRO_API_KEY": _key(), "Accept": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()["data"]
    return Signal(
        name="fear_greed",
        value=float(data["value"]),
        classification=str(data.get("value_classification", "")),
    )


def quote_usd(symbol: str) -> float:
    """Spot USD price for a symbol via CMC listings."""
    r = requests.get(
        f"{CMC_BASE}/v2/cryptocurrency/quotes/latest",
        headers={"X-CMC_PRO_API_KEY": _key(), "Accept": "application/json"},
        params={"symbol": symbol.upper(), "convert": "USD"},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()["data"][symbol.upper()]
    entry = payload[0] if isinstance(payload, list) else payload
    return float(entry["quote"]["USD"]["price"])
