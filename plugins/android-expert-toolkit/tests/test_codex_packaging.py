#!/usr/bin/env python3
"""Tests for Codex plugin packaging."""

import json
import subprocess
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
OWN_SKILLS = {"android-conventions", "android-expert", "android-testing", "android-error-handling"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_ships_no_hooks():
    """The pipeline hooks were removed in 4.0.0; neither runtime registers hooks."""
    assert not (PROJECT_ROOT / "hooks").exists()
    assert "hooks" not in read_json(PROJECT_ROOT / ".codex-plugin" / "plugin.json")
    assert "hooks" not in read_json(PROJECT_ROOT / ".claude-plugin" / "plugin.json")


def test_codex_short_description_lives_in_openai_yaml():
    """Codex documents only name and description in SKILL.md frontmatter;
    the UI short text belongs in agents/openai.yaml as interface.short_description.
    Vendored official skills are left exactly as upstream ships them."""
    for name in sorted(OWN_SKILLS):
        skill = PROJECT_ROOT / "skills" / name / "SKILL.md"
        frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
        assert "metadata:" not in frontmatter, skill
        assert "short-description" not in frontmatter, skill
        yaml = (skill.parent / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert yaml.startswith("interface:\n  short_description: "), skill


def test_codex_agents_match_markdown_agents():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "codex-agents-gen.py"), "--check"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_codex_agents_are_valid_toml_with_required_fields():
    agents = sorted((PROJECT_ROOT / "agents").glob("*.md"))
    tomls = sorted((PROJECT_ROOT / "codex-agents").glob("*.toml"))
    assert [p.stem for p in agents] == [p.stem for p in tomls]
    for path in tomls:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        assert data["name"] == path.stem
        assert data["description"]
        assert "## Scope Boundaries" in data["developer_instructions"]
        assert "Codex runtime adapter" in data["developer_instructions"]
