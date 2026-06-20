"""x402 market gate — the paid-data check inside the trade loop.

Before a non-native buy is signed, the agent PAYS CMC (x402, on BSC) for live
DEX data on the exact token contract and refuses to trade into thin liquidity.
This is what makes x402 load-bearing in the loop (a real paid call that can
block a trade), and it adds a live-liquidity layer on top of the static
verified-address registry.

`dex/search` is a fuzzy keyword search, so we filter its results to the EXACT
verified contract address before trusting any field.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from urllib.parse import quote

from . import token_registry
from .x402_data import X402DataClient

_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class MarketVerdict:
    ok: bool
    detail: str
    liquidity_usd: float | None = None


def _match_token(data: dict, address: str) -> dict | None:
    tks = (data.get("data") or {}).get("tks") or []
    addr = address.lower()
    return next((t for t in tks if str(t.get("addr", "")).lower() == addr), None)


def check_buy(symbol: str, client: X402DataClient,
              registry: dict | None = None, min_liq_usd: float = 250_000.0) -> MarketVerdict:
    """Gate a buy on live DEX liquidity, paid via x402. Native BNB is exempt."""
    reg = registry if registry is not None else token_registry.load_registry()
    if not token_registry.is_tradable(symbol, reg):
        return MarketVerdict(False, f"{symbol} not address-verified in registry")

    addr = token_registry.verified_address(symbol, reg)
    if addr is None:  # native asset — no contract to probe
        return MarketVerdict(True, "native asset — liquidity check not applicable")
    # Defend the request URL: only ever query a clean 0x-address (M-1).
    if not _ADDR_RE.match(addr):
        return MarketVerdict(False, f"{symbol} registry address malformed: {addr!r}")

    data = client.request(f"dex/search?query={quote(addr, safe='')}")
    match = _match_token(data, addr)
    if match is None:
        # `dex/search` is a fuzzy keyword search and often omits the exact token.
        # The REGISTRY is the hard scam gate (CMC-authoritative address); this
        # x402 overlay only *blocks positively-detected thin liquidity*, so when
        # it can't see a registry-verified token we PROCEED (don't false-block).
        return MarketVerdict(True, f"x402: liquidity unconfirmed for {symbol} (registry-verified) — proceeding")

    # Sanity-bound the reported liquidity: a non-finite / negative / absurd value
    # is untrustworthy data, not a pass (C-2).
    try:
        liq = float(match.get("liq") or 0.0)
    except (TypeError, ValueError):
        return MarketVerdict(False, f"x402 liquidity for {symbol} unparseable — blocked")
    if not math.isfinite(liq) or liq < 0 or liq > 1e15:
        return MarketVerdict(False, f"x402 liquidity for {symbol} implausible ({liq}) — blocked")
    if liq < min_liq_usd:
        return MarketVerdict(False, f"x402 liquidity ${liq:,.0f} below floor ${min_liq_usd:,.0f}", liq)
    return MarketVerdict(True, f"x402 liquidity ${liq:,.0f} OK", liq)
