#!/usr/bin/env python3
"""Tests for manifest versions and the shape of the plugin after the 4.0.0 rework."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def version() -> str:
    return json.loads(read(".claude-plugin/plugin.json"))["version"]


def test_manifest_versions_match():
    codex = json.loads(read(".codex-plugin/plugin.json"))["version"]
    assert version() == codex
    assert re.fullmatch(r"\d+\.\d+\.\d+", version()), f"not semver: {version()}"


def test_marketplace_entry_matches_manifest():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    entry = next(p for p in marketplace["plugins"] if p["name"] == "android-expert-toolkit")
    assert "version" not in entry or entry["version"] == version()
    assert "pipeline" not in entry["description"].lower()


def test_manifest_version_has_changelog_entry():
    """The released version is the newest CHANGELOG heading."""
    headings = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.MULTILINE)
    assert headings, "CHANGELOG.md has no version headings"
    assert headings[0] == version(), f"manifest is {version()}, newest CHANGELOG entry is {headings[0]}"


def test_pipeline_components_are_gone():
    for path in ["skills/aet-pipeline", "skills/aet-status", "hooks", "templates", "examples"]:
        assert not (PROJECT_ROOT / path).exists(), path


def test_aet_check_keeps_cache_contract():
    """An external consumer reads this path; it must not move."""
    assert ".artifacts/aet/cache/detected-patterns.json" in read("skills/android-conventions/SKILL.md")
    assert ".artifacts/aet/cache/detected-patterns.json" in read("skills/android-conventions/scripts/preflight.sh")
