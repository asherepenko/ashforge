#!/usr/bin/env python3
"""Tests for runtime-generic packaging (capability profiles + degradation path)."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def test_runtime_adapter_files_replaced_codex_files():
    assert (PROJECT_ROOT / "references" / "runtime-adapters.md").exists()
    assert (PROJECT_ROOT / "references" / "runtime-fallback.md").exists()
    for legacy in ["codex-tools.md", "codex-fallback.md", "codex-runtime-notes.md"]:
        assert not (PROJECT_ROOT / "references" / legacy).exists(), legacy


def test_orchestration_protocol_documents_cost_controlled_degradation():
    text = read("references/orchestration-protocol.md")

    assert "## Mode Selection & Cost-Controlled Degradation" in text
    assert "Cost-Controlled Quick Mode (autonomous downgrade)" in text
    assert "**Capability trigger:**" in text
    assert "**Proportionality trigger:**" in text
    assert "**Availability trigger:**" in text
    assert "### Mandatory disclosure" in text
    assert "Run mode: Quick Mode — cost-controlled degradation from Full Council" in text
    # No stale runtime-name branching annotations left in the protocol
    assert "**Codex:**" not in text
    assert "**Claude:**" not in text


def test_skills_reference_runtime_adapters_and_mode_selection():
    for skill in [
        "skills/council-plan-review/SKILL.md",
        "skills/council-code-review/SKILL.md",
    ]:
        text = read(skill)
        assert "references/runtime-adapters.md" in text, skill
        assert "references/runtime-fallback.md" in text, skill
        assert "orchestration-protocol.md#mode-selection--cost-controlled-degradation" in text, skill
        assert "== Runtime capability ==" in text, skill
        assert "Codex multi_agent capability" not in text, skill
        # silent-downgrade guard
        assert "three-trigger cost-controlled disclosure" in text, skill


def test_preflight_emits_capability_profile():
    for script in [
        "skills/council-plan-review/scripts/preflight.sh",
        "skills/council-code-review/scripts/preflight.sh",
    ]:
        text = read(script)
        assert "== Runtime capability ==" in text, script
        assert "RUNTIME=$runtime" in text, script
        assert "SPAWN=$spawn" in text, script
        assert "TRANSPORT=$transport" in text, script
        # definitive env markers before install-dir heuristics
        zcode_idx = text.index("ZCODE_APP_VERSION")
        claude_idx = text.index("CLAUDECODE")
        codex_dir_idx = text.index('elif [ -d "$HOME/.codex" ]')
        assert zcode_idx < codex_dir_idx
        assert claude_idx < codex_dir_idx


def test_verdict_template_has_run_mode_disclosure():
    text = read("assets/verdict-template.md")

    assert "## Run Mode" in text
    assert "cost-controlled degradation" in text
    assert "Single-orchestrator fallback" in text


def test_skills_resolve_plugin_root_without_env_var():
    """Runtimes without a plugin-root env var install into a versioned cache."""
    for skill in [
        "skills/council-plan-review/SKILL.md",
        "skills/council-code-review/SKILL.md",
    ]:
        text = read(skill)
        assert "ZCODE_PLUGIN_ROOT" in text, skill
        assert ".zcode/cli/plugins/cache" in text, skill


def test_manifest_versions_match():
    claude = (PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    codex = (PROJECT_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")

    import json

    assert json.loads(claude)["version"] == json.loads(codex)["version"]
    assert json.loads(claude)["version"] == "3.3.0"
