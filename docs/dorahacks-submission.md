# DoraHacks submission — paste-ready

Fill the DoraHacks BUIDL form with the fields below.

---

**Project name:** Helmsman

**Intro / one-liner:** Self-custody trader, unattended-safe.

**Track:** Track 1, Autonomous Trading Agents. Also entering the three special
prizes: Best Use of Trust Wallet Agent Kit, Best Use of CMC Agent Hub, Best Use
of BNB AI Agent SDK.

**Agent wallet address (BSC):** 0xa7B70b8dC19196d0B9a2c9151568C66669Be957D

**GitHub:** https://github.com/Yonkoo11/helmsman

**Demo / video:** (optional) clear setup and run instructions are in the README.

---

## Description

Helmsman is an autonomous trading agent for BNB Smart Chain that you can actually
leave running. It reads CoinMarketCap signals, scores a market regime, and rotates
between ETH and stables, signing every trade locally through the Trust Wallet Agent
Kit so the keys never leave the user.

The hard part of an unattended self-custody trader is not the alpha, it is not
blowing up. Helmsman makes the risk layer the product:
- A drawdown circuit-breaker halts risk-taking at 15% from peak, under the 30%
  disqualify line, and only allows de-risking into stables.
- Per-trade, daily-turnover and concentration caps, a slippage bound, and a gas
  reserve so it can never strand itself unable to pay for a transaction.
- A token registry pinned to CoinMarketCap-authoritative BSC contract addresses,
  so it trades only verified majors, never a scam look-alike ticker.
- A daily-qualify net that guarantees at least one trade per day.
- Confirm-before-record plus pending-tx reconciliation, so a slow confirmation
  cannot cause a double-trade.

How the three sponsor tools are load-bearing:
- Trust Wallet Agent Kit is the sole execution layer: wallet, local keychain
  signing for every swap, on-chain competition registration, and x402 payment
  signing.
- CoinMarketCap Agent Hub is the data brain: a four-factor regime (Fear & Greed,
  momentum, macro market-cap, BTC dominance) over three live endpoints, plus
  x402-paid DEX data inside the trade loop.
- BNB Agent SDK provides the x402 SessionBudgetTracker (a hard cap on data spend
  that can refuse a call) and the ERC-8004 identity registry config.

## Strategy (how it achieves its results)

A four-factor regime model scores risk appetite and maps it to a target
allocation: risk-on accumulates ETH, risk-off rotates to a stable, neutral holds.
It is trend-aware on purpose. A backtest showed a contrarian buy-the-dip default
underperforms in downtrends, so momentum is the dominant factor. Across BTC, ETH
and BNB and across walk-forward sub-periods, the strategy cut drawdown below
buy-and-hold in every window. It trades rally upside for materially lower
drawdown, which is the contest's "most profit without blowing up" posture.

## On-chain proof (BSC mainnet)

- Agent wallet: 0xa7B70b8dC19196d0B9a2c9151568C66669Be957D
- Competition registration: 0x2b3ae2ff1f7493dfeb1a9a6f435e396dbef47a7e47c6f6e39500ff6142e32296
- TWAK-signed risk-on swap: 0xff1a49c4d16ae879b006e0027c6584f703f2233b7caad10c8008652938d7cbbf
- Autonomous daily-qualify swap: 0x5b9479cd80985144056f86c550862f8a743f2bfe3adecbe437a5f7ad5929b671
- ERC-8004 identity mint (agent #138851): 0x0c0afd338e37811b19cbd7b939a70f66ce25e12a3af30fbff66f0f1ededa85f3

## Reproducible

Public repo, MIT license, README setup steps, 63 passing tests. The live read
command (`python -m agent.orchestrator`) spends nothing.
