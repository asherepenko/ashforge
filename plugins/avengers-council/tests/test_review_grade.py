import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def grade(*args):
    return subprocess.run(
        ["python3", str(SCRIPTS / "review-grade.py"), "--ladder", "severity", *args],
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
