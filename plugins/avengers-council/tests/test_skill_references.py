"""Own skills are named `/{name}` in skills, agents and references.

A bare skill name is not a command on every runtime. Paths, a skill's own
`name:` line, hyphenated compounds and plain words are not references.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = sorted(p.parent.name for p in ROOT.glob("skills/*/SKILL.md"))


def _patterns(names):
    alt = "|".join(re.escape(n) for n in names)
    return [
        re.compile(rf"`(?:{alt})`"),
        re.compile(rf"\buse (?:the )?(?:{alt})(?![\w/-])", re.I),
        re.compile(rf"\bthe (?:{alt}) skill\b", re.I),
    ]


def _files():
    files = list(ROOT.glob("skills/*/SKILL.md"))
    files += ROOT.glob("agents/*.md")
    files += ROOT.glob("references/*.md")
    return sorted(files)


def bare_mentions(text, names=NAMES):
    pats = _patterns(names)
    return [
        (i, line.strip())
        for i, line in enumerate(text.splitlines(), 1)
        for pat in pats
        if pat.search(line)
    ]


def test_skill_names_found_on_disk():
    assert "council-plan-review" in NAMES
    assert len(NAMES) >= 3


def test_no_bare_skill_names():
    hits = [
        f"{path.relative_to(ROOT)}:{n}: {line}"
        for path in _files()
        for n, line in bare_mentions(path.read_text())
    ]
    assert not hits, "name skills as /{name}:\n" + "\n".join(hits)


def test_guard_flags_bare_forms_and_passes_slash_forms():
    bad = [
        "Run `council-advise` first.",
        "For plans, use council-plan-review instead.",
        "Hand off to the council-code-review skill.",
    ]
    good = [
        "Run `/council-advise` first.",
        "For plans, use /council-plan-review instead.",
        "name: council-code-review",
        "Read `skills/council-code-review/SKILL.md`.",
    ]
    for line in bad:
        assert bare_mentions(line), line
    for line in good:
        assert not bare_mentions(line), line
