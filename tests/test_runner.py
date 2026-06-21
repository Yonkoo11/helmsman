"""Tests for the autonomous runner's daily-qualify trigger (review #2/#5/#7)."""
from __future__ import annotations

import datetime as dt

from agent import runner, token_registry
from agent.guardrails import Portfolio
from agent.state import RiskState

DAY = dt.datetime(2026, 6, 22, 21, tzinfo=dt.timezone.utc)
FAKE_REG = {
    "USDT": {"address": "0x55d398326f99059ff775485246999027b3197955", "verified": True},
    "USDC": {"address": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "verified": True},
}


def test_should_qualify_truth_table():
    f = runner.should_qualify
    assert f(ensure_daily=True, has_traded_today=False, hour_utc=21, qualify_after_hour=20)
    assert not f(ensure_daily=True, has_traded_today=True, hour_utc=21, qualify_after_hour=20)
    assert not f(ensure_daily=True, has_traded_today=False, hour_utc=10, qualify_after_hour=20)
    assert not f(ensure_daily=False, has_traded_today=False, hour_utc=23, qualify_after_hour=20)


def _wire(monkeypatch, st, calls, equity=100.0):
    monkeypatch.setattr(runner.state, "load", lambda: st)
    monkeypatch.setattr(runner.state, "save", lambda x: None)
    monkeypatch.setattr(runner, "strategy_pass", lambda st, day, **k: False)  # no organic trade
    monkeypatch.setattr(runner.portfolio, "build_live_portfolio",
                        lambda st, day: Portfolio(equity_usd=equity, peak_equity_usd=equity,
                                                  holdings_usd={"USDT": equity / 2, "USDC": equity / 2}))
    monkeypatch.setattr(token_registry, "load_registry", lambda: FAKE_REG)

    def fake_attempt(trade, pf, st, day, **k):
        calls.append((trade.sell_symbol, trade.buy_symbol))
        st.record_trade(trade.notional_usd, day)
        return True

    monkeypatch.setattr(runner, "attempt_trade", fake_attempt)


def test_forces_qualifying_trade_when_no_trade_today(monkeypatch):
    st, calls = RiskState(), []
    _wire(monkeypatch, st, calls)
    out = runner.run_cycle(now=DAY)
    assert calls, "a qualifying trade should have been attempted"
    assert calls[0][0] in ("USDT", "USDC") and calls[0][1] in ("USDT", "USDC")
    assert out["traded_today"]


def test_no_qualify_when_already_traded(monkeypatch):
    st, calls = RiskState(), []
    st.record_trade(5.0, "2026-06-22")  # an organic trade already happened today
    _wire(monkeypatch, st, calls)
    runner.run_cycle(now=DAY)
    assert not calls, "must not force a qualify trade when already traded today"


def test_qualifies_on_first_cycle_any_hour(monkeypatch):
    # New default (cutoff 0): the daily-qualify fires on the first cycle of the
    # day even early on, so host uptime timing is irrelevant. The strategy held
    # (mock returns no trade), so the qualify net must fire.
    st, calls = RiskState(), []
    _wire(monkeypatch, st, calls)
    runner.run_cycle(now=dt.datetime(2026, 6, 22, 9, tzinfo=dt.timezone.utc))
    assert calls, "qualify must fire on the first cycle even early in the UTC day"


def test_cycle_survives_strategy_failure(monkeypatch):
    # A transient CMC/RPC/x402 error must NOT crash the unattended cycle.
    # Fully wire the externals first (no real network/trade), then make the
    # strategy pass raise.
    st, calls = RiskState(), []
    _wire(monkeypatch, st, calls)

    def boom(st, day, **k):
        raise RuntimeError("CMC API 500")

    monkeypatch.setattr(runner, "strategy_pass", boom)
    out = runner.run_cycle(now=dt.datetime(2026, 6, 22, 9, tzinfo=dt.timezone.utc))
    # The cycle returned cleanly despite the strategy raising (no exception).
    assert out["day"] == "2026-06-22"
