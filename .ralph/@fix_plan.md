# Fix Plan — Helmsman

## Phase 1 (core action — TWAK-signed trade on testnet + guardrail refusal)

- [ ] Task 1: Stand up the TWAK local-signing path on BSC testnet
  - Acceptance: a hardcoded swap is signed locally via TWAK and lands a real BSC testnet tx hash; no raw private key in agent process
  - Files: agent/execution/twak_signer.py, .env (OPERATOR via os.getenv only)

- [ ] Task 2: Pull one live CMC signal through the Agent Hub
  - Acceptance: one real CMC signal (e.g. funding rate or Fear&Greed) returns into the agent and is logged
  - Files: agent/data/cmc_client.py

- [ ] Task 3: Wire BNB SDK X402Signer to pay for the CMC call per-request
  - Acceptance: an x402 payment precedes the data fetch; a payment over the session cap is refused with a logged reason
  - Files: agent/payments/x402.py

- [ ] Task 4: Decision + guardrail layer (drawdown breaker, per-trade/daily cap, token allowlist, slippage bound)
  - Acceptance: one command runs read→decide→sign→submit once and produces a tx hash; a deliberately over-cap trade is REFUSED with a logged reason
  - Files: agent/strategy/decide.py, agent/guardrails/limits.py

## Phase 2 (data flows)
- [ ] Task 5: ≥3 CMC signal streams (funding + F&G + derivatives positioning) into a regime decision
- [ ] Task 6: x402 trust-gate scores signal freshness/reliability before acting (IDEAS #4 mechanism)

## Phase 3 (product complete)
- [ ] Task 7: On-chain competition registration via `twak compete register` (agent address on BSC contract)
- [ ] Task 8: Full guardrail suite + autonomous unattended loop (≥1 trade/day)
- [ ] Task 9: Mainnet cutover with explicit capital cap; SigningPolicy EIP-712 gating live
- [ ] Task 10: Public repo (LICENSE, README reproduce steps, CONTRIBUTING.md) + per-special-track writeups

## Phase 4 (polish + submission)
- [ ] Task 11: /design helmsman (trade-log + verdict UI)
- [ ] Task 12: /demo-video — show the self-custody + autonomous-signing loop end to end with a BSC tx hash
- [ ] Task 13: /submit helmsman — agent address + strategy on DoraHacks; link tests

## Completed
(builder fills this in)
