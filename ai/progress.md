# Helmsman — Progress

## 2026-06-20 — Phase 1 PASSED (live on BSC mainnet)

### What Changed (Plain English)
The agent did its first real trade. It registered itself in the competition,
then read a price, ran the trade through its own safety check, and signed and
sent a real swap on the BNB chain — turning a little BNB into about 1.49 in
stablecoin. Both transactions are confirmed on the public blockchain. The agent
signed everything itself; nobody handed over a private key.

### Done + verified live
- Agent wallet funded (~$4 BNB) and backed up (outside the repo).
- Registered on-chain: tx 0x2b3ae2ff…32296.
- First signed trade: tx 0xe9228df5…16ea (confirmed, 1.49 USDT received).
- Keychain signing works → the agent can sign unattended.
- Execution adapter fixed to match the real Trust Wallet CLI (USD swaps,
  priceImpact, keychain fallback) and verified against a live quote.
- Guardrail engine: 12/12 unit tests; blocks bad trades in the live dry-run.

### Honest caveats
- The live trade used a RELAXED TEST PROFILE so a ~$1.5 swap passed on a ~$4
  account. The real trading-week caps ($5 floor, 10%/trade, 15% drawdown halt)
  are unchanged and NOT yet exercised live.
- The main orchestrator still uses a synthetic $1,000 portfolio; only the proof
  script reads the real balance. Live-portfolio wiring is next.
- Not yet built: multi-signal regime model (Phase 2), x402 metering, the
  unattended scheduler/watch loop, real capital sizing for the week.

### Next
- Wire the real TWAK portfolio into the orchestrator (replace synthetic state).
- Add the multi-signal regime strategy (funding + F&G + derivatives).
- Add x402 metering on CMC calls (sponsor depth).
- Build the unattended loop (≥1 trade/day) under PRODUCTION caps.
- Decide real trading-week capital before 2026-06-22.
