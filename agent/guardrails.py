"""The guardrail engine — Helmsman's differentiator.

Pure logic, no I/O, no external deps: every proposed trade is vetted against
hard risk caps before it can reach the signer. A deliberately over-cap trade is
refused with a logged reason. A drawdown past the halt line trips a circuit
breaker that only permits de-risking (rotating into stables).

This is what makes the agent safe to leave unattended, and it is half of the
Phase 1 gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import RiskConfig


@dataclass(frozen=True)
class Portfolio:
    """Snapshot of the agent's account at decision time (USD-denominated)."""

    equity_usd: float
    peak_equity_usd: float
    holdings_usd: dict[str, float] = field(default_factory=dict)
    traded_today_usd: float = 0.0

    def drawdown_pct(self) -> float:
        if self.peak_equity_usd <= 0:
            return 0.0
        return max(0.0, (self.peak_equity_usd - self.equity_usd) / self.peak_equity_usd * 100.0)

    def held(self, symbol: str) -> float:
        return self.holdings_usd.get(symbol.upper(), 0.0)


@dataclass(frozen=True)
class ProposedTrade:
    """A swap the strategy wants to make: sell -> buy for `notional_usd`."""

    sell_symbol: str
    buy_symbol: str
    notional_usd: float
    quoted_slippage_bps: float = 0.0


@dataclass(frozen=True)
class Decision:
    """Verdict for a proposed trade. `allowed` only when no reason fired."""

    allowed: bool
    reasons: tuple[str, ...]
    breaker_halted: bool

    def log_line(self) -> str:
        verdict = "ALLOW" if self.allowed else "REFUSE"
        why = "; ".join(self.reasons) if self.reasons else "all checks passed"
        halt = " [CIRCUIT-BREAKER HALTED]" if self.breaker_halted else ""
        return f"{verdict}{halt}: {why}"


def evaluate(trade: ProposedTrade, pf: Portfolio, cfg: RiskConfig | None = None) -> Decision:
    """Vet a proposed trade against the risk caps. Returns an explained verdict."""
    cfg = cfg or RiskConfig()
    reasons: list[str] = []

    sell = trade.sell_symbol.upper()
    buy = trade.buy_symbol.upper()
    drawdown = pf.drawdown_pct()
    halted = drawdown >= cfg.max_drawdown_halt_pct
    buy_is_stable = cfg.is_stable(buy)

    # 1. Both legs must be competition-eligible (off-list trades don't count).
    if not cfg.is_eligible(sell):
        reasons.append(f"sell token {sell} not in eligible allowlist")
    if not cfg.is_eligible(buy):
        reasons.append(f"buy token {buy} not in eligible allowlist")

    # 2. Sanity on the pair + size.
    if sell == buy:
        reasons.append("sell and buy token are identical")
    if trade.notional_usd <= 0:
        reasons.append("trade notional must be positive")

    # 3. Cannot sell more of a token than is held.
    if trade.notional_usd > pf.held(sell) + 1e-9:
        reasons.append(
            f"notional ${trade.notional_usd:,.2f} exceeds held {sell} "
            f"${pf.held(sell):,.2f}"
        )

    # 4. Per-trade notional cap.
    per_trade_cap = cfg.per_trade_cap_pct / 100.0 * pf.equity_usd
    if trade.notional_usd > per_trade_cap + 1e-9:
        reasons.append(
            f"notional ${trade.notional_usd:,.2f} exceeds per-trade cap "
            f"${per_trade_cap:,.2f} ({cfg.per_trade_cap_pct:.0f}% of equity)"
        )

    # 5. Daily turnover cap.
    daily_cap = cfg.daily_turnover_cap_pct / 100.0 * pf.equity_usd
    if pf.traded_today_usd + trade.notional_usd > daily_cap + 1e-9:
        reasons.append(
            f"daily turnover ${pf.traded_today_usd + trade.notional_usd:,.2f} "
            f"would exceed cap ${daily_cap:,.2f}"
        )

    # 6. Slippage bound.
    if trade.quoted_slippage_bps > cfg.max_slippage_bps:
        reasons.append(
            f"quoted slippage {trade.quoted_slippage_bps:.0f}bps exceeds "
            f"max {cfg.max_slippage_bps:.0f}bps"
        )

    # 7. Dust floor — in dust territory (near the $1/hour=0% rule) only allow
    #    de-risking into stables; never add risk on a near-drained account.
    if pf.equity_usd <= cfg.dust_floor_usd and not buy_is_stable:
        reasons.append(
            f"equity ${pf.equity_usd:,.2f} at/below dust floor "
            f"${cfg.dust_floor_usd:,.2f}; only de-risking to stables allowed"
        )

    # 8. Concentration — cap exposure to any one non-stable token after buying.
    if not buy_is_stable:
        resulting = pf.held(buy) + trade.notional_usd
        max_pos = cfg.max_position_pct / 100.0 * pf.equity_usd
        if resulting > max_pos + 1e-9:
            reasons.append(
                f"resulting {buy} position ${resulting:,.2f} exceeds max "
                f"${max_pos:,.2f} ({cfg.max_position_pct:.0f}% of equity)"
            )

    # 8b. Gas reserve — never trade the native gas balance below the reserve, or
    #     the agent strands itself unable to pay for any future tx (mid-week DQ).
    gas_held = pf.held(cfg.gas_asset)
    gas_after = gas_held - (trade.notional_usd if sell == cfg.gas_asset.upper() else 0.0)
    if gas_after < cfg.min_gas_reserve_usd:
        reasons.append(
            f"gas reserve: {cfg.gas_asset} ${gas_after:,.2f} below "
            f"${cfg.min_gas_reserve_usd:,.2f} needed to pay for transactions"
        )

    # 9. Circuit breaker — when halted, only de-risking (buy a stable) is allowed.
    if halted and not buy_is_stable:
        reasons.append(
            f"circuit breaker: drawdown {drawdown:.1f}% >= halt "
            f"{cfg.max_drawdown_halt_pct:.0f}%, only de-risking to stables allowed"
        )

    return Decision(allowed=not reasons, reasons=tuple(reasons), breaker_halted=halted)
