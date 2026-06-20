"""Tests for the daily-qualify trade selection + sizing (review #5)."""
from __future__ import annotations

from agent.daily_qualify import (needs_qualifying_trade, pick_qualifying_pair,
                                 qualifying_size)

REG = {
    "BNB": {"address": None, "native": True, "verified": True},
    "USDT": {"address": "0x55d398326f99059ff775485246999027b3197955", "verified": True},
    "USDC": {"address": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "verified": True},
}


def test_needs_when_no_trade_today():
    assert needs_qualifying_trade(False)
    assert not needs_qualifying_trade(True)


def test_prefers_stable_to_stable():
    pair = pick_qualifying_pair({"USDT": 5.0, "BNB": 3.0}, REG)
    assert pair is not None
    sell, buy = pair
    assert sell in ("USDC", "USDT") and buy in ("USDC", "USDT") and sell != buy


def test_fallback_sells_holding_into_stable_when_no_stable_pair():
    # Only BNB held; route BNB -> USDC.
    pair = pick_qualifying_pair({"BNB": 4.0}, REG)
    assert pair == ("BNB", "USDC")


def test_none_when_nothing_verified_or_too_small():
    assert pick_qualifying_pair({"SCAM": 100.0}, REG) is None
    assert pick_qualifying_pair({"USDT": 0.01}, REG) is None  # below min_held


def test_size_respects_per_trade_cap():
    # equity $4, 10% cap => $0.40 max; 90% of that = $0.36 < $0.50 target.
    assert qualifying_size(4.0, 10.0, held_usd=4.0, target=0.50) == 0.36
    # large account: capped by the $0.50 target.
    assert qualifying_size(1000.0, 10.0, held_usd=1000.0, target=0.50) == 0.50
    # limited by what's held.
    assert qualifying_size(1000.0, 10.0, held_usd=0.20, target=0.50) == 0.19
