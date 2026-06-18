# Helmsman — Phase 1 Build Plan (verified 2026-06-18)

## Toolchain reality (all confirmed installed + working locally)
- **TWAK** = `@trustwallet/cli` v0.19.1 (bin `twak`). Local self-custody (keys in OS keychain). Commands that ARE our execution layer: `wallet create/sign-message/portfolio`, `swap`, `price/search/trending/risk`, `balance`, `compete register/status`, `x402`, `automate` (DCA/limit), `watch`, `serve` (MCP/REST). Auth: needs `TWAK_ACCESS_ID` + `TWAK_HMAC_SECRET` for backend data + compete + swaps. `wallet create` works non-interactively; `chains` works with no creds.
- **BNB Agent SDK** = `bnbagent` v0.3.6 (Python, venv .venv on 3.12). Modules: `signing`, `wallets`, `x402`, `networks`, `erc20`, `erc8004` (agent identity), `erc8183` (commerce). Provides X402Signer / SigningPolicy / EVMWalletProvider.
- **BSC testnet** RPC live (chainId 0x61=97). **CMC** key not set.

## Blocked-on-user (credential signups only — exact commands provided)
1. CMC API key — sign up coinmarketcap.com/api (free Basic tier ok for build). Set `CMC_API_KEY`.
2. TWAK creds + agent wallet — run `npx twak setup` (interactive: credentials + wallet create). Produces the agent address we register + sign with.

## Architecture
Python orchestrator (the brain) calls:
- **Data:** CMC REST/MCP (signals) + TWAK `price/trending/risk` (BSC-native quotes). x402-metered.
- **Decide:** strategy module → proposed trade (token pair + notional + side).
- **Guard:** guardrail engine vets the proposed trade (PURE LOGIC, no deps) → allow/refuse + reason. Circuit breaker on drawdown.
- **Execute:** execution adapter → TWAK `swap` (real, self-custody local signing) on BSC. Dry-run mode when creds absent.
- **Pay:** bnbagent X402Signer gates per-call data payments (session + per-call caps).

Clean adapter boundary so no single tool is hard-coupled; TWAK is the load-bearing execution + signing surface (5/5 special target).

## Phase 1 Gate — two halves
(a) Guardrail refuses a deliberately over-cap trade with a logged reason. → **buildable + testable NOW (pure logic).**
(b) A real TWAK-signed trade lands an on-chain tx, no custodial step. → code now, runs when TWAK creds + funds arrive.
   - Open question to confirm: TWAK BSC = mainnet only? If testnet unsupported, prove signing via `wallet sign-message` (no funds, any chain) + a tiny hard-capped mainnet `swap`; or a true testnet tx via bnbagent EVMWalletProvider. Decide after `twak chains`/swap probe with creds.

## Build order (this session)
1. Guardrail engine + config + eligible-token allowlist + pytest suite → RUN tests. ✅ provable today.
2. CMC client (one signal) — code; runs when key set.
3. Execution adapter (TWAK swap wrapper + dry-run).
4. Orchestrator loop wiring read→decide→guard→execute.
5. Hand user the 2 exact credential commands; then run (b) live.

## Risk caps (defaults — tighter than the 30% DQ line on purpose)
- max_drawdown_halt = 15% from peak (circuit breaker; DQ line is 30%, we halt well before).
- per_trade_cap = 10% of equity; daily_cap = 40% of equity turnover.
- max_position = 35% in any one non-stable token.
- dust_floor = keep equity > $5 (the contest scores any hour starting ≤ $1 as 0%).
- slippage_max = 100 bps; off-allowlist token = hard refuse (won't count + wastes gas).
- Capital cap for live week = explicit user decision before mainnet (REAL money).
