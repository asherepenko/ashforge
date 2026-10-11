import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).parents[1]


def profile(tmp_path, **overrides):
    env = {k: v for k, v in os.environ.items() if k not in (
        "CODEX_HOME", "CLAUDECODE", "CLAUDE_PLUGIN_ROOT", "ZCODE_APP_VERSION",
        "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "AVENGERS_COUNCIL_INTERACTIVE")}
    env.update(HOME=str(tmp_path), **overrides)
    result = subprocess.run(["bash", str(ROOT / "skills/council-code-review/scripts/preflight.sh")],
                            env=env, capture_output=True, text=True, check=True)
    return result.stdout


def test_claude_requires_enabled_and_verified_interactive(tmp_path):
    assert "TRANSPORT=hub" in profile(tmp_path, CLAUDECODE="1")
    assert "TRANSPORT=hub" in profile(tmp_path, CLAUDECODE="1", CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="1")
    assert "TRANSPORT=hub" in profile(tmp_path, CLAUDECODE="1", CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="1", AVENGERS_COUNCIL_INTERACTIVE="0")
    assert "TRANSPORT=stay-alive" in profile(tmp_path, CLAUDECODE="1", CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="1", AVENGERS_COUNCIL_INTERACTIVE="1")


def test_codex_modern_default_and_disable(tmp_path):
    home = tmp_path / "codex"
    home.mkdir()
    assert "SPAWN=prompt-embed" in profile(tmp_path, CODEX_HOME=str(home))
    (home / "config.toml").write_text("[agents]\nenabled = false\n")
    assert "SPAWN=none" in profile(tmp_path, CODEX_HOME=str(home))
