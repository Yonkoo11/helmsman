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
    holdings: dict[str, float] = {}
    for x in arr:
        if x.get("chain") != "bsc":
            continue
        usd = float(x.get("usdValue") or 0)
        if usd > 0:
            holdings[str(x["symbol"]).upper()] = holdings.get(str(x["symbol"]).upper(), 0.0) + usd
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
