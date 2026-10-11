#!/usr/bin/env python3
"""Tests for runtime-generic packaging (capability profiles + fallback path)."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize("config, expected", [
    (None, "prompt-embed"),
    ("[agents]\nenabled = true\n", "prompt-embed"),
    ("[agents]\nenabled = false\n", "none"),
    ("[features]\nmulti_agent = true # legacy\n", "prompt-embed"),
    ("[features]\nmulti_agent = false\n", "none"),
    ("[features]\nmulti_agent = false\n[agents]\nenabled = true\n", "prompt-embed"),
])
def test_preflight_codex_capability_config_hints(tmp_path, config, expected):
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    if config is not None:
        (codex_home / "config.toml").write_text(config)
    env = {**os.environ, "HOME": str(tmp_path), "CODEX_HOME": str(codex_home)}
    result = subprocess.run(["bash", str(PROJECT_ROOT / "skills/aet-pipeline/scripts/preflight.sh")],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "RUNTIME=codex" in result.stdout
    assert f"SPAWN={expected}" in result.stdout
    assert "actual exposed tools" in result.stdout


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


def test_feature_build_does_not_force_setup_dependent_agents_in_parallel():
    text = read("skills/aet-pipeline/SKILL.md")
    assert "always parallel (no mutual dependency)" not in text
    assert "Parallel dispatch for `feature-build` pipelines (mandatory)" not in text
    assert "target modules" in text and "setup handoff dependency" in text


def test_runtime_contract_does_not_assume_blocking_results_or_reused_names():
    text = read("references/runtime-adapters.md") + read("skills/aet-pipeline/SKILL.md")
    assert "latest wins" not in text
    assert "results return inline" not in text
    assert "idle notifications" in text
    assert "agent ID" in text and "followup_task" in text
    assert "bounded" in text and "no close" in text


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

    version = json.loads(claude)["version"]

    assert version == json.loads(codex)["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"not semver: {version}"


def test_manifest_version_has_changelog_entry():
    """The released version is the newest CHANGELOG heading.

    Replaces a hardcoded version literal, which broke on every bump. This
    still catches a manifest bumped without a changelog entry.
    """
    version = json.loads(
        (PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    headings = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.MULTILINE)

    assert headings, "CHANGELOG.md has no version headings"
    assert headings[0] == version, (
        f"manifest is {version}, newest CHANGELOG entry is {headings[0]}"
    )
