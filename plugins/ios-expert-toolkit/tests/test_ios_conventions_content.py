#!/usr/bin/env python3
"""Structural checks for the ios-conventions skill and its pattern reference."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SKILL = PROJECT_ROOT / "skills/ios-conventions/SKILL.md"
REFERENCE = PROJECT_ROOT / "references/pattern-detection.md"
SCRIPT = PROJECT_ROOT / "tests/fixtures/run-sweeps.py"
OPENAI = PROJECT_ROOT / "skills/ios-conventions/agents/openai.yaml"

VERDICTS = ["NEW", "TCA", "MVVM", "MIXED"]
SWEEP_PATTERNS = [
    "@Reducer", "@Observable", "ObservableObject", "UIViewController",
    "@Dependency", "static let shared", "import Testing", "XCTestCase",
    "@Model", "NSManagedObject", "swiftLanguageModes", "SWIFT_VERSION", "@MainActor",
    "NavigationStack", "Coordinator", "Package.resolved", "IPHONEOS_DEPLOYMENT_TARGET",
]


def section(text: str, heading: str) -> str:
    """Body of the `## heading` section, up to the next `## ` heading. Empty if absent."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def decision_rows(body: str) -> dict:
    """Map verdict -> table row text for rows like | `NEW` | ... |."""
    rows = {}
    for line in body.splitlines():
        m = re.match(r"\|\s*`?(NEW|TCA|MVVM|MIXED)`?\s*\|(.*)\|\s*$", line)
        if m:
            rows[m.group(1)] = m.group(2)
    return rows


def has_decision_rule(text: str) -> bool:
    body = section(text, "Decision rule")
    rows = decision_rows(body)
    return set(rows) == set(VERDICTS) and "80%" in body


def names_all_sweep_patterns(text: str) -> bool:
    body = section(text, "Sweeps")
    return all(p in body for p in SWEEP_PATTERNS)


def reference_patterns() -> dict:
    out = {}
    for line in REFERENCE.read_text().splitlines():
        m = re.match(r"\|\s*(TCA|MVVM_OBSERVABLE|MVVM_OBJECT|UIKIT)\s*\|[^|]*\|\s*`(.+)`\s*\|\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).replace("\\|", "|")
    return out


def test_decision_rule_has_all_four_verdicts_and_80_percent():
    assert has_decision_rule(SKILL.read_text())


def test_decision_rule_negative_controls():
    text = SKILL.read_text()
    assert not has_decision_rule(text.replace("## Decision rule", "## Notes"))
    assert not has_decision_rule(text.replace("| `MIXED` |", "| `OTHER` |"))
    assert not has_decision_rule(section(text, "Decision rule").replace("80%", "most"))


def test_decision_rule_rows_state_the_policy():
    rows = decision_rows(section(SKILL.read_text(), "Decision rule"))
    assert "TCA required" in rows["NEW"]
    assert "Never force TCA" in rows["MVVM"]
    assert "TCA only on request" in rows["MIXED"]
    assert "Follow the dominant local pattern" in rows["MIXED"]


def test_sweep_section_names_every_pattern():
    assert names_all_sweep_patterns(SKILL.read_text())


def test_sweep_section_negative_controls():
    text = SKILL.read_text()
    for pattern in SWEEP_PATTERNS:
        stripped = section(text, "Sweeps").replace(pattern, "")
        mutated = text.replace(section(text, "Sweeps"), stripped)
        assert not names_all_sweep_patterns(mutated), pattern
    assert not names_all_sweep_patterns(text.replace("## Sweeps", "## Areas"))


def test_skill_points_at_the_single_source_reference():
    assert "references/pattern-detection.md" in SKILL.read_text()


def test_reference_has_the_same_decision_rule():
    assert has_decision_rule(REFERENCE.read_text())


def test_reference_patterns_are_the_ones_the_script_runs():
    patterns = reference_patterns()
    assert set(patterns) == {"TCA", "MVVM_OBSERVABLE", "MVVM_OBJECT", "UIKIT"}
    script = SCRIPT.read_text()
    for name, pattern in patterns.items():
        assert pattern in script, name


def test_pattern_agreement_negative_control():
    script = SCRIPT.read_text().replace("@Reducer", "@Store")
    assert not all(p in script for p in reference_patterns().values())


def test_skill_architecture_patterns_match_reference_ids():
    body = section(SKILL.read_text(), "Sweeps")
    assert "@Reducer" in body and reference_patterns()["TCA"] == "@Reducer"
    assert "@Observable" in body and "ObservableObject" in body


def test_frontmatter_and_codex_interface():
    head = SKILL.read_text().split("---")[1]
    assert re.search(r"^name: ios-conventions$", head, re.M)
    assert re.search(r"^description: ", head, re.M)
    assert "short_description:" in OPENAI.read_text()
    assert "interface:" in OPENAI.read_text()


def test_version_section_reads_resolved_target_and_swift_mode():
    body = section(SKILL.read_text(), "Sweeps")
    for token in ["Package.resolved", "IPHONEOS_DEPLOYMENT_TARGET", "SWIFT_VERSION", "swiftLanguageModes"]:
        assert token in body
    assert re.search(r"iOS 17", SKILL.read_text())
