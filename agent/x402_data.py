"""x402 paid-data layer — the integration that ties all three sponsors together.

  CMC `/x402/v1/...`  ──(HTTP 402)──>  TWAK signs an on-chain payment authorization
                                       on BSC with the agent's own held stablecoin
                                       ──>  BNB SDK SessionBudgetTracker caps the
                                            cumulative data spend (can refuse a call)

- CMC Agent Hub: the paid data source (real x402 endpoint, $0.01/request).
- TWAK: signs the payment locally (self-custody preserved — no raw key here).
- BNB Agent SDK: `SessionBudgetTracker` enforces a hard per-token spend budget;
  once the session cap is hit the agent stops paying (a real guardrail on money,
  mirroring the trade guardrails).

Verified live 2026-06-20: `/dex/search` offers 7 payment options, incl. USDT on
BSC (0x55d3…7955, permit2) and United Stables (0xcE24…6666, eip3009 gasless).
"""
from __future__ import annotations

from dataclasses import dataclass

from bnbagent.x402 import SessionBudgetTracker

from .execution import _twak

CMC_X402_BASE = "https://pro-api.coinmarketcap.com/x402/v1"
USDT_BSC = "0x55d398326f99059fF775485246999027B3197955"  # 18 decimals on BSC
ONE_CENT = 10 ** 16  # 0.01 USDT in atomic units (CMC charges $0.01/request)


class X402BudgetExhausted(RuntimeError):
    pass


@dataclass
class X402DataClient:
    """Pays CMC x402 endpoints on BSC under a hard session spend budget."""

    chain: str = "bsc"
    asset: str = USDT_BSC
    per_call_atomic: int = ONE_CENT
    session_cap_atomic: int = 20 * ONE_CENT      # $0.20 / session (≈20 requests)
    prefer_method: str = "permit2-exact"
    auto_approve: bool = True                     # one-time approve(Permit2) if needed

    def __post_init__(self) -> None:
        self._budget = SessionBudgetTracker(caps={self.asset: self.session_cap_atomic})

    def spent_usd(self) -> float:
        return self._budget.spent(self.asset) / 1e18

    def quote(self, path: str) -> dict:
        """Read-only preview of payment options (no wallet, no spend)."""
        return _twak(["x402", "quote", f"{CMC_X402_BASE}/{path}"], timeout=60)

    def request(self, path: str) -> dict:
        """Pay $0.01 and fetch an x402-gated CMC endpoint; budget-gated."""
        if self._budget.would_exceed(self.asset, self.per_call_atomic):
            raise X402BudgetExhausted(
                f"session data-spend budget hit (spent ${self.spent_usd():.2f} of "
                f"${self.session_cap_atomic / 1e18:.2f}) — refusing to pay"
            )
        args = ["x402", "request", f"{CMC_X402_BASE}/{path}",
                "--prefer-network", self.chain, "--prefer-asset", self.asset,
                "--prefer-method", self.prefer_method,
                "--max-payment", str(self.per_call_atomic), "--yes"]
        if self.auto_approve:
            args.append("--auto-approve")
        out = _twak(args, timeout=180)
        # Only record spend after a successful paid response.
        self._budget.commit(self.asset, self.per_call_atomic)
        return out
