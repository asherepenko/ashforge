#!/usr/bin/env bash
# Avengers Council — ExitPlanMode hook (Claude Code only)
# Suggests or auto-invokes the council-plan-review skill when exiting plan mode.
#
# Controlled by AVENGERS_COUNCIL_ON_PLAN env var:
#   off     (default) — do nothing
#   prompt  — suggest invoking the council-plan-review skill
#   auto    — instruct Claude to invoke the council-plan-review skill before proceeding

set -euo pipefail

MODE="${AVENGERS_COUNCIL_ON_PLAN:-off}"

case "$MODE" in
  off)
    exit 0
    ;;
  prompt)
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The Avengers Council plugin is active. Consider invoking the `council-plan-review` skill (via the Skill tool) to get a multi-expert engineering advisory review of this plan before proceeding."
  }
}
EOF
    ;;
  auto)
    cat <<'EOF'
{
  "decision": "block",
  "reason": "Council review required before proceeding. Invoke the council-plan-review skill first (Skill tool with skill=council-plan-review).",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The Avengers Council plugin is active with auto-review enabled. BEFORE proceeding with this plan, invoke the `council-plan-review` skill (via the Skill tool) to get the council's verdict on this plan. Do not continue until the council review is complete."
  }
}
EOF
    ;;
  *)
    echo "Warning: Unknown AVENGERS_COUNCIL_ON_PLAN value: $MODE (expected: off, prompt, auto)" >&2
    exit 0
    ;;
esac
