#!/usr/bin/env bash
# Pre-flight context for the aet-status skill.
# Output is labeled with `== section ==` headers. All probes parallelize.
# Use the output to short-circuit Step 1 (Read State File) and Step 6
# (Feature History) — the JSON, handoff dirs, and recent pipeline commits
# are already in scope.
set -uo pipefail

(
  echo "== State file =="
  cat .artifacts/aet/state.json 2>/dev/null || echo "NO_STATE_FILE"
) &

(
  echo "== Handoff directories =="
  ls -1 .artifacts/aet/handoffs/ 2>/dev/null || echo "NO_HANDOFFS"
) &

(
  echo "== Recent pipeline commits =="
  git log --oneline -20 --grep='^aet:' 2>/dev/null || echo "NO_COMMITS"
) &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) &

(
  echo "== Latest handoff artifact (mtime) =="
  if [ -d .artifacts/aet/handoffs ]; then
    find .artifacts/aet/handoffs -name '*.md' -type f 2>/dev/null \
      | xargs -I{} stat -f '%m %N' {} 2>/dev/null \
      | sort -rn | head -5
  else
    echo "NO_HANDOFFS"
  fi
) &

wait
