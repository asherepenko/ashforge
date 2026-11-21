#!/usr/bin/env python3
"""Run the architecture sweep over each fixture project and check its verdict."""

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = FIXTURES.parent.parent / "skills" / "ios-conventions" / "scripts" / "detect-patterns.py"

EXPECTED = {
    "tca-app": "TCA",
    "mvvm-app": "MVVM",
    "legacy-oo-app": "MVVM",
    "mixed-app": "MIXED",
    "new-app": "NEW",
    "exactly-80-tca": "TCA",
    "exactly-80-mvvm": "MVVM",
    "observable-not-named-model": "MVVM",
    "pods-ignored-app": "MVVM",
    "tca-full-app": "TCA",
    "mvvm-observable-app": "MVVM",
    "mixed-60-40-app": "MIXED",
}


def sweep(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "architecture"], capture_output=True, text=True, timeout=30
    )


def verdict_of(result: subprocess.CompletedProcess) -> str:
    lines = [l for l in result.stdout.splitlines() if l.startswith("verdict_architecture=")]
    assert len(lines) == 1, result.stdout
    return lines[0].split("=", 1)[1]


@pytest.mark.parametrize("name,verdict", sorted(EXPECTED.items()))
def test_fixture_verdict(name, verdict):
    result = sweep(FIXTURES / name)
    assert result.returncode == 0, result.stderr
    assert verdict_of(result) == verdict


def test_every_fixture_directory_has_an_expectation():
    on_disk = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
    assert on_disk == set(EXPECTED)


def test_architecture_section_has_counts_then_one_verdict_line():
    result = sweep(FIXTURES / "mixed-app")
    assert result.stdout.splitlines()[4:] == [
        "== architecture ==",
        "count tca files=3",
        "count mvvm_observable files=1",
        "count mvvm_object files=1",
        "count mvvm files=2",
        "count uikit files=0",
        "count feature_files files=5",
        "verdict_architecture=MIXED",
    ]


def test_pods_tests_and_previews_are_ignored():
    # Pods/, *Tests/ and *Preview* files hold six reducers; counting any would flip the verdict.
    result = sweep(FIXTURES / "pods-ignored-app")
    assert verdict_of(result) == "MVVM"
    assert "count tca files=0" in result.stdout.splitlines()


def test_missing_directory_argument_fails():
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=30)
    assert result.returncode != 0


def test_negative_control_unexcluded_pods_would_change_the_verdict(tmp_path):
    # Copy the Pods fixture under a name the exclusion list does not cover and expect a different verdict.
    import shutil

    src = FIXTURES / "pods-ignored-app"
    dst = tmp_path / "app"
    shutil.copytree(src, dst)
    shutil.move(str(dst / "Pods"), str(dst / "Vendor"))
    assert verdict_of(sweep(dst)) != "MVVM"
