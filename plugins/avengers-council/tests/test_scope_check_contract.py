from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = (ROOT / "references" / "orchestration-protocol.md").read_text()
TEMPLATE = (ROOT / "assets" / "verdict-template.md").read_text()
CAPTAIN = (ROOT / "references" / "captain-america-orchestrator.md").read_text()
DOCS = (ROOT / "docs" / "skills.md").read_text()
PLAN = (ROOT / "skills" / "council-plan-review" / "SKILL.md").read_text()
CODE = (ROOT / "skills" / "council-code-review" / "SKILL.md").read_text()

NEW_SECTIONS = [
    "## Scope Check",
    "## Acceptance Criteria Validation",
    "## Standards Compliance",
]
LEGEND = "✅ covered · ⚠️ partial · ❌ missing · ⏸ deferred"
TABLE_HEAD = "| # | Requested item | Covered | Where |"


def test_sections_in_order_after_domain_alignment():
    positions = [TEMPLATE.index(h) for h in ["## Domain Alignment", *NEW_SECTIONS, "## Conditions for Approval"]]
    assert positions == sorted(positions)


def test_no_new_section_between_consensus_and_risk_tier():
    between = TEMPLATE[TEMPLATE.index("## Consensus"):TEMPLATE.index("## Risk Tier")]
    for heading in NEW_SECTIONS:
        assert heading not in between


def test_scope_check_table_and_legend():
    assert TABLE_HEAD in TEMPLATE
    assert LEGEND in TEMPLATE
    assert LEGEND in DOCS
    assert TABLE_HEAD in DOCS


def test_severity_mapping_text():
    for text in ("❌ = one HIGH finding", "⚠️ = one MEDIUM finding", "⏸ = no finding"):
        assert text in TEMPLATE
    assert "Source not readable: <path>" in TEMPLATE
    assert "partial" in TEMPLATE and "defers a source requirement on its own" in TEMPLATE


def test_dedup_sentence():
    sentence = "One underlying gap counts once across Scope Check, AC Validation and member findings; the highest severity wins."
    assert sentence in TEMPLATE
    assert "cites the finding it shares" in TEMPLATE
    assert sentence in PLAN


def test_plan_only_wording():
    assert TEMPLATE.count("Include this section ONLY for plan reviews.") == 2
    assert "Omit it for code reviews" not in TEMPLATE


def test_requested_scope_block_in_spawn_template():
    start = ORCH.index("REQUESTED SCOPE:")
    block = ORCH[start:ORCH.index("REVIEW RULES:", start)]
    assert "Include this block ONLY for plan reviews" in block
    for tag in ("[PRD]", "[source]", "[goal]", "[AC]"):
        assert tag in block
    assert ORCH.index("RESEARCH BRIEF:") < start


def test_plan_skill_lists_scope_check():
    assert "Requested Scope" in PLAN
    synth = PLAN[PLAN.index("**Verdict synthesis additions:**"):PLAN.index("### Hook-triggered")]
    red = PLAN[PLAN.index("## Red Flags"):PLAN.index("## Verification")]
    ver = PLAN[PLAN.index("## Verification"):]
    for part in (synth, red, ver):
        assert "Scope Check" in part


def test_captain_lists_scope_check():
    assert "Scope Check" in CAPTAIN


def test_code_review_skill_has_no_scope_check():
    assert "Scope Check" not in CODE


def test_never_defer_banned_everywhere():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".sh", ".json", ".toml"} and "__pycache__" not in path.parts:
            if path.name == "test_scope_check_contract.py":
                continue
            assert "never defer" not in path.read_text(errors="ignore").lower(), path
