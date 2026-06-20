# Deploying Helmsman for the live week (Jun 22–28)

The agent runs **one safe cycle per fire** (lock → reconcile pending → strategy →
daily-qualify → save). A scheduler fires it hourly. The single-instance lock makes
overlapping fires safe.

## Option A — this Mac (simplest; keychain already set up here)
The TWAK wallet lives in this machine's **OS keychain**, so the agent signs here
with no extra setup.

1. Install the hourly scheduler:
   ```
   cp deploy/com.helmsman.agent.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.helmsman.agent.plist
   ```
2. **Keep the Mac awake for the whole window** (otherwise cycles are missed):
   ```
   nohup deploy/keepawake.sh >/dev/null 2>&1 &
   ```
   Leave the Mac on AC power, lid open or clamshell with external power.
3. Watch the heartbeat:
   ```
   tail -f runtime/agent.log
   ```
   Each cycle stamps `=== cycle <UTC time> ===`. The daily-qualify net forces a
   trade by **12:00 UTC** if the strategy hasn't traded that day, so even a few
   awake hours mid-day keep you ranked.

### Single point of failure
If this Mac is fully off/asleep across the **entire** UTC day, no trade lands and
you risk a daily disqualification. Mitigations: keepawake.sh + AC power, and check
`runtime/agent.log` daily.

## Option B — cloud host (most robust, more setup)
A small always-on Linux VM removes the sleep risk. **Caveat:** TWAK stores keys in
the macOS keychain; on Linux it uses a different keyring, so you must run
`npx twak setup` **on the VM** to create a wallet there, fund it, and
`twak compete register` that wallet (or import — TWAK had no import at time of
writing, so it'd be a fresh agent wallet). Then deploy this repo + a cron entry:
```
7 * * * * cd /opt/helmsman && bash deploy/run_agent.sh
```
This is more work and re-funds a new wallet; only do it if Option A's uptime worries you.

## Verify before the window opens
```
npx twak compete status            # registered: true
PYTHONPATH=. .venv/bin/python -m agent.orchestrator   # live read, no spend
```
