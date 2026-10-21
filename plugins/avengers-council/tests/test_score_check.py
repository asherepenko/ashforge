import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "score-check.sh"


def check(score, critical=0, high=0, medium=0, low=0, weak=0):
    return subprocess.run(
        ["bash", str(SCRIPT), "--score", str(score), "--critical", str(critical),
         "--high", str(high), "--medium", str(medium), "--low", str(low), "--weak", str(weak)],
        capture_output=True, text=True)


def test_high_finding_caps_score_at_six():
    r = check(8, high=1)
    assert r.returncode == 1
    assert r.stdout.startswith("FLAG: ")
    assert check(6, high=1).returncode == 0


def test_critical_caps_score_at_four():
    assert check(5, critical=1).returncode == 1
    assert check(4, critical=1).returncode == 0


def test_clean_domain_needs_seven_or_more():
    assert check(6).returncode == 1
    assert check(7).returncode == 0


def test_medium_or_weak_caps_score_at_eight():
    assert check(9, weak=1).returncode == 1
    assert check(8, medium=1).returncode == 0


def test_three_medium_or_weak_caps_score_at_six():
    assert check(7, medium=2, weak=1).returncode == 1


def test_low_findings_never_flag():
    assert check(10, low=5).returncode == 0


def test_bad_input_is_usage_error():
    assert check(11).returncode == 2
