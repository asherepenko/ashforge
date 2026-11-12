#!/usr/bin/env python3
"""Review mode keeps one output shape, and its rows track the rubric headings."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REF = ROOT / "references" / "review-rules.md"


def rubric_rows(name: str, prefix: str) -> list[str]:
    text = (ROOT / "references" / name).read_text(encoding="utf-8")
    return [f"{prefix}{n} {title}" for n, title in re.findall(r"^## (\d+)\. (.+)$", text, re.M)]


def test_rows_match_rubric_headings():
    text = REF.read_text(encoding="utf-8")
    rows = rubric_rows("rubric-swiftui.md", "C") + rubric_rows("rubric-ios-architecture.md", "A")
    assert len(rows) == 11
    for row in rows:
        assert row in text, f"review-rules.md is missing rubric row: {row}"


def test_template_sections_and_verdicts():
    rules = REF.read_text(encoding="utf-8")
    assert "Any ❌ FAIL → ⚠️ **Changes needed**" in rules and "No ❌ FAIL → ✅ **Approve**" in rules
    assert "../assets/review-template.md" in rules
    tpl = (ROOT / "assets" / "review-template.md").read_text(encoding="utf-8")
    for needle in ["### ⚠️ iOS review — Changes needed", "| **Rows** | ✅", "| **Findings** |",
                   "| ID | Criterion | Evidence |", "#### ❌ Fails (", "#### 📋 Pre-existing (",
                   "#### 🔔 Notes (", "No findings."]:
        assert needle in tpl, needle


def test_router_and_architect_point_to_review_mode():
    assert "references/review-rules.md" in (ROOT / "skills/ios-expert/SKILL.md").read_text(encoding="utf-8")
    assert "references/review-rules.md" in (ROOT / "agents/ios-architect.md").read_text(encoding="utf-8")
