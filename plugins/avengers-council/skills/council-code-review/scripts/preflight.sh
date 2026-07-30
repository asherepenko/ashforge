#!/usr/bin/env bash
# Pre-flight context for the council-code-review skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to bound review scope before Step 1 — if working tree is
# clean and no commits ahead, there is no `--diff` to review.
set -uo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

resolve_base() {
  git merge-base HEAD origin/main 2>/dev/null \
    || git merge-base HEAD main 2>/dev/null \
    || git merge-base HEAD master 2>/dev/null \
    || echo ""
}

(
  echo "== Current branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) > "$tmp/01" 2>&1 &

(
  echo "== Working tree status =="
  git status -s 2>/dev/null | head -40 || echo "NO_REPO"
) > "$tmp/02" 2>&1 &

(
  echo "== Diff stat (vs base) =="
  BASE="$(resolve_base)"
  if [ -z "$BASE" ]; then
    echo "NO_BASE"
  else
    git diff --stat "$BASE"...HEAD 2>/dev/null | tail -30
  fi
) > "$tmp/03" 2>&1 &

(
  echo "== Commits ahead =="
  BASE="$(resolve_base)"
  if [ -z "$BASE" ]; then
    echo "NONE"
  else
    git log --oneline "$BASE"..HEAD 2>/dev/null | head -20
  fi
) > "$tmp/04" 2>&1 &

(
  echo "== Project markers =="
  ls build.gradle.kts package.json pyproject.toml go.mod Cargo.toml settings.gradle.kts 2>/dev/null \
    || echo "NO_MARKERS"
) > "$tmp/05" 2>&1 &

(
  echo "== Recent reviews =="
  ls -1t .artifacts/reviews/*.md 2>/dev/null | head -5 || echo "NO_REVIEWS"
) > "$tmp/06" 2>&1 &

(
  echo "== Codex multi_agent capability =="
  # Skip on Claude — Agent spawning is not gated by a feature flag
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
) > "$tmp/07" 2>&1 &

wait
cat "$tmp"/*
