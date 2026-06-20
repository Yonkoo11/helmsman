"""Strategy — turns the multi-signal regime into a proposed trade.

The regime engine (agent/regime.py) blends sentiment + momentum + macro into a
risk-appetite score. This module maps that score to an action:
  risk-on  -> accumulate the core asset (buy with a stable)
  risk-off -> de-risk into a stable
  neutral  -> hold

The strategy only PROPOSES — the guardrail engine has the final say.
"""
from __future__ import annotations

from .guardrails import Portfolio, ProposedTrade
from .regime import RegimeScore

CORE_ASSET = "ETH"   # accumulate target in risk-on (BEP-20, competition-eligible)
STABLE = "USDT"      # de-risk destination in risk-off


def decide(regime: RegimeScore, pf: Portfolio, trade_pct: float = 8.0) -> ProposedTrade | None:
    """Propose one trade from the regime + current portfolio, or None to hold."""
    notional = trade_pct / 100.0 * pf.equity_usd

    if regime.label == "risk-on":
        size = min(notional, pf.held(STABLE))
        return ProposedTrade(STABLE, CORE_ASSET, size) if size > 0 else None

    if regime.label == "risk-off":
        size = min(notional, pf.held(CORE_ASSET))
        return ProposedTrade(CORE_ASSET, STABLE, size) if size > 0 else None

    return None  # neutral -> hold
