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
  codex_profile() {
    runtime="codex"; transport="hub"; spawn="prompt-embed"
    cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
    # Modern agents.enabled defaults true. Config is only a hint: exposed
    # spawn tools and session restrictions are authoritative in the skill.
    if [ -f "$cfg" ] && awk '
      /^\[agents\]/ { section="agents"; next }
      /^\[features\]/ { section="features"; next }
      /^\[/ { section="" }
      section == "agents" && /^[[:space:]]*enabled[[:space:]]*=/ { modern=$0 }
      section == "features" && /^[[:space:]]*multi_agent[[:space:]]*=/ { legacy=$0 }
      END { selected=(modern != "" ? modern : legacy); exit !(selected ~ /=[[:space:]]*false([[:space:]]|$)/) }
    ' "$cfg"; then spawn="none"; fi
    notes="config hint only; discover actual spawn/continuation tools before dispatch; agents.enabled defaults true, features.multi_agent is legacy"
  }
  if [ -n "${ZCODE_APP_VERSION:-}" ]; then
    runtime="zcode"; spawn="registry"; transport="hub"
    notes="result-returning Agent spawns; SendMessage resume available; TaskCreate -> TodoWrite"
  elif [ -n "${CLAUDECODE:-}" ] || [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    runtime="claude-code"; spawn="registry"; transport="hub"
    notes="ordinary subagents; only select stay-alive after verifying interactive session and enabled agent teams; main is ordinary-subagent lead"
    if [ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-0}" = "1" ] && [ "${AVENGERS_COUNCIL_INTERACTIVE:-0}" = "1" ]; then
      transport="stay-alive"
      notes="interactive hint supplied by orchestrator; confirm actual teammate launch before using team-lead"
    fi
  elif [ -n "${CODEX_HOME:-}" ]; then
    codex_profile
  elif [ -d "$HOME/.antigravity" ]; then
    runtime="antigravity"; transport="hub"
    notes="discover actual spawn tools before dispatch"
  elif [ -d "$HOME/.pi" ]; then
    runtime="pi"; spawn="none"; transport="hub"
    notes="no native subagent tool; discover installed subagent extension before dispatch"
  elif [ -d "$HOME/.codex" ]; then
    codex_profile
  fi
  echo "RUNTIME=$runtime"
  echo "SPAWN=$spawn"
  echo "TRANSPORT=$transport"
  echo "NOTES=${notes:-none}"
) > "$tmp/08" 2>&1 &

wait
cat "$tmp"/*
