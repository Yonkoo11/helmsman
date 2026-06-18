"""Tests for the guardrail engine — the safety core + half the Phase 1 gate."""
from __future__ import annotations

import pytest

from agent.config import RiskConfig
from agent.guardrails import Portfolio, ProposedTrade, evaluate

CFG = RiskConfig()


def healthy_pf(equity: float = 1000.0, **kw) -> Portfolio:
    """A portfolio at its peak (no drawdown) holding mostly stables + some BNB."""
    defaults = dict(
        equity_usd=equity,
        peak_equity_usd=equity,
        holdings_usd={"USDT": equity * 0.7, "BNB": equity * 0.3},
        traded_today_usd=0.0,
    )
    defaults.update(kw)
    return Portfolio(**defaults)


def test_normal_trade_allowed():
    # Sell $50 USDT (held) into BNB: well within all caps, at peak equity.
    pf = healthy_pf()
    d = evaluate(ProposedTrade("USDT", "BNB", 50.0, quoted_slippage_bps=20), pf, CFG)
    assert d.allowed, d.log_line()
    assert not d.breaker_halted


def test_off_allowlist_buy_refused():
    pf = healthy_pf()
    d = evaluate(ProposedTrade("USDT", "FAKECOIN", 50.0), pf, CFG)
    assert not d.allowed
    assert any("not in eligible allowlist" in r for r in d.reasons)


def test_per_trade_cap_refused():
    # $200 on $1000 equity = 20% > 10% per-trade cap.
    pf = healthy_pf()
    d = evaluate(ProposedTrade("USDT", "BNB", 200.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("per-trade cap" in r for r in d.reasons)


def test_daily_turnover_cap_refused():
    # Already churned $380 today; another $50 tips past the $400 (40%) cap.
    pf = healthy_pf(traded_today_usd=380.0)
    d = evaluate(ProposedTrade("USDT", "BNB", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("daily turnover" in r for r in d.reasons)


def test_slippage_bound_refused():
    pf = healthy_pf()
    d = evaluate(ProposedTrade("USDT", "BNB", 50.0, quoted_slippage_bps=250), pf, CFG)
    assert not d.allowed
    assert any("slippage" in r for r in d.reasons)


def test_cannot_sell_more_than_held():
    # Holds $300 BNB, tries to sell $90 (within per-trade cap) — fine size-wise,
    # but selling $90 of a $300 holding is ok; push it: hold only $40.
    pf = healthy_pf(holdings_usd={"USDT": 960.0, "BNB": 40.0})
    d = evaluate(ProposedTrade("BNB", "ETH", 90.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("exceeds held" in r for r in d.reasons)


def test_concentration_cap_refused():
    # Already 30% in BNB; buying another 10% pushes to 40% > 35% max position.
    pf = healthy_pf(holdings_usd={"USDT": 700.0, "BNB": 300.0})
    d = evaluate(ProposedTrade("USDT", "BNB", 100.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("max" in r and "position" in r for r in d.reasons)


def test_circuit_breaker_halts_risk_on_drawdown():
    # Peak $1000, now $820 = 18% drawdown >= 15% halt. Buying BNB (risk) refused.
    pf = Portfolio(
        equity_usd=820.0,
        peak_equity_usd=1000.0,
        holdings_usd={"USDT": 500.0, "BNB": 320.0},
        traded_today_usd=0.0,
    )
    d = evaluate(ProposedTrade("USDT", "BNB", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert d.breaker_halted
    assert any("circuit breaker" in r for r in d.reasons)


def test_circuit_breaker_allows_derisking_to_stable():
    # Same 18% drawdown, but rotating BNB -> USDT (de-risk) is permitted.
    pf = Portfolio(
        equity_usd=820.0,
        peak_equity_usd=1000.0,
        holdings_usd={"USDT": 500.0, "BNB": 320.0},
        traded_today_usd=0.0,
    )
    d = evaluate(ProposedTrade("BNB", "USDT", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert d.allowed, d.log_line()
    assert d.breaker_halted  # halted, but de-risking is still allowed


def test_dust_floor_refuses_risk_when_drained():
    # Account drained to $4 (below the $5 floor): adding risk (buy BNB) refused.
    pf = Portfolio(
        equity_usd=4.0,
        peak_equity_usd=10.0,
        holdings_usd={"USDT": 4.0},
        traded_today_usd=0.0,
    )
    d = evaluate(ProposedTrade("USDT", "BNB", 0.3, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("dust floor" in r for r in d.reasons)


def test_dust_floor_allows_holding_stable():
    # Same drained $4 account, but a USDT->USDC de-risk is permitted.
    pf = Portfolio(
        equity_usd=4.0,
        peak_equity_usd=10.0,
        holdings_usd={"USDT": 4.0},
        traded_today_usd=0.0,
    )
    d = evaluate(ProposedTrade("USDT", "USDC", 0.3, quoted_slippage_bps=10), pf, CFG)
    assert d.allowed, d.log_line()


def test_eligible_list_loaded():
    cfg = RiskConfig()
    assert "BNB" in cfg.eligible
    assert "TWT" in cfg.eligible  # a sponsor token from the list
    assert cfg.is_stable("USDT") and not cfg.is_stable("BNB")
