"""Own markdown must not depend on a plugin-root env var.

Prose links to plugin files are relative markdown links. Skills run their
scripts by skill-relative path; preflight prints the plugin root. No markdown
file names a plugin-root variable, not even inside fences.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROOT_VARS = re.compile(r"\b(?:CLAUDE_|ZCODE_)?PLUGIN_ROOT\b")
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


def test_no_plugin_root_variable_anywhere():
    hits = [
        f"{p.relative_to(ROOT)}:{n}: {line.strip()}"
        for p in _own_markdown()
        if p.name not in ALLOWED_FILES
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if ROOT_VARS.search(line)
    ]
    assert not hits, "use a skill-relative path or the root preflight prints:\n" + "\n".join(hits)


def test_negative_control_root_vars_detected():
    for var in ("${CLAUDE_PLUGIN_ROOT}", "$PLUGIN_ROOT", "ZCODE_PLUGIN_ROOT"):
        assert ROOT_VARS.search(f"x {var}/scripts y"), var


def _broken_links(path):
    broken = []
    for n, line in _prose_lines(path):
        for target in LINK.findall(line):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if not (path.parent / file_part).exists():
                broken.append(f"{n}: {target}")
    return broken


@pytest.mark.parametrize("path", _own_markdown(), ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(path):
    broken = _broken_links(path)
    assert not broken, "\n".join(broken)


def test_link_checker_skips_urls_and_anchors_but_flags_missing_files(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text(
        "[web](https://example.com/missing.md)\n"
        "[anchor](#section)\n"
        "[gone](missing.md)\n"
    )
    assert _broken_links(doc) == ["3: missing.md"]
