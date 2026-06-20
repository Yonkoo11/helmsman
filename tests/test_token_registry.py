"""Tests for the verified token registry (scam-ticker defense, review #4)."""
from __future__ import annotations

from agent import token_registry as tr

# Trusted, independently-known canonical BSC addresses.
KNOWN = {
    "USDT": "0x55d398326f99059ff775485246999027b3197955",
    "USDC": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
}


def test_registry_present_and_addresses_match_trusted():
    reg = tr.load_registry()
    assert reg, "registry not built — run `python -m agent.token_registry --build`"
    for sym, addr in KNOWN.items():
        assert tr.verified_address(sym, reg) == addr, f"{sym} address drift"


def test_native_and_majors_tradable():
    reg = tr.load_registry()
    assert tr.is_tradable("BNB", reg)   # native
    assert tr.is_tradable("USDT", reg)
    assert tr.is_tradable("usdc", reg)  # case-insensitive


def test_unverified_or_unknown_not_tradable():
    reg = tr.load_registry()
    assert not tr.is_tradable("SCAMUSDT", reg)
    assert not tr.is_tradable("", reg)


def test_gate_blocks_symbol_absent_from_registry():
    # A token not in the curated universe is never tradable, even if real.
    reg = {"BNB": {"address": None, "native": True, "verified": True}}
    assert tr.is_tradable("BNB", reg)
    assert not tr.is_tradable("DOGE", reg)
