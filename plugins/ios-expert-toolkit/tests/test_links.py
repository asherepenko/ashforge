#!/usr/bin/env python3
"""Every plugin-owned Markdown link and reference path must resolve.

Vendored skills (skills/community, skills/xcode) are excluded: they are upstream content.
"""

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
OWN_SKILLS = ["ios-conventions", "ios-expert", "ios-testing", "ios-error-handling", "tca", "swiftui-pro"]
ROOT_DOCS = {"SKILL.md", "README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "QUICK_START.md"}


def own_markdown() -> list[Path]:
    files = [p for p in PROJECT_ROOT.glob("*.md")]
    files += list((PROJECT_ROOT / "agents").glob("*.md"))
    files += list((PROJECT_ROOT / "references").glob("*.md"))
    files += [PROJECT_ROOT / "skills" / s / "SKILL.md" for s in OWN_SKILLS]
    return sorted(files)


def link_targets(text: str) -> list[str]:
    text = re.sub(r"```[\s\S]*?```", "", text)
    return re.findall(r"\]\(([^)\s]+)\)", text)


def unresolved_links(path: Path) -> list[str]:
    bad = []
    for target in link_targets(path.read_text(encoding="utf-8")):
        if re.match(r"[a-z]+://|#|mailto:", target):
            continue
        if not (path.parent / target.split("#", 1)[0]).exists():
            bad.append(target)
    return bad


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_relative_links_resolve(path):
    assert unresolved_links(path) == [], f"{path.name}: broken links"


def skill_script_refs(text: str) -> list[str]:
    """Skills run their scripts by a path relative to the skill folder: `scripts/<x>.py`."""
    return re.findall(r"(?<![\w./-])(scripts/[\w.-]+\.(?:py|sh))", text)


@pytest.mark.parametrize("skill", OWN_SKILLS)
def test_skill_relative_script_paths_exist(skill):
    folder = PROJECT_ROOT / "skills" / skill
    for ref in skill_script_refs((folder / "SKILL.md").read_text(encoding="utf-8")):
        assert (folder / ref).exists(), f"{skill}: missing {ref}"


def test_negative_control_skill_script_ref_detected():
    assert skill_script_refs("Run `python3 scripts/preflight.py`") == ["scripts/preflight.py"]
    assert skill_script_refs("see ../../scripts/gen.py") == []


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_reference_file_names_in_tables_exist(path):
    """Router tables name references by bare file name (`navigation.md`)."""
    if path.parent.name == "swiftui-pro":
        pytest.skip("swiftui-pro names upstream files (api.md, data.md) that its fork replaces; owned by the fork test")
    text = path.read_text(encoding="utf-8")
    refs = {p.name for p in (PROJECT_ROOT / "references").glob("*.md")}
    refs |= {p.name for p in (path.parent / "references").glob("*.md")}  # a skill's own references
    if path.name == "SKILL.md":  # a skill may name a sibling skill's reference, e.g. swiftui-specialist `structure.md`
        refs |= {p.name for p in (PROJECT_ROOT / "skills").glob("**/references/*.md")}
    for name in re.findall(r"`([a-z0-9-]+\.md)`", text):
        if name in ROOT_DOCS:
            continue
        assert name in refs, f"{path.name}: unknown reference {name}"


ROOT_VARS = re.compile(r"(?:CLAUDE_|ZCODE_)?PLUGIN_ROOT")


def skips_root_var_check(path: Path) -> bool:
    return path.name == "CHANGELOG.md" or path.parent.name == "swiftui-pro"


@pytest.mark.parametrize("path", own_markdown(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_no_plugin_root_variables_in_markdown(path):
    """Skills call scripts by skill-relative path; scripts find the root from __file__."""
    if skips_root_var_check(path):
        pytest.skip("history entries or vendored fork")
    assert ROOT_VARS.findall(path.read_text(encoding="utf-8")) == []


def test_root_var_skip_covers_only_history_and_vendored_fork():
    assert skips_root_var_check(PROJECT_ROOT / "skills" / "swiftui-pro" / "SKILL.md")
    assert skips_root_var_check(PROJECT_ROOT / "CHANGELOG.md")
    assert not skips_root_var_check(PROJECT_ROOT / "skills" / "ios-conventions" / "SKILL.md")
    assert not skips_root_var_check(PROJECT_ROOT / "README.md")


def test_negative_control_root_vars_detected():
    for var in ("${CLAUDE_PLUGIN_ROOT}", "$PLUGIN_ROOT", "ZCODE_PLUGIN_ROOT"):
        assert ROOT_VARS.findall(f"x {var} y") != []


def test_negative_control_broken_link_is_detected(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("[gone](missing.md) and [ok](doc.md)\n", encoding="utf-8")
    assert unresolved_links(doc) == ["missing.md"]
