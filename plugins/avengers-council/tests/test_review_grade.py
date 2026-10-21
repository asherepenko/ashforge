import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SIBLING_ROOT = ROOT.parent / "android-expert-toolkit"
AGENTS_SCRIPTS = Path.home() / ".agents" / "scripts"


def grade(*args):
    return subprocess.run(
        ["bash", str(SCRIPTS / "review-grade.sh"), "--ladder", "severity", *args],
        capture_output=True, text=True)


def test_critical_finding_grades_f():
    r = grade("--critical", "1")
    assert r.stdout.startswith("Quality: F")


def test_high_finding_grades_d():
    assert grade("--high", "1").stdout.startswith("Quality: D")


def test_three_medium_findings_grade_c():
    assert grade("--medium", "3").stdout.startswith("Quality: C")


def test_one_medium_finding_grades_b():
    assert grade("--medium", "1").stdout.startswith("Quality: B")


def test_four_low_findings_grade_b():
    assert grade("--low", "4").stdout.startswith("Quality: B")


def test_three_low_findings_grade_a():
    assert grade("--low", "3").stdout.startswith("Quality: A")


@pytest.mark.parametrize("name", ["review-grade.sh", "change-size.sh"])
def test_script_matches_sibling_plugin(name):
    if not SIBLING_ROOT.exists():
        pytest.skip("android-expert-toolkit plugin not present")
    assert (SCRIPTS / name).read_bytes() == (SIBLING_ROOT / "scripts" / name).read_bytes()


@pytest.mark.parametrize("name", ["review-grade.sh", "change-size.sh"])
def test_script_matches_dotfiles_source(name):
    source = AGENTS_SCRIPTS / name
    if not source.exists():
        pytest.skip("~/.agents/scripts not present")
    assert (SCRIPTS / name).read_bytes() == source.read_bytes()
