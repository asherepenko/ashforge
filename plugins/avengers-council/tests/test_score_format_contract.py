"""Guard: the Round 1 table checks the Verdict word before printing it.

Regression: a council code review printed `B` in the Round 1 Score column
because nothing checked the format before the table. The Score cell is now
script output (scripts/domain-score.py); only the Verdict is gated.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORCH = (ROOT / "references/orchestration-protocol.md").read_text()
DEBATE = (ROOT / "references/debate-protocol.md").read_text()


def gate():
    return ORCH.split("**Format gate (before the table).**", 1)[1].split("\n\n", 1)[0]


def test_round1_table_has_verdict_format_gate():
    assert "**Format gate (before the table).**" in ORCH
    text = gate()
    assert "APPROVE, CONCERNS or REJECT" in text
    assert "n/a ⚠" in text
    assert "Never copy an invalid value into the table." in text


def test_format_gate_no_longer_checks_a_score():
    text = gate()
    assert "^([1-9]|10)/10$" not in text
    assert "Score flag" not in text
    assert "DOMAIN SCORE" not in text


def test_member_prompts_ask_for_no_score():
    assert "Do not send a score" in ORCH
    assert "Do not send a score" in DEBATE
    assert "never a letter grade" not in ORCH


def test_round1_score_cell_is_script_output():
    assert "Fill Score by running `domain-score.py`" in ORCH
