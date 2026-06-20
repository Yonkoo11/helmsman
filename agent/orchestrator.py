"""Helmsman orchestrator — the trade pipeline, shared by every trade.

  registry gate -> quote -> GUARDRAIL -> x402 liquidity gate -> TWAK sign
                -> confirm on-chain -> record state

`attempt_trade` runs one proposed trade through that full pipeline and is reused
by both the strategy pass and the daily-qualify net (agent/runner.py), so no
trade can bypass a safety layer. Live mode reads the REAL BSC portfolio and the
persisted peak/daily risk state; a trade is only recorded once the chain confirms.

  python -m agent.orchestrator --dry-run     # synthetic, no creds, no tx
  python -m agent.orchestrator               # live read; signs only with --execute
  python -m agent.orchestrator --execute     # live, signs + sends
"""
from __future__ import annotations

import argparse
import os
import sys

from . import data_cmc, market_gate, portfolio, regime, state, strategy, token_registry
from .execution import Executor
from .guardrails import Portfolio, ProposedTrade, evaluate
from .regime import Signals
from .state import RiskState
from .x402_data import X402DataClient

CORE = "BNB"


def _synthetic_signals(fg: float) -> Signals:
    """Dry-run signals: regime driven by F&G, momentum/macro neutral."""
    cls = "Extreme Fear" if fg <= 25 else "Extreme Greed" if fg >= 75 else "Neutral"
    return Signals(fear_greed=fg, momentum_7d_pct=0.0, momentum_24h_pct=0.0,
                   macro_mcap_24h_pct=0.0, btc_dom_24h_change=0.0, classification=cls)


def _synthetic_portfolio() -> Portfolio:
    return Portfolio(equity_usd=1000.0, peak_equity_usd=1000.0,
                     holdings_usd={"USDT": 700.0, "BNB": 300.0}, traded_today_usd=0.0)


def attempt_trade(trade: ProposedTrade, pf: Portfolio, st: RiskState, day: str, *,
                  dry_run: bool, execute: bool, label: str = "trade") -> bool:
    """Run one trade through the full pipeline. Returns True iff confirmed+recorded.

    Does NOT persist state — the caller saves once per cycle.
    """
    # Registry gate (live): both legs must be address-verified (anti scam-ticker).
    if not dry_run:
        for leg in (trade.sell_symbol, trade.buy_symbol):
            if not token_registry.is_tradable(leg):
                print(f"[registry] {leg} not address-verified — {label} BLOCKED")
                return False

    ex = Executor(chain="bsc", dry_run=dry_run,
                  password=None if dry_run else os.getenv("TWAK_WALLET_PASSWORD"))
    q = ex.quote(trade.sell_symbol, trade.buy_symbol, trade.notional_usd)
    decision = evaluate(ProposedTrade(trade.sell_symbol, trade.buy_symbol,
                                      trade.notional_usd, q.slippage_bps), pf)
    print(f"[guard]  {decision.log_line()}")
    if not decision.allowed:
        print(f"[guard]  {label} BLOCKED by guardrails — not signed")
        return False

    if not (execute or dry_run):
        print("[stop]   guardrail PASSED; x402 gate + signing run at --execute")
        return False

    # x402 PAID market gate (live): pay CMC for live DEX liquidity on the buy token.
    if not dry_run:
        mkt = X402DataClient()
        verdict = market_gate.check_buy(trade.buy_symbol, mkt)
        print(f"[x402]   {verdict.detail} (data spend ${mkt.spent_usd():.2f})")
        if not verdict.ok:
            print(f"[x402]   {label} BLOCKED by liquidity gate — not signed")
            return False

    result = ex.execute(q)
    if result.dry_run:
        print(f"[exec]   {result.detail}")
        return False
    print(f"[exec]   submitted tx={result.tx_hash}")
    if result.tx_hash and ex.confirm(result.tx_hash):
        st.record_trade(trade.notional_usd, day)
        print(f"[confirm] on-chain confirmed; recorded. trades_total={st.trades_total}")
        print(f"[proof]  https://bscscan.com/tx/{result.tx_hash}")
        return True
    print("[confirm] NOT confirmed — trade not recorded (state safe)")
    return False


def strategy_pass(st: RiskState, day: str, *, dry_run: bool, execute: bool,
                  fg_value: float | None = None) -> bool:
    """One regime-driven decision + (maybe) trade. Returns True iff it traded."""
    signals = _synthetic_signals(20.0 if fg_value is None else fg_value) if dry_run else data_cmc.fetch_signals(CORE)
    rs = regime.score(signals)
    print(f"[signal] FG={signals.fear_greed:.0f}({signals.classification}) "
          f"mom7d={signals.momentum_7d_pct:+.1f}% mcap24h={signals.macro_mcap_24h_pct:+.2f}% "
          f"btcDomΔ={signals.btc_dom_24h_change:+.2f}")
    print(f"[regime] {rs.log_line()}")

    pf = _synthetic_portfolio() if dry_run else portfolio.build_live_portfolio(st, day)
    print(f"[state]  equity=${pf.equity_usd:,.2f} peak=${pf.peak_equity_usd:,.2f} "
          f"drawdown={pf.drawdown_pct():.1f}% tradedToday=${pf.traded_today_usd:,.2f} "
          f"holdings={ {k: round(v,2) for k,v in pf.holdings_usd.items()} }")

    trade = strategy.decide(rs, pf)
    if trade is None:
        print("[decide] hold — no trade proposed this pass")
        return False
    print(f"[decide] propose swap ${trade.notional_usd:,.2f} {trade.sell_symbol}->{trade.buy_symbol}")
    return attempt_trade(trade, pf, st, day, dry_run=dry_run, execute=execute)


def run_once(dry_run: bool, execute: bool, fg_value: float | None) -> int:
    day = state.today_utc()
    st = state.load()
    strategy_pass(st, day, dry_run=dry_run, execute=execute, fg_value=fg_value)
    if not dry_run:
        state.save(st)
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
