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

try:  # load project .env (gitignored) so CMC_API_KEY is available
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv ships with bnbagent; degrade gracefully
    pass

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


def _quote(symbol: str) -> dict:
    r = requests.get(
        f"{CMC_BASE}/v2/cryptocurrency/quotes/latest",
        headers={"X-CMC_PRO_API_KEY": _key(), "Accept": "application/json"},
        params={"symbol": symbol.upper(), "convert": "USD"},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()["data"][symbol.upper()]
    entry = payload[0] if isinstance(payload, list) else payload
    return entry["quote"]["USD"]


def quote_usd(symbol: str) -> float:
    """Spot USD price for a symbol via CMC listings."""
    return float(_quote(symbol)["price"])


def momentum(symbol: str) -> tuple[float, float, float]:
    """(24h %change, 7d %change, 24h volume %change) for a symbol — the trend stream."""
    u = _quote(symbol)
    return (float(u.get("percent_change_24h") or 0.0),
            float(u.get("percent_change_7d") or 0.0),
            float(u.get("volume_change_24h") or 0.0))


def global_macro() -> tuple[float, float]:
    """(total market-cap 24h %change, BTC dominance 24h pp change) — the macro stream."""
    r = requests.get(
        f"{CMC_BASE}/v1/global-metrics/quotes/latest",
        headers={"X-CMC_PRO_API_KEY": _key(), "Accept": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    d = r.json()["data"]
    mcap_24h = float(d["quote"]["USD"].get("total_market_cap_yesterday_percentage_change") or 0.0)
    btc_dom_chg = float(d.get("btc_dominance_24h_percentage_change") or 0.0)
    return (mcap_24h, btc_dom_chg)


def fetch_signals(core_symbol: str = "BNB"):
    """Assemble the multi-stream regime snapshot from 3 live CMC endpoints."""
    from .regime import Signals
    fg = fear_greed()
    mom_24h, mom_7d, _vol = momentum(core_symbol)
    mcap_24h, btc_dom_chg = global_macro()
    return Signals(
        fear_greed=fg.value,
        momentum_7d_pct=mom_7d,
        momentum_24h_pct=mom_24h,
        macro_mcap_24h_pct=mcap_24h,
        btc_dom_24h_change=btc_dom_chg,
        classification=fg.classification,
    )
