# Helmsman: DoraHacks submission

**Pitch:** Self-custody trader, unattended-safe.

**Tagline:** An autonomous BSC trading agent whose edge is risk discipline. It
signs every trade itself and is built to survive the week without blowing up.

**Track:** 1, Autonomous Trading Agents. Also entering all three special prizes
(Best Use of TWAK, Best Use of CMC Agent Hub, Best Use of BNB AI Agent SDK).

**Agent wallet (BSC):** `0xa7B70b8dC19196d0B9a2c9151568C66669Be957D`
**Repo:** https://github.com/Yonkoo11/helmsman   **Demo:** <video/loom URL>

## What it does
Helmsman reads CoinMarketCap data, scores a market regime, and rotates between a
core asset (ETH) and stables, signing every trade locally through the Trust
Wallet Agent Kit. A hard risk layer governs it: a 15% drawdown circuit-breaker
that sits under the 30% disqualify line, per-trade and daily and concentration
caps, a slippage bound, a gas reserve, and a token registry pinned to
CoinMarketCap-authoritative BSC contract addresses. A daily-qualify net
guarantees at least one trade per day. It pays for live DEX data per request via
x402, budget-capped by the BNB Agent SDK, and holds a verifiable ERC-8004
on-chain identity.

## Strategy (how it decides)
A four-factor regime score from three live CMC endpoints:
- Sentiment, from Fear & Greed (contrarian).
- Momentum, from the core asset's 7-day trend (the dominant factor).
- Macro, from total market-cap 24h change.
- Dominance, from the BTC dominance shift.

A score at or above +0.20 goes risk-on (accumulate ETH); at or below -0.20 goes
risk-off (rotate to stable); otherwise it holds. It is trend-aware on purpose. A
backtest (reproducible with `python -m agent.backtest --robustness`) showed a
contrarian default catches falling knives. Across BTC, ETH and BNB and across
walk-forward sub-periods, the strategy cut drawdown below buy-and-hold in every
one of 18 windows, and beat it on both return and drawdown on all three full
windows. It trades rally upside for lower drawdown, which is the contest's "most
profit without blowing up" posture.

## Best Use of Trust Wallet Agent Kit
TWAK is the sole execution layer, used across several surfaces:
- Local keychain signing for every swap. Self-custody holds end to end, with no
  custodial step (first signed swap `0xe9228df5…16ea`).
- Autonomous, hands-off execution under the guardrail rules. A full cycle ran and
  traded by itself (`0x5b9479cd…b671`).
- On-chain competition registration via `twak compete register` (`0x2b3ae2ff…32296`).
- x402 payment signing for data in the trade loop.

Remove TWAK and the product does not exist.

## Best Use of CoinMarketCap Agent Hub
CMC is the data brain. Three live endpoints feed a four-factor regime, and the
agent pays for DEX data inside the loop over x402 ($0.01 per request on BSC, paid
with the agent's own USDT) as a live-liquidity check. Token addresses are resolved
from CMC's authoritative API to gate out scam tickers.

## Best Use of BNB AI Agent SDK
The SDK is load-bearing in two places. Its x402 `SessionBudgetTracker` enforces a
hard cap on data spend, a real guardrail on money that can refuse a call. Its
ERC-8004 registry config backs the agent's minted on-chain identity (agent
#138851, `0x0c0afd33…85f3`).

## Reproduce
Public repo with an MIT license, README setup steps, and 63 passing tests.
`python -m agent.orchestrator` is a live read that spends nothing.

## Honest notes
Live PnL is unproven until the trading week. The validated claim is risk control.
The backtest covers about one year (the Fear & Greed history limit) and
trend-following whipsaws in ranging markets. Stated plainly, not hidden.
