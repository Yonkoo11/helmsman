# Contributing to Helmsman

Thanks for your interest. This is a self-custody trading agent that moves real
funds, so contributions are held to a careful bar.

## Ground rules
- **Never commit secrets.** Keys live in the OS keychain (TWAK) and `.env`
  (gitignored). No private keys, passwords, or API keys in code, argv, logs, or
  commits. See `SECURITY.md`.
- **Every safety change needs a test.** The guardrail engine, risk state, and
  execution path are covered by `tests/`; keep them green (`pytest`).
- **No silent failure.** Errors that should stop trading must stop it, not be
  swallowed. Be explicit about confirmed vs. pending vs. failed states.

## Dev setup
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
npm install
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
```

## Before a PR
1. `pytest` passes.
2. New money-path logic has tests, including the failure cases.
3. Run the live read (`python -m agent.orchestrator`), it must not spend.
4. Describe what you changed and how you verified it.

## Good first areas
- Additional CMC regime factors (funding/derivatives on a higher tier).
- A bounded Permit2 approval path / gasless eip3009 payment token support.
- Equity cross-check against CMC prices.
- A longer backtest data source (beyond the Fear & Greed history window).
