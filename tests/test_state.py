"""Tests for durable risk state — the persistence the safety caps depend on.

These guard the two critical review findings: without persisted peak equity the
drawdown breaker can't fire, and without a UTC day boundary the daily cap is
meaningless.
"""
from __future__ import annotations

import pytest

from agent.state import CorruptStateError, RiskState, load, save


def test_peak_equity_is_monotonic():
    s = RiskState()
    s.observe_equity(100.0)
    s.observe_equity(120.0)
    s.observe_equity(90.0)   # a dip must NOT lower the high-water mark
    assert s.peak_equity_usd == 120.0


def test_drawdown_breaker_now_has_history():
    # Peak 120 persisted; equity 96 => 20% drawdown the breaker can see.
    s = RiskState()
    s.observe_equity(120.0)
    from agent.guardrails import Portfolio
    pf = Portfolio(equity_usd=96.0, peak_equity_usd=s.peak_equity_usd, holdings_usd={})
    assert round(pf.drawdown_pct(), 1) == 20.0


def test_daily_turnover_accumulates_then_resets_on_new_day():
    s = RiskState()
    s.record_trade(30.0, "2026-06-22")
    s.record_trade(20.0, "2026-06-22")
    assert s.traded_today("2026-06-22") == 50.0
    # New UTC day -> same-day turnover reads zero even before an explicit roll.
    assert s.traded_today("2026-06-23") == 0.0
    s.roll_day("2026-06-23")
    assert s.traded_today_usd == 0.0


def test_has_traded_on_tracks_daily_qualification():
    s = RiskState()
    assert not s.has_traded_on("2026-06-22")
    s.record_trade(5.0, "2026-06-22")
    assert s.has_traded_on("2026-06-22")
    assert not s.has_traded_on("2026-06-23")


def test_roundtrip_persistence(tmp_path):
    p = tmp_path / "state.json"
    s = RiskState(peak_equity_usd=200.0, day_utc="2026-06-22",
                  traded_today_usd=40.0, last_trade_day_utc="2026-06-22", trades_total=3)
    save(s, p)
    loaded = load(p)
    assert loaded == s


def test_corrupt_state_file_halts_not_resets(tmp_path):
    # A corrupt EXISTING file must raise, never silently reset peak->0 (which
    # would disable the drawdown breaker). (H-3)
    p = tmp_path / "state.json"
    p.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(CorruptStateError):
        load(p)


def test_missing_state_file_is_fresh(tmp_path):
    assert load(tmp_path / "nope.json") == RiskState()
