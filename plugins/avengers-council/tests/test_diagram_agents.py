"""Iron Man and Hulk carry a diagram item in their Planning Mode Checklist."""
import re
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"

PHRASES = {
    "iron-man": (
        "- [ ] Architecture diagram (plan reviews): mermaid or ASCII — "
        "components, data flow, dependencies, boundaries"
    ),
    "hulk": (
        "- [ ] Flow diagram (plan reviews): user/state flow with happy, error "
        "and edge paths; map every path to a planned test; an unmapped path "
        "is a finding"
    ),
}


def _checklist(name):
    text = (AGENTS_DIR / f"{name}.md").read_text()
    match = re.search(
        r"^## Planning Mode Checklist\n(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    return match.group(1) if match else None


@pytest.mark.parametrize("name", sorted(PHRASES))
def test_checklist_has_diagram_item(name):
    section = _checklist(name)
    assert section is not None
    assert PHRASES[name] in section
