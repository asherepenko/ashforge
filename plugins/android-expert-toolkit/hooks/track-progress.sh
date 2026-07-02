#!/usr/bin/env bash
# Cost guard for track-progress.py.
# PostToolUse fires on every Write/Edit/Bash in every project; spawning
# python3 each time is wasteful. No-op fast unless an AET pipeline is
# active (.artifacts/aet exists at cwd — the pipeline always runs from
# the project root). The hook payload arrives on stdin and must reach
# the python script unchanged when we proceed, so stdin is consumed on
# no-op and passed through untouched (via exec) otherwise.

if [ ! -d .artifacts/aet ]; then
  cat > /dev/null 2>&1
  exit 0
fi

if ! command -v python3 > /dev/null 2>&1; then
  cat > /dev/null 2>&1
  exit 0
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$script_dir/track-progress.py"
