#!/bin/bash
# Keep this Mac awake for the live competition week so the hourly launchd agent
# actually fires. Run in a terminal (or `nohup ... &`) for the trading window:
#   deploy/keepawake.sh
# -d prevent display sleep, -i prevent idle sleep, -m prevent disk sleep,
# -s prevent system sleep while on AC power. Ctrl-C to stop.
exec caffeinate -dims
