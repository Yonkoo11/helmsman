# Helmsman — Win Plan (2026-06-20)

## Honest thesis (what winning actually requires)
Track 1's headline is **live PnL over one week** — variance-dominated, not engineerable.
What IS controllable:
1. **The 3 discretionary special prizes ($2K each)** — skill-judged, published rubric. This is where effort converts to winning.
2. **Surviving the week without DQ** (30% drawdown cap, ≥1 trade/day, keep capital deployed).

So we optimize for: deepest load-bearing sponsor integration + disciplined survival. A main
placement is upside lottery on top; we don't bet the build on it.

## "Best Use of TWAK" rubric → our coverage (the money board)
| Criterion (weight) | Status | Work |
|---|---|---|
| TWAK integration depth — sole exec layer, >1 surface (30) | partial | signing ✓; add x402 + autonomous mode via TWAK |
| Self-custody integrity — local signing whole loop (25) | ✓ | keychain, dedicated wallet, no custodial step (proven on-chain) |
| Autonomous execution + guardrails (20) | partial | guardrails ✓ + persistent state ✓; **need the unattended loop** |
| Native x402 usage — real, in the trade loop (10) | **FEASIBLE, not built** | pay CMC `/dex/search` per request on BSC via TWAK x402 |
| Originality + real-world relevance (10) | ✓ | "a self-custody user would actually let it run" thesis |
| Demo — self-custody + autonomous loop + on-chain proof (5) | todo | record the loop + tx hashes |
Tie-breakers: cleanest self-custody → deepest least-replaceable TWAK → most substantive x402. We aim to win all three.

## Deep-integration plan (verified feasible 2026-06-20)
- **x402 (CMC + TWAK + BNB SDK in one):** agent pays CMC `/dex/search` per request via
  `twak x402 request` on BSC, paying with held USDT (permit2) or United Stables (eip3009).
  Wrap with a **session spend budget** (mirrors bnbagent `SessionBudgetTracker`) + a
  recipient/amount **signing policy** (mirrors bnbagent `SigningPolicy`). One feature, three sponsors.
- **BNB SDK identity:** register the agent via `erc8004` `ERC8004Agent` → verifiable on-chain
  agent identity. Unique, deep "Best Use of BNB SDK" signal.
- **CMC depth:** regime from ≥3 streams (Fear&Greed + funding + derivatives positioning),
  pre-computed indicators consumed (not recomputed). Optionally publish the strategy as a CMC Skill (Track 2 double-dip).

## Prioritized backlog (EV × safety)
P0 — deep integration that scores (this is the win):
  1. x402 data layer: pay CMC `/dex/search` on BSC, session budget + signing policy. [BUILDING]
  2. Autonomous loop: unattended, ≥1 trade/day, single-instance lock, production caps.
  3. bnbagent erc8004 agent-identity registration.
P1 — survival/safety (or we lose money / get DQ'd):
  4. Token allowlist pinned to the 149 BSC contract addresses (anti scam-ticker). [review #4]
  5. Daily-qualify trade guarantee (≥1/day or DQ). [review #5]
  6. MEV/slippage: tight slippage + liquidity gate; evaluate private RPC. [review #6]
  7. Single-instance lock. [review #7]
P2 — depth/CMC:
  8. Multi-signal regime (funding + derivatives + F&G).
  9. CMC Skill (Track 2 double-dip).
P3 — present:
  10. Demo video (self-custody + autonomous loop + on-chain proof), submission writeups per special.

## Critique guards (check each build against these)
- Is the integration LOAD-BEARING (remove it → demo breaks) or decorative? Only load-bearing counts.
- Is it REAL on-chain (tx hash / paid request), not a mock? The rubric explicitly rejects README-only.
- Does it preserve self-custody (no raw key in process, no custodial hop)?
- Does it move us toward survival (no DQ) AND a special-prize criterion? If neither, deprioritize.
