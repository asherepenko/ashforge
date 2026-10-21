#!/usr/bin/env python3
"""Tests that Ant-Man is wired in as the example optional member."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

PHRASE = "8 " + "core"

EIGHT_CORE_COUNTS = {
    "AGENTS.md": 1,
    "README.md": 3,
    "CHANGELOG.md": 1,
    "references/orchestration-protocol.md": 2,
    "references/debate-protocol.md": 1,
    "references/member-registry.md": 1,
    "references/verdict-rules.md": 1,
    ".claude-plugin/plugin.json": 1,
}


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_debate_protocol_score_table_has_ant_man_row():
    protocol = read("references/debate-protocol.md")
    table = protocol.split("## Domain Scoring", 1)[1]
    assert "| Ant-Man (optional) | Reuse & Placement |" in table


def test_orchestration_step_one_names_ant_man_and_registry_rule():
    protocol = read("references/orchestration-protocol.md")
    step = protocol.split("### Step 1: Determine Active Roster", 1)[1].split("5. **Calculate", 1)[0]
    optional = next(line for line in step.splitlines() if "**Optional members**" in line)
    assert "Ant-Man" in optional
    assert "member-registry.md" in optional


def test_verdict_template_shows_ant_man_as_optional_example():
    template = read("assets/verdict-template.md")
    stub = template.split("<!-- If optional members participated", 1)[1].split("<!-- End optional members -->", 1)[0]
    assert "Ant-Man (Reuse & Placement)" in stub
    scores = template.split("## Domain Scores", 1)[1].split("**Average", 1)[0]
    assert "| Ant-Man (optional) | Reuse & Placement |" in scores


def test_skills_doc_mirrors_ant_man_example():
    doc = read("docs/skills.md")
    assert "Ant-Man (optional) | Reuse & Placement" in doc


def test_eight_core_wording_unchanged():
    for path, expected in EIGHT_CORE_COUNTS.items():
        lines = [line for line in read(path).splitlines() if PHRASE in line]
        assert len(lines) == expected, path
