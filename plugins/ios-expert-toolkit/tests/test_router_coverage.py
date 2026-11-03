#!/usr/bin/env python3
"""The ios-expert router names every skill and agent exactly once, with distinct triggers."""

import re
from collections import Counter
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
ROUTER = PROJECT_ROOT / "skills" / "ios-expert" / "SKILL.md"
OWN_SKILLS = {"ios-conventions", "ios-testing", "ios-error-handling", "tca", "swiftui-pro"}
AGENTS = {"ios-architect", "ios-developer", "swiftui-expert", "ios-testing-specialist", "xcode-build-engineer"}
MCP_TOOL_GROUPS = {
    "build": {"BuildProject", "GetBuildLog"},
    "test": {"RunSomeTests", "RunAllTests", "GetTestList"},
    "preview": {"RenderPreview"},
    "diagnostics": {"XcodeRefreshCodeIssuesInFile", "GetConsoleOutput"},
}


def inventory() -> set[str]:
    """Skill names on disk, cross-checked against ios-skills.lock. Excludes the router itself."""
    disk = {p.parent.name for p in (PROJECT_ROOT / "skills").glob("*/SKILL.md")}
    disk |= {p.parent.name for p in (PROJECT_ROOT / "skills" / "community").glob("*/SKILL.md")}
    disk |= {p.parent.name for p in (PROJECT_ROOT / "skills" / "xcode").glob("*/SKILL.md")}
    disk.discard("ios-expert")
    lock = (PROJECT_ROOT / "ios-skills.lock").read_text(encoding="utf-8")
    locked = set(re.findall(r"^community\.([\w-]+)\.repo=", lock, re.M))
    locked |= set(re.findall(r"^xcode\.skill=([\w-]+)$", lock, re.M))
    locked |= set(re.findall(r"^fork\.([\w-]+)\.repo=", lock, re.M))
    assert disk == locked | OWN_SKILLS, f"disk and lock disagree: {disk ^ (locked | OWN_SKILLS)}"
    return disk


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"missing section {heading}"
    return m.group(1)


def routes(text: str) -> list[tuple[list[str], str]]:
    """(triggers, target) for every table row in the Topic and Agents sections.

    Topic rows are `| triggers | target |`; Agent rows are `| target | brief |`.
    """
    rows = []
    for heading in ("Topic → load", "Agents"):
        agents = heading == "Agents"
        for line in section(text, heading).splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not line.startswith("|") or len(cells) != 2 or set(cells[0]) <= {"-"}:
                continue
            if cells[0] in ("Triggers", "Agent"):
                continue
            name_cell, other = (cells[0], cells[1]) if agents else (cells[1], cells[0])
            target = re.fullmatch(r"`([^`]+)`", name_cell)
            assert target, f"route target must be one backticked name: {line}"
            triggers = [other.lower()] if agents else [t.strip().lower() for t in other.split(",")]
            rows.append((triggers, target.group(1)))
    return rows


def check_exactly_once(text: str, expected: set[str]) -> None:
    counts = Counter(target for _, target in routes(text))
    missing = expected - set(counts)
    dupes = {n for n in expected if counts[n] > 1}
    assert not missing, f"not routed: {sorted(missing)}"
    assert not dupes, f"routed more than once: {sorted(dupes)}"


def check_distinct_triggers(text: str) -> None:
    seen = Counter()
    for triggers, target in routes(text):
        if target in AGENTS:
            continue
        seen.update(triggers)
    repeated = sorted(t for t, n in seen.items() if n > 1)
    assert not repeated, f"trigger claimed by more than one route: {repeated}"


def router_text() -> str:
    return ROUTER.read_text(encoding="utf-8")


def test_inventory_is_seventeen_skills_besides_the_router():
    assert len(inventory()) == 17


def test_every_skill_routed_exactly_once():
    check_exactly_once(router_text(), inventory())


def test_every_agent_routed_exactly_once():
    check_exactly_once(router_text(), AGENTS)


def test_every_reference_routed():
    refs = {p.name for p in (PROJECT_ROOT / "references").glob("*.md")}
    check_exactly_once(router_text(), refs)


def test_no_trigger_phrase_repeats_across_routes():
    check_distinct_triggers(router_text())


def test_swiftui_split():
    by_target = {t: trig for trig, t in routes(router_text())}
    assert any("review my swiftui" in t for t in by_target["swiftui-pro"])
    assert any("@observable" in t for t in by_target["swiftui-specialist"])
    assert any("ios 27" in t for t in by_target["swiftui-whats-new-27"])
    assert any("swiftdata" in t for t in by_target["swiftdata-pro"])


def check_mcp_section(text: str) -> None:
    body = section(text, "Xcode MCP")
    assert "xcrun mcpbridge" in body, "mcpbridge not named"
    named = set(re.findall(r"`([A-Z][A-Za-z]+)`", body))
    for group, tools in MCP_TOOL_GROUPS.items():
        assert tools <= named, f"{group}: missing {sorted(tools - named)}"


def test_xcode_mcp_section_names_the_bridge_and_real_tools():
    check_mcp_section(router_text())


def test_version_rule_precedes_the_routing_table():
    text = router_text()
    rules = text[: text.index("## Topic → load")]
    assert "ios-conventions" in rules
    assert re.search(r"iOS 17", rules) and re.search(r"iOS 27", rules)
    assert "deployment target" in rules


def test_router_has_codex_interface_metadata():
    yaml = (PROJECT_ROOT / "skills" / "ios-expert" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert re.search(r"^interface:\n  short_description: \"[^\"]+\"", yaml, re.M)


# Negative controls: the check functions must fail on a broken router.

def test_negative_control_duplicate_route_fails():
    text = router_text()
    broken = text.replace(
        "| @Reducer, TestStore, @ObservableState, @Shared, swift-composable-architecture | `tca` |",
        "| @Reducer, TestStore, @ObservableState, @Shared, swift-composable-architecture | `tca` |\n"
        "| an extra phrase | `tca` |",
    )
    assert broken != text
    with pytest.raises(AssertionError, match="more than once"):
        check_exactly_once(broken, inventory())


def test_negative_control_missing_skill_fails():
    text = router_text()
    broken = "\n".join(l for l in text.splitlines() if not l.rstrip().endswith("| `xctrace` |"))
    assert broken != text
    with pytest.raises(AssertionError, match="not routed"):
        check_exactly_once(broken, inventory())


def test_negative_control_missing_agent_fails():
    text = router_text()
    broken = "\n".join(l for l in text.splitlines() if "`ios-architect`" not in l)
    with pytest.raises(AssertionError, match="not routed"):
        check_exactly_once(broken, AGENTS)


def test_negative_control_repeated_trigger_fails():
    text = router_text()
    broken = text.replace("| SwiftData, @Model,", "| @Observable, @Model,", 1)
    assert broken != text
    with pytest.raises(AssertionError, match="trigger claimed"):
        check_distinct_triggers(broken)


def test_negative_control_stripped_mcp_section_fails():
    with pytest.raises(AssertionError, match="mcpbridge"):
        check_mcp_section(router_text().replace("xcrun mcpbridge", "the bridge"))


def test_negative_control_missing_preview_tool_fails():
    with pytest.raises(AssertionError, match="preview"):
        check_mcp_section(router_text().replace("`RenderPreview`", "`Render`"))
