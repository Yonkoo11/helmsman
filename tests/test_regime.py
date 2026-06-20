"""Tests for the multi-signal regime engine + strategy mapping."""
from __future__ import annotations

from agent.guardrails import Portfolio
from agent.regime import RegimeScore, Signals, score
from agent.strategy import decide


def sig(fg, mom7d=0.0, mcap=0.0, domchg=0.0):
    return Signals(fear_greed=fg, momentum_7d_pct=mom7d, momentum_24h_pct=0.0,
                   macro_mcap_24h_pct=mcap, btc_dom_24h_change=domchg)


def test_fear_with_uptrend_is_risk_on():
    rs = score(sig(10, mom7d=10, mcap=2))
    assert rs.label == "risk-on" and rs.score > 0.2


def test_greed_with_downtrend_is_risk_off():
    rs = score(sig(85, mom7d=-10, mcap=-2))
    assert rs.label == "risk-off" and rs.score < -0.2


def test_extreme_fear_in_hard_downtrend_does_not_knife_catch():
    # The whole point of multi-signal: extreme fear during a hard downtrend must
    # NOT trigger a buy. Under trend-aware weights it goes risk-off (de-risk),
    # under more contrarian weights neutral — either way, never risk-on.
    rs = score(sig(10, mom7d=-20, mcap=-3, domchg=1.0))
    assert rs.label != "risk-on", rs.log_line()


def test_flat_signals_neutral():
    assert score(sig(50)).label == "neutral"


def test_breakdown_sums_to_score():
    rs = score(sig(20, mom7d=5, mcap=1, domchg=-0.5))
    assert round(sum(rs.breakdown.values()), 4) == rs.score


def test_clamping_bounds_each_factor():
    # Absurd inputs must not blow past the weighted bounds.
    rs = score(sig(0, mom7d=999, mcap=999, domchg=-999))
    # Each factor is bounded by its weight; the largest weight is momentum (0.50).
    assert rs.score <= 1.0 and all(abs(v) <= 0.5001 for v in rs.breakdown.values())


def _pf(usdt=600.0, eth=300.0, bnb=100.0):
    return Portfolio(equity_usd=usdt + eth + bnb, peak_equity_usd=usdt + eth + bnb,
                     holdings_usd={"USDT": usdt, "ETH": eth, "BNB": bnb})


def test_strategy_risk_on_buys_core():
    t = decide(RegimeScore(0.5, "risk-on", {}), _pf())
    assert t and t.sell_symbol == "USDT" and t.buy_symbol == "ETH"


def test_strategy_risk_off_sells_to_stable():
    t = decide(RegimeScore(-0.5, "risk-off", {}), _pf())
    assert t and t.sell_symbol == "ETH" and t.buy_symbol == "USDT"


def test_strategy_neutral_holds():
    assert decide(RegimeScore(0.0, "neutral", {}), _pf()) is None
