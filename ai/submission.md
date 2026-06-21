# Helmsman — DoraHacks submission

**Pitch:** Self-custody trader, unattended-safe.

**Tagline:** An autonomous BSC trading agent whose edge is risk discipline, not
hype — it signs every trade itself and is built to survive the week without
blowing up.

**Track:** 1 — Autonomous Trading Agents. Also entering all three special prizes
(Best Use of TWAK, Best Use of CMC Agent Hub, Best Use of BNB AI Agent SDK).

**Agent wallet (BSC):** `0xa7B70b8dC19196d0B9a2c9151568C66669Be957D`
**Repo:** <github URL once pushed>   **Demo:** <video/loom URL>

## What it does
Helmsman reads CoinMarketCap data, scores a market regime, and rotates between a
core asset (ETH) and stables — signing every trade locally through the Trust
Wallet Agent Kit. A hard risk layer governs it: a 15% drawdown circuit-breaker
(under the 30% DQ line), per-trade/daily/concentration caps, a slippage bound, a
gas reserve, and a token registry pinned to CoinMarketCap-authoritative BSC
contract addresses. A daily-qualify net guarantees ≥1 trade/day. It pays for live
DEX data per request via x402, budget-capped by the BNB Agent SDK, and holds a
verifiable ERC-8004 on-chain identity.

## Strategy (how it decides)
A 4-factor regime score from three live CMC endpoints:
- **Sentiment** — Fear & Greed (contrarian).
- **Momentum** — core-asset 7-day trend (dominant factor).
- **Macro** — total market-cap 24h change.
- **Dominance** — BTC dominance shift.

Score ≥ +0.20 → risk-on (accumulate ETH); ≤ −0.20 → risk-off (rotate to stable);
else hold. It is trend-aware on purpose: a backtest (reproducible:
`python -m agent.backtest --robustness`) showed a contrarian default catches
falling knives. Across **BTC, ETH, BNB and walk-forward sub-periods the strategy
cut drawdown below buy-and-hold in every one of 18 windows**, beating it on both
return and drawdown on all three full windows. It trades rally upside for lower
drawdown — the contest's "most profit without blowing up" posture.

## Best Use of Trust Wallet Agent Kit
TWAK is the **sole execution layer**, used across multiple surfaces:
- Local keychain signing for **every** swap (self-custody preserved end to end —
  no custodial step; first signed swap `0xe9228df5…16ea`).
- Autonomous, hands-off execution under the guardrail rules (a full cycle ran and
  traded by itself: `0x5b9479cd…b671`).
- On-chain competition registration via `twak compete register` (`0x2b3ae2ff…32296`).
- **x402** payment signing for data in the trade loop.
Remove TWAK and the product does not exist.

## Best Use of CoinMarketCap Agent Hub
CMC is the data brain across **three live endpoints** feeding a 4-factor regime,
plus **x402-paid DEX data inside the loop** ($0.01/request on BSC, paid with the
agent's own USDT) used as a live-liquidity check. Token addresses are resolved
from CMC's authoritative API to gate out scam tickers.

## Best Use of BNB AI Agent SDK
The SDK is load-bearing in two places: its x402 `SessionBudgetTracker` enforces a
hard cap on data spend (a real guardrail on money — it can refuse a call), and its
ERC-8004 registry config backs the agent's minted on-chain identity (**agent
#138851**, `0x0c0afd33…85f3`).

## Reproduce
Public repo with MIT license, README reproduce steps, and 63 passing tests.
`python -m agent.orchestrator` is a live read that spends nothing.

## Honest notes
Live PnL is unproven until the trading week; the validated claim is risk control.
The backtest is ~1 year (Fear & Greed history cap) and trend-following whipsaws in
ranging markets. Disclosed, not hidden.
