"""Build the guardrail's Portfolio from the agent's REAL on-chain balances.

Reads BSC holdings (with USD valuation) from the live TWAK CLI and fuses them
with the persisted peak-equity / daily-turnover state so the drawdown breaker
and daily cap operate on real, continuous history.
"""
from __future__ import annotations

import json
import subprocess

from .guardrails import Portfolio
from .state import RiskState, today_utc


def read_bsc_holdings() -> dict[str, float]:
    """Symbol -> USD value for BSC holdings, from `twak wallet portfolio`."""
    out = subprocess.run(
        ["npx", "twak", "--no-analytics", "wallet", "portfolio", "--json"],
        capture_output=True, text=True, timeout=90,
    )
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout or "twak portfolio failed").strip()[:200])
    start = out.stdout.find("[")
    arr = json.loads(out.stdout[start:]) if start != -1 else []
    import math
    holdings: dict[str, float] = {}
    for x in arr:
        if x.get("chain") != "bsc":
            continue
        try:
            usd = float(x.get("usdValue") or 0)
        except (TypeError, ValueError) as e:
            # A balance whose USD value won't parse must not silently become 0 and
            # then lift the percentage caps elsewhere — reject the read (M-3).
            raise RuntimeError(f"unparseable usdValue for {x.get('symbol')}: {e}") from e
        # Reject non-finite or absurd values (a poisoned/mis-scaled balance would
        # inflate equity and therefore every percent-of-equity cap).
        if not math.isfinite(usd) or usd < 0 or usd > 1e12:
            raise RuntimeError(f"implausible usdValue {usd} for {x.get('symbol')}")
        if usd > 0:
            sym = str(x["symbol"]).upper()
            holdings[sym] = holdings.get(sym, 0.0) + usd
    return holdings


def build_live_portfolio(state: RiskState, day: str | None = None) -> Portfolio:
    """Real BSC portfolio + persisted peak/daily state -> a guardrail Portfolio."""
    day = day or today_utc()
    holdings = read_bsc_holdings()
    equity = round(sum(holdings.values()), 6)

    state.roll_day(day)          # reset daily counter if the UTC day changed
    state.observe_equity(equity)  # update high-water mark BEFORE measuring drawdown

    return Portfolio(
        equity_usd=equity,
        peak_equity_usd=state.peak_equity_usd,
        holdings_usd=holdings,
        traded_today_usd=state.traded_today(day),
    )
