# DoraHacks BUIDL submission — copy/paste by form tab

The DoraHacks form has five tabs: Profile, Details, Team, Contact, Submission.
Each field below is labelled to match. Items in [brackets] are yours to provide.

================================================================
PROFILE
================================================================

**BUIDL (project) name**
Helmsman

**BUIDL logo**
[upload a 480x480 PNG/JPEG under 2 MB]

**Vision (the problem this project solves)**
Self-custody users will not let an AI agent trade for them, because the two
options on offer are both bad: hand your keys to a bot, or trust a black box not
to blow up your account. Most trading agents make this worse. They are a thin
wrapper around a single swap call, with the real risk controls missing, so one
bad run can drain the wallet. Helmsman solves the trust problem: the agent signs
every trade itself through Trust Wallet, the keys never leave you, and a hard
risk layer makes it safe to leave running unattended.

**Category**
Crypto / Web3 (secondary: AI / Robotics)

================================================================
DETAILS
================================================================

**Short description / tagline**
Self-custody trader, unattended-safe.

**Full description**
Helmsman is an autonomous trading agent for BNB Smart Chain that you can actually
leave running. It reads CoinMarketCap signals, scores a market regime, and rotates
between ETH and stables, signing every trade locally through the Trust Wallet
Agent Kit so the keys never leave the user.

The hard part of an unattended self-custody trader is not the alpha, it is not
blowing up. Helmsman makes the risk layer the product:
- A drawdown circuit-breaker halts risk-taking at 15 percent from peak, under the
  30 percent disqualify line, and only allows de-risking into stables.
- Per-trade, daily-turnover and concentration caps, a slippage bound, and a gas
  reserve, so it can never strand itself unable to pay for a transaction.
- A token registry pinned to CoinMarketCap-authoritative BSC contract addresses,
  so it trades only verified majors, never a scam look-alike ticker.
- A daily-qualify safeguard that guarantees at least one trade per day.
- Confirm-before-record and pending-transaction reconciliation, so a slow
  confirmation cannot cause a double-trade.

How the three sponsor tools are load-bearing:
- Trust Wallet Agent Kit is the sole execution layer. It does the wallet, the
  local keychain signing for every swap, the on-chain competition registration,
  and the x402 payment signing.
- CoinMarketCap Agent Hub is the data brain. A four-factor regime (Fear and Greed,
  momentum, total market cap, BTC dominance) reads three live endpoints, and the
  agent pays for DEX data inside the trade loop over x402.
- BNB Agent SDK provides the x402 session budget tracker, a hard cap on data spend
  that can refuse a call, plus the ERC-8004 identity registry config.

**Strategy (how it gets its results)**
A four-factor regime model scores risk appetite and maps it to a target
allocation: risk-on accumulates ETH, risk-off rotates to a stable, neutral holds.
It is trend-aware on purpose. A backtest showed that a contrarian buy-the-dip
default underperforms in downtrends, so momentum is the dominant factor. Across
BTC, ETH and BNB, and across walk-forward sub-periods, the strategy cut drawdown
below buy-and-hold in every window. It trades rally upside for lower drawdown,
which is the contest goal of most profit without blowing up.

**Tech stack**
Python agent (regime, guardrails, risk state), Trust Wallet Agent Kit (TWAK) for
signing and execution, CoinMarketCap Agent Hub for data, BNB Agent SDK for the
x402 budget tracker and ERC-8004 identity, BNB Smart Chain.

**Demo video**
[optional link. The README has full setup and run instructions.]

**Repository**
https://github.com/Yonkoo11/helmsman

================================================================
TEAM
================================================================
[your name / handle and any teammates]

================================================================
CONTACT
================================================================
[your email and socials, e.g. X / Telegram]

================================================================
SUBMISSION
================================================================

**Agent wallet address (BSC, required for Track 1)**
0xa7B70b8dC19196d0B9a2c9151568C66669Be957D

**On-chain proof (BSC mainnet)**
- Competition registration: 0x2b3ae2ff1f7493dfeb1a9a6f435e396dbef47a7e47c6f6e39500ff6142e32296
- TWAK-signed risk-on swap: 0xff1a49c4d16ae879b006e0027c6584f703f2233b7caad10c8008652938d7cbbf
- Autonomous daily-qualify swap: 0x5b9479cd80985144056f86c550862f8a743f2bfe3adecbe437a5f7ad5929b671
- ERC-8004 identity mint (agent number 138851): 0x0c0afd338e37811b19cbd7b939a70f66ce25e12a3af30fbff66f0f1ededa85f3

**Tracks entered**
Track 1, Autonomous Trading Agents. Plus the three special prizes: Best Use of
Trust Wallet Agent Kit, Best Use of CMC Agent Hub, Best Use of BNB AI Agent SDK.

**Reproducible**
Public repository, MIT license, README setup steps, 63 passing tests. The live
read command spends nothing.
