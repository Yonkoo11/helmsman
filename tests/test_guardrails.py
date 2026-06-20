"""Tests for the guardrail engine — the safety core + half the Phase 1 gate.

Model: ETH is the tradable core (BEP-20, competition-eligible); BNB is held only
to pay gas and must stay above the reserve. Trades route USDT <-> ETH.
"""
from __future__ import annotations

from agent.config import RiskConfig
from agent.guardrails import Portfolio, ProposedTrade, evaluate

CFG = RiskConfig()


def healthy_pf(equity: float = 1000.0, **kw) -> Portfolio:
    """At peak (no drawdown): stables + ETH (tradable) + a BNB gas reserve."""
    defaults = dict(
        equity_usd=equity,
        peak_equity_usd=equity,
        holdings_usd={"USDT": equity * 0.6, "ETH": equity * 0.3, "BNB": equity * 0.1},
        traded_today_usd=0.0,
    )
    defaults.update(kw)
    return Portfolio(**defaults)


def test_normal_trade_allowed():
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, quoted_slippage_bps=20), healthy_pf(), CFG)
    assert d.allowed, d.log_line()
    assert not d.breaker_halted


def test_off_allowlist_buy_refused():
    d = evaluate(ProposedTrade("USDT", "FAKECOIN", 50.0), healthy_pf(), CFG)
    assert not d.allowed
    assert any("not in eligible allowlist" in r for r in d.reasons)


def test_native_bnb_not_eligible_to_trade():
    # BNB is gas-only — buying it is not a scoring trade and must be refused.
    d = evaluate(ProposedTrade("USDT", "BNB", 50.0), healthy_pf(), CFG)
    assert not d.allowed
    assert any("not in eligible allowlist" in r for r in d.reasons)


def test_per_trade_cap_refused():
    d = evaluate(ProposedTrade("USDT", "ETH", 200.0, quoted_slippage_bps=10), healthy_pf(), CFG)
    assert not d.allowed
    assert any("per-trade cap" in r for r in d.reasons)


def test_daily_turnover_cap_refused():
    pf = healthy_pf(traded_today_usd=380.0)
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("daily turnover" in r for r in d.reasons)


def test_slippage_bound_refused():
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, quoted_slippage_bps=250), healthy_pf(), CFG)
    assert not d.allowed
    assert any("slippage" in r for r in d.reasons)


def test_cannot_sell_more_than_held():
    pf = healthy_pf(holdings_usd={"USDT": 870.0, "ETH": 40.0, "BNB": 90.0})
    d = evaluate(ProposedTrade("ETH", "USDT", 90.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("exceeds held" in r for r in d.reasons)


def test_concentration_cap_refused():
    # Already 30% in ETH; buying 10% more pushes to 40% > 35% max position.
    pf = healthy_pf(holdings_usd={"USDT": 600.0, "ETH": 300.0, "BNB": 100.0})
    d = evaluate(ProposedTrade("USDT", "ETH", 100.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("max" in r and "position" in r for r in d.reasons)


def test_gas_reserve_blocks_trade_when_gas_low():
    # Plenty of stables, but BNB gas below the $1 reserve => no trade can be paid.
    pf = healthy_pf(holdings_usd={"USDT": 900.0, "ETH": 99.5, "BNB": 0.5})
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("gas reserve" in r for r in d.reasons)


def test_circuit_breaker_halts_risk_on_drawdown():
    pf = Portfolio(equity_usd=820.0, peak_equity_usd=1000.0,
                   holdings_usd={"USDT": 400.0, "ETH": 320.0, "BNB": 100.0})
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert d.breaker_halted
    assert any("circuit breaker" in r for r in d.reasons)


def test_circuit_breaker_allows_derisking_to_stable():
    pf = Portfolio(equity_usd=820.0, peak_equity_usd=1000.0,
                   holdings_usd={"USDT": 400.0, "ETH": 320.0, "BNB": 100.0})
    d = evaluate(ProposedTrade("ETH", "USDT", 50.0, quoted_slippage_bps=10), pf, CFG)
    assert d.allowed, d.log_line()
    assert d.breaker_halted  # halted, but de-risking is still allowed


def test_dust_floor_refuses_risk_when_drained():
    pf = Portfolio(equity_usd=4.0, peak_equity_usd=10.0,
                   holdings_usd={"USDT": 3.0, "BNB": 1.0})
    d = evaluate(ProposedTrade("USDT", "ETH", 0.3, quoted_slippage_bps=10), pf, CFG)
    assert not d.allowed
    assert any("dust floor" in r for r in d.reasons)


def test_dust_floor_allows_holding_stable():
    pf = Portfolio(equity_usd=4.0, peak_equity_usd=10.0,
                   holdings_usd={"USDT": 3.0, "BNB": 1.0})
    d = evaluate(ProposedTrade("USDT", "USDC", 0.3, quoted_slippage_bps=10), pf, CFG)
    assert d.allowed, d.log_line()


def test_eligible_list_excludes_native_bnb():
    cfg = RiskConfig()
    assert "ETH" in cfg.eligible
    assert "TWT" in cfg.eligible          # a sponsor token from the list
    assert "BNB" not in cfg.eligible      # native gas, not a BEP-20 / not eligible
    assert cfg.is_stable("USDT") and not cfg.is_stable("ETH")
