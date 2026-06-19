"""Execution adapter — the self-custody signing + swap layer (TWAK).

Every trade is signed locally by TWAK (keys in the OS keychain), so the agent
process never sees a raw private key and there is no custodial step. This is the
load-bearing "Best Use of TWAK" surface.

Aligned to the real `@trustwallet/cli` v0.19.x contract (verified live):
  quote:    twak swap <from> <to> --usd <amt> --chain bsc --quote-only --json
  execute:  twak swap <from> <to> --usd <amt> --chain bsc --slippage <pct> --password <pw>
Quote JSON fields: input / output / minReceived / provider / priceImpact.
`--usd` mode prints a human line before the JSON, so we extract the JSON object
rather than parsing whole stdout.

In dry-run mode no `twak` calls are made: quotes are synthetic and no tx is sent,
so the full decide->guard pipeline can run before the wallet is funded.
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
    slippage_bps: float       # from quoted priceImpact
    output: str = ""          # e.g. "0.01718 BNB"
    min_received: str = ""
    provider: str = ""


@dataclass(frozen=True)
class SwapResult:
    tx_hash: str | None
    dry_run: bool
    detail: str


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of stdout (TWAK may prepend a human line)."""
    start = text.find("{")
    if start == -1:
        raise TwakError(f"no JSON in twak output: {text[:200]}")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return obj
    except json.JSONDecodeError as e:
        raise TwakError(f"bad JSON from twak: {text[start:start+200]}") from e


def _twak(args: list[str], timeout: int = 120) -> dict:
    if shutil.which("npx") is None:
        raise TwakError("npx not found; cannot reach the TWAK CLI")
    proc = subprocess.run(
        ["npx", "twak", "--no-analytics", *args, "--json"],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise TwakError((proc.stderr or proc.stdout or "twak failed").strip()[:300])
    return _extract_json(proc.stdout)


def _price_impact_bps(raw: object) -> float:
    """Convert a priceImpact percentage (e.g. '0.5') to basis points."""
    try:
        return float(str(raw)) * 100.0
    except (TypeError, ValueError):
        return 0.0


class Executor:
    """Wraps TWAK for quotes + swaps. Set dry_run=True to stub all network I/O.

    password: the wallet password TWAK requires to sign an execution. Read from
    the environment by the caller (never hardcoded). None => dry-run / quote only.
    """

    def __init__(self, chain: str = "bsc", dry_run: bool = False,
                 password: str | None = None, slippage_pct: float = 1.0):
        self.chain = chain
        self.dry_run = dry_run
        self._password = password
        self.slippage_pct = slippage_pct

    def quote(self, sell: str, buy: str, amount_usd: float) -> SwapQuote:
        if self.dry_run:
            return SwapQuote(sell, buy, amount_usd, slippage_bps=25.0,
                             output="(dry-run)", provider="dry-run")
        out = _twak(["swap", sell, buy, "--usd", str(amount_usd),
                     "--chain", self.chain, "--quote-only"])
        return SwapQuote(
            sell_symbol=sell, buy_symbol=buy, amount_usd=amount_usd,
            slippage_bps=_price_impact_bps(out.get("priceImpact", 0)),
            output=str(out.get("output", "")),
            min_received=str(out.get("minReceived", "")),
            provider=str(out.get("provider", "")),
        )

    def execute(self, q: SwapQuote) -> SwapResult:
        if self.dry_run:
            return SwapResult(None, True,
                              f"[dry-run] would swap ${q.amount_usd} {q.sell_symbol}->{q.buy_symbol}")
        if not self._password:
            raise TwakError("wallet password required to execute (set in env, never hardcoded)")
        out = _twak(["swap", q.sell_symbol, q.buy_symbol, "--usd", str(q.amount_usd),
                     "--chain", self.chain, "--slippage", str(self.slippage_pct),
                     "--password", self._password])
        tx = out.get("txHash") or out.get("hash") or out.get("transactionHash")
        return SwapResult(tx_hash=tx, dry_run=False,
                          detail=str(out.get("status", out.get("provider", "submitted"))))
