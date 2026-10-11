#!/usr/bin/env bash
# Pre-flight context for the aet-pipeline skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to skip the project-discovery phase and pass values to
# dispatched agents (architect, gradle-build-engineer) so they don't re-scan.
set -uo pipefail

# Configuration is a hint: only the orchestrator can inspect exposed tools.
codex_spawn_hint() {
  local cfg="$1" enabled="true"
  if [ -f "$cfg" ]; then
    enabled="$(awk '
      /^[[:space:]]*\[/ {
        section = $0; sub(/[[:space:]]*#.*/, "", section)
        gsub(/[[:space:]]/, "", section); next
      }
      section == "[agents]" && /^[[:space:]]*enabled[[:space:]]*=/ {
        value = $0; sub(/^[^=]*=[[:space:]]*/, "", value)
        sub(/[[:space:]]*#.*/, "", value); gsub(/[[:space:]]/, "", value)
        if (value == "true" || value == "false") modern = value
      }
      section == "[features]" && /^[[:space:]]*multi_agent[[:space:]]*=/ {
        value = $0; sub(/^[^=]*=[[:space:]]*/, "", value)
        sub(/[[:space:]]*#.*/, "", value); gsub(/[[:space:]]/, "", value)
        if (value == "true" || value == "false") legacy = value
      }
      END { print (modern != "" ? modern : (legacy != "" ? legacy : "true")) }
    ' "$cfg")"
  fi
  if [ "$enabled" = "false" ]; then spawn="none"; else spawn="prompt-embed"; fi
  notes="config hint only (agents.enabled defaults true; legacy features.multi_agent supported); actual exposed tools override SPAWN"
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

(
  echo "== Settings file =="
  if [ -f settings.gradle.kts ]; then
    head -60 settings.gradle.kts
  elif [ -f settings.gradle ]; then
    head -60 settings.gradle
  else
    echo "NO_SETTINGS_GRADLE"
  fi
) > "$tmp/01" 2>&1 &

(
  echo "== Module count =="
  find . -maxdepth 4 -name 'build.gradle.kts' \
    -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null \
    | wc -l | tr -d ' '
) > "$tmp/02" 2>&1 &

(
  echo "== Top-level modules =="
  find . -maxdepth 3 -name 'build.gradle.kts' \
    -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null \
    | head -30
) > "$tmp/03" 2>&1 &

(
  echo "== Existing pipeline state =="
  if [ -f .artifacts/aet/state.json ]; then
    head -40 .artifacts/aet/state.json
  else
    echo "NO_ACTIVE_PIPELINE"
  fi
) > "$tmp/04" 2>&1 &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) > "$tmp/05" 2>&1 &

(
  echo "== Per-project settings =="
  if [ -f android-expert-toolkit.local.md ]; then
    head -40 android-expert-toolkit.local.md
  else
    echo "NO_LOCAL_SETTINGS"
  fi
) > "$tmp/06" 2>&1 &

(
  echo "== Runtime capability =="
  # Definitive env markers of the RUNNING runtime first; install-dir
  # heuristics (~/.codex etc.) only when nothing else matched — a directory
  # proves installation, not the current runtime.
  runtime="unknown"; spawn="unknown"; transport="unknown"; notes=""
  if [ -n "${CODEX_HOME:-}" ]; then
    runtime="codex"; transport="hub"
    cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
    codex_spawn_hint "$cfg"
  elif [ -n "${ZCODE_APP_VERSION:-}" ]; then
    runtime="zcode"; spawn="registry"; transport="hub"
    notes="result-returning Agent spawns; TaskCreate -> TodoWrite"
  elif [ -n "${CLAUDECODE:-}" ] || [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    runtime="claude-code"; spawn="registry"; transport="hub"
    notes="named Agent launches may report via teammate idle notifications when teams enabled; wait for final answer and validate artifact"
  elif [ -d "$HOME/.antigravity" ]; then
    runtime="antigravity"; transport="hub"
    notes="spawn hint unknown — discover actual exposed tools and inspect their schemas (references/runtime-adapters.md)"
  elif [ -d "$HOME/.pi" ]; then
    runtime="pi"; spawn="none"; transport="hub"
    notes="spawn hint none — discover actual exposed tools/extensions before selecting fallback"
  elif [ -d "$HOME/.codex" ]; then
    runtime="codex"; transport="hub"
    cfg="$HOME/.codex/config.toml"
    codex_spawn_hint "$cfg"
  fi
  echo "RUNTIME=$runtime"
  echo "SPAWN=$spawn"
  echo "TRANSPORT=$transport"
  echo "NOTES=${notes:-none}"
) > "$tmp/07" 2>&1 &

wait
cat "$tmp"/*
