#!/usr/bin/env bash
# Pre-flight context for the council-plan-review skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to short-circuit Step 1 plan auto-detection and to surface
# domain artifacts (CONTEXT.md / docs/adr/) that feed every reviewer's brief.
set -uo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

(
  echo "== Local plans dir =="
  ls -1t .claude/plans/*.md 2>/dev/null | head -10 || echo "NO_LOCAL_PLANS"
) > "$tmp/01" 2>&1 &

(
  echo "== Global plans dir =="
  ls -1t "$HOME/.claude/plans"/*.md 2>/dev/null | head -10 || echo "NO_GLOBAL_PLANS"
) > "$tmp/02" 2>&1 &

(
  echo "== Artifact specs (PRDs) =="
  ls -1t .artifacts/specs/prd-*.md 2>/dev/null | head -5 || echo "NO_PRDS"
) > "$tmp/03" 2>&1 &

(
  echo "== Recent reviews =="
  ls -1t .artifacts/reviews/*.md 2>/dev/null | head -5 || echo "NO_REVIEWS"
) > "$tmp/04" 2>&1 &

(
  echo "== Domain glossary =="
  for f in CONTEXT-MAP.md CONTEXT.md; do
    if [ -f "$f" ]; then
      echo "$f"
      exit 0
    fi
  done
  echo "NONE"
) > "$tmp/05" 2>&1 &

(
  echo "== ADRs (most recent 20) =="
  ls -1t docs/adr/*.md 2>/dev/null | head -20 || echo "NONE"
) > "$tmp/06" 2>&1 &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) > "$tmp/07" 2>&1 &

(
  echo "== Codex multi_agent capability =="
  # Skip on Claude — TeamCreate/Agent are not gated by a feature flag
  if [ -z "${CODEX_HOME:-}" ] && [ ! -d "$HOME/.codex" ]; then
    echo "NOT_CODEX"
  elif [ -f "${CODEX_HOME:-$HOME/.codex}/config.toml" ]; then
    if awk '
      /^\[features\]/ { in_features = 1; next }
      /^\[/           { in_features = 0 }
      in_features && /^[[:space:]]*multi_agent[[:space:]]*=[[:space:]]*true/ { found = 1; exit }
      END { exit !found }
    ' "${CODEX_HOME:-$HOME/.codex}/config.toml" 2>/dev/null; then
      echo "ENABLED"
    else
      echo "DISABLED"
    fi
  else
    echo "NO_CONFIG"
  fi
) > "$tmp/08" 2>&1 &

wait
cat "$tmp"/*
