"""Own markdown must not depend on Claude Code filling in ${CLAUDE_PLUGIN_ROOT}.

Prose links to plugin files are relative markdown links. The token may only
appear inside fenced shell blocks (the resolver snippets that read the env var).
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "${CLAUDE_PLUGIN_ROOT"
SHELL_FENCES = {"bash", "sh", "shell", "zsh"}
# CHANGELOG history describes past releases verbatim.
ALLOWED_FILES = {"CHANGELOG.md"}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def _own_markdown():
    return sorted(
        p for p in ROOT.rglob("*.md")
        if "tests" not in p.relative_to(ROOT).parts
        and not p.is_symlink()
    )


def _prose_lines(path):
    """Yield (lineno, line) for lines outside fenced shell blocks."""
    fence = None
    for n, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if fence is None:
                fence = stripped[3:].strip().lower() or "plain"
            else:
                fence = None
            continue
        if fence in SHELL_FENCES:
            continue
        yield n, line


def test_no_claude_plugin_root_in_prose():
    hits = [
        f"{p.relative_to(ROOT)}:{n}: {line.strip()}"
        for p in _own_markdown()
        if p.name not in ALLOWED_FILES
        for n, line in _prose_lines(p)
        if TOKEN in line
    ]
    assert not hits, "use a relative link instead:\n" + "\n".join(hits)


@pytest.mark.parametrize("path", _own_markdown(), ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(path):
    broken = []
    for n, line in _prose_lines(path):
        for target in LINK.findall(line):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if not (path.parent / file_part).exists():
                broken.append(f"{n}: {target}")
    assert not broken, "\n".join(broken)
