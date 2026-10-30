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


LINK_SCRIPT = PROJECT_ROOT / "hooks" / "link-codex-agents.sh"


def test_only_codex_registers_the_link_hook():
    assert read_json(PROJECT_ROOT / ".codex-plugin" / "plugin.json")["hooks"] == "./hooks/hooks-codex.json"
    assert "hooks" not in read_json(PROJECT_ROOT / ".claude-plugin" / "plugin.json")
    assert not (PROJECT_ROOT / "hooks" / "hooks.json").exists()
    hooks = read_json(PROJECT_ROOT / "hooks" / "hooks-codex.json")["hooks"]
    assert list(hooks) == ["SessionStart"]
    assert "link-codex-agents.sh" in hooks["SessionStart"][0]["hooks"][0]["command"]


def run_link(codex_home: Path, plugin_root: Path = PROJECT_ROOT) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "HOME": str(codex_home), "CODEX_HOME": str(codex_home), "PLUGIN_ROOT": str(plugin_root)}
    return subprocess.run(["bash", str(LINK_SCRIPT)], env=env, capture_output=True, text=True, check=False)


def test_link_hook_creates_link(tmp_path):
    result = run_link(tmp_path)
    link = tmp_path / "agents" / "android-expert-toolkit"
    assert result.returncode == 0
    assert link.is_symlink()
    assert link.resolve() == (PROJECT_ROOT / "codex-agents").resolve()
    assert (link / "compose-expert.toml").is_file()


def test_link_hook_is_a_no_op_when_valid(tmp_path):
    run_link(tmp_path)
    link = tmp_path / "agents" / "android-expert-toolkit"
    before = link.lstat().st_mtime_ns
    assert run_link(tmp_path).returncode == 0
    assert link.lstat().st_mtime_ns == before


def test_link_hook_repairs_broken_or_stale_link(tmp_path):
    agents = tmp_path / "agents"
    agents.mkdir()
    link = agents / "android-expert-toolkit"
    link.symlink_to(tmp_path / "old-version" / "codex-agents")
    assert run_link(tmp_path).returncode == 0
    assert link.resolve() == (PROJECT_ROOT / "codex-agents").resolve()


def test_link_hook_never_replaces_a_real_directory(tmp_path):
    real = tmp_path / "agents" / "android-expert-toolkit"
    real.mkdir(parents=True)
    (real / "mine.toml").write_text("x", encoding="utf-8")
    result = run_link(tmp_path)
    assert result.returncode == 0
    assert not real.is_symlink()
    assert (real / "mine.toml").exists()
    assert "not a symlink" in result.stderr


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
