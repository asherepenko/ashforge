"""Every core council agent carries a Research Focus section and web tools."""
import re
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
CORE = [
    "black-widow",
    "doctor-strange",
    "hawkeye",
    "hulk",
    "iron-man",
    "scarlet-witch",
    "thor",
    "vision",
]


def _text(name):
    return (AGENTS_DIR / f"{name}.md").read_text()


def _section(text):
    match = re.search(r"^## Research Focus\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else None


@pytest.mark.parametrize("name", CORE)
def test_has_research_focus_section(name):
    assert _section(_text(name)) is not None


@pytest.mark.parametrize("name", CORE)
def test_tools_line_has_web_tools(name):
    tools = re.search(r"^tools:.*$", _text(name), re.M)
    assert tools and "WebSearch, WebFetch" in tools.group(0)


@pytest.mark.parametrize("name", CORE)
def test_section_points_at_research_protocol(name):
    section = _section(_text(name))
    assert section is not None
    assert "references/research-protocol.md" in section
