"""Preflight finds the plugin root from its own file and prints it."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "skills" / "council-plan-review" / "scripts" / "preflight.py",
    ROOT / "skills" / "council-code-review" / "scripts" / "preflight.py",
]
ROOT_VARS = ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "ZCODE_PLUGIN_ROOT", "CLAUDECODE")


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.parent.parent.name)
def test_preflight_prints_plugin_root_from_any_cwd(script, tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ROOT_VARS}
    env["HOME"] = str(tmp_path / "home")
    out = subprocess.run(["python3", str(script)], cwd=tmp_path, env=env,
                         capture_output=True, text=True, check=True).stdout
    lines = out.splitlines()
    assert "== Plugin root ==" in lines
    assert lines[lines.index("== Plugin root ==") + 1] == str(ROOT)
