"""Phase 1 (b) live proof: one real TWAK-signed BNB->USDT swap on BSC mainnet.

Reads the agent's real balance, sizes a tiny swap that leaves gas, runs it
through the guardrail under a RELAXED TEST PROFILE (so a ~$1.5 trade on a ~$4
account is allowed), and signs via TWAK (keychain). The production caps in
RiskConfig() are NOT changed — this profile is local to this proof script.

Usage: .venv/bin/python scripts/live_proof.py [--usd 1.5] [--execute]
Without --execute it stops at the guardrail verdict (no signing).
"""
from __future__ import annotations

import argparse
import json
import subprocess

from agent.config import RiskConfig
from agent.execution import Executor
from agent.guardrails import Portfolio, ProposedTrade, evaluate

# Relaxed profile for a tiny-account proof ONLY. Production stays RiskConfig().
TEST_PROFILE = RiskConfig(
    dust_floor_usd=0.50,
    per_trade_cap_pct=60.0,
    daily_turnover_cap_pct=100.0,
    max_position_pct=100.0,
)


def bsc_balance() -> tuple[float, float]:
    """Return (BNB available, USD value) from the live TWAK CLI."""
    out = subprocess.run(
        ["npx", "twak", "--no-analytics", "wallet", "balance", "--chain", "bsc", "--json"],
        capture_output=True, text=True, timeout=60,
    ).stdout
    obj = json.loads(out[out.find("{"):])
    return float(obj["available"]), float(obj["totalUsd"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usd", type=float, default=1.5, help="swap notional in USD")
    ap.add_argument("--execute", action="store_true", help="actually sign + send")
    args = ap.parse_args()

    bnb, equity = bsc_balance()
    print(f"[balance] {bnb:.6f} BNB  (~${equity:.2f}) on bsc")

    # Keep ~$1 of BNB for gas; never swap more than 40% in this proof.
    trade_usd = min(args.usd, max(0.0, equity - 1.0), equity * 0.40)
    if trade_usd < 0.5:
        print(f"[abort]  sized trade ${trade_usd:.2f} too small after gas reserve")
        return 1

    pf = Portfolio(equity_usd=equity, peak_equity_usd=equity,
                   holdings_usd={"BNB": equity}, traded_today_usd=0.0)
    print(f"[propose] swap ${trade_usd:.2f} BNB->USDT  (TEST PROFILE — prod caps unchanged)")

    ex = Executor(chain="bsc", dry_run=False, slippage_pct=1.0)
    q = ex.quote("BNB", "USDT", trade_usd)
    vetted = ProposedTrade("BNB", "USDT", trade_usd, q.slippage_bps)
    decision = evaluate(vetted, pf, TEST_PROFILE)
    print(f"[quote]   out={q.output} minRecv={q.min_received} impact={q.slippage_bps:.1f}bps via {q.provider}")
    print(f"[guard]   {decision.log_line()}")
    if not decision.allowed:
        print("[guard]   BLOCKED — not signed")
        return 0
    if not args.execute:
        print("[stop]    guardrail PASSED; rerun with --execute to sign + send")
        return 0

    res = ex.execute(q)
    print(f"[exec]    tx={res.tx_hash}  ({res.detail})")
    if res.tx_hash:
        print(f"[proof]   https://bscscan.com/tx/{res.tx_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
