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
  echo "== Runtime capability =="
  runtime="unknown"; spawn="unknown"; transport="unknown"; notes=""
  # Definitive env markers of the RUNNING runtime first; install-dir
  # heuristics (~/.codex etc.) only when nothing else matched — a directory
  # proves installation, not the current runtime.
  if [ -n "${CODEX_HOME:-}" ]; then
    runtime="codex"; transport="hub"
    cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
    if [ -f "$cfg" ] && awk '
      /^\[features\]/ { in_features = 1; next }
      /^\[/           { in_features = 0 }
      in_features && /^[[:space:]]*multi_agent[[:space:]]*=[[:space:]]*true/ { found = 1; exit }
      END { exit !found }
    ' "$cfg" 2>/dev/null; then
      spawn="prompt-embed"
    else
      spawn="none"
      if [ -f "$cfg" ]; then
        notes="multi_agent is off — single-orchestrator fallback (references/runtime-fallback.md)"
      else
        notes="no config.toml — treat multi_agent as off; single-orchestrator fallback (references/runtime-fallback.md)"
      fi
    fi
  elif [ -n "${ZCODE_APP_VERSION:-}" ]; then
    runtime="zcode"; spawn="registry"; transport="hub"
    notes="result-returning Agent spawns; SendMessage resume available; TaskCreate -> TodoWrite"
  elif [ -n "${CLAUDECODE:-}" ] || [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    runtime="claude-code"; spawn="registry"; transport="stay-alive"
  elif [ -d "$HOME/.antigravity" ]; then
    runtime="antigravity"; transport="hub"
    notes="custom subagents exist — confirm spawn shape conversationally (references/runtime-adapters.md)"
  elif [ -d "$HOME/.pi" ]; then
    runtime="pi"; spawn="none"; transport="hub"
    notes="no native subagent tool — SPAWN=none unless a subagent skill/extension is installed; confirm conversationally"
  elif [ -d "$HOME/.codex" ]; then
    runtime="codex"; transport="hub"
    cfg="$HOME/.codex/config.toml"
    if [ -f "$cfg" ] && awk '
      /^\[features\]/ { in_features = 1; next }
      /^\[/           { in_features = 0 }
      in_features && /^[[:space:]]*multi_agent[[:space:]]*=[[:space:]]*true/ { found = 1; exit }
      END { exit !found }
    ' "$cfg" 2>/dev/null; then
      spawn="prompt-embed"
    else
      spawn="none"
      notes="~/.codex heuristic (CODEX_HOME unset); multi_agent off or unconfirmed — single-orchestrator fallback (references/runtime-fallback.md)"
    fi
  fi
  echo "RUNTIME=$runtime"
  echo "SPAWN=$spawn"
  echo "TRANSPORT=$transport"
  echo "NOTES=${notes:-none}"
) > "$tmp/07" 2>&1 &

wait
cat "$tmp"/*
