#!/usr/bin/env bash
# Called by cron. Runs one radar scan for the given tier (free|morning|evening|night|all).
# Default "free" = no-cost sources only. Appends to radar.log.
cd "$(dirname "$0")"
/usr/bin/python3 radar.py "${1:-free}" >> radar.log 2>&1
