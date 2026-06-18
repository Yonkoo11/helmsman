"""Helmsman configuration: risk caps + the eligible-token allowlist.

Risk caps are deliberately tighter than the contest's 30% drawdown DQ line —
the whole product thesis is "most profit WITHOUT blowing up", so we halt early.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "eligible_tokens.txt"

# Stablecoins inside the eligible set — the de-risk destinations the circuit
# breaker is always allowed to rotate INTO even when the agent is halted.
STABLES: frozenset[str] = frozenset(
    {
        "USDT", "USDC", "DAI", "USD1", "USDe", "USDD", "TUSD", "FDUSD",
        "USDf", "FRAX", "FRXUSD", "USDF", "DUSD", "lisUSD", "EURI", "XUSD",
    }
)


def load_eligible_tokens(path: Path = _DATA) -> frozenset[str]:
    """Return the uppercased set of competition-eligible token symbols."""
    syms: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        syms.add(line.upper())
    return frozenset(syms)


@dataclass(frozen=True)
class RiskConfig:
    """Hard risk caps the guardrail engine enforces on every proposed trade."""

    # Circuit breaker: halt risk-increasing trades once equity draws down this
    # far from its peak. Set well below the 30% DQ line for safety margin.
    max_drawdown_halt_pct: float = 15.0
    # Single trade notional ceiling, as a fraction of current equity.
    per_trade_cap_pct: float = 10.0
    # Cumulative same-day turnover ceiling, as a fraction of current equity.
    daily_turnover_cap_pct: float = 40.0
    # Max share of equity allowed in any one non-stable token after a trade.
    max_position_pct: float = 35.0
    # Never let a trade pull equity below this USD floor (contest scores any
    # hour starting <= $1 as 0% — keep capital deployed).
    dust_floor_usd: float = 5.0
    # Max acceptable quoted slippage, in basis points.
    max_slippage_bps: float = 100.0
    # Allowlist of tradable symbols (both legs must be in it).
    eligible: frozenset[str] = field(default_factory=load_eligible_tokens)
    stables: frozenset[str] = STABLES

    def is_eligible(self, symbol: str) -> bool:
        return symbol.upper() in self.eligible

    def is_stable(self, symbol: str) -> bool:
        return symbol.upper() in self.stables
