## SECURITY — KEYS NEVER IN REPO OR CONTEXT (BLOCKING)

The deployer + operator + RPC keys live ONLY in `~/.zshenv`. Hard rules:

- **NEVER read `~/.zshenv`, `~/.zshrc`, `~/.zprofile`, `~/.bashrc`, `~/.bash_profile`, `~/.netrc`, `~/.npmrc`, `~/.git-credentials`, SSH keys, `*.key`, `*.pem`, or any `keystore/*` file.** Not `Read`, not `cat`, not `head`, not `grep -v`. Project + global hooks block these.
- **NEVER print, echo, or log key values.** `echo $KEY`, `print(os.getenv("KEY"))`, `console.log(process.env.KEY)` are banned.
- **NEVER commit `.env*`, `*.key`, `*.pem`, `keystore/`, `secrets/`** — covered by `.gitignore`. Verify `git diff --cached` before every save point.
- **NEVER use `git add -A` for the first save point.** Add by explicit file name.
- **Python agent uses `os.getenv("OPERATOR_PRIVATE_KEY")`.** Never `dotenv.load_dotenv("~/.zshenv")`. Never shell out to echo env vars.
- **TWAK holds the signing keys locally — the agent NEVER sees raw private keys.** All signing goes through TWAK local self-custody. This is both the security model AND the product thesis.
- **Check var presence without value:** `[ -n "$VARNAME" ] && echo "set"`.
- **If a key ever surfaces, STOP. Tell the user to rotate. Do not paginate the value back into context.**

Full playbook: `SECURITY.md`. Read it before any deploy or signing work.

---

## Vibecoder Mode

### Communication Rules
- Never say: branch, commit, merge, PR, push, pull, diff, npm, deploy, env var. Say: version, save point, combine changes, publish, update, install.
- Never show raw terminal output or error messages. Summarize in one sentence; describe changes by what the user SEES.

### Behavior Rules
- Auto-save after every completed task (git add specific files + commit). Never ask.
- Fix failing tests silently. Update `ai/progress.md` with a "What Changed (Plain English)" section after each task.
- Keep explanations to 1-3 sentences.

---

## Project: Helmsman — Self-Custody Autonomous Trading Agent (BNB Hack)

**Pitch:** Self-custody trader, unattended-safe.

**What it is:** an autonomous BSC trading agent whose differentiator is a hard risk-governance layer + verifiable self-custody. It reads CoinMarketCap signals, decides an allocation across eligible BEP-20 tokens, and signs + submits every trade locally through the Trust Wallet Agent Kit (TWAK) — paying for data/inference per-call via x402. A drawdown circuit-breaker + per-trade/daily caps + token allowlist + slippage bound can halt it. "Most profit without blowing up."

**Hackathon:** BNB Hack: AI Trading Agent Edition (CoinMarketCap × Trust Wallet × BNB Chain).
**Tracks entered:** Track 1 (Autonomous Trading Agents, $24K) + all 3 special prizes ($2K each). Track 2 (Strategy Skill, $6K) as a reuse double-dip if the engine permits.
**Competition contract (BSC):** 0x212c61b9b72c95d95bf29cf032f5e5635629aed5
**Register via:** `twak compete register` or MCP `competition_register` — BEFORE the trading window opens (raw date in ai/memory.md).

## Phase 1 Gate (MUST PASS BEFORE ANY OTHER WORK)
Core Action: agent reads one live CMC signal, decides a trade, and signs + submits it on BSC **testnet** through TWAK local signing, with the drawdown breaker blocking any trade that would exceed the cap — end to end, no custodial step.
Success Test: a single command runs the loop once; a real BSC testnet tx hash is produced by TWAK-signed execution; a deliberately over-cap trade is refused by the guardrail with a logged reason.
Min Tech: CMC Agent Hub (1 signal via MCP/x402), TWAK local signing on BSC testnet, BNB SDK X402Signer for the data payment.
NOT Phase 1: multi-signal regime model, personality/chat, copy-trading, mainnet, dashboard, Track 2 Skill, visual polish.

## Build Order (NEVER skip)
1. Core action (TWAK-signed trade on testnet + guardrail refusal) → 2. Data flows (real CMC signals, x402 payments) → 3. Product complete (regime logic, guardrail suite, on-chain registration, mainnet) → 4. Visual polish (`/design helmsman`) + demo (`/demo-video`).

## Sponsor Depth Targets (load-bearing or it doesn't count)
- **TWAK (Best Use of TWAK special):** target 5/5 — sole execution layer, signing + autonomous mode + x402, full self-custody trade loop, on-chain register.
- **CMC Agent Hub (Best Use of Agent Hub special):** target 5/5 — funding rates + Fear&Greed + derivatives positioning + pre-computed RSI/MACD, consumed via MCP and paid per-call via x402.
- **BNB AI Agent SDK (Best Use of SDK special):** target 4/5 — X402Signer + SigningPolicy gate every payment; runs on BSC; optionally publish trade-decision attestations via ERC-8183.

Detail + acceptance tests: `ai/sponsor-integration.md`.

## Research base
`~/Projects/IDEAS-SUMMARY.md` (#4 reliability oracle — x402 data-trust gate), winners bank `~/Projects/hackathon-winners/` (A5 Latinum/MCPay, B7 agentic).
