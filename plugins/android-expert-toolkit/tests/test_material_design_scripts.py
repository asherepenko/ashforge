#!/usr/bin/env python3
"""Behavior pins for the android-material-design resolve-doc and fetch-doc scripts."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "skills" / "android-material-design" / "scripts"
RESOLVE = SCRIPTS / "resolve-doc.py"
FETCH = SCRIPTS / "fetch-doc.py"
BASE = "https://raw.githubusercontent.com/material-components/material-components-android/master/docs/"


def run(script: Path, *args: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        check=False,
    )


def key(out: str, name: str) -> str:
    for line in out.splitlines():
        if line.startswith(name + "="):
            return line[len(name) + 1 :]
    return ""


@pytest.mark.parametrize(
    ("query", "doc"),
    [
        ("topappbar", "components/TopAppBar.md"),
        ("button", "components/CommonButton.md"),
        ("Buttons", "components/CommonButton.md"),
        ("Extended FAB", "components/ExtendedFloatingActionButton.md"),
        ("fab", "components/FloatingActionButton.md"),
        ("text-field", "components/TextField.md"),
        ("Color", "theming/Color.md"),
        ("predictive back", "foundations/PredictiveBack.md"),
        ("canonical layouts", "adaptive/CanonicalLayouts.md"),
        ("getting started", "getting-started.md"),
        ("dark", "theming/Dark.md"),
    ],
)
def test_resolve_maps_alias_to_doc_url(tmp_path, query, doc):
    r = run(RESOLVE, query, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert key(r.stdout, "URL") == BASE + doc


def test_resolve_labels_component_and_theming_pages(tmp_path):
    assert key(run(RESOLVE, "topappbar", cwd=tmp_path).stdout, "LABEL") == "material-TopAppBar"
    assert key(run(RESOLVE, "Color", cwd=tmp_path).stdout, "LABEL") == "material-theming-Color"


def test_resolve_ambiguous_unknown_and_catalog(tmp_path):
    r = run(RESOLVE, "picker", cwd=tmp_path)
    assert r.returncode == 3
    assert "CANDIDATE=DatePicker" in r.stdout and "CANDIDATE=TimePicker" in r.stdout
    assert run(RESOLVE, "nonexistentwidget", cwd=tmp_path).returncode == 4
    r = run(RESOLVE, cwd=tmp_path)
    assert r.returncode == 0
    assert "components\tTopAppBar\tTopAppBar.md" in r.stdout
    assert "Typography" in r.stdout


DOC = (
    "# Top app bars\n![hero](assets/topappbar/hero.png)\n## Using top app bars\nIntro text.\n"
    "```xml\n<!-- # not a heading inside a fence -->\n# fenced hash\n"
    "<com.google.android.material.appbar.MaterialToolbar />\n```\n"
    "### Collapsing toolbar\nUse CollapsingToolbarLayout.\n## Theming\nTheme overlay text.\n"
    '<img src="assets/x.png" alt="x">\n'
)


@pytest.fixture
def doc_env(tmp_path):
    doc = tmp_path / "TopAppBar.md"
    doc.write_text(DOC)
    return {"MATERIAL_DOC_FILE": str(doc)}


def test_fetch_full_doc_strips_images(tmp_path, doc_env):
    r = run(FETCH, "topappbar", cwd=tmp_path, env=doc_env)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split("\n", 1)[0] == "SOURCE=" + BASE + "components/TopAppBar.md"
    assert "Theme overlay text." in r.stdout
    assert "hero.png" not in r.stdout
    assert "<img" not in r.stdout


def test_fetch_toc_skips_fenced_hashes(tmp_path, doc_env):
    r = run(FETCH, "topappbar", "--toc", cwd=tmp_path, env=doc_env)
    assert r.returncode == 0
    assert "### Collapsing toolbar" in r.stdout
    assert "fenced hash" not in r.stdout
    assert "Intro text." not in r.stdout


def test_fetch_section_keeps_children_stops_at_sibling(tmp_path, doc_env):
    r = run(FETCH, "topappbar", "--section", "using top", cwd=tmp_path, env=doc_env)
    assert r.returncode == 0
    assert "MaterialToolbar />" in r.stdout
    assert "Use CollapsingToolbarLayout." in r.stdout
    assert "Theme overlay text." not in r.stdout


def test_fetch_exit_codes(tmp_path, doc_env):
    r = run(FETCH, "topappbar", "--section", "nosuchthing", cwd=tmp_path, env=doc_env)
    assert r.returncode == 6
    assert "## Theming" in r.stdout
    assert run(FETCH, "nosuchcomponent", cwd=tmp_path, env=doc_env).returncode == 4
    r = run(FETCH, "nav", cwd=tmp_path, env=doc_env)
    assert r.returncode == 3
    assert "CANDIDATE=" in r.stdout
    r = run(FETCH, "topappbar", cwd=tmp_path, env={"MATERIAL_DOC_FILE": str(tmp_path / "missing.md")})
    assert r.returncode == 5
    assert "TopAppBar.md" in r.stderr
