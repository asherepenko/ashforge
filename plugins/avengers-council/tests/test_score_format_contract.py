"""Guard: a member's Round-1 score must be N/10, never a letter grade.

Regression: a council code review printed `B` in the Round 1 Score column
because nothing checked the format before the table.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORCH = (ROOT / "references/orchestration-protocol.md").read_text()
DEBATE = (ROOT / "references/debate-protocol.md").read_text()


def test_round1_table_has_format_gate():
    assert "**Format gate (before the table).**" in ORCH
    assert "^([1-9]|10)/10$" in ORCH
    assert "n/a ⚠" in ORCH
    assert "Never copy an invalid value into the table." in ORCH


def test_member_prompts_forbid_letter_grades():
    assert "never a letter grade" in ORCH
    assert "Never a letter grade such as B" in DEBATE
