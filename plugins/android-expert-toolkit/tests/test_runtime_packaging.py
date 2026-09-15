#!/usr/bin/env python3
"""Tests for runtime-generic packaging (capability profiles + fallback path)."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_runtime_adapter_files_replaced_codex_files():
    assert (PROJECT_ROOT / "references" / "runtime-adapters.md").exists()
    assert (PROJECT_ROOT / "references" / "runtime-fallback.md").exists()
    for legacy in ["codex-tools.md", "codex-fallback.md"]:
        assert not (PROJECT_ROOT / "references" / legacy).exists(), legacy


def test_pipeline_skill_references_capability_profiles():
    text = read("skills/aet-pipeline/SKILL.md")

    assert "references/runtime-adapters.md" in text
    assert "references/runtime-fallback.md" in text
    assert "== Runtime capability ==" in text
    assert "Codex multi_agent capability" not in text
    assert "SPAWN=none" in text


def test_unattended_decision_point_rule():
    text = read("skills/aet-pipeline/SKILL.md")

    assert "Unattended runs (user unavailable):" in text
    assert "DP2 always pauses" in text
    assert "Never choose Abort or Skip-validation autonomously" in text


def test_pipeline_preflight_emits_capability_profile():
    text = read("skills/aet-pipeline/scripts/preflight.sh")

    assert "== Runtime capability ==" in text
    assert "RUNTIME=$runtime" in text
    assert "SPAWN=$spawn" in text
    # definitive env markers before install-dir heuristics
    zcode_idx = text.index("ZCODE_APP_VERSION")
    claude_idx = text.index("CLAUDECODE")
    codex_dir_idx = text.index('elif [ -d "$HOME/.codex" ]')
    assert zcode_idx < codex_dir_idx
    assert claude_idx < codex_dir_idx


def test_pipeline_skill_resolves_plugin_root_without_env_var():
    text = read("skills/aet-pipeline/SKILL.md")

    assert "ZCODE_PLUGIN_ROOT" in text
    assert ".zcode/cli/plugins/cache" in text


def test_manifest_versions_match():
    claude = (PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    codex = (PROJECT_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")

    assert json.loads(claude)["version"] == json.loads(codex)["version"]
    assert json.loads(claude)["version"] == "3.3.1"
