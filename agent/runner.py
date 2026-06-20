"""Autonomous cycle runner (review #2 + #7) — the hands-off heart.

One invocation = one safe cycle:
  single-instance lock  ->  strategy pass (live)  ->  daily-qualify net  ->  save

Designed to be fired by a scheduler (launchd/cron) every hour. The lock stops an
overlapping run from double-trading. The daily-qualify net guarantees >=1 trade
per UTC day (competition ranking) but only forces a trade late in the day, so the
strategy owns the day first.

  PYTHONPATH=. .venv/bin/python -m agent.runner
"""
from __future__ import annotations

import datetime as _dt

from . import daily_qualify, portfolio, state
from .config import RiskConfig
from .guardrails import ProposedTrade
from .lock import AlreadyRunning, single_instance
from .orchestrator import attempt_trade, strategy_pass

QUALIFY_AFTER_UTC_HOUR = 20  # strategy owns the day; force a trade only late


def should_qualify(*, ensure_daily: bool, has_traded_today: bool,
                   hour_utc: int, qualify_after_hour: int) -> bool:
    """Pure decision: do we need to force a qualifying trade this cycle?"""
    return ensure_daily and (not has_traded_today) and hour_utc >= qualify_after_hour


def run_cycle(*, ensure_daily: bool = True,
              qualify_after_hour: int = QUALIFY_AFTER_UTC_HOUR,
              now: _dt.datetime | None = None) -> dict:
    now = now or _dt.datetime.now(_dt.timezone.utc)
    day = now.strftime("%Y-%m-%d")
    st = state.load()

    # 1. Strategy pass (live, executes through the full safety pipeline).
    strategy_pass(st, day, dry_run=False, execute=True)

    # 2. Daily-qualify net — never lose ranking to a zero-trade day.
    if should_qualify(ensure_daily=ensure_daily, has_traded_today=st.has_traded_on(day),
                      hour_utc=now.hour, qualify_after_hour=qualify_after_hour):
        pf = portfolio.build_live_portfolio(st, day)
        pair = daily_qualify.pick_qualifying_pair(pf.holdings_usd)
        if pair is None:
            print("[qualify] no eligible verified pair held — cannot self-trade")
        else:
            sell, buy = pair
            size = daily_qualify.qualifying_size(
                pf.equity_usd, RiskConfig().per_trade_cap_pct, pf.held(sell))
            if size <= 0:
                print("[qualify] sized to zero — skipping")
            else:
                print(f"[qualify] daily-qualify trade {sell}->{buy} ${size:.2f}")
                attempt_trade(ProposedTrade(sell, buy, size), pf, st, day,
                              dry_run=False, execute=True, label="qualify")

    state.save(st)
    out = {"traded_today": st.has_traded_on(day), "trades_total": st.trades_total, "day": day}
    print(f"[cycle]  traded_today={out['traded_today']} trades_total={out['trades_total']}")
    return out


def main() -> int:
    try:
        with single_instance():
            run_cycle()
        return 0
    except AlreadyRunning as e:
        print(f"[lock]   {e} — exiting (no double-trade)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
