#!/usr/bin/env python3
"""Pin the observable behavior of the link hooks and the sweep script: silence, exit codes, stderr."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODEX_LINK = PROJECT_ROOT / "hooks" / "link-codex-agents.py"
CURSOR_LINK = PROJECT_ROOT / "hooks" / "link-cursor-agents.py"
SWEEPS = PROJECT_ROOT / "tests" / "fixtures" / "run-sweeps.py"
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"


def run(script: Path, args=(), env=None):
    return subprocess.run([sys.executable, str(script), *args], env=env, capture_output=True, text=True, timeout=30, check=False)


def codex_env(home: Path, root: Path = PROJECT_ROOT) -> dict:
    return {"PATH": "/usr/bin:/bin", "HOME": str(home), "CODEX_HOME": str(home), "PLUGIN_ROOT": str(root)}


def cursor_env(home: Path, root: Path = PROJECT_ROOT) -> dict:
    return {"PATH": "/usr/bin:/bin", "HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(root)}


def test_scripts_are_executable():
    for script in (CODEX_LINK, CURSOR_LINK, SWEEPS):
        assert os.access(script, os.X_OK), script


def test_codex_hook_is_silent_on_success(tmp_path):
    result = run(CODEX_LINK, env=codex_env(tmp_path))
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    again = run(CODEX_LINK, env=codex_env(tmp_path))
    assert (again.returncode, again.stdout, again.stderr) == (0, "", "")


def test_codex_hook_does_nothing_without_codex_agents_dir(tmp_path):
    root = tmp_path / "plugin"
    root.mkdir()
    home = tmp_path / "home"
    result = run(CODEX_LINK, env=codex_env(home, root))
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert not home.exists()


def test_codex_hook_defaults_to_home_dot_codex(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "PLUGIN_ROOT": str(PROJECT_ROOT)}
    assert run(CODEX_LINK, env=env).returncode == 0
    assert (tmp_path / ".codex" / "agents" / "ios-expert-toolkit").is_symlink()


def test_codex_hook_reports_but_survives_an_unwritable_agents_dir(tmp_path):
    blocker = tmp_path / "agents"
    blocker.write_text("a file where the directory should be", encoding="utf-8")
    result = run(CODEX_LINK, env=codex_env(tmp_path))
    assert result.returncode == 0
    assert result.stdout == ""
    assert blocker.read_text(encoding="utf-8") == "a file where the directory should be"


def test_cursor_hook_is_silent_on_success(tmp_path):
    (tmp_path / ".cursor").mkdir()
    result = run(CURSOR_LINK, env=cursor_env(tmp_path))
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    again = run(CURSOR_LINK, env=cursor_env(tmp_path))
    assert (again.returncode, again.stdout, again.stderr) == (0, "", "")


def test_cursor_hook_does_nothing_without_agents_dir_in_plugin(tmp_path):
    root = tmp_path / "plugin"
    root.mkdir()
    (tmp_path / ".cursor").mkdir()
    result = run(CURSOR_LINK, env=cursor_env(tmp_path, root))
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert not (tmp_path / ".cursor" / "agents").exists()


def test_cursor_hook_honors_cursor_home(tmp_path):
    cursor_home = tmp_path / "elsewhere"
    cursor_home.mkdir()
    env = cursor_env(tmp_path) | {"CURSOR_HOME": str(cursor_home)}
    assert run(CURSOR_LINK, env=env).returncode == 0
    assert any((cursor_home / "agents").glob("*.md"))
    assert not (tmp_path / ".cursor").exists()


def test_cursor_hook_keeps_a_resolving_link_of_another_version_when_the_agent_still_exists(tmp_path):
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    other = tmp_path / "cache" / "ios-expert-toolkit" / "0.9.0" / "agents" / "kept-agent.md"
    other.parent.mkdir(parents=True)
    other.write_text("x", encoding="utf-8")
    kept = agents / "kept-agent.md"
    kept.symlink_to(other)
    result = run(CURSOR_LINK, env=cursor_env(tmp_path))
    assert result.returncode == 0
    assert kept.readlink() == other


def test_cursor_hook_ignores_non_markdown_entries(tmp_path):
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    note = agents / "notes.txt"
    note.write_text("n", encoding="utf-8")
    dangling = agents / "dangling.txt"
    dangling.symlink_to(tmp_path / "cache" / "ios-expert-toolkit" / "0.9.0" / "agents" / "dangling.txt")
    assert run(CURSOR_LINK, env=cursor_env(tmp_path)).returncode == 0
    assert note.read_text(encoding="utf-8") == "n"
    assert dangling.is_symlink()


def test_cursor_hook_survives_an_unwritable_agents_dir(tmp_path):
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "agents").write_text("a file", encoding="utf-8")
    result = run(CURSOR_LINK, env=cursor_env(tmp_path))
    assert result.returncode == 0
    assert result.stdout == ""
    assert "cannot create" in result.stderr


def test_sweeps_stderr_reports_the_counts():
    result = run(SWEEPS, [str(FIXTURES / "mixed-app")])
    assert re.fullmatch(r"tca=\d+ mvvm=\d+ uikit=\d+ feature_files=\d+\n", result.stderr)
    assert result.stdout == "MIXED\n"


def test_sweeps_counts_for_new_app_and_pods_fixture():
    assert run(SWEEPS, [str(FIXTURES / "new-app")]).stderr == "tca=0 mvvm=0 uikit=0 feature_files=0\n"
    pods = run(SWEEPS, [str(FIXTURES / "pods-ignored-app")]).stderr
    assert pods.startswith("tca=0 mvvm=")


def test_sweeps_missing_directory_fails_with_usage():
    result = run(SWEEPS)
    assert result.returncode != 0
    assert "usage" in result.stderr
    assert result.stdout == ""


def test_sweeps_nonexistent_directory_fails(tmp_path):
    result = run(SWEEPS, [str(tmp_path / "nope")])
    assert result.returncode != 0
    assert result.stdout == ""


def test_sweeps_empty_directory_is_new(tmp_path):
    result = run(SWEEPS, [str(tmp_path)])
    assert result.returncode == 0
    assert result.stdout == "NEW\n"
    assert result.stderr == "tca=0 mvvm=0 uikit=0 feature_files=0\n"


def test_sweeps_classifies_uikit_and_counts_a_file_once(tmp_path):
    (tmp_path / "A.swift").write_text("final class A: UIViewController {}\n", encoding="utf-8")
    (tmp_path / "B.swift").write_text("@Observable\nclass B: ObservableObject {}\n", encoding="utf-8")
    result = run(SWEEPS, [str(tmp_path)])
    assert result.stdout == "MVVM\n"
    assert result.stderr == "tca=0 mvvm=1 uikit=1 feature_files=2\n"


def test_sweeps_skips_main_and_contentview_when_counting_features(tmp_path):
    (tmp_path / "ContentView.swift").write_text("struct ContentView {}\n", encoding="utf-8")
    (tmp_path / "App.swift").write_text("@main struct App {}\n", encoding="utf-8")
    (tmp_path / "Thing.swift").write_text("struct Thing {}\n", encoding="utf-8")
    result = run(SWEEPS, [str(tmp_path)])
    assert result.stdout == "MIXED\n"
    assert result.stderr == "tca=0 mvvm=0 uikit=0 feature_files=1\n"
