"""Tests for the ERC-8004 agent-card builder (pure parts; review #3)."""
from __future__ import annotations

import base64
import json

from agent import identity


def test_card_has_required_fields():
    card = identity.agent_card("0xWALLET", "0xREG")
    for k in ("name", "type", "version", "wallet", "registry", "integrations", "guardrails"):
        assert k in card
    assert card["wallet"] == "0xWALLET"
    assert card["registry"] == "0xREG"
    # all three sponsors named in the integration map
    blob = json.dumps(card["integrations"]).lower()
    assert "trust wallet" in blob and "coinmarketcap" in blob and "bnb agent sdk" in blob


def test_data_uri_round_trips():
    card = identity.agent_card("0xWALLET", "0xREG")
    uri = identity.card_data_uri(card)
    assert uri.startswith("data:application/json;base64,")
    back = json.loads(base64.b64decode(uri.split("base64,", 1)[1]))
    assert back == card
