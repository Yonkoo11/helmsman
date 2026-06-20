#!/bin/bash
# Helmsman autonomous cycle — one safe pass (lock + strategy + daily-qualify).
# Fired by the scheduler (launchd/cron). Logs to runtime/agent.log.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p runtime
PYTHONPATH=. .venv/bin/python -m agent.runner >> runtime/agent.log 2>&1
