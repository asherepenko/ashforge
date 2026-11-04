import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def cmd(rel):
    return ["python3", str(ROOT / (rel + ".py"))]


def run(rel, *args, cwd=None, env=None):
    return subprocess.run(cmd(rel) + list(args), capture_output=True, text=True, cwd=cwd, env=env)


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


@pytest.mark.parametrize("args,out", [
    (["--blocking", "2"], "Quality: F (blocked) — 2 BLOCKING open; Stage 2 not run\n"),
    ([], "Quality: A — 0 Optional, 0 Nit\n"),
    (["--optional", "1"], "Quality: B — 1 Optional, 0 Nit\n"),
    (["--nit", "4", "--fyi", "9"], "Quality: B — 0 Optional, 4 Nit\n"),
    (["--optional", "3"], "Quality: C — 3 Optional, 0 Nit\n"),
    (["--spec-open", "1"], "Quality: C — 0 Optional, 0 Nit, 1 open spec finding\n"),
    (["--spec-open", "2"], "Quality: C — 0 Optional, 0 Nit, 2 open spec findings\n"),
    (["--accepted-deviation", "--optional", "1"], "Quality: D — 1 Optional, 0 Nit, accepted deviation\n"),
    (["--ladder", "pr", "--critical", "1"], "Quality: F — 1 critical, 0 important, 0 suggestion, 0 nit\n"),
    (["--ladder", "pr", "--important", "1"], "Quality: D — 0 critical, 1 important, 0 suggestion, 0 nit\n"),
    (["--ladder", "pr", "--suggestion", "3", "--info", "2"], "Quality: C — 0 critical, 0 important, 3 suggestion, 0 nit\n"),
    (["--ladder", "pr", "--nit", "4"], "Quality: B — 0 critical, 0 important, 0 suggestion, 4 nit\n"),
    (["--ladder", "severity", "--medium", "1", "--low", "2"], "Quality: B — 0 critical, 0 high, 1 medium, 2 low\n"),
])
def test_review_grade_output(args, out):
    r = run("scripts/review-grade", *args)
    assert (r.returncode, r.stdout) == (0, out)


@pytest.mark.parametrize("args", [
    ["--bogus"], ["--blocking"], ["--blocking", "x"], ["--ladder"], ["--ladder", "nope"],
    ["--ladder", "pr", "--high", "1"], ["--ladder", "severity", "--nit", "1"],
    ["--ladder", "pr", "--blocking", "1"], ["--critical", "1"],
])
def test_review_grade_usage_errors(args):
    r = run("scripts/review-grade", *args)
    assert r.returncode == 2 and r.stdout == "" and r.stderr.startswith("usage: review-grade.py")


@pytest.mark.parametrize("args,out,rc", [
    (["--score", "8"], "ok\n", 0),
    (["--score", "08"], "ok\n", 0),
    (["--score", "5", "--critical", "1"],
     "FLAG: score 5 with 1 CRITICAL; a CRITICAL caps the score at 4 (band 3-4 or lower)\n", 1),
    (["--score", "7", "--high", "2"],
     "FLAG: score 7 with 2 HIGH; a HIGH caps the score at 6 (band 5-6 or lower)\n", 1),
    (["--score", "7", "--medium", "2", "--weak", "1"],
     "FLAG: score 7 with 3 MEDIUM/WEAK; three or more cap the score at 6 (band 5-6 or lower)\n", 1),
    (["--score", "9", "--weak", "1", "--low", "5"],
     "FLAG: score 9 with 1 MEDIUM/WEAK; any cap the score at 8 (band 7-8 or lower)\n", 1),
    (["--score", "6"],
     "FLAG: score 6 with no CRITICAL, HIGH, MEDIUM or WEAK findings; a clean domain scores 7 or more (band 7-8 or higher)\n", 1),
])
def test_score_check_output(args, out, rc):
    r = run("scripts/score-check", *args)
    assert (r.returncode, r.stdout) == (rc, out)


@pytest.mark.parametrize("args", [[], ["--score"], ["--score", "0"], ["--score", "11"],
                                  ["--score", "x"], ["--score", "5", "--bogus"]])
def test_score_check_usage_errors(args):
    r = run("scripts/score-check", *args)
    assert r.returncode == 2 and r.stdout == "" and r.stderr.startswith("usage: score-check.py")


@pytest.mark.parametrize("n,bucket", [("0", "good"), ("200", "good"), ("201", "acceptable"),
                                      ("600", "acceptable"), ("601", "too-large")])
def test_change_size_classify(n, bucket):
    r = run("scripts/change-size", "--classify", n)
    assert (r.returncode, r.stdout) == (0, bucket + "\n")


@pytest.mark.parametrize("args", [[], ["--classify"], ["--classify", "x"], ["--classify", "1", "2"],
                                  ["a", "b", "c"]])
def test_change_size_usage_errors(args):
    r = run("scripts/change-size", *args)
    assert r.returncode == 2 and r.stdout == "" and r.stderr.startswith("usage: change-size.py")


def test_change_size_diff_counts_text_lines_not_binary(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "a.txt").write_text("1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "feat")
    (tmp_path / "a.txt").write_text("1\n2\n3\n")
    (tmp_path / "b.bin").write_bytes(b"\x00\x01" * 50)
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "change")
    r = run("scripts/change-size", "main", cwd=tmp_path)
    assert (r.returncode, r.stdout) == (0, "LINES=2\nBUCKET=good\n")
    r = run("scripts/change-size", "main", "feat", cwd=tmp_path)
    assert r.stdout == "LINES=2\nBUCKET=good\n"
    r = run("scripts/change-size", "nope", cwd=tmp_path)
    assert r.returncode == 2 and r.stderr == "change-size.py: unknown base 'nope'\n"
    r = run("scripts/change-size", "main", "nope", cwd=tmp_path)
    assert r.returncode == 2 and r.stderr == "change-size.py: unknown head 'nope'\n"


def test_plan_review_preflight_sections(tmp_path):
    home = tmp_path / "home"
    (home / ".claude/plans").mkdir(parents=True)
    (home / ".claude/plans/g.md").write_text("x")
    repo = tmp_path / "repo"
    (repo / ".claude/plans").mkdir(parents=True)
    (repo / ".claude/plans/l.md").write_text("x")
    (repo / "DOMAIN.md").write_text("x")
    (repo / "CONTEXT.md").write_text("x")
    (repo / "docs/adr").mkdir(parents=True)
    (repo / "docs/adr/0001.md").write_text("x")
    env = {k: v for k, v in os.environ.items() if k not in (
        "CODEX_HOME", "CLAUDECODE", "CLAUDE_PLUGIN_ROOT", "ZCODE_APP_VERSION")}
    env["HOME"] = str(home)
    r = run("skills/council-plan-review/scripts/preflight", cwd=repo, env=env)
    assert r.returncode == 0
    assert r.stdout == (
        f"== Plugin root ==\n{ROOT}\n"
        "== Local plans dir ==\n.claude/plans/l.md\n"
        f"== Global plans dir ==\n{home}/.claude/plans/g.md\n"
        "== Artifact specs (PRDs) ==\nNO_PRDS\n"
        "== Recent reviews ==\nNO_REVIEWS\n"
        "== Domain glossary ==\nDOMAIN.md\n"
        "== ADRs (most recent 20) ==\ndocs/adr/0001.md\n"
        "== Active branch ==\nNOT_A_REPO\n"
        "== Runtime capability ==\nRUNTIME=unknown\nSPAWN=unknown\nTRANSPORT=unknown\nNOTES=none\n")
