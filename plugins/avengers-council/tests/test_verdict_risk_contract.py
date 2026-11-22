"""Guard: Captain America never applies the consensus rules or picks the Risk
tier by hand; verdict.py and risk-tier.py compute both."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATORS = ["references/orchestration-protocol.md",
                 "skills/council-code-review/SKILL.md",
                 "skills/council-plan-review/SKILL.md",
                 "references/runtime-fallback.md"]


def text(rel):
    return (ROOT / rel).read_text()


def test_orchestrators_run_both_scripts():
    for rel in ORCHESTRATORS:
        t = text(rel)
        assert "scripts/verdict.py" in t, rel
        assert "scripts/risk-tier.py" in t, rel


def test_verdict_rules_point_at_scripts():
    t = text("references/verdict-rules.md")
    assert "scripts/verdict.py" in t
    assert "scripts/risk-tier.py" in t
    assert "NO CONSENSUS" in t


def test_risk_tags_documented():
    spec = importlib.util.spec_from_file_location("rt", ROOT / "scripts" / "risk-tier.py")
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    t = text("references/verdict-rules.md")
    for tag in rt.TIER_OF:
        assert f"`{tag}`" in t, tag


def test_template_has_risk_tags_line():
    assert "risk-tier.py" in text("assets/verdict-template.md")
