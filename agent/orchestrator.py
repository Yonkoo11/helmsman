"""Helmsman orchestrator — one pass of the trade loop.

  read signal  ->  strategy proposes  ->  GUARDRAIL vets  ->  TWAK signs+sends

Run `python -m agent.orchestrator --dry-run` to exercise the whole pipeline with
a synthetic signal + portfolio and no credentials. Drop --dry-run (with
CMC_API_KEY + TWAK creds + a funded agent wallet) to trade live.
"""
from __future__ import annotations

import argparse
import sys

from . import data_cmc, strategy
from .data_cmc import Signal
from .execution import Executor
from .guardrails import Portfolio, evaluate


def _synthetic_signal(value: float) -> Signal:
    cls = "Extreme Fear" if value <= 25 else "Extreme Greed" if value >= 75 else "Neutral"
    return Signal(name="fear_greed", value=value, classification=cls)


def _synthetic_portfolio() -> Portfolio:
    return Portfolio(
        equity_usd=1000.0,
        peak_equity_usd=1000.0,
        holdings_usd={"USDT": 700.0, "BNB": 300.0},
        traded_today_usd=0.0,
    )


def run_once(dry_run: bool, fg_value: float | None) -> int:
    # 1. READ a signal.
    if dry_run:
        signal = _synthetic_signal(20.0 if fg_value is None else fg_value)
    else:
        signal = data_cmc.fear_greed()
    print(f"[read]   signal {signal.name}={signal.value:.0f} ({signal.classification})")

    # 2. Load portfolio (synthetic in dry-run; TWAK portfolio when live).
    pf = _synthetic_portfolio()  # live portfolio wiring lands with TWAK creds
    print(f"[state]  equity=${pf.equity_usd:,.0f} drawdown={pf.drawdown_pct():.1f}% "
          f"holdings={pf.holdings_usd}")

    # 3. STRATEGY proposes.
    trade = strategy.decide(signal, pf)
    if trade is None:
        print("[decide] hold — no trade proposed this pass")
        return 0
    print(f"[decide] propose swap ${trade.notional_usd:,.2f} "
          f"{trade.sell_symbol}->{trade.buy_symbol}")

    # 4. Price the swap, then GUARDRAIL vets it (final say).
    ex = Executor(chain="bsc", dry_run=dry_run)
    q = ex.quote(trade.sell_symbol, trade.buy_symbol, trade.notional_usd)
    vetted = type(trade)(trade.sell_symbol, trade.buy_symbol,
                         trade.notional_usd, q.slippage_bps)
    decision = evaluate(vetted, pf)
    print(f"[guard]  {decision.log_line()}")
    if not decision.allowed:
        print("[guard]  trade BLOCKED by guardrails — not signed")
        return 0

    # 5. EXECUTE via TWAK local signing (self-custody, no custodial step).
    result = ex.execute(q)
    if result.dry_run:
        print(f"[exec]   {result.detail}")
    else:
        print(f"[exec]   submitted tx={result.tx_hash} ({result.detail})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Helmsman — one trade-loop pass")
    p.add_argument("--dry-run", action="store_true",
                   help="synthetic signal + portfolio, no creds, no tx")
    p.add_argument("--fg", type=float, default=None,
                   help="override Fear&Greed value in dry-run (0-100)")
    args = p.parse_args(argv)
    try:
        return run_once(dry_run=args.dry_run, fg_value=args.fg)
    except data_cmc.MissingCMCKey as e:
        print(f"[error]  {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
