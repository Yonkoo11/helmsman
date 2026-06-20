"""Tests for the x402 data client's budget guard (the BNB SDK spend cap).

The live payment path can't be unit-tested (it signs on-chain), but the
budget-exhaustion guard — the thing that stops the agent overspending on data —
is pure and must hold.
"""
from __future__ import annotations

import pytest

from agent import x402_data


def test_budget_tracks_and_blocks_overspend(monkeypatch):
    # Stub the TWAK payment so no real call happens; every "payment" succeeds.
    monkeypatch.setattr(x402_data, "_twak", lambda args, timeout=180: {"data": "ok"})
    c = x402_data.X402DataClient(session_cap_atomic=2 * x402_data.ONE_CENT)  # 2 requests

    c.request("dex/search?query=BNB")
    c.request("dex/search?query=BNB")
    assert round(c.spent_usd(), 2) == 0.02

    with pytest.raises(x402_data.X402BudgetExhausted):
        c.request("dex/search?query=BNB")  # 3rd would exceed the session cap


def test_no_spend_recorded_when_payment_fails(monkeypatch):
    def boom(args, timeout=180):
        raise RuntimeError("twak payment failed")

    monkeypatch.setattr(x402_data, "_twak", boom)
    c = x402_data.X402DataClient()
    with pytest.raises(RuntimeError):
        c.request("dex/search?query=BNB")
    assert c.spent_usd() == 0.0  # failed payment must not be counted as spend
