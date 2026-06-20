"""Daily-qualify trade (review #5) — never lose ranking to a zero-trade day.

The competition requires >=1 trade per day or the wallet isn't ranked. On a day
where the strategy chose to hold, the loop performs one minimal QUALIFYING trade:
a stable->stable swap (both address-verified, ~$1 each => near-zero price risk),
sized within the per-trade cap. It satisfies the rule without taking a view.
"""
from __future__ import annotations

from . import token_registry

# Preference order of stables to route a qualifying swap through.
STABLE_PREF = ["USDC", "USDT", "FDUSD", "USD1"]


def needs_qualifying_trade(has_traded_today: bool) -> bool:
    return not has_traded_today


def pick_qualifying_pair(holdings_usd: dict[str, float], registry: dict | None = None,
                         min_held_usd: float = 0.30) -> tuple[str, str] | None:
    """Choose (sell, buy) for the lowest-risk compliant trade, or None.

    Prefers stable->different-stable. Falls back to selling a sliver of the
    largest verified holding into a stable. Both legs must be address-verified.
    """
    reg = registry if registry is not None else token_registry.load_registry()

    def ok(sym: str) -> bool:
        return token_registry.is_tradable(sym, reg)

    # 1. stable -> a different stable (near-zero price risk)
    for sell in STABLE_PREF:
        if holdings_usd.get(sell, 0.0) >= min_held_usd and ok(sell):
            for buy in STABLE_PREF:
                if buy != sell and ok(buy):
                    return (sell, buy)

    # 2. fallback: largest verified holding -> a stable
    for sym, usd in sorted(holdings_usd.items(), key=lambda kv: -kv[1]):
        if usd >= min_held_usd and ok(sym):
            buy = "USDC" if sym != "USDC" else "USDT"
            if ok(buy):
                return (sym, buy)
    return None


def qualifying_size(equity_usd: float, per_trade_cap_pct: float,
                    held_usd: float, target: float = 0.50) -> float:
    """Size a qualifying trade within the per-trade cap and what's held."""
    cap = per_trade_cap_pct / 100.0 * equity_usd
    return round(max(0.0, min(target, cap * 0.9, held_usd * 0.95)), 4)
