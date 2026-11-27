"""The council's orchestrator must be the session the user talks to.

A council run handed to a subagent spawns its members, then ends its turn to
wait for them. A subagent's turn ending returns it to its caller, so the run
hands back with no round tables and no verdict. These checks keep the rule,
and the no-partial-verdict rule, in every council skill and the protocol.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ["council-advise", "council-code-review", "council-plan-review"]
PROTOCOL = ROOT / "references" / "orchestration-protocol.md"

MAIN_SESSION_MARKER = "<main-session-only>"
NOT_RUN_LINE = "COUNCIL NOT RUN"
NO_VERDICT_LINE = "NO VERDICT"


def read(path: Path) -> str:
    return path.read_text()


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_requires_main_session(skill):
    text = read(ROOT / "skills" / skill / "SKILL.md")
    assert MAIN_SESSION_MARKER in text
    assert NOT_RUN_LINE in text
    assert "references/orchestration-protocol.md#main-session-only" in text


def test_protocol_defines_main_session_rule():
    text = read(PROTOCOL)
    assert "## Main session only" in text
    assert NOT_RUN_LINE in text
    assert "never delegate" in text.lower()


def test_protocol_forbids_partial_verdict():
    text = read(PROTOCOL)
    assert NO_VERDICT_LINE in text
    assert "before `verdict.py`" in text
