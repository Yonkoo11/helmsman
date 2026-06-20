"""Verified token registry — the scam-ticker defense (review finding #4).

On BSC anyone can deploy a token with ticker "USDT". Trading by symbol alone can
route into a worthless look-alike. This module pins the agent's CURATED trading
universe (liquid majors + stables) to BSC contract addresses RESOLVED FROM CMC's
authoritative API — never hardcoded from memory — and the loop trades only
symbols that are present and address-verified here.

Build once (writes agent/data/token_registry.json):
    PYTHONPATH=. .venv/bin/python -m agent.token_registry --build
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests

from . import data_cmc  # noqa: F401  (imports load the .env CMC key)

REGISTRY_PATH = Path(__file__).parent / "data" / "token_registry.json"
BSC_PLATFORM = "BNB Smart Chain (BEP20)"

# Curated, genuinely-liquid, COMPETITION-ELIGIBLE BSC universe (all BEP-20, all
# on the 149-token list). Small on purpose: thin/scam tokens are excluded by
# construction, which also reduces MEV/sandwich exposure.
# Native BNB is intentionally ABSENT — it is not BEP-20, not on the eligible
# list, and is held only to pay gas. Trading it would not count.
CURATED_UNIVERSE = [
    "ETH", "USDT", "USDC", "USD1", "FDUSD", "CAKE",
]
NATIVE: set[str] = set()  # no native asset is competition-tradable


def _resolve_bsc_address(symbol: str, key: str) -> str | None:
    """Authoritative BSC contract for `symbol` from CMC, or None if native/absent."""
    if symbol in NATIVE:
        return None
    r = requests.get(
        "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info",
        headers={"X-CMC_PRO_API_KEY": key, "Accept": "application/json"},
        params={"symbol": symbol}, timeout=20,
    )
    r.raise_for_status()
    payload = r.json()["data"][symbol]
    entry = payload[0] if isinstance(payload, list) else payload
    for c in entry.get("contract_address", []):
        if c.get("platform", {}).get("name") == BSC_PLATFORM:
            return c["contract_address"]
    return None


def build_registry(path: Path = REGISTRY_PATH) -> dict[str, dict]:
    """Resolve the curated universe to verified BSC addresses and persist."""
    key = os.getenv("CMC_API_KEY")
    if not key:
        raise data_cmc.MissingCMCKey("CMC_API_KEY required to build the registry")
    reg: dict[str, dict] = {}
    for sym in CURATED_UNIVERSE:
        addr = _resolve_bsc_address(sym, key)
        reg[sym] = {
            "address": addr.lower() if addr else None,
            "native": sym in NATIVE,
            "verified": (sym in NATIVE) or (addr is not None),
            "source": "cmc:v2/cryptocurrency/info",
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return reg


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, dict]:
    # A MISSING file is a deployment error, not "nothing is tradable" — fail loud
    # so a path/build bug can't degrade the scam-gate into a silent no-op (H-4).
    if not path.exists():
        raise FileNotFoundError(
            f"token registry not found at {path} — run "
            "`python -m agent.token_registry --build`"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def is_tradable(symbol: str, registry: dict[str, dict] | None = None) -> bool:
    """True only if the symbol is in the curated universe AND address-verified."""
    reg = registry if registry is not None else load_registry()
    e = reg.get(symbol.upper())
    return bool(e and e.get("verified"))


def verified_address(symbol: str, registry: dict[str, dict] | None = None) -> str | None:
    reg = registry if registry is not None else load_registry()
    return (reg.get(symbol.upper()) or {}).get("address")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    if ap.parse_args().build:
        out = build_registry()
        for s, e in out.items():
            mark = "native" if e["native"] else (e["address"] or "UNRESOLVED")
            print(f"  {s:6} {'OK ' if e['verified'] else 'MISS'} {mark}")
