from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIELD = (
    "CONCERN FOR THE USER (optional): [a risk the change knowingly takes on, "
    "or a judgment call for the user — not a finding]"
)
RULE = "A concern that meets a severity definition or a red line is a finding, not a concern."


def read(rel):
    return (ROOT / rel).read_text()


def test_round_3_format_has_optional_concern_field():
    debate = read("references/debate-protocol.md")
    round3 = debate.split("### Round 3", 1)[1].split("## Domain Scoring", 1)[0]
    assert FIELD in round3
    assert round3.index(FIELD) > round3.index("KEY CONDITION:")


def test_template_section_follows_conditions_for_approval():
    template = read("assets/verdict-template.md")
    assert "## Concerns for the User" in template
    headings = [l for l in template.splitlines() if l.startswith("## ")]
    i = headings.index("## Concerns for the User")
    assert headings[i - 1] == "## Conditions for Approval"
    assert headings[i + 1] == "## Pre-existing"
    section = template.split("## Concerns for the User", 1)[1].split("\n## ", 1)[0]
    assert "Include this section ONLY when a member raised a concern." in section
    for phrase in ("advisory", "never a condition", "not counted in quality", "never changes the verdict"):
        assert phrase in section.lower()


def test_classification_rule_in_phase_4_and_captain():
    protocol = read("references/orchestration-protocol.md")
    phase4 = protocol.split("## Phase 4", 1)[1].split("## Phase 5", 1)[0]
    assert RULE in phase4
    assert RULE in read("references/captain-america-orchestrator.md")


def test_save_as_todos_skips_concerns_unless_asked():
    actions = read("references/post-verdict-actions.md")
    todos = actions.split('### "Save as TODOs"', 1)[1].split("###", 1)[0]
    assert "Concerns for the User" in todos
    assert "unless the user asks" in todos


def test_both_skills_collect_concerns_in_synthesis():
    for skill in ("council-plan-review", "council-code-review"):
        text = read(f"skills/{skill}/SKILL.md")
        synth = text.split("**Verdict synthesis additions:**", 1)[1]
        assert "Concerns for the User" in synth
        assert "CONCERN FOR THE USER" in synth


def test_skills_docs_mirror_template_section():
    docs = read("docs/skills.md")
    assert "## Concerns for the User" in docs
    assert docs.index("## Concerns for the User") > docs.index("## Conditions for Approval")
