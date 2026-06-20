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

## Status
Fixed pass 1: 1, 2, 3 (+ real-balance wiring).
Fixed pass 2 (automode): 4 (token registry), 5 (daily-qualify), 7 (single-instance lock),
  + x402 wired load-bearing into the loop, + ERC-8004 identity minted (agentId 138851).
Partially addressed: 6 — tight slippage (--slippage 1) + a live-liquidity overlay,
  but NO private/MEV-protected RPC yet (sandwich risk on public mempool remains; low EV
  on the small trade sizes used, but a real-capital week should route through a private RPC).
Still open: 8 (equity x-check vs CMC prices), deeper multi-signal CMC regime, demo + writeups.
