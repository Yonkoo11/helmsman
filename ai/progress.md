# Helmsman — Progress

## 2026-06-20 — Automode pass: deep integrations + safety backlog (all on-chain verified)

### What Changed (Plain English)
The agent can now run itself safely and unattended. It only trades a checked
list of real, liquid coins (no look-alike scams), it guarantees at least one
trade a day (a competition rule), it can't run twice at once, it pays for live
market data with on-chain micro-payments under a spending cap, and it now has
its own verifiable on-chain identity. A full automatic cycle ran and made a real
trade by itself.

### Shipped + verified live (one git save each)
- **Verified token registry (#4):** trades only CMC-address-verified BSC majors;
  unresolved/scam tickers refused. Cross-checked USDT/USDC against known addresses.
- **x402 in the loop (#6/x402):** before a buy, the agent PAYS CMC for live DEX
  data (BSC, our USDT) under a BNB-SDK budget cap. Real $0.01 payments on-chain.
- **Daily-qualify net (#5):** guarantees >=1 trade/day via a tiny stable->stable
  swap when the strategy holds. Forced-path verified with a real on-chain trade.
- **Autonomous runner + single-instance lock (#2/#7):** one safe cycle per fire,
  schedulable hourly (launchd plist in deploy/). Live cycle: strategy refused a
  bad trade (dust floor), daily-qualify executed USDT->USDC on-chain (0x5b9479cd).
- **ERC-8004 identity (#3):** minted agent NFT #138851 (tx 0x0c0afd33); card
  embeds all three sponsor integrations; TWAK-signed, BNB-SDK registry config.

### On-chain proofs this pass
- Daily-qualify trade: 0x5b9479cd80985144056f86c550862f8a743f2bfe3adecbe437a5f7ad5929b671
- ERC-8004 mint:       0x0c0afd338e37811b19cbd7b939a70f66ce25e12a3af30fbff66f0f1ededa85f3
- x402 data payment:   USDT 1.4904 -> 1.4804 (earlier), budget-tracked

### Tests: 44 passing (guardrails, state, x402 budget, registry, market gate,
  daily-qualify, lock, runner, identity).

### Still NOT done (honest)
- CMC regime now 3-stream multi-signal (DONE below). Funding/derivatives positioning
  still absent — not on our CMC tier (would need a higher tier).
- MEV: tight slippage + liquidity overlay, but no private/MEV-protected RPC.
- Equity not cross-checked vs CMC prices (#8). Demo video + submission writeups pending.
- Real trading-week capital not decided; account ~$4 (proof scale).
- PnL is unproven and unprovable until the live week.

## 2026-06-20 — Deeper CMC regime (multi-signal)
### What Changed (Plain English)
The agent now reads three CoinMarketCap data streams (market mood, price trend,
and the whole-market backdrop) instead of just mood, and blends them into one
risk score. On live data it correctly held back from buying into fear because the
7-day trend was still down — a smarter call than mood alone.
### Built + verified
- regime.py: 4-factor score (sentiment contrarian + momentum trend + macro mcap +
  BTC dominance). Knife-catch prevention tested. data_cmc: momentum() + global_macro()
  + fetch_signals() (3 live endpoints). strategy maps regime->action.
- Live read: FG=20 but mom7d=-3.9% -> regime neutral -> HOLD (single-signal would buy).
- Honest: funding rates / derivatives positioning are NOT on our CMC tier (403) — omitted, not faked.
- 53 tests pass.
