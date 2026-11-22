import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verdict.py"


def run(*args):
    return subprocess.run(["python3", str(SCRIPT), *args], capture_output=True, text=True)


def v(mode="full", approve=0, concerns=0, reject=0, critical=0, high=0,
      red_lines=0, standards=0, veto=False):
    args = ["--mode", mode, "--approve", str(approve), "--concerns", str(concerns),
            "--reject", str(reject), "--critical", str(critical), "--high", str(high),
            "--red-lines", str(red_lines), "--standards", str(standards)]
    if veto:
        args.append("--veto")
    r = run(*args)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.mark.parametrize("kw, head", [
    # full mode, 9 voters: majority 5, BLOCKED threshold 4
    (dict(approve=9), "APPROVED"),
    (dict(approve=5, concerns=4), "APPROVED"),
    (dict(approve=5, concerns=4, high=2), "APPROVED WITH CONDITIONS"),
    (dict(approve=4, concerns=5), "APPROVED WITH CONDITIONS"),
    (dict(approve=5, concerns=3, reject=1), "APPROVED WITH CONDITIONS"),
    (dict(approve=3, concerns=6), "NO CONSENSUS"),
    (dict(concerns=9, high=3), "NO CONSENSUS"),
    (dict(approve=6, concerns=1, reject=2), "NEEDS REVISION"),
    (dict(approve=9, critical=1), "NEEDS REVISION"),
    (dict(approve=9, red_lines=1), "NEEDS REVISION"),
    (dict(approve=9, standards=1), "NEEDS REVISION"),
    (dict(approve=5, reject=4), "BLOCKED"),
    (dict(approve=9, veto=True), "BLOCKED"),
    (dict(approve=9, standards=2), "BLOCKED"),
    # quick mode, 3 voters
    (dict(mode="quick", approve=3), "APPROVED"),
    (dict(mode="quick", approve=3, high=1), "APPROVED WITH CONDITIONS"),
    (dict(mode="quick", approve=2, concerns=1), "APPROVED WITH CONDITIONS"),
    (dict(mode="quick", approve=1, concerns=2), "NEEDS REVISION"),
    (dict(mode="quick", approve=3, critical=1), "NEEDS REVISION"),
    (dict(mode="quick", approve=2, reject=1), "BLOCKED"),
    (dict(mode="quick", approve=3, veto=True), "BLOCKED"),
])
def test_verdict_table(kw, head):
    out = v(**kw)
    assert out.split(" — ")[0] == head, out


def test_conditions_name_high_count():
    assert v(approve=4, concerns=5, high=2) == "APPROVED WITH CONDITIONS — 2 HIGH as conditions"


def test_blocked_names_reason():
    assert v(approve=9, veto=True) == "BLOCKED — Black Widow veto"


def test_ten_voters_use_floor_thresholds():
    # N=10: majority 6, BLOCKED threshold 4
    assert v(approve=5, concerns=5) == "APPROVED WITH CONDITIONS — 0 HIGH as conditions"
    assert v(approve=6, concerns=4) == "APPROVED"


@pytest.mark.parametrize("args", [
    ["--mode", "full"],
    ["--mode", "lazy", "--approve", "3"],
    ["--mode", "quick", "--approve", "2"],
    ["--mode", "full", "--approve", "x"],
    ["--mode", "full", "--approve", "3", "--bogus", "1"],
])
def test_bad_input_exits_2(args):
    r = run(*args)
    assert r.returncode == 2 and r.stdout == ""


def test_missing_acceptance_criteria_force_revision():
    for mode, votes in (("full", ["--approve", "9", "--concerns", "0", "--reject", "0"]),
                        ("quick", ["--approve", "3", "--concerns", "0", "--reject", "0"])):
        r = run("--mode", mode, *votes, "--missing-ac", "1")
        assert r.stdout.strip() == "NEEDS REVISION — 1 missing acceptance criteria", r.stdout + r.stderr


@pytest.mark.parametrize("approve, concerns", [(2, 0), (1, 1), (1, 0)])
def test_small_full_roster_never_blocks_without_reject(approve, concerns):
    # Timed-out members don't vote, so N can shrink below 9. The threshold
    # floor(N*0.45) is 0 for N<=2; zero REJECT votes must never block.
    assert not v(approve=approve, concerns=concerns).startswith("BLOCKED")


def test_small_full_roster_one_reject_blocks():
    assert v(approve=2, reject=1).startswith("BLOCKED")
