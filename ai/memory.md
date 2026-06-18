# Helmsman — Memory

## Phase 1 Gate (MUST PASS BEFORE ANY OTHER WORK)
Core Action: agent reads one live CMC signal, decides a trade, and signs + submits it on BSC testnet through TWAK local signing, with the drawdown breaker blocking any over-cap trade — end to end, no custodial step.
Success Test: one command runs the loop once → real BSC testnet tx hash from a TWAK-signed trade; a deliberately over-cap trade is refused by the guardrail with a logged reason.
Min Tech: CMC Agent Hub (1 signal), TWAK local signing on BSC testnet, BNB SDK X402Signer for the data payment.
NOT Phase 1: regime model, personality/chat, copy-trading, mainnet, dashboard, Track 2 Skill, polish.
Status: [ ] NOT STARTED

## Hackathon Context (raw facts)
- Event: BNB Hack: AI Trading Agent Edition — CoinMarketCap × Trust Wallet × BNB Chain
- URL: https://dorahacks.io/hackathon/bnbhack-twt-cmc
- Telegram: https://t.me/+MhiOLT0YUnlmNWFk
- Prize pool: $36,000. Track 1 $24K (5 winners: $10K/6/4/2/2). Track 2 $6K (3 winners: $3K/2/1). 3 special prizes $2K each.
- Registration opened: 2026-06-03. Build window: 2026-06-03 → 2026-06-21. Live trading (Track 1): 2026-06-22 → 2026-06-28. Judging: 2026-06-29 → 2026-07-05. Winners: week of 2026-07-06.
- Track 1 on-chain registration deadline: before 2026-06-22 (trading window open). Track 2 submit by 2026-06-21.
- Competition contract (BSC): https://bsctrace.com/address/0x212c61b9b72c95d95bf29cf032f5e5635629aed5
- Register: `twak compete register` OR MCP `competition_register`.

## Track 1 rules (judged on LIVE PnL)
- Ranked by total return over the held-out week. Max drawdown cap (e.g. 30%) = DISQUALIFIED no matter the headline return.
- Min trades: ≥1 per day (7 over the week). Simulated tx costs apply.
- Eligible tokens: fixed list of 149 BEP-20 tokens listed on CMC (ETH, USDT, USDC, XRP, TRX, DOGE, BNB-set, TWT, CAKE, etc.). Trades outside the list DO NOT count.
- Must hold non-zero in-scope balance at competition start to be ranked. Any hour starting with portfolio ≤ $1 is scored 0% for that hour (drained-to-dust penalty). Keep capital deployed.
- Must register agent address on DoraHacks + explain the strategy.

## Special prizes (discretionary panel — CONTROLLABLE EV)
- Best Use of TWAK (Track 1): TWAK integration depth 30 / self-custody integrity 25 (penalty ladder if custodial step) / autonomous execution + guardrails 20 / native x402 10 / originality 10 / demo 5. Tie-break: cleanest self-custody → deepest least-replaceable TWAK → most substantive x402.
- Best Use of Agent Hub (both tracks).
- Best Use of BNB AI Agent SDK (both tracks). Can win a main placement AND a special.

## Chosen idea — Helmsman (Candidate A)
Risk-governed self-custody trading agent. Differentiator = hard guardrail layer (drawdown circuit-breaker, per-trade/daily caps, token allowlist, slippage bound) + verifiable self-custody trade loop through TWAK, x402-metered CMC data. The drawdown cap is the product thesis, not an afterthought. File tie: IDEAS #4 (x402/CMC data-trust gate scores signal reliability before acting).

## Why this over alternatives
- B (copy-trader) is the organizers' own listed example → crowded + low originality + high DQ risk.
- C (Track 2 Skill) alone leaves $24K + TWAK special on the table; better as a reuse double-dip from the strategy engine.
- A is the only one at 5/5 depth on TWAK (the load-bearing primitive) and wins on a controllable axis (discretionary special) instead of pure PnL luck.

## Competitive landscape
Most teams ship the three listed examples (funding-rate rotation, DCA-with-personality, copy-trader) — undifferentiated degen bots that risk the drawdown DQ. Gap = risk-governance + verifiable self-custody.

## Fatal flaws / risks
1. REAL MONEY at risk during 2026-06-22..28 — mitigate with a hard capital cap + the drawdown breaker as the core feature. Decide capital allocation explicitly before mainnet.
2. Live PnL is variance — engineer survival + a special-prize win, not a guaranteed #1.
3. CMC signal latency — x402 trust-gate flags stale data and de-risks rather than trading on it.
4. NEVER auto-fund beyond the agreed capital cap. The agent's allowlist must exclude draining to dust.

## Required deliverables checklist
- [ ] Agent wallet address registered on BSC competition contract before 2026-06-22
- [ ] Agent address + strategy writeup submitted on DoraHacks
- [ ] Public GitHub repo (OSI LICENSE, README with reproduce steps, CONTRIBUTING.md)
- [ ] Demo link/video showing the self-custody + autonomous-signing loop end to end, with a BSC tx hash
- [ ] One paragraph per special-prize track (TWAK / CMC Hub / BNB SDK), not reused
- [ ] No token launches during the event

## Sponsor surface (verified live 2026-06-18)
- TWAK: local self-custody signing + autonomous mode (DCA/limit/scheduled) + x402 per-call gating; MCP/CLI/LangChain; 25+ chains incl. BNB Chain; `twak compete register`.
- CMC Agent Hub: CEX/derivatives/on-chain/social/KOL/news data; pre-computed MACD/RSI/EMA + Fear&Greed; interfaces MCP + x402 + Skills marketplace; agent-ready output (less JSON bloat).
- BNB AI Agent SDK: ERC-8183 agent-commerce/job-escrow framework. X402Signer (scoped per-call + session budget caps), SigningPolicy (EIP-712 gating), EVMWalletProvider (keystore V3). BSC testnet (97) gas-free via MegaFuel paymaster, BSC mainnet (56). NOTE: no built-in market data or DEX — agent must integrate CMC for data and a BSC DEX/TWAK for execution.
