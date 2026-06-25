#!/usr/bin/env bash
# Called by cron. Runs one radar scan; appends to radar.log.
cd "$(dirname "$0")"
/usr/bin/python3 radar.py >> radar.log 2>&1
