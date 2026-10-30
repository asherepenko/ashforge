#!/usr/bin/env python3
"""Tests for the Claude-side hook that links the agents into Cursor."""

import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
LINK_SCRIPT = PROJECT_ROOT / "hooks" / "link-cursor-agents.sh"
AGENTS = sorted(p.name for p in (PROJECT_ROOT / "agents").glob("*.md"))


def run_link(home: Path, plugin_root: Path = PROJECT_ROOT) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(plugin_root)}
    return subprocess.run(["bash", str(LINK_SCRIPT)], env=env, capture_output=True, text=True, check=False)


def test_claude_registers_only_the_cursor_link_hook():
    hooks = json.loads((PROJECT_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    assert list(hooks) == ["SessionStart"]
    assert "link-cursor-agents.sh" in hooks["SessionStart"][0]["hooks"][0]["command"]


def test_no_cursor_home_means_no_op(tmp_path):
    assert run_link(tmp_path).returncode == 0
    assert not (tmp_path / ".cursor").exists()


def test_links_every_agent(tmp_path):
    (tmp_path / ".cursor").mkdir()
    assert run_link(tmp_path).returncode == 0
    agents = tmp_path / ".cursor" / "agents"
    assert sorted(p.name for p in agents.iterdir()) == AGENTS
    for name in AGENTS:
        assert (agents / name).is_symlink()
        assert (agents / name).resolve() == (PROJECT_ROOT / "agents" / name).resolve()


def test_no_op_when_valid(tmp_path):
    (tmp_path / ".cursor").mkdir()
    run_link(tmp_path)
    link = tmp_path / ".cursor" / "agents" / AGENTS[0]
    before = link.lstat().st_mtime_ns
    assert run_link(tmp_path).returncode == 0
    assert link.lstat().st_mtime_ns == before


def test_repairs_stale_link_and_drops_removed_agent(tmp_path):
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    old = tmp_path / "cache" / "android-expert-toolkit" / "4.0.0" / "agents"
    stale = agents / AGENTS[0]
    stale.symlink_to(old / AGENTS[0])
    gone = agents / "retired-agent.md"
    gone.symlink_to(old / "retired-agent.md")
    assert run_link(tmp_path).returncode == 0
    assert stale.resolve() == (PROJECT_ROOT / "agents" / AGENTS[0]).resolve()
    assert not gone.is_symlink()


def test_never_replaces_a_real_file_or_foreign_link(tmp_path):
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / AGENTS[0]).write_text("mine", encoding="utf-8")
    foreign = agents / "other.md"
    foreign.symlink_to(tmp_path / "nowhere.md")
    result = run_link(tmp_path)
    assert result.returncode == 0
    assert (agents / AGENTS[0]).read_text(encoding="utf-8") == "mine"
    assert "not a symlink" in result.stderr
    assert foreign.is_symlink()
