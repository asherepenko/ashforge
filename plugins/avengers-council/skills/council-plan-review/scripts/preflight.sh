#!/usr/bin/env bash
# Pre-flight context for the council-plan-review skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to short-circuit Step 1 plan auto-detection and to surface
# domain artifacts (DOMAIN.md / docs/adr/) that feed every reviewer's brief.
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
  for f in DOMAIN-MAP.md DOMAIN.md CONTEXT-MAP.md CONTEXT.md; do
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
) > "$tmp/08" 2>&1 &

wait
cat "$tmp"/*
