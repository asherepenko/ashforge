#!/usr/bin/env bash
# Avengers Council — ExitPlanMode hook
# Suggests or auto-invokes /avengers-council:plan-review when exiting plan mode.
#
# Controlled by AVENGERS_COUNCIL_ON_PLAN env var:
#   off     (default) — do nothing
#   prompt  — suggest running /avengers-council:plan-review
#   auto    — instruct Claude to invoke /avengers-council:plan-review before proceeding

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
    "additionalContext": "The Avengers Council plugin is active. Consider running `/avengers-council:plan-review` to get a multi-expert engineering advisory review of this plan before proceeding."
  }
}
EOF
    ;;
  auto)
    cat <<'EOF'
{
  "decision": "block",
  "reason": "Council review required before proceeding. Run /avengers-council:plan-review first.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The Avengers Council plugin is active with auto-review enabled. BEFORE proceeding with this plan, invoke `/avengers-council:plan-review` to get the council's verdict on this plan. Do not continue until the council review is complete."
  }
}
EOF
    ;;
  *)
    echo "Warning: Unknown AVENGERS_COUNCIL_ON_PLAN value: $MODE (expected: off, prompt, auto)" >&2
    exit 0
    ;;
esac
