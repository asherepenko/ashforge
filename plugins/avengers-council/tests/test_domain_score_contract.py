"""Guard: members never pick a domain score; the orchestrator computes it.

Regression: a member wrote `DOMAIN SCORE: B` and the Round 1 table printed it.
The score now comes only from scripts/domain-score.py.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ["agents", "references", "skills", "assets", "docs"]
SCAN_FILES = ["AGENTS.md", "CLAUDE.md", "README.md"]


def scanned():
    for d in SCAN_DIRS:
        for p in (ROOT / d).rglob("*"):
            if p.is_file() and p.suffix in {".md", ".json"}:
                yield p
    for f in SCAN_FILES:
        p = ROOT / f
        if p.exists():
            yield p


def test_score_check_script_retired():
    assert not (ROOT / "scripts" / "score-check.py").exists()
    assert (ROOT / "scripts" / "domain-score.py").exists()


def test_no_member_picked_score_left():
    banned = [
        re.compile(r"score-check"),
        re.compile(r"DOMAIN SCORE:?\s*X/10"),
        re.compile(r"Final Domain Score:?\s*X/10", re.I),
        re.compile(r"Score flag", re.I),
    ]
    hits = []
    for p in scanned():
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if any(b.search(line) for b in banned):
                hits.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()[:100]}")
    assert not hits, "member-picked score text remains:\n" + "\n".join(hits)


def test_orchestrators_run_domain_score():
    for rel in ["references/orchestration-protocol.md",
                "skills/council-code-review/SKILL.md",
                "skills/council-plan-review/SKILL.md"]:
        assert "domain-score.py" in (ROOT / rel).read_text(), rel


def test_verdict_rules_band_table_is_exact():
    text = (ROOT / "references/verdict-rules.md").read_text()
    for row in ["2+ CRITICAL", "1 CRITICAL", "2+ HIGH, or 1 HIGH and 3+ MEDIUM/WEAK"]:
        assert row in text, row
