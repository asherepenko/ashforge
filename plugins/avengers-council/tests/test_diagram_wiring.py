"""Diagram fields flow from the debate protocol to the verdict, for plan reviews only."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(rel):
    return (ROOT / rel).read_text()


def _round1(text):
    match = re.search(r"^### Round 1.*?(?=^### Round 2)", text, re.M | re.S)
    assert match
    return match.group(0)


def test_debate_protocol_defines_member_specific_fields():
    section = _round1(_read("references/debate-protocol.md"))
    assert "#### Member-specific fields (plan review only)" in section
    sub = section.split("#### Member-specific fields (plan review only)")[1]
    for field in ("ARCHITECTURE DIAGRAM:", "FLOW DIAGRAM:", "PATH → TEST:"):
        assert field in sub
    assert "iron-man" in sub and "hulk" in sub
    assert "applies only to its named member" in sub
    assert "unmapped" in sub


def test_no_round_heading_for_subsection():
    text = _read("references/debate-protocol.md")
    for line in text.splitlines():
        if "Member-specific fields" in line:
            assert line.startswith("#### ")
            assert "### Round " not in line.replace("#### ", "", 1)


def test_spawn_template_scoped_to_named_members():
    text = _read("references/orchestration-protocol.md")
    assert "ARCHITECTURE DIAGRAM" in text and "FLOW DIAGRAM" in text
    assert "PATH → TEST" in text
    assert "only in iron-man's" in text and "only in hulk's" in text


def test_quick_flow_and_fallback_apply_when_member_present():
    orch = _read("references/orchestration-protocol.md")
    quick = orch.split("## Quick Mode (3-member quorum)")[1]
    assert "ARCHITECTURE DIAGRAM" in quick and "FLOW DIAGRAM" in quick
    fb = _read("references/runtime-fallback.md")
    assert "ARCHITECTURE DIAGRAM" in fb and "FLOW DIAGRAM" in fb
    assert "when the member is present" in fb


def test_verdict_template_diagrams_section():
    text = _read("assets/verdict-template.md")
    assert "## Diagrams" in text
    order = [text.index(h) for h in ("## Standards Compliance", "## Diagrams", "## Conditions for Approval")]
    assert order == sorted(order)
    body = text.split("## Diagrams")[1].split("\n## ")[0]
    assert "Include this section ONLY for plan reviews." in body
    assert "Omit it for code reviews" not in body
    assert "not drawn — <member> not in Quick roster" in body
    assert "Architecture" in body and "Flow" in body
    heading = next(line for line in text.splitlines() if line.startswith("## Diagrams"))
    for word in ("APPROVED", "NEEDS REVISION", "BLOCKED"):
        assert word not in heading


def test_plan_skill_lists_fields_in_round1_redflags_verification():
    text = _read("skills/council-plan-review/SKILL.md")
    additions = text.split("**Verdict synthesis additions:**")[0]
    assert "ARCHITECTURE DIAGRAM:" in additions and "FLOW DIAGRAM:" in additions
    assert "PATH → TEST:" in additions
    red = text.split("## Red Flags")[1].split("## Verification")[0]
    assert "diagram" in red.lower()
    ver = text.split("## Verification")[1]
    assert "ARCHITECTURE DIAGRAM:" in ver and "FLOW DIAGRAM:" in ver


def test_code_review_skill_untouched_by_diagrams():
    assert "DIAGRAM" not in _read("skills/council-code-review/SKILL.md")


def test_docs_mirror_diagrams_section():
    text = _read("docs/skills.md")
    assert "## Diagrams" in text
    assert "not drawn — <member> not in Quick roster" in text
