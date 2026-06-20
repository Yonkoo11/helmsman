"""Regression tests for the independent-audit fixes (C-2, H-1, M-1, M-3, M-4)."""
from __future__ import annotations

import pytest

from agent import orchestrator, portfolio
from agent.execution import BLOCK_SLIPPAGE_BPS, _price_impact_bps
from agent.guardrails import Portfolio, ProposedTrade, evaluate
from agent.market_gate import check_buy
from agent.state import RiskState


# --- M-4: untrustworthy quote data must block, not pass as 0-slippage ---

def test_price_impact_blocks_on_bad_data():
    assert _price_impact_bps("0.5") == 50.0
    assert _price_impact_bps("abc") == BLOCK_SLIPPAGE_BPS
    assert _price_impact_bps("-1") == BLOCK_SLIPPAGE_BPS
    assert _price_impact_bps(None) == BLOCK_SLIPPAGE_BPS


def test_block_slippage_fails_guardrail():
    pf = Portfolio(1000.0, 1000.0, {"USDT": 600.0, "ETH": 300.0, "BNB": 100.0})
    d = evaluate(ProposedTrade("USDT", "ETH", 50.0, BLOCK_SLIPPAGE_BPS), pf)
    assert not d.allowed and any("slippage" in r for r in d.reasons)


# --- H-1: pending-tx reconciliation prevents the double-trade window ---

class _FakeEx:
    def __init__(self, status):
        self._status = status

    def __call__(self, *a, **k):
        return self

    def confirm(self, tx, **k):
        return self._status


def test_reconcile_confirmed_records_and_clears(monkeypatch):
    st = RiskState(pending_tx="0xabc", pending_notional_usd=5.0)
    monkeypatch.setattr(orchestrator, "Executor", _FakeEx("confirmed"))
    assert orchestrator.reconcile_pending(st, "2026-06-22") is True
    assert st.trades_total == 1 and st.pending_tx == ""


def test_reconcile_still_pending_blocks_trading(monkeypatch):
    st = RiskState(pending_tx="0xabc", pending_notional_usd=5.0)
    monkeypatch.setattr(orchestrator, "Executor", _FakeEx("pending"))
    assert orchestrator.reconcile_pending(st, "2026-06-22") is False
    assert st.pending_tx == "0xabc"  # kept for next cycle


def test_reconcile_no_pending_is_safe():
    assert orchestrator.reconcile_pending(RiskState(), "2026-06-22") is True


# --- M-1: malformed registry address must not reach the x402 URL ---

def test_malformed_address_blocked():
    reg = {"X": {"address": "0xnothex", "verified": True}}

    class C:
        def request(self, p):  # pragma: no cover - must never be called
            raise AssertionError("should not pay on a malformed address")

    v = check_buy("X", C(), reg)
    assert not v.ok and "malformed" in v.detail


# --- M-3: implausible portfolio USD value must be rejected, not silently used ---

def test_portfolio_rejects_implausible_value(monkeypatch):
    class P:
        returncode = 0
        stdout = '[{"chain":"bsc","symbol":"X","usdValue":1e20}]'
        stderr = ""

    monkeypatch.setattr(portfolio.subprocess, "run", lambda *a, **k: P())
    with pytest.raises(RuntimeError):
        portfolio.read_bsc_holdings()
