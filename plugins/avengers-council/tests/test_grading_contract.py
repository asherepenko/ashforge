#!/usr/bin/env python3
"""Tests for the review-grading contract across verdict template, rules, and actions."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_verdict_template_consensus_block_has_headline_and_table_in_order():
    template = read("assets/verdict-template.md")
    block = template.split("## Consensus\n", 1)[1].split("## Risk", 1)[0]
    markers = [
        "### ",
        "| **Quality** |",
        "| **Risk** |",
        "| **Vote** |",
        "| **Score** |",
    ]
    positions = [block.find(marker) for marker in markers]
    assert all(pos >= 0 for pos in positions), positions
    assert positions == sorted(positions)
    assert "Vote adjustments" in block
    score_row = next(line for line in block.splitlines() if line.startswith("| **Score** |"))
    assert "(info)" not in score_row


def test_examples_use_table_consensus_block():
    for path in sorted((PROJECT_ROOT / "examples").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "## Consensus" not in text:
            continue
        assert "| **Quality** |" in text, path.name
        assert "**Verdict**:" not in text, path.name


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
    import re

    rubric = read("references/rubric-code-quality.md")
    slugs = re.findall(r"^## \d\. .*\((\w+)\)$", rubric, re.M)
    assert len(slugs) == 5
    rules = read("references/verdict-rules.md")
    quality = rules.split("### Quality", 1)[1].split("### Risk", 1)[0]
    assert "· weak:" in quality
    assert "(" + ", ".join(slugs) + ")" in quality
    assert "no suffix" in quality
    for path in (
        "references/orchestration-protocol.md",
        "skills/council-code-review/SKILL.md",
        "skills/council-plan-review/SKILL.md",
    ):
        text = read(path)
        assert re.search(r"weak.{0,200}verdict-rules\.md#quality\b(?!-)", text), path
    assert "· weak:" in read("assets/verdict-template.md")


def test_consensus_table_rows_have_two_columns():
    paths = ["assets/verdict-template.md", "docs/skills.md"]
    paths += [f"examples/{p.name}" for p in sorted((PROJECT_ROOT / "examples").glob("*.md"))]
    for path in paths:
        rows = [l for l in read(path).splitlines() if re.match(r"^\| \*\*(Quality|Risk|Vote|Score)\*\* \|", l)]
        if path.startswith("examples/") and not rows:
            continue
        assert rows, path
        for row in rows:
            assert row.count("|") == 3, (path, row)


def _verdict_docs():
    paths = ["assets/verdict-template.md", "docs/skills.md"]
    return paths + [f"examples/{p.name}" for p in sorted((PROJECT_ROOT / "examples").glob("*.md"))]


def test_consensus_headlines_use_matching_emoji():
    expected = {"APPROVED WITH CONDITIONS": "✅", "APPROVED": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "⛔"}
    for path in _verdict_docs():
        for line in read(path).splitlines():
            if not line.startswith("### ") or not re.search(r"APPROVED|NEEDS REVISION|BLOCKED", line):
                continue
            if line.startswith("### ["):
                continue
            assert line[4:].startswith(("✅", "⚠️", "⛔")), (path, line)
            label = line[4:].split(" ", 1)[1].strip()
            assert label in expected, (path, line)
            assert line[4:].startswith(expected[label]), (path, line)


def test_concrete_risk_rows_start_with_matching_emoji():
    expected = {"🟢": "low", "🟡": "medium", "🔴": "high"}
    for path in _verdict_docs():
        for line in read(path).splitlines():
            if not line.startswith("| **Risk** |") or "[" in line:
                continue
            cell = line.split("|")[2].strip()
            emoji, level = cell.split(" ")[:2]
            assert expected.get(emoji) == level, (path, line)


PRODUCER_DOCS = [
    "skills/council-code-review/SKILL.md",
    "skills/council-plan-review/SKILL.md",
    "references/orchestration-protocol.md",
    "references/runtime-fallback.md",
]


def test_producer_docs_name_quality_and_risk_rows():
    for path in PRODUCER_DOCS:
        text = read(path)
        assert "**Quality**" in text, path
        assert "**Risk**" in text, path


def test_producer_docs_name_grading_steps():
    for path in PRODUCER_DOCS:
        text = read(path)
        assert "score-check.sh" in text, path
        assert "review-grade.sh" in text, path
        assert "verdict-rules.md#quality-and-risk" in text, path


def test_quick_flow_names_grading_steps():
    text = read("references/orchestration-protocol.md")
    quick = text[text.index("### Quick Flow"):]
    quick = quick[: quick.index("\n## ")] if "\n## " in quick else quick
    for fact in ["score-check.sh", "review-grade.sh", "Score flag:", "**Risk**"]:
        assert fact in quick, fact


def test_fallback_and_protocol_fill_rows_the_same_way():
    for path in ["references/orchestration-protocol.md", "references/runtime-fallback.md"]:
        text = read(path)
        assert "leading `Quality: `" in text, path
        assert "verdict-rules.md#quality" in text, path
        assert "`<emoji> <level> — <basis>`" in text, path


def test_captain_round_3_collects_final_score_with_basis():
    line = next(l for l in read("references/captain-america-orchestrator.md").splitlines() if l.startswith("- **Round 3**:"))
    assert "FINAL DOMAIN SCORE (with basis)" in line
    assert "CONCERN FOR THE USER" in line
