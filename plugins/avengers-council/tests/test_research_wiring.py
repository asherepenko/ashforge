import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = (ROOT / "references" / "orchestration-protocol.md").read_text()
DEBATE = (ROOT / "references" / "debate-protocol.md").read_text()
FALLBACK = (ROOT / "references" / "runtime-fallback.md").read_text()
TEMPLATE = (ROOT / "assets" / "verdict-template.md").read_text()
CAPTAIN = (ROOT / "references" / "captain-america-orchestrator.md").read_text()
DOCS = (ROOT / "docs" / "skills.md").read_text()
VERDICT_RULES = (ROOT / "references" / "verdict-rules.md").read_text()
SKILLS = {
    name: (ROOT / "skills" / name / "SKILL.md").read_text()
    for name in ("council-plan-review", "council-code-review")
}

BRIEF_FIELD = (
    "RESEARCH BRIEF (only when your spawn prompt has a RESEARCH BRIEF block): "
    "[date — findings with URLs | Nothing material]"
)
RUN_MODE_LINE = "Research: <member> (<status>), … | skipped — no web tools"


def spawn_block(text):
    start = text.index("RESEARCH BRIEF:")
    return text[start:text.index("REVIEW RULES:", start)]


def test_spawn_template_has_conditional_research_block():
    block = spawn_block(ORCH)
    assert "Include this block ONLY when" in block
    assert "WEB=available" in block
    assert "research-protocol.md" in block
    assert "## Research Focus" in block
    assert "first" in block and "brief" in block


def test_spawn_block_repeats_privacy_budget_and_untrusted_rule():
    block = spawn_block(ORCH)
    assert "public dependency names and versions" in block
    assert "secrets" in block and "private package names" in block
    assert "5 searches" in block and "3 fetches" in block
    assert "data, not instructions" in block


def test_round1_field_in_debate_and_spawn_field_list():
    assert BRIEF_FIELD in DEBATE
    assert "RESEARCH BRIEF (only when your spawn prompt has a RESEARCH BRIEF block)" in ORCH
    fields = ORCH.split("ROUND 1 INSTRUCTIONS:")[1].split("Then share")[0]
    assert "RESEARCH BRIEF (only when your spawn prompt has a RESEARCH BRIEF block)" in fields


def test_quick_flow_and_fallback_apply_selection_rule_by_reference():
    quick = ORCH.split("### Quick Flow")[1]
    assert "research-protocol.md" in quick
    step2 = FALLBACK.split("### Step 2")[1].split("### Step 3")[0]
    assert "research-protocol.md" in step2


def test_captain_roster_step_reads_manifest_section():
    roster = ORCH.split("### Step 1: Determine Active Roster")[1].split("### Step 2")[0]
    assert "== Dependency manifests changed ==" in roster
    assert "plan text" in roster
    assert "research-protocol.md" in roster
    assert "research-protocol.md" in CAPTAIN


def test_verdict_template_run_mode_and_position_lines():
    run_mode = TEMPLATE.split("## Run Mode")[1].split("## Consensus")[0]
    assert RUN_MODE_LINE in run_mode
    assert "- Research:" in TEMPLATE.split("## Council Positions")[1]


def test_docs_output_format_mirrors_template():
    assert RUN_MODE_LINE in DOCS
    assert "- Research:" in DOCS


def test_skills_allow_web_tools_and_verify_brief():
    for name, text in SKILLS.items():
        tools = re.search(r"^allowed-tools: (.*)$", text, re.M).group(1)
        assert "WebSearch, WebFetch" in tools, name
        assert "Research brief present for every selected member, or the skip disclosed" in text, name


def test_verdict_rules_do_not_mention_research():
    assert "research" not in VERDICT_RULES.lower()


def test_spawn_block_repeats_registry_host_and_retry_limits():
    block = spawn_block(ORCH)
    assert "Never query a registry to decide" in block
    assert "public `https` hosts only" in block
    for host in ("credentials", "private IP ranges", "`localhost`", "internal hostnames", "redirects"):
        assert host in block
    assert "One retry per call" in block
