"""Strategy — turns CMC signals into a proposed trade.

Phase 1 keeps this intentionally simple: a Fear & Greed regime rule. Extreme
fear accumulates a core asset; extreme greed de-risks into a stable; the middle
holds. Phase 2 blends funding rates + derivatives positioning into the regime.

The strategy only PROPOSES — the guardrail engine has the final say.
"""
from __future__ import annotations

from .data_cmc import Signal
from .guardrails import Portfolio, ProposedTrade

CORE_ASSET = "BNB"   # accumulate target on fear
STABLE = "USDT"      # de-risk destination on greed


def decide(signal: Signal, pf: Portfolio, trade_pct: float = 8.0) -> ProposedTrade | None:
    """Propose one trade from the signal + current portfolio, or None to hold."""
    notional = trade_pct / 100.0 * pf.equity_usd

    # Extreme fear -> accumulate the core asset (buy the dip).
    if signal.value <= 25:
        size = min(notional, pf.held(STABLE))
        if size <= 0:
            return None
        return ProposedTrade(STABLE, CORE_ASSET, size)

    # Extreme greed -> take risk off into a stable.
    if signal.value >= 75:
        size = min(notional, pf.held(CORE_ASSET))
        if size <= 0:
            return None
        return ProposedTrade(CORE_ASSET, STABLE, size)

    # Neutral -> hold.
    return None
