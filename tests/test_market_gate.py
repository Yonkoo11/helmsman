"""Tests for the x402 market gate (liquidity check inside the loop)."""
from __future__ import annotations

from agent.market_gate import check_buy

REG = {
    "BNB": {"address": None, "native": True, "verified": True},
    "CAKE": {"address": "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82", "native": False, "verified": True},
}


class FakeClient:
    """Stand-in X402DataClient: returns canned DEX data, records calls."""
    def __init__(self, data):
        self._data = data
        self.calls = 0

    def request(self, path):
        self.calls += 1
        return self._data


def _dex(addr, liq):
    return {"data": {"tks": [{"addr": addr, "liq": liq}]}}


def test_native_bnb_exempt_no_payment():
    c = FakeClient({})
    v = check_buy("BNB", c, REG)
    assert v.ok and c.calls == 0  # native skips the paid call


def test_liquid_token_passes():
    addr = REG["CAKE"]["address"]
    c = FakeClient(_dex(addr, 5_000_000))
    v = check_buy("CAKE", c, REG, min_liq_usd=250_000)
    assert v.ok and v.liquidity_usd == 5_000_000


def test_thin_liquidity_blocked():
    addr = REG["CAKE"]["address"]
    c = FakeClient(_dex(addr, 1_000))
    v = check_buy("CAKE", c, REG, min_liq_usd=250_000)
    assert not v.ok and "below floor" in v.detail


def test_unconfirmed_liquidity_proceeds_for_verified_token():
    # Fuzzy search returned a different token (didn't surface CAKE). The registry
    # already verified CAKE's address, so the overlay proceeds rather than
    # false-blocking a real major.
    c = FakeClient(_dex("0xdeadbeef00000000000000000000000000000000", 9_000_000))
    v = check_buy("CAKE", c, REG, min_liq_usd=250_000)
    assert v.ok and "unconfirmed" in v.detail


def test_positively_thin_token_still_blocked():
    # When x402 DOES surface the token and liquidity is thin, block it.
    addr = REG["CAKE"]["address"]
    c = FakeClient(_dex(addr, 500))
    v = check_buy("CAKE", c, REG, min_liq_usd=250_000)
    assert not v.ok and "below floor" in v.detail


def test_unverified_symbol_blocked_without_payment():
    c = FakeClient(_dex("0x0", 9_000_000))
    v = check_buy("SCAMUSDT", c, REG)
    assert not v.ok and c.calls == 0
