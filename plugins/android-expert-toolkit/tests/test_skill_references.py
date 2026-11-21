#!/usr/bin/env python3
"""Our own skills, agents and references name a skill as `/{name}`, never bare.

Vendored skills under skills/android/ are not scanned (upstream text), but
their names count as skill names when we refer to them.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# (file relative to the plugin root, matched text) pairs that are not references.
ALLOWLIST: set[tuple[str, str]] = set()


def skill_names() -> list[str]:
    return sorted(p.parent.name for p in (PROJECT_ROOT / "skills").rglob("SKILL.md"))


def our_files() -> list[Path]:
    skills = [
        p
        for p in (PROJECT_ROOT / "skills").glob("*/SKILL.md")
        if p.parent.name != "android"
    ]
    agents = (PROJECT_ROOT / "agents").glob("*.md")
    references = (PROJECT_ROOT / "references").glob("*.md")
    return sorted([*skills, *agents, *references])


def bare_skill_references(text: str, names: list[str]) -> list[str]:
    """Return the bare skill mentions in text.

    Flags: a backticked name (`name` or `name args`), "use name", "the name
    skill", and a name opening a line in a code block. The "use name" form
    covers hyphenated names only, since a single word such as "adaptive" is
    ordinary English ("use adaptive layouts").
    """
    hits = []
    for name in names:
        n = re.escape(name)
        patterns = [
            rf"(?<![/\w-])`{n}(?=[` ])",
            rf"(?i:\bthe) {n} skill\b",
            rf"(?m)^{n}(?=\s|$)",
        ]
        if "-" in name:
            patterns.append(rf"(?i:\buse )(?:the )?{n}(?![\w-])")
        for pattern in patterns:
            hits += [m.group(0) for m in re.finditer(pattern, text)]
    return hits


def test_no_bare_skill_names_in_our_files():
    names = skill_names()
    offenders = []
    for path in our_files():
        rel = str(path.relative_to(PROJECT_ROOT))
        for hit in bare_skill_references(path.read_text(encoding="utf-8"), names):
            if (rel, hit) not in ALLOWLIST:
                offenders.append(f"{rel}: {hit!r}")
    assert not offenders, "name skills as /{name}:\n" + "\n".join(offenders)


def test_detector_catches_bare_names_and_accepts_slash_names():
    names = ["android-conventions", "testing-setup", "adaptive"]
    bare = [
        "run `android-conventions di` first",
        "(use testing-setup)",
        "use the testing-setup skill",
        "the testing-setup skill covers it",
        "see `adaptive`",
        "```\nandroid-conventions state\n```",
    ]
    for text in bare:
        assert bare_skill_references(text, names), text
    slashed = [
        "run `/android-conventions di` first",
        "(use /testing-setup)",
        "the `/testing-setup` skill",
        "use adaptive layouts",
        "name: android-conventions",
        "[testing-setup](../x.md)",
    ]
    for text in slashed:
        assert not bare_skill_references(text, names), text
