#!/usr/bin/env bash
# Pre-flight context for the council-plan-review skill.
# Output is labeled with `== section ==` headers. All probes parallelize.
# Use the output to short-circuit Step 1 plan auto-detection and to surface
# domain artifacts (CONTEXT.md / docs/adr/) that feed every reviewer's brief.
set -uo pipefail

(
  echo "== Local plans dir =="
  ls -1t .claude/plans/*.md 2>/dev/null | head -10 || echo "NO_LOCAL_PLANS"
) &

(
  echo "== Global plans dir =="
  ls -1t "$HOME/.claude/plans"/*.md 2>/dev/null | head -10 || echo "NO_GLOBAL_PLANS"
) &

(
  echo "== Artifact specs (PRDs) =="
  ls -1t .artifacts/specs/prd-*.md 2>/dev/null | head -5 || echo "NO_PRDS"
) &

(
  echo "== Recent reviews =="
  ls -1t .artifacts/reviews/*.md 2>/dev/null | head -5 || echo "NO_REVIEWS"
) &

(
  echo "== Domain glossary =="
  for f in CONTEXT-MAP.md CONTEXT.md; do
    if [ -f "$f" ]; then
      echo "$f"
      exit 0
    fi
  done
  echo "NONE"
) &

(
  echo "== ADRs (most recent 20) =="
  ls -1t docs/adr/*.md 2>/dev/null | head -20 || echo "NONE"
) &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) &

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
) &

wait
