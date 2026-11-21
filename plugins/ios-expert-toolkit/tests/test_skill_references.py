#!/usr/bin/env python3
"""Our own files name a skill as /{name}, never as a bare name.

Vendored skills (skills/community, skills/xcode) and the sha-locked swiftui-pro upstream
references are excluded. Agents (subagents) are not skills and keep plain names.
"""

import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
OWN_SKILLS = ["ios-conventions", "ios-error-handling", "ios-expert", "ios-testing", "tca", "swiftui-pro"]

# (file name, hit fragment, reason) for text that looks like a bare skill name but is not one.
ALLOWED: list[tuple[str, str, str]] = []


def skill_names() -> list[str]:
    return sorted({p.parent.name for p in SKILLS_DIR.rglob("SKILL.md")})


def own_files() -> list[Path]:
    files = [PROJECT_ROOT / "skills" / s / "SKILL.md" for s in OWN_SKILLS]
    files.append(SKILLS_DIR / "swiftui-pro" / "FORK.md")
    files.append(SKILLS_DIR / "swiftui-pro" / "references" / "views.md")
    files += (PROJECT_ROOT / "agents").glob("*.md")
    files += (PROJECT_ROOT / "references").glob("*.md")
    return sorted(files)


def bare_patterns(names: list[str]) -> re.Pattern:
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(
        rf"`(?:{alt})`"
        rf"|\[(?:{alt})\]\([^)]*SKILL\.md\)"
        rf"|(?<![/\w-])[Uu]se (?:{alt})(?![\w/-])"
        rf"|(?<![/\w-])[Tt]he (?:{alt}) skill\b"
        rf"|(?<![/\w`-])(?:{alt}) skill\b"
    )


def bare_references(text: str, names: list[str]) -> list[str]:
    pattern = bare_patterns(names)
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("name:") or line.lstrip().startswith("<!--"):
            continue
        for match in pattern.finditer(line):
            hits.append(f"{number}: {match.group(0)}")
    return hits


def test_skill_names_come_from_disk():
    names = skill_names()
    assert set(OWN_SKILLS) <= set(names)
    assert "swift-concurrency" in names and "swiftui-specialist" in names


@pytest.mark.parametrize("path", own_files(), ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_skills_are_named_with_a_slash(path):
    hits = bare_references(path.read_text(encoding="utf-8"), skill_names())
    hits = [h for h in hits if not any(a[0] == path.name and a[1] in h for a in ALLOWED)]
    assert not hits, f"{path.name} names a skill without the slash: {hits}"


def test_guard_flags_bare_names_and_accepts_slash_names():
    names = skill_names()
    assert bare_references("Load `tca` for reducers.", names)
    assert bare_references("For reducers, use tca.", names)
    assert bare_references("See the swiftui-pro skill.", names)
    assert bare_references("See [tca](../tca/SKILL.md).", names)
    assert not bare_references("See [/tca](../tca/SKILL.md) and [tca](tca.md).", names)
    assert not bare_references("Load /tca for reducers.", names)
    assert not bare_references("Use /swiftui-pro, see skills/tca/SKILL.md.", names)
    assert not bare_references("name: tca", names)
