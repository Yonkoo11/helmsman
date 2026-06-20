"""Helmsman orchestrator — one pass of the trade loop.

  read signal  ->  strategy proposes  ->  GUARDRAIL vets  ->  TWAK signs+sends
                                                           ->  confirm -> record

Live mode reads the REAL BSC portfolio and the persisted peak/daily risk state,
so the drawdown breaker and daily cap operate on continuous history. A trade is
only recorded after the chain confirms it.

  python -m agent.orchestrator --dry-run         # synthetic, no creds, no tx
  python -m agent.orchestrator                   # live read; signs only if --execute
  python -m agent.orchestrator --execute         # live, will sign + send
"""
from __future__ import annotations

import argparse
import os
import sys

from . import data_cmc, portfolio, state, strategy
from .data_cmc import Signal
from .execution import Executor
from .guardrails import Portfolio, ProposedTrade, evaluate


def _synthetic_signal(value: float) -> Signal:
    cls = "Extreme Fear" if value <= 25 else "Extreme Greed" if value >= 75 else "Neutral"
    return Signal(name="fear_greed", value=value, classification=cls)


def _synthetic_portfolio() -> Portfolio:
    return Portfolio(equity_usd=1000.0, peak_equity_usd=1000.0,
                     holdings_usd={"USDT": 700.0, "BNB": 300.0}, traded_today_usd=0.0)


def run_once(dry_run: bool, execute: bool, fg_value: float | None) -> int:
    day = state.today_utc()
    st = state.load()

    # 1. READ a signal.
    signal = _synthetic_signal(20.0 if fg_value is None else fg_value) if dry_run else data_cmc.fear_greed()
    print(f"[read]   signal {signal.name}={signal.value:.0f} ({signal.classification})")

    # 2. Load portfolio — synthetic in dry-run, real BSC + persisted state when live.
    pf = _synthetic_portfolio() if dry_run else portfolio.build_live_portfolio(st, day)
    print(f"[state]  equity=${pf.equity_usd:,.2f} peak=${pf.peak_equity_usd:,.2f} "
          f"drawdown={pf.drawdown_pct():.1f}% tradedToday=${pf.traded_today_usd:,.2f} "
          f"holdings={ {k: round(v,2) for k,v in pf.holdings_usd.items()} }")

    # 3. STRATEGY proposes.
    trade = strategy.decide(signal, pf)
    if trade is None:
        print("[decide] hold — no trade proposed this pass")
        if not dry_run:
            state.save(st)  # persist the updated peak high-water mark
        return 0
    print(f"[decide] propose swap ${trade.notional_usd:,.2f} {trade.sell_symbol}->{trade.buy_symbol}")

    # 4. Quote, then GUARDRAIL vets (final say).
    ex = Executor(chain="bsc", dry_run=dry_run,
                  password=None if dry_run else os.getenv("TWAK_WALLET_PASSWORD"))
    q = ex.quote(trade.sell_symbol, trade.buy_symbol, trade.notional_usd)
    decision = evaluate(ProposedTrade(trade.sell_symbol, trade.buy_symbol,
                                      trade.notional_usd, q.slippage_bps), pf)
    print(f"[guard]  {decision.log_line()}")
    if not decision.allowed:
        print("[guard]  trade BLOCKED by guardrails — not signed")
        if not dry_run:
            state.save(st)
        return 0

    if not (execute or dry_run):
        print("[stop]   guardrail PASSED; rerun with --execute to sign + send")
        state.save(st)
        return 0

    # 5. EXECUTE via TWAK local signing, then confirm before recording.
    result = ex.execute(q)
    if result.dry_run:
        print(f"[exec]   {result.detail}")
        return 0
    print(f"[exec]   submitted tx={result.tx_hash}")
    if result.tx_hash and ex.confirm(result.tx_hash):
        st.record_trade(trade.notional_usd, day)
        state.save(st)
        print(f"[confirm] on-chain confirmed; recorded. trades_total={st.trades_total}")
        print(f"[proof]  https://bscscan.com/tx/{result.tx_hash}")
    else:
        state.save(st)  # peak persists; trade NOT recorded (unconfirmed/failed)
        print("[confirm] NOT confirmed — trade not recorded (state safe)")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Helmsman — one trade-loop pass")
    p.add_argument("--dry-run", action="store_true", help="synthetic signal + portfolio, no tx")
    p.add_argument("--execute", action="store_true", help="live: actually sign + send")
    p.add_argument("--fg", type=float, default=None, help="override Fear&Greed in dry-run (0-100)")
    args = p.parse_args(argv)
    try:
        return run_once(dry_run=args.dry_run, execute=args.execute, fg_value=args.fg)
    except data_cmc.MissingCMCKey as e:
        print(f"[error]  {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
