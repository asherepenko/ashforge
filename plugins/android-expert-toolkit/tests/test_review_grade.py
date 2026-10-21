import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SIBLING_ROOT = ROOT.parent / "avengers-council"
AGENTS_SCRIPTS = Path.home() / ".agents" / "scripts"


def test_high_finding_grades_d():
    r = subprocess.run(
        ["bash", str(SCRIPTS / "review-grade.sh"), "--ladder", "severity", "--high", "1"],
        capture_output=True, text=True)
    assert r.stdout.startswith("Quality: D")


@pytest.mark.parametrize("name", ["review-grade.sh", "change-size.sh"])
def test_script_matches_sibling_plugin(name):
    if not SIBLING_ROOT.exists():
        pytest.skip("avengers-council plugin not present")
    assert (SCRIPTS / name).read_bytes() == (SIBLING_ROOT / "scripts" / name).read_bytes()


@pytest.mark.parametrize("name", ["review-grade.sh", "change-size.sh"])
def test_script_matches_dotfiles_source(name):
    source = AGENTS_SCRIPTS / name
    if not source.exists():
        pytest.skip("~/.agents/scripts not present")
    assert (SCRIPTS / name).read_bytes() == source.read_bytes()
