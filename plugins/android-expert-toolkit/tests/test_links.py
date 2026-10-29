#!/usr/bin/env python3
"""Every plugin-owned Markdown link and reference path must resolve.

Vendored official skills are excluded: they are upstream content.
"""

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
OWN_SKILLS = ["aet-check", "android-expert", "android-testing", "android-error-handling"]
REMOVED = ["aet-pipeline", "aet-status", "handoff", "session-start", "track-progress",
           "validate-handoff", "validate-dependencies", "runtime-adapters", "agent-routing"]


def own_markdown() -> list[Path]:
    files = [p for p in PROJECT_ROOT.glob("*.md")]
    files += list((PROJECT_ROOT / "agents").glob("*.md"))
    files += list((PROJECT_ROOT / "references").glob("*.md"))
    files += [PROJECT_ROOT / "skills" / s / "SKILL.md" for s in OWN_SKILLS]
    return sorted(files)


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_relative_links_resolve(path):
    text = re.sub(r"```[\s\S]*?```", "", path.read_text(encoding="utf-8"))
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"[a-z]+://|#|mailto:", target):
            continue
        assert (path.parent / target.split("#", 1)[0]).exists(), f"{path.name}: broken link {target}"


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_plugin_root_reference_paths_exist(path):
    text = path.read_text(encoding="utf-8")
    for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+\.(?:md|sh|py))", text):
        assert (PROJECT_ROOT / ref).exists(), f"{path.name}: missing {ref}"


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_reference_file_names_in_tables_exist(path):
    """Router tables name references by bare file name (`presentation.md`)."""
    text = path.read_text(encoding="utf-8")
    refs = {p.name for p in (PROJECT_ROOT / "references").glob("*.md")}
    for name in re.findall(r"`([a-z0-9-]+\.md)`", text):
        if name in {"SKILL.md", "README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "QUICK_START.md"}:
            continue
        assert name in refs, f"{path.name}: unknown reference {name}"


@pytest.mark.parametrize("path", [p for p in own_markdown() if p.name != "CHANGELOG.md"],
                         ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_no_mentions_of_removed_components(path):
    text = path.read_text(encoding="utf-8")
    for word in REMOVED:
        assert word not in text, f"{path.name} mentions removed component '{word}'"
