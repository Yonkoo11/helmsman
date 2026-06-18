"""Execution adapter — the self-custody signing + swap layer (TWAK).

Every trade is signed locally by TWAK (keys in the OS keychain), so the agent
process never sees a raw private key and there is no custodial step. This is the
load-bearing "Best Use of TWAK" surface.

In dry-run mode no `twak` calls are made: quotes are synthetic and no tx is sent,
so the full decide->guard pipeline can be exercised before credentials exist.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass


class TwakError(RuntimeError):
    pass


@dataclass(frozen=True)
class SwapQuote:
    sell_symbol: str
    buy_symbol: str
    amount_usd: float
    slippage_bps: float


@dataclass(frozen=True)
class SwapResult:
    tx_hash: str | None
    dry_run: bool
    detail: str


def _twak(args: list[str], timeout: int = 90) -> dict:
    """Run a `twak ... --json` command and parse its JSON output."""
    if shutil.which("npx") is None:
        raise TwakError("npx not found; cannot reach the TWAK CLI")
    proc = subprocess.run(
        ["npx", "twak", "--no-analytics", *args, "--json"],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise TwakError((proc.stderr or proc.stdout or "twak failed").strip())
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise TwakError(f"twak returned non-JSON: {proc.stdout[:200]}") from e


class Executor:
    """Wraps TWAK for quotes + swaps. Set dry_run=True to stub all network I/O."""

    def __init__(self, chain: str = "bsc", dry_run: bool = False):
        self.chain = chain
        self.dry_run = dry_run

    def quote(self, sell: str, buy: str, amount_usd: float) -> SwapQuote:
        if self.dry_run:
            # Synthetic, deterministic quote for pipeline testing.
            return SwapQuote(sell, buy, amount_usd, slippage_bps=25.0)
        out = _twak(["swap", str(amount_usd), sell, buy, "--chain", self.chain, "--quote-only"])
        return SwapQuote(sell, buy, amount_usd, slippage_bps=float(out.get("slippageBps", 0)))

    def execute(self, q: SwapQuote) -> SwapResult:
        if self.dry_run:
            return SwapResult(tx_hash=None, dry_run=True,
                              detail=f"[dry-run] would swap ${q.amount_usd} {q.sell_symbol}->{q.buy_symbol}")
        out = _twak(["swap", str(q.amount_usd), q.sell_symbol, q.buy_symbol, "--chain", self.chain, "--execute"])
        return SwapResult(tx_hash=out.get("txHash"), dry_run=False,
                          detail=out.get("status", "submitted"))
