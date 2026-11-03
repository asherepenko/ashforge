#!/usr/bin/env python3
"""Avengers Council — ExitPlanMode hook (Claude Code only).

Suggests or auto-invokes the council-plan-review skill when exiting plan mode.

Controlled by the AVENGERS_COUNCIL_ON_PLAN env var:
  off     (default) — do nothing
  prompt  — suggest invoking the council-plan-review skill
  auto    — instruct Claude to invoke the council-plan-review skill before proceeding
"""
import os
import sys

PROMPT_OUTPUT = """{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The Avengers Council plugin is active. Consider invoking the `council-plan-review` skill (via the Skill tool) to get a multi-expert engineering advisory review of this plan before proceeding."
  }
}
"""


def main():
    mode = os.environ.get("AVENGERS_COUNCIL_ON_PLAN", "off")
    if mode == "off":
        return 0
    if mode == "prompt":
        sys.stdout.write(PROMPT_OUTPUT)
        return 0
    if mode == "auto":
        approval = os.path.join(os.path.dirname(os.path.abspath(__file__)), "council-plan-approval.py")
        sys.stdout.flush()
        os.execvp("python3", ["python3", approval, "check"])
    print(f"Warning: Unknown AVENGERS_COUNCIL_ON_PLAN value: {mode} (expected: off, prompt, auto)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
