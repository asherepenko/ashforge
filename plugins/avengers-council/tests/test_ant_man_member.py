"""Ant-Man is an optional Reuse & Placement member, registered and bounded by a red line."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / "agents" / "ant-man.md"
REGISTRY = ROOT / "references" / "member-registry.md"
RED_LINES = ROOT / "references" / "red-lines.md"

REQUIRED_SECTIONS = [
    "Specialty",
    "Character",
    "Expertise",
    "Planning Mode Checklist",
    "Code Review Checklist",
    "Debate Protocol",
    "Debate Behavior",
    "Red Lines",
    "Communication Style",
]


def _frontmatter():
    text = AGENT.read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, "ant-man.md has no frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


def _section(text, title):
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, f"missing section: {title}"
    return match.group(1)


def test_frontmatter_fields():
    fm = _frontmatter()
    assert fm["name"] == "ant-man"
    assert fm["model"] == "sonnet"
    assert fm["tools"] == "Read, Grep, Glob, Bash, SendMessage"
    assert fm["optional"] == "true"
    assert fm["description"]
    assert fm["color"]
    invoke = fm["invoke_when"].lower()
    assert "adds or moves code" in invoke
    assert "docs-only" in invoke and "config-only" in invoke


@pytest.mark.parametrize("title", REQUIRED_SECTIONS)
def test_required_sections(title):
    _section(AGENT.read_text(), title)


def test_no_research_focus_section():
    assert "## Research Focus" not in AGENT.read_text()


def test_debate_protocol_one_liner():
    body = _section(AGENT.read_text(), "Debate Protocol")
    assert "${CLAUDE_PLUGIN_ROOT}/references/debate-protocol.md" in body


@pytest.mark.parametrize(
    "title", ["Planning Mode Checklist", "Code Review Checklist"]
)
def test_checklists_cover_the_lens(title):
    body = _section(AGENT.read_text(), title).lower()
    assert "codegraph" in body and ".codegraph/" in body and "grep" in body
    assert "owner module" in body and "layer" in body
    assert "premature abstraction" in body and "fewer than 3" in body
    assert "duplication" in body


def test_debate_behavior_targets():
    body = _section(AGENT.read_text(), "Debate Behavior")
    for name in ("Iron Man", "Thor", "Scarlet Witch"):
        assert re.search(rf"Challenges {name}", body), name
    assert re.search(r"Supports Hulk", body)


def test_registry_row_and_rule():
    text = REGISTRY.read_text()
    row = next(
        (l for l in text.splitlines() if l.startswith("| ant-man |")), None
    )
    assert row, "no ant-man row in the registry"
    assert "avengers-council:ant-man" in row
    assert "Reuse & Placement" in row
    for phrase in (
        "== Code files added or moved ==",
        "`COUNT` > 0",
        "`ADDED_DEFS` > 0",
        "`UNKNOWN`",
        "Captain reads the diff",
        "File Structure Map",
        "Create rows",
        "docs-only",
        "config-only",
    ):
        assert phrase in row, phrase


def test_registry_template_and_sections():
    text = REGISTRY.read_text()
    assert "tools: Read, Glob, Grep, SendMessage" in text
    assert "tools: Read, Glob, Grep\n" not in text
    assert "## Research Focus" in text


def test_red_lines_section():
    body = _section(RED_LINES.read_text(), "Reuse & Placement (Ant-Man)")
    assert "No reimplementing an existing helper" in body
    assert "No code in a module or layer that doesn't own the concept" in body


def test_not_in_quick_mode_tables():
    text = REGISTRY.read_text()
    quick = text[text.index("## Quick Mode Member Selection"):text.index("## How to Add")]
    assert "ant-man" not in quick
