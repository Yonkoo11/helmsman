# Self-custody trader, unattended-safe

**Helmsman** is an autonomous crypto trading agent for BNB Smart Chain that you
can actually leave running. It reads CoinMarketCap signals, decides an
allocation, and **signs every trade locally through the Trust Wallet Agent Kit**
— so the keys never leave you — while a hard risk-governance layer (drawdown
circuit-breaker, per-trade and daily caps, token allowlist, gas reserve) keeps it
from blowing up. It pays for live market data per request via **x402**, budget-
capped by the **BNB Agent SDK**, and carries a verifiable **ERC-8004** on-chain
identity.

Built for **BNB Hack: AI Trading Agent Edition** (CoinMarketCap × Trust Wallet ×
BNB Chain). Track 1 (Autonomous Trading Agents) + the three special prizes.

## On-chain proof (BSC mainnet)
- Agent wallet (registered participant): [`0xa7B70b8dC19196d0B9a2c9151568C66669Be957D`](https://bscscan.com/address/0xa7B70b8dC19196d0B9a2c9151568C66669Be957D)
- Competition registration tx: [`0x2b3ae2ff…32296`](https://bscscan.com/tx/0x2b3ae2ff1f7493dfeb1a9a6f435e396dbef47a7e47c6f6e39500ff6142e32296)
- First TWAK-signed swap: [`0xe9228df5…16ea`](https://bscscan.com/tx/0xe9228df5aaaadc3607797d5d3027ae91c5053a0812f624899c3ef86af35016ea)
- Autonomous daily-qualify swap: [`0x5b9479cd…b671`](https://bscscan.com/tx/0x5b9479cd80985144056f86c550862f8a743f2bfe3adecbe437a5f7ad5929b671)
- ERC-8004 identity mint (agent #138851): [`0x0c0afd33…85f3`](https://bscscan.com/tx/0x0c0afd338e37811b19cbd7b939a70f66ce25e12a3af30fbff66f0f1ededa85f3)

## Why it's different
Most trading-agent builds are a thin LLM wrapper around a single swap call. The
hard part of an *unattended* self-custody trader is not the alpha — it's not
blowing up. Helmsman makes the risk layer the product:

- **Drawdown circuit-breaker** halts risk-taking at 15% from peak (well under the
  contest's 30% disqualify line) and only allows de-risking into stables.
- **Per-trade (10%), daily-turnover (40%), and concentration (35%) caps**, a
  **slippage bound**, and a **gas reserve** so it can never strand itself unable
  to pay for a transaction.
- **Token registry pinned to CMC-authoritative BSC contract addresses** — it
  trades only verified majors, never a scam look-alike ticker.
- **Daily-qualify net** guarantees ≥1 trade/day (a ranking requirement) with a
  minimal stable→stable swap when the strategy decides to hold.
- **Confirm-before-record + pending-tx reconciliation** so a slow confirmation
  can't double-trade.

## How the three sponsor tools are load-bearing
- **Trust Wallet Agent Kit (TWAK)** is the *sole* execution layer: wallet, local
  keychain signing for every swap, on-chain competition registration, and the
  x402 payment signing. Remove it and there is no product.
- **CoinMarketCap Agent Hub** is the data brain: a 4-factor regime (Fear & Greed,
  momentum, macro market-cap, BTC dominance) across three live endpoints, plus
  **x402-paid DEX data inside the trade loop**.
- **BNB Agent SDK** provides the x402 `SessionBudgetTracker` (a hard cap on data
  spend) and the ERC-8004 identity registry config.

## Strategy
A multi-signal **regime** model scores risk appetite from CoinMarketCap data and
maps it to a target allocation (risk-on → accumulate ETH, risk-off → rotate to a
stable, neutral → hold). It is **trend-aware** on purpose: a backtest showed a
contrarian "buy the dip" default underperforms in downtrends, so momentum is the
dominant factor. Across BTC/ETH/BNB and walk-forward sub-periods the strategy cut
drawdown below buy-and-hold in every window (see [`ai/backtest-report.md`](ai/backtest-report.md)).
It trades upside in rallies for materially lower drawdown — the "don't blow up"
posture the contest rewards.

## Run it
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
npm install                                   # TWAK CLI (@trustwallet/cli)
cp .env.example .env                          # add your CMC_API_KEY
npx twak setup                                # create + fund the agent wallet
PYTHONPATH=. .venv/bin/python -m agent.token_registry --build
PYTHONPATH=. .venv/bin/python -m agent.orchestrator    # live read (no spend)
PYTHONPATH=. .venv/bin/python -m agent.backtest --robustness
```
Run one autonomous cycle: `PYTHONPATH=. .venv/bin/python -m agent.runner`.
Deploy hourly: see [`deploy/README.md`](deploy/README.md). Tests: `pytest`.

## Honest limitations
- Live PnL is unproven and unknowable until the trading week; the validated claim
  is risk control (lower drawdown), not guaranteed profit.
- The backtest is ~1 year (Fear & Greed history cap); trend-following whipsaws in
  ranging markets.
- The x402 liquidity overlay fail-opens for registry-verified majors (the registry
  is the hard scam gate).
- A Permit2 MAX-allowance is granted on first x402 payment; bounded by the
  dedicated wallet's small balance.

MIT licensed. Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
