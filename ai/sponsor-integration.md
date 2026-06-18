# Sponsor Integration Depth — Helmsman

Surface verified live 2026-06-18 via sponsor docs. Hard rule: any track we submit for must score ≥3; the load-bearing primitive targets ≥4.

## TWAK (Trust Wallet Agent Kit) — Best Use of TWAK special ($2K)
Current planned depth: 5/5 (target 5/5). TWAK is the SOLE execution layer.
Surface used: local self-custody signing + autonomous mode + x402 per-call gating + `twak compete register`.
Committed wins (V1, must ship):
1. Every trade signed locally via TWAK — no CEX, no third-party co-sign, no custodial step. Acceptance: tx hash on BSC traces back to the TWAK agent wallet; no private key ever in agent process memory.
2. Autonomous mode runs the full trade loop unattended inside the guardrail rules. Acceptance: agent completes ≥1 trade/day for the window with zero manual approvals.
3. x402 used as a real payment rail in the trade loop (pay CMC/inference per request). Acceptance: an x402 payment tx precedes a data fetch that feeds a real decision.
4. On-chain competition registration via `twak compete register`. Acceptance: agent address appears in the BSC competition contract participant list before 2026-06-22.
Stretch (V2): WalletConnect user-approval mode as an alternate custody profile to demo the dual-custody model.

## CoinMarketCap Agent Hub — Best Use of Agent Hub special ($2K)
Current planned depth: 5/5 (target 5/5). CMC is the SOLE data brain.
Surface used: funding rates, Fear & Greed, derivatives positioning, pre-computed RSI/MACD/EMA; via MCP and paid per-call via x402.
Committed wins (V1):
1. ≥3 distinct CMC signal streams feed the decision (e.g. funding rate + F&G + derivatives positioning). Acceptance: removing any one changes the allocation output in a logged case.
2. Pre-computed indicators consumed instead of recomputed in-agent (uses Hub's agent-ready output). Acceptance: no local RSI/MACD math; values sourced from CMC.
3. x402 metering on CMC requests. Acceptance: per-call payment visible in the trade-loop log.
Stretch (V2): publish the strategy as a CMC Skill (doubles into Track 2).

## BNB AI Agent SDK — Best Use of BNB AI Agent SDK special ($2K)
Current planned depth: 4/5 (target 4/5). SDK is the payment-gating + on-chain spine.
Surface used: X402Signer (scoped per-call + session budget caps), SigningPolicy (EIP-712 gating), BSC deploy.
Committed wins (V1):
1. X402Signer enforces per-call + session budget caps on every data/inference payment. Acceptance: a payment exceeding the session cap is refused by the signer with a logged reason.
2. SigningPolicy gates trade authorizations (EIP-712 typed-data). Acceptance: a malformed/out-of-policy authorization is rejected.
3. Runs on BSC (testnet 97 for Phase 1, mainnet 56 for competition). Acceptance: tx hashes on the correct chain id.
Stretch (V2): publish each trade decision (signal → action → guardrail verdict) as an ERC-8183 job/attestation for a verifiable public trade trail.

## Track triage
- Track 1 (Autonomous Trading Agents): ENTER — depth 5/5 on TWAK load-bearing.
- Best Use of TWAK / CMC Hub / BNB SDK: ENTER all three — depth ≥4 each, can win alongside a main placement.
- Track 2 (Strategy Skill): conditional double-dip — enter only if the strategy engine yields a clean standalone CMC Skill at near-zero marginal cost (depth 4/5 CMC-only is allowed for this track). Do not split focus from Track 1.
