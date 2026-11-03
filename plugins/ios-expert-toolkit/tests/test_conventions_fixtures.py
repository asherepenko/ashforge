#!/usr/bin/env python3
"""Run the architecture sweep over each fixture project and check its verdict."""

import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = FIXTURES / "run-sweeps.sh"

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
}


def sweep(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(path)], capture_output=True, text=True, timeout=30
    )


@pytest.mark.parametrize("name,verdict", sorted(EXPECTED.items()))
def test_fixture_verdict(name, verdict):
    result = sweep(FIXTURES / name)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == verdict


def test_every_fixture_directory_has_an_expectation():
    on_disk = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
    assert on_disk == set(EXPECTED)


def test_stdout_is_exactly_one_verdict_line():
    result = sweep(FIXTURES / "mixed-app")
    assert result.stdout.splitlines() == ["MIXED"]


def test_pods_tests_and_previews_are_ignored():
    # Pods/, *Tests/ and *Preview* files hold six reducers; counting any would flip the verdict.
    assert sweep(FIXTURES / "pods-ignored-app").stdout.strip() == "MVVM"
    assert "tca=0" in sweep(FIXTURES / "pods-ignored-app").stderr


def test_missing_directory_argument_fails():
    result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, timeout=30)
    assert result.returncode != 0


def test_negative_control_unexcluded_pods_would_change_the_verdict(tmp_path):
    # Copy the Pods fixture under a name the exclusion list does not cover and expect a different verdict.
    import shutil

    src = FIXTURES / "pods-ignored-app"
    dst = tmp_path / "app"
    shutil.copytree(src, dst)
    shutil.move(str(dst / "Pods"), str(dst / "Vendor"))
    assert sweep(dst).stdout.strip() != "MVVM"
