#!/usr/bin/env python3
"""Tests for the plugin manifests, the Xcode MCP config and the maintainer docs."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SKILL_GROUPS = ["./skills/", "./skills/community/", "./skills/xcode/"]


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def claude() -> dict:
    return json.loads(read(".claude-plugin/plugin.json"))


def codex() -> dict:
    return json.loads(read(".codex-plugin/plugin.json"))


def test_manifest_names_and_versions_match():
    assert claude()["name"] == codex()["name"] == "ios-expert-toolkit"
    assert claude()["version"] == codex()["version"] == "1.0.0"


def test_claude_manifest_lists_skill_groups():
    assert claude()["skills"] == SKILL_GROUPS


def test_codex_manifest_scans_nested_groups_with_a_string():
    manifest = codex()
    assert manifest["skills"] == "./skills/"
    assert manifest["hooks"] == "./hooks/hooks-codex.json"
    assert manifest["interface"]["displayName"] == "iOS Expert Toolkit"


def test_descriptions_match():
    assert claude()["description"] == codex()["description"]


def test_mcp_config_points_at_xcode_bridge():
    assert json.loads(read(".mcp.json")) == {
        "mcpServers": {"xcode": {"type": "stdio", "command": "xcrun", "args": ["mcpbridge"], "env": {}}}
    }


def test_claude_md_is_symlink_to_agents_md():
    link = PROJECT_ROOT / "CLAUDE.md"
    assert link.is_symlink()
    assert link.readlink() == Path("AGENTS.md")


def test_readme_states_xcode_requirements():
    readme = read("README.md")
    assert "xcode-select" in readme
    assert "MCP_XCODE_PID" in readme


def test_manifest_version_has_changelog_entry():
    headings = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.MULTILINE)
    assert headings and headings[0] == claude()["version"]
