# Helmsman — Progress

## Session 2026-06-18 — Phase 1 started

### What Changed (Plain English)
The trading agent's brain now runs end to end in a safe practice mode. You can
watch it read a market mood signal, decide a trade, and then have its built-in
safety guard either approve or block that trade — all printed step by step. In
testing, the guard correctly blocked a trade that would put too much money into
one coin, and approved a trade that reduced risk. None of this touches real
money yet.

### Done + verified
- Confirmed all three sponsor tools are real and working on this machine: Trust
  Wallet Agent Kit (`@trustwallet/cli` v0.19.1), BNB Agent SDK (`bnbagent`
  v0.3.6 in a Python 3.12 venv), BSC testnet reachable. CMC key not set yet.
- Built the **guardrail engine** (the safety core): per-trade cap, daily
  turnover cap, position-concentration cap, slippage bound, eligible-token
  allowlist (the 149 BNB-Hack tokens), dust-floor protection, and a drawdown
  circuit breaker that halts risk and only allows de-risking. **12/12 unit
  tests pass.**
- Wired the full loop: CMC data client, TWAK execution adapter (local signing +
  dry-run), Fear&Greed regime strategy, orchestrator. **Dry-run runs the whole
  read->decide->guard->execute path across fear/neutral/greed with no creds.**

### Phase 1 gate status
- (a) "an over-cap trade is refused with a logged reason" — DONE + demonstrated
  in both unit tests and the live dry-run loop.
- (b) "a real TWAK-signed trade lands an on-chain tx, no custodial step" —
  code written, NOT yet run live. Blocked only on the two credential steps below.

### Blocked on user (credential signups only)
1. CMC API key: get one at coinmarketcap.com/api, then `export CMC_API_KEY=...`.
2. TWAK creds + agent wallet: run `npx twak setup` (interactive — creates the
   self-custody wallet + API credentials). Then `npx twak compete status` should
   recognise it.

### Next
- With creds: run `python -m agent.orchestrator` live for half (b); confirm a
  BSC tx hash from a TWAK-signed swap.
- Confirm whether TWAK BSC swaps are mainnet-only (decides testnet vs tiny-mainnet
  proof for the on-chain tx).
- Wire live TWAK portfolio into the orchestrator (replace synthetic state).
- Register the agent on-chain before the trading window (`twak compete register`).
