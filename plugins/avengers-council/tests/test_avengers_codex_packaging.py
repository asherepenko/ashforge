#!/usr/bin/env python3
"""Tests for Codex plugin packaging."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_codex_manifest_declares_empty_codex_hooks_manifest():
    manifest = read_json(PROJECT_ROOT / ".codex-plugin" / "plugin.json")

    assert manifest["hooks"] == "./hooks/hooks-codex.json"
    assert manifest["hooks"] != "./hooks/hooks.json"


def test_codex_hooks_do_not_register_claude_exit_plan_hook():
    hooks_path = PROJECT_ROOT / "hooks" / "hooks-codex.json"
    hooks_text = hooks_path.read_text(encoding="utf-8")
    hooks = json.loads(hooks_text)

    assert hooks == {"hooks": {}}
    assert "ExitPlanMode" not in hooks_text
    assert "${CLAUDE_PLUGIN_ROOT}" not in hooks_text


def test_claude_exit_plan_hook_remains_claude_specific():
    hooks_text = (PROJECT_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8")

    assert "ExitPlanMode" in hooks_text
    assert "${CLAUDE_PLUGIN_ROOT}" in hooks_text


def test_claude_hooks_no_op_when_plugin_root_is_unset():
    """Codex auto-discovers the legacy hooks/hooks.json alongside its own manifest.

    There, ${CLAUDE_PLUGIN_ROOT} expands to an empty string. The ExitPlanMode
    matcher never fires on Codex today, but any command in this manifest must
    still guard on the resolved path so it no-ops instead of running `bash
    "/hooks/..."` if a matcher ever does match.
    """
    hooks = read_json(PROJECT_ROOT / "hooks" / "hooks.json")

    commands = [
        hook["command"]
        for entries in hooks["hooks"].values()
        for entry in entries
        for hook in entry["hooks"]
    ]
    assert commands, "no hook commands found"

    for command in commands:
        assert command.startswith('if [ -f "${CLAUDE_PLUGIN_ROOT}/'), (
            f"hook command must guard on the resolved plugin root: {command}"
        )
        assert "${PLUGIN_ROOT" not in command, (
            "Codex's PLUGIN_ROOT must not leak into the Claude manifest — a "
            f"PLUGIN_ROOT set in the environment would pick the wrong root: {command}"
        )
