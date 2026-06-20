# Helmsman — Senior Review (2026-06-20)

Reviewed at the bar of a top BNB/DeFi engineer. Findings ordered by live-week blast radius.

## 🔴 Critical
1. **Drawdown circuit breaker was dead code.** `peak_equity` not persisted → drawdown always 0% → 15% halt never fires → no protection against the 30% DQ. FIXED: `agent/state.py` persists peak equity across runs.
2. **Daily turnover cap was dead.** `traded_today_usd` not persisted, no UTC day reset. FIXED: state tracks `day_utc` + resets on rollover.

## 🟠 High
3. **No post-trade confirmation before recording.** Submit-then-crash corrupts state / risks double-trade. FIXED: `Executor.confirm()` polls the tx to `confirmed` before the trade is recorded.
4. **Allowlist by ticker, not contract address.** A scam token with ticker "USDT" could be routed into. OPEN — Phase 2: pin the 149 eligible tokens to their BSC contract addresses (resolve via CMC), validate the buy-leg contract before signing. Sell-leg is bounded (must be held).
5. **Competition DQ risk: no guaranteed daily trade.** Ranking needs ≥1 trade/day; neutral regime = hold = possible zero-trade day. OPEN — add a tiny compliant qualifying round-trip if no organic trade happened by a daily cutoff.

## 🟡 Medium
6. **MEV / slippage.** Gate liquidity on `priceImpact`, keep `--slippage` tight, document BSC sandwich risk; evaluate a private/MEV-protected RPC for the live week. OPEN.
7. **No single-instance lock** for the unattended loop → overlapping runs double-trade. OPEN — lockfile before the loop ships.
8. **Equity from TWAK USD valuation**, not cross-checked vs CMC prices. OPEN — cross-check in Phase 2.

## Pre-demo review (2026-06-20) — 3 blockers found + fixed
- **BLOCKER 1 (eligibility):** core asset was BNB (native, NOT on the 149 BEP-20 list)
  → strategy trades didn't count. FIXED: core = ETH; BNB removed from eligible list +
  registry; BNB is gas-only now.
- **BLOCKER 2 (gas):** nothing stopped the agent draining BNB → no gas → mid-week brick.
  FIXED: hard gas-reserve check in the guardrail (RiskConfig.min_gas_reserve_usd).
- **BLOCKER 3 (resilience):** the unattended loop had no error handling → a transient
  CMC/RPC/x402 failure crashed the cycle. FIXED: each phase wrapped; logs + continues.
- Still open: #4 always-on-machine dependency for daily-qualify (operational — run on an
  always-on host or cloud); #5 x402 gate is thin (fail-open for majors — honest framing);
  #6 regime weights not backtested; #7 confirm-timeout reconciliation.
- **CAPITAL SETUP NOTE for the live week:** fund the wallet with ETH + stables (in-scope),
  keep only a little BNB for gas. Right now ~$2.56 of $4 is in BNB (gas, not tradable).

## Status
Fixed pass 1: 1, 2, 3 (+ real-balance wiring).
Fixed pass 2 (automode): 4 (token registry), 5 (daily-qualify), 7 (single-instance lock),
  + x402 wired load-bearing into the loop, + ERC-8004 identity minted (agentId 138851).
Partially addressed: 6 — tight slippage (--slippage 1) + a live-liquidity overlay,
  but NO private/MEV-protected RPC yet (sandwich risk on public mempool remains; low EV
  on the small trade sizes used, but a real-capital week should route through a private RPC).
Still open: 8 (equity x-check vs CMC prices), deeper multi-signal CMC regime, demo + writeups.

## Independent audit pass (2026-06-20) — external agent review + fixes
An independent auditor reviewed the money-path. Fixed:
- H-2: removed password-from-argv path (was dormant/keychain; now impossible to leak).
- H-1: confirm() returns confirmed/failed/PENDING; pending tx persisted + reconciled next
  cycle before any new trade (no double-trade on slow confirms).
- C-2/M-4: untrustworthy quote/liquidity data (missing priceImpact, non-finite/absurd liq)
  now BLOCKS instead of passing as 0; strengthens the x402 gate.
- M-3: portfolio rejects non-finite/negative/absurd usdValue (can't inflate the % caps).
- M-1: x402 query address validated (^0x[40hex]$) + URL-encoded.
- H-3: corrupt state file raises (halts) instead of zeroing peak (which disabled the breaker);
  budget-exhaustion halts the cycle instead of forcing a qualify trade.
- H-4: missing registry file fails loud instead of silent no-op.
- L-2/L-3: ERC-8004 card reads guardrail numbers from RiskConfig; --wallet required.
- 63 tests. Still open: M-2 (Permit2 MAX-approval bounded only by small wallet balance;
  budget resets per-trade but <=2 calls/cycle so spend is bounded), backtest, always-on host.
