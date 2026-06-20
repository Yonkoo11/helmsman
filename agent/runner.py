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
from .orchestrator import attempt_trade, reconcile_pending, strategy_pass
from .x402_data import X402BudgetExhausted

# Force the daily-qualify by MIDDAY UTC, not late evening: if the host sleeps in
# the evening the late cutoff could miss the trade entirely (DQ). Noon gives the
# strategy the morning to trade organically, then a wide afternoon catch window.
QUALIFY_AFTER_UTC_HOUR = 12


def should_qualify(*, ensure_daily: bool, has_traded_today: bool,
                   hour_utc: int, qualify_after_hour: int) -> bool:
    """Pure decision: do we need to force a qualifying trade this cycle?"""
    return ensure_daily and (not has_traded_today) and hour_utc >= qualify_after_hour


def run_cycle(*, ensure_daily: bool = True,
              qualify_after_hour: int = QUALIFY_AFTER_UTC_HOUR,
              now: _dt.datetime | None = None) -> dict:
    now = now or _dt.datetime.now(_dt.timezone.utc)
    day = now.strftime("%Y-%m-%d")
    st = state.load()  # CorruptStateError propagates -> main halts (don't zero risk)

    # 0. Reconcile any pending (slow-confirm) tx before trading again (H-1).
    if not reconcile_pending(st, day):
        state.save(st)
        return {"traded_today": st.has_traded_on(day), "trades_total": st.trades_total,
                "day": day, "blocked": "pending-tx"}

    # 1. Strategy pass (live). A transient CMC/RPC/x402 error logs and continues;
    #    a data-spend budget exhaustion HALTS the cycle (no forced qualify) — H-3.
    halted_budget = False
    try:
        strategy_pass(st, day, dry_run=False, execute=True)
    except X402BudgetExhausted as e:
        halted_budget = True
        print(f"[halt]   data-spend budget exhausted: {e} — skipping qualify this cycle")
    except Exception as e:  # noqa: BLE001 — resilience: never let one cycle die
        print(f"[error]  strategy pass failed: {type(e).__name__}: {e} — continuing")

    # 2. Daily-qualify net — never lose ranking to a zero-trade day. Skipped if
    #    the data budget halted this cycle (don't spend more chasing a forced trade).
    if not halted_budget and should_qualify(
            ensure_daily=ensure_daily, has_traded_today=st.has_traded_on(day),
            hour_utc=now.hour, qualify_after_hour=qualify_after_hour):
        try:
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
        except Exception as e:  # noqa: BLE001
            print(f"[error]  daily-qualify failed: {type(e).__name__}: {e}")

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
    except state.CorruptStateError as e:
        # Refuse to trade on unreadable risk history rather than resetting it.
        print(f"[halt]   {e} — refusing to trade; fix or remove the state file")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
