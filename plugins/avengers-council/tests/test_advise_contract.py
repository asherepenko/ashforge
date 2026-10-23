import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "skills" / "council-advise" / "SKILL.md"


def skill():
    return SKILL_PATH.read_text()


def test_skill_exists_with_matching_name():
    text = skill()
    front = text.split("---", 2)[1]
    assert re.search(r"^name: council-advise$", front, re.MULTILINE)
    assert "argument-hint:" in front
    assert "council-plan-review" in front and "council-code-review" in front


def test_skill_reuses_runtime_scaffolding():
    text = skill()
    assert "references/runtime-adapters.md" in text
    assert "references/runtime-fallback.md" in text
    assert "== Runtime capability ==" in text
    assert "ZCODE_PLUGIN_ROOT" in text
    assert ".zcode/cli/plugins/cache" in text
    assert "skills/council-plan-review/scripts/preflight.sh" in text


def test_skill_routes_members_by_focus_table():
    text = skill()
    assert "member-registry.md#quick-mode-member-selection" in text
    for flag in ("--focus", "--members", "--debate"):
        assert flag in text, flag


def test_member_answer_shape():
    text = skill()
    for field in ("POSITION:", "WHY:", "TRADE-OFFS:", "WOULD CHANGE MY MIND IF:", "CONFIDENCE:"):
        assert field in text, field


def test_synthesis_has_no_review_verdict():
    text = skill()
    synthesis = text.split("### Step 4", 1)[1].split("## Common Rationalizations", 1)[0]
    for section in ("Where they agree", "Where they split", "Captain's recommendation", "Open questions"):
        assert section in synthesis, section
    for review_only in ("review-grade.sh", "score-check.sh", "APPROVED WITH CONDITIONS", "DOMAIN SCORE"):
        assert review_only not in synthesis, review_only


def test_skill_is_listed_everywhere_skills_are_listed():
    for path in ("AGENTS.md", "README.md", "docs/skills.md"):
        assert "council-advise" in (ROOT / path).read_text(), path
