import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "domain-score.py"


def run(*args):
    return subprocess.run(["python3", str(SCRIPT), *args], capture_output=True, text=True)


def score(critical=0, high=0, medium=0, low=0, weak=0):
    return run("--critical", str(critical), "--high", str(high), "--medium", str(medium),
               "--low", str(low), "--weak", str(weak))


@pytest.mark.parametrize("counts, expected", [
    ({}, "10/10"),
    ({"low": 5}, "10/10"),
    ({"medium": 1}, "8/10"),
    ({"weak": 1}, "8/10"),
    ({"medium": 1, "weak": 1}, "7/10"),
    ({"medium": 3}, "6/10"),
    ({"medium": 2, "weak": 1}, "6/10"),
    ({"high": 1}, "6/10"),
    ({"high": 1, "medium": 2}, "6/10"),
    ({"high": 1, "medium": 3}, "5/10"),
    ({"high": 2}, "5/10"),
    ({"critical": 1}, "3/10"),
    ({"critical": 1, "high": 4}, "3/10"),
    ({"critical": 2}, "1/10"),
])
def test_counts_give_one_exact_score(counts, expected):
    r = score(**counts)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == expected


def test_low_never_lowers_score():
    assert score(medium=1, low=9).stdout.strip() == score(medium=1).stdout.strip()


@pytest.mark.parametrize("args", [
    ["--high", "x"],
    ["--high", "-1"],
    ["--bogus", "1"],
    ["--high"],
])
def test_bad_input_exits_2(args):
    r = run(*args)
    assert r.returncode == 2
    assert r.stdout == ""


def test_average_of_scores():
    r = run("--average", "6/10", "5/10", "8/10")
    assert r.returncode == 0
    assert r.stdout.strip() == "6.3/10"


def test_average_skips_na():
    assert run("--average", "6/10", "n/a", "8/10").stdout.strip() == "7.0/10"


def test_average_all_na():
    assert run("--average", "n/a").stdout.strip() == "n/a"


def test_average_rejects_letter_grade():
    r = run("--average", "6/10", "B")
    assert r.returncode == 2
