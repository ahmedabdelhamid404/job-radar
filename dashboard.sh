#!/usr/bin/env bash
# Opens the Job Radar dashboard, starting the local server first if needed.
cd "$(dirname "$0")"
if ! curl -s -o /dev/null "http://127.0.0.1:5000/"; then
  nohup /usr/bin/python3 dashboard.py >> dashboard.log 2>&1 &
  for i in $(seq 1 10); do
    curl -s -o /dev/null "http://127.0.0.1:5000/" && break
    sleep 0.5
  done
fi
xdg-open "http://127.0.0.1:5000/" >/dev/null 2>&1 &
