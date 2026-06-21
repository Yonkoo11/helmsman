# BNB Hack — exact requirements vs Helmsman status (2026-06-21)

Track chosen: **Track 1 (Autonomous Trading Agents, $24K)** + all 3 special prizes
(cross-track bonuses; can win a main placement AND a special). "Pick one" = one
main track, so NO Track 2 Skill.

## A. Track 1 mechanics
| # | Requirement | Status |
|---|---|---|
| A1 | Reads markets via CMC | ✅ 4-factor regime over 3 live CMC endpoints + x402 DEX data |
| A2 | Decides + signs + processes its own txs via TWAK | ✅ TWAK keychain signing every swap |
| A3 | Operates within rules you set | ✅ guardrail engine (caps, breaker, gas, allowlist) |
| A4 | Trades live on BSC during the week (Jun 22–28) | ⏳ needs funding + an always-on host |
| A5 | Scored on real PnL, max drawdown cap (e.g. 30%) = DQ | ✅ breaker halts at 15% (under the line) |

## B. Registration (on-chain) — DONE
| B1 | Register via `twak compete register` before trading opens Jun 22 | ✅ `registered: true` |
| B2 | Competition contract 0x212c…aed5 | ✅ our address recorded |

## C. Eligible tokens — "trades outside the list do NOT count"
The list is **149 BEP-20 tokens**. **BNB (native) is NOT on it.** What we trade:
| Token | On list? | Our use |
|---|---|---|
| ETH | ✅ | strategy core (risk-on buy) |
| USDT | ✅ | de-risk / stable leg |
| USDC | ✅ | daily-qualify stable |
| USD1, FDUSD | ✅ | registry stables |
| CAKE | ✅ | registry (liquid major) |
| **BNB** | ❌ NOT on list | **gas only — never traded** (fixed) |
All trades route ETH↔USDT and USDT↔USDC — every leg is in-scope. ✅

## D. Ranking rules — ACTION NEEDED
| D1 | ≥1 trade/day (7 over the week) | ✅ daily-qualify net — **but only if the host is running** |
| D2 | Hold non-zero **in-scope** balance at competition start (Jun 22) | ⚠️ we hold USDT+USDC (in-scope) but only ~$1.45; **$2.56 is in BNB which is NOT in-scope** |
| D3 | Any hour starting with portfolio ≤ $1 scores 0% — keep capital deployed | ✅ dust-floor + gas-reserve guards; keep > $1 in-scope |
| D4 | Simulated tx costs apply | ✅ slippage bound + small trade sizes |

## E. Submission requirements
| E1 | On-chain proof: agent address on BSC | ✅ `0xa7B7…957D` + 4 proof tx hashes |
| E2 | Reproducible: public repo + demo link/video **OR** clear setup instructions | ⏳ repo READY to push (not yet public); README has setup steps (satisfies the OR); demo video not built |
| E3 | Register + submit agent address on DoraHacks + explain strategy | ⏳ writeup ready (ai/submission.md); **you submit the form** |
| E4 | No token launches during the event | ✅ none |

## F. Special-prize scoring — Best Use of TWAK (the controllable win)
| Criterion (weight) | Status |
|---|---|
| TWAK integration depth — sole exec layer, >1 surface (30) | ✅ signing + x402 + registration + ERC-8004; autonomous loop. (Could add TWAK `automate`/`watch` for an explicit "autonomous mode" surface — optional depth.) |
| Self-custody integrity — local signing whole loop (25) | ✅ keychain, no custodial step → top band (20–25) |
| Autonomous execution + guardrails (20) | ✅ hands-off loop + drawdown/allowlist/per-trade/daily/slippage |
| Native x402 in the trade loop (10) | ✅ real $0.01 on-chain payments, budget-capped |
| Originality + real-world relevance (10) | ✅ "a self-custody user would actually let it run" |
| Demo (5) | ⏳ **demo video not built** |

## GAPS TO CLOSE (ranked)
1. **Fund the wallet with IN-SCOPE assets** (ETH + USDT/USDC) before Jun 22 — BNB does NOT count for ranking; keep a little BNB only for gas. (you) — **most important**
2. **Always-on host running Jun 22–28** so the daily trade fires (else DQ). (you)
3. **Push the public repo** (ready, gh logged in as Yonkoo11). (1 word from you)
4. **Demo video** — required for the 5-pt demo criterion + panel. (me)
5. **Submit the DoraHacks form** with repo + demo + address + strategy. (you)
