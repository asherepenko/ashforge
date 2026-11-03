#!/usr/bin/env python3
"""Tests for Codex plugin packaging."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_codex_manifest_declares_no_hooks():
    manifest = read_json(PROJECT_ROOT / ".codex-plugin" / "plugin.json")

    assert "hooks" not in manifest


def test_codex_short_description_lives_in_openai_yaml():
    """Codex documents only name and description in SKILL.md frontmatter;
    the UI short text belongs in agents/openai.yaml as interface.short_description."""
    for skill in sorted((PROJECT_ROOT / "skills").glob("*/SKILL.md")):
        frontmatter = skill.read_text(encoding="utf-8").split("---", 2)[1]
        assert "metadata:" not in frontmatter, skill
        assert "short-description" not in frontmatter, skill
        yaml = (skill.parent / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert yaml.startswith("interface:\n  short_description: "), skill
