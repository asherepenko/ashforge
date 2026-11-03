#!/usr/bin/env python3
"""Structural checks for the ios-testing skill and its patterns reference."""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SKILL = PROJECT_ROOT / "skills/ios-testing/SKILL.md"
REFERENCE = PROJECT_ROOT / "references/testing-patterns.md"
OPENAI = PROJECT_ROOT / "skills/ios-testing/agents/openai.yaml"


def section(text: str, heading: str) -> str:
    """Body of the `## heading` section, up to the next `## ` heading. Empty if absent."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def method_rules(text: str) -> list:
    return re.findall(r"^\d+\. \*\*", section(text, "Method"), re.M)


def pitfalls_name_all(text: str) -> bool:
    body = section(text, "Pitfalls")
    return all(t in body for t in ("@MainActor", "confirmation", "Clock"))


def link_targets(text: str, name: str) -> list:
    return [t for label, t in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text) if name in t]


def test_method_lists_three_rules():
    assert len(method_rules(SKILL.read_text())) == 3


def test_method_negative_control():
    assert len(method_rules("## Method\n\n1. **One.** x\n2. **Two.** y\n")) == 2
    assert method_rules("## Other\n\n1. **One.** x\n") == []


def test_pitfalls_name_mainactor_confirmation_clock():
    assert pitfalls_name_all(SKILL.read_text())


def test_pitfalls_negative_control():
    assert not pitfalls_name_all("## Pitfalls\n\n- @MainActor and confirmation only\n")
    assert not pitfalls_name_all("## Other\n\n@MainActor confirmation Clock\n")


def test_links_swift_testing_expert_and_target_exists():
    targets = link_targets(SKILL.read_text(), "swift-testing-expert")
    assert targets
    for t in targets:
        assert (SKILL.parent / t).exists(), t


@pytest.mark.skipif(
    not (PROJECT_ROOT / "skills/tca/SKILL.md").exists(),
    reason="skills/tca is authored by a parallel leaf and may not exist yet",
)
def test_links_tca_and_target_exists():
    targets = link_targets(SKILL.read_text(), "tca")
    assert targets
    for t in targets:
        assert (SKILL.parent / t).exists(), t


def test_link_negative_control():
    assert link_targets("see [x](../nowhere/SKILL.md)", "swift-testing-expert") == []
    assert not (SKILL.parent / "../nowhere/SKILL.md").exists()


def test_skill_does_not_copy_swift_testing_expert():
    assert "expectedCount" not in section(SKILL.read_text(), "Method")
    assert len(SKILL.read_text().splitlines()) < 200


def test_reference_has_clock_and_swiftdata_samples():
    text = REFERENCE.read_text()
    for token in ("TestClock", "isStoredInMemoryOnly", "confirmation", "#require"):
        assert token in text


def test_openai_yaml_short_description():
    text = OPENAI.read_text()
    assert "interface:" in text and re.search(r"short_description:\s*\".+\"", text)
