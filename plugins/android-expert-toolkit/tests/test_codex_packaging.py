#!/usr/bin/env python3
"""Tests for Codex plugin packaging."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_codex_manifest_declares_codex_hooks_manifest():
    manifest = read_json(PROJECT_ROOT / ".codex-plugin" / "plugin.json")

    assert manifest["hooks"] == "./.codex-plugin/hooks.json"
    assert manifest["hooks"] != "./hooks/hooks.json"


def test_codex_hooks_use_codex_root_and_matchers():
    hooks_path = PROJECT_ROOT / ".codex-plugin" / "hooks.json"
    hooks_text = hooks_path.read_text(encoding="utf-8")
    hooks = json.loads(hooks_text)

    assert "${PLUGIN_ROOT}" in hooks_text
    assert "${CLAUDE_PLUGIN_ROOT}" not in hooks_text

    post_tool_use = hooks["hooks"]["PostToolUse"]
    matchers = {entry["matcher"] for entry in post_tool_use}
    assert "apply_patch" in matchers
    assert "local_shell|shell|shell_command|exec_command" in matchers


def test_claude_hooks_remain_claude_specific():
    hooks_text = (PROJECT_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")

    assert "${CLAUDE_PLUGIN_ROOT}" in hooks_text
    assert "Write" in hooks_text
    assert "Bash" in hooks_text
