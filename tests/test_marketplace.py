"""Marketplace wiring: every plugin is listed in both marketplaces with a consistent version."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def plugin_dirs(root=ROOT):
    return sorted(p.parent.parent for p in (root / "plugins").glob("*/.claude-plugin/plugin.json"))


def load(path):
    return json.loads(Path(path).read_text())


def claude_entries(root=ROOT):
    return {e["name"]: e for e in load(root / ".claude-plugin/marketplace.json")["plugins"]}


def codex_entries(root=ROOT):
    return {e["name"]: e for e in load(root / ".agents/plugins/marketplace.json")["plugins"]}


def changelog_version(plugin_dir):
    text = (plugin_dir / "CHANGELOG.md").read_text()
    m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, re.M)
    return m.group(1) if m else None


def problems(root=ROOT):
    out = []
    claude, codex = claude_entries(root), codex_entries(root)
    for d in plugin_dirs(root):
        name = d.name
        version = load(d / ".claude-plugin/plugin.json")["version"]
        if name not in claude:
            out.append(f"{name}: missing from claude marketplace")
        elif claude[name].get("version") != version:
            out.append(f"{name}: claude marketplace version {claude[name].get('version')} != {version}")
        if name not in codex:
            out.append(f"{name}: missing from codex marketplace")
        codex_manifest = d / ".codex-plugin/plugin.json"
        if codex_manifest.exists() and load(codex_manifest)["version"] != version:
            out.append(f"{name}: codex manifest version differs from {version}")
        if changelog_version(d) != version:
            out.append(f"{name}: newest changelog heading {changelog_version(d)} != {version}")
    return out


def test_marketplaces_and_versions_consistent():
    assert problems() == []


def test_plugins_found():
    assert {"android-expert-toolkit", "ios-expert-toolkit", "avengers-council"} <= {d.name for d in plugin_dirs()}


def test_negative_control_detects_drift(tmp_path):
    import shutil

    shutil.copytree(ROOT / ".claude-plugin", tmp_path / ".claude-plugin")
    shutil.copytree(ROOT / ".agents", tmp_path / ".agents")
    shutil.copytree(ROOT / "plugins", tmp_path / "plugins", ignore=shutil.ignore_patterns("skills", "tests", ".pytest_cache"))
    assert problems(tmp_path) == []
    mp = tmp_path / ".claude-plugin/marketplace.json"
    data = load(mp)
    data["plugins"] = [e for e in data["plugins"] if e["name"] != "ios-expert-toolkit"]
    data["plugins"][0]["version"] = "0.0.0"
    mp.write_text(json.dumps(data))
    found = problems(tmp_path)
    assert any("ios-expert-toolkit: missing from claude" in p for p in found)
    assert any("0.0.0" in p for p in found)
