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
) > "$tmp/07" 2>&1 &

wait
cat "$tmp"/*
