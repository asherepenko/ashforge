#!/usr/bin/env bash
# Pre-flight context for the aet-status skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to short-circuit Step 1 (Read State File) and Step 6
# (Feature History) — the JSON, handoff dirs, and recent pipeline commits
# are already in scope.
set -uo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

(
  echo "== State file =="
  cat .artifacts/aet/state.json 2>/dev/null || echo "NO_STATE_FILE"
) > "$tmp/01" 2>&1 &

(
  echo "== Handoff directories =="
  ls -1 .artifacts/aet/handoffs/ 2>/dev/null || echo "NO_HANDOFFS"
) > "$tmp/02" 2>&1 &

(
  echo "== Recent pipeline commits =="
  git log --oneline -20 --grep='^aet:' 2>/dev/null || echo "NO_COMMITS"
) > "$tmp/03" 2>&1 &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) > "$tmp/04" 2>&1 &

(
  echo "== Latest handoff artifact (mtime) =="
  if [ -d .artifacts/aet/handoffs ]; then
    # GNU vs BSD stat: probe once (`stat -c` fails silently on BSD, works on
    # GNU). A plain `stat -f || stat -c` fallback won't do — GNU `stat -f`
    # exits 1 but still dumps filesystem info to stdout first.
    if stat -c '%Y' . > /dev/null 2>&1; then
      stat_mtime() { stat -c '%Y %n' "$1" 2>/dev/null; }
    else
      stat_mtime() { stat -f '%m %N' "$1" 2>/dev/null; }
    fi
    find .artifacts/aet/handoffs -name '*.md' -type f 2>/dev/null \
      | while IFS= read -r f; do stat_mtime "$f"; done \
      | sort -rn | head -5
  else
    echo "NO_HANDOFFS"
  fi
) > "$tmp/05" 2>&1 &

wait
cat "$tmp"/*
