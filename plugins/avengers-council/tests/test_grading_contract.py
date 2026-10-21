#!/usr/bin/env python3
"""Tests for the review-grading contract across verdict template, rules, and actions."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_verdict_template_consensus_block_has_five_lines_in_order():
    template = read("assets/verdict-template.md")
    block = template.split("## Consensus\n", 1)[1].split("## Risk", 1)[0]
    markers = [
        "**Verdict**:",
        "**Quality**:",
        "**Risk**:",
        "**Vote**:",
        "**Score**:",
    ]
    positions = [block.find(marker) for marker in markers]
    assert all(pos >= 0 for pos in positions), positions
    assert positions == sorted(positions)
    assert "**Vote adjustments**" in block


def test_verdict_template_risk_section_covers_code_reviews():
    template = read("assets/verdict-template.md")
    assert "Omit it for code reviews" not in template


def test_verdict_template_member_headers_carry_basis_and_scores_are_info():
    template = read("assets/verdict-template.md")
    assert "| Score: X/10 — basis:" in template
    assert "Interpretation per verdict-rules.md" not in template
    assert "(info — never changes the verdict)" in template
    assert "Score flag:" in template


def test_verdict_rules_drop_score_override_and_use_new_conditions_wording():
    rules = read("references/verdict-rules.md")
    assert "< 5.0" not in rules
    assert "Score Override" not in rules
    assert "re-evaluation" not in rules
    assert "Every HIGH issue is a condition" in rules
    assert "Merge only after every condition is fixed" in rules


def test_debate_protocol_requires_score_basis():
    assert "— basis:" in read("references/debate-protocol.md")


def test_post_verdict_actions_conditions_menu():
    actions = read("references/post-verdict-actions.md")
    assert "Proceed without addressing" not in actions
    conditions = actions.split("### APPROVED WITH CONDITIONS", 1)[1].split("### NEEDS REVISION", 1)[0]
    assert "Address conditions now" in conditions
    assert "Override — record why" in conditions


def test_score_check_runs_before_round_3_in_both_trigger_blocks():
    protocol = read("references/orchestration-protocol.md")
    debate = protocol.split("**Barrier B:**", 1)[1].split("## Phase 4", 1)[0]
    assert "score-check.sh" in debate
    assert debate.count("Score flag") >= 2


def test_quality_line_weak_suffix_has_a_producer_in_rules_and_protocol():
    for path in ("references/verdict-rules.md", "references/orchestration-protocol.md"):
        assert "· weak:" in read(path), path
