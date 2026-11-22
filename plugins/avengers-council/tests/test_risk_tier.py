import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "risk-tier.py"


def run(*args):
    return subprocess.run(["python3", str(SCRIPT), *args], capture_output=True, text=True)


@pytest.mark.parametrize("tags, out", [
    ("docs", "low — touches: docs"),
    ("docs,copy", "low — touches: docs, copy"),
    ("product", "medium — touches: product"),
    ("docs,product", "medium — touches: product"),
    ("auth", "high — touches: auth"),
    ("docs,product,secrets,ci-deploy", "high — touches: secrets, ci-deploy"),
])
def test_highest_tier_wins(tags, out):
    r = run("--touches", tags)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == out


def test_list_prints_every_tag():
    r = run("--list")
    assert r.returncode == 0
    for tag in ["docs", "product", "auth", "billing", "data-migration", "secrets"]:
        assert tag in r.stdout


@pytest.mark.parametrize("args", [[], ["--touches", ""], ["--touches", "vibes"], ["--bogus"]])
def test_bad_input_exits_2(args):
    r = run(*args)
    assert r.returncode == 2 and r.stdout == ""
