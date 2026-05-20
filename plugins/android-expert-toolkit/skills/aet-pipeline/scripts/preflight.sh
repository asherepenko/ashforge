#!/usr/bin/env bash
# Pre-flight context for the aet-pipeline skill.
# Output is labeled with `== section ==` headers. All probes parallelize.
# Use the output to skip the project-discovery phase and pass values to
# dispatched agents (architect, gradle-build-engineer) so they don't re-scan.
set -uo pipefail

(
  echo "== Settings file =="
  if [ -f settings.gradle.kts ]; then
    head -60 settings.gradle.kts
  elif [ -f settings.gradle ]; then
    head -60 settings.gradle
  else
    echo "NO_SETTINGS_GRADLE"
  fi
) &

(
  echo "== Module count =="
  find . -maxdepth 4 -name 'build.gradle.kts' \
    -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null \
    | wc -l | tr -d ' '
) &

(
  echo "== Top-level modules =="
  find . -maxdepth 3 -name 'build.gradle.kts' \
    -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null \
    | head -30
) &

(
  echo "== Existing pipeline state =="
  if [ -f .artifacts/aet/state.json ]; then
    head -40 .artifacts/aet/state.json
  else
    echo "NO_ACTIVE_PIPELINE"
  fi
) &

(
  echo "== Active branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) &

(
  echo "== Per-project settings =="
  if [ -f android-expert-toolkit.local.md ]; then
    head -40 android-expert-toolkit.local.md
  else
    echo "NO_LOCAL_SETTINGS"
  fi
) &

wait
