#!/usr/bin/env python3
"""The detect-patterns constants must equal the sweeps in references/pattern-detection.md."""

import importlib.util
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE = PROJECT_ROOT / "references" / "pattern-detection.md"
SKILL = PROJECT_ROOT / "skills" / "ios-conventions" / "SKILL.md"
AGENTS_MD = PROJECT_ROOT / "AGENTS.md"
SCRIPT = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts" / "detect-patterns.py"

SECTIONS = {
    "di": "Dependency injection",
    "testing": "Tests",
    "persistence": "Persistence",
    "concurrency": "Concurrency",
    "navigation": "Navigation",
}
ARCH_IDS = {"TCA": "tca", "MVVM_OBSERVABLE": "mvvm_observable", "MVVM_OBJECT": "mvvm_object", "UIKIT": "uikit"}
RG_FILES = re.compile(r"""^rg -l '([^']*)' --glob '\*\.swift'""")
RG_SETTINGS = re.compile(r"""^rg -n '([^']*)' (Package\.swift) \./(\*\.xcodeproj/project\.pbxproj)""")


def load_script():
    spec = importlib.util.spec_from_file_location("detect_patterns", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_text() -> str:
    return REFERENCE.read_text(encoding="utf-8")


def architecture_patterns() -> dict:
    out = {}
    for line in reference_text().splitlines():
        m = re.match(r"\|\s*(TCA|MVVM_OBSERVABLE|MVVM_OBJECT|UIKIT)\s*\|[^|]*\|\s*`(.+)`\s*\|\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).replace("\\|", "|")
    return out


def reference_sweeps(category: str) -> set:
    text = reference_text()
    section = text.split(f"### {SECTIONS[category]}\n", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
    block = re.search(r"```bash\n(.*?)```", section, re.S).group(1)
    sweeps = set()
    for line in block.splitlines():
        line = line.split("   # ")[0].strip()
        if not line:
            continue
        files = RG_FILES.match(line)
        if files:
            sweeps.add(("grep", files.group(1)))
            continue
        settings = RG_SETTINGS.match(line)
        assert settings, f"unparsed reference line: {line}"
        sweeps.add(("settings", settings.group(1), (settings.group(2), settings.group(3))))
    return sweeps


def script_sweeps(module, category: str) -> set:
    out = set()
    for sweep in module.SWEEPS[category]:
        if isinstance(sweep, module.Grep):
            out.add(("grep", sweep.pattern))
        else:
            out.add(("settings", sweep.pattern, tuple(sweep.paths)))
    return out


def test_architecture_patterns_equal_reference_table():
    module = load_script()
    reference = architecture_patterns()
    assert set(reference) == set(ARCH_IDS)
    script = {s.id: s.pattern for s in module.SWEEPS["architecture"]}
    assert script == {ARCH_IDS[k]: v for k, v in reference.items()}


@pytest.mark.parametrize("category", sorted(SECTIONS))
def test_script_sweeps_equal_reference(category):
    expected = reference_sweeps(category)
    assert expected, category
    assert script_sweeps(load_script(), category) == expected


def test_reference_parser_sees_every_command_in_the_five_sections():
    assert sum(len(reference_sweeps(c)) for c in SECTIONS) == 11


def test_parity_negative_control():
    module = load_script()
    first = module.SWEEPS["di"][0]
    mutated = set(script_sweeps(module, "di"))
    mutated.discard(("grep", first.pattern))
    mutated.add(("grep", first.pattern + "x"))
    assert mutated != reference_sweeps("di")


def test_sweep_ids_are_unique_per_category():
    module = load_script()
    for category, sweeps in module.SWEEPS.items():
        ids = [s.id for s in sweeps]
        assert len(ids) == len(set(ids)), category


def test_decision_candidates_name_real_sweeps_and_stay_disjoint():
    module = load_script()
    for category, decisions in module.DECISIONS.items():
        ids = {s.id for s in module.SWEEPS[category]}
        for decision in decisions:
            for candidate, members in decision.candidates.items():
                assert members and set(members) <= ids, (category, decision.key, candidate)
        used = [m for d in decisions for ms in d.candidates.values() for m in ms]
        assert len(used) == len(set(used)), category


def test_every_category_is_covered_in_canonical_order():
    module = load_script()
    assert list(module.SWEEPS) == ["architecture", *SECTIONS, "version"]
    assert list(module.DECISIONS) == list(module.SWEEPS)


def test_only_testing_sweeps_scan_test_directories():
    module = load_script()
    for category, sweeps in module.SWEEPS.items():
        for sweep in sweeps:
            if isinstance(sweep, module.Grep):
                assert sweep.in_tests == (category == "testing"), sweep.id


def test_thresholds_are_the_matrix_documented_in_the_reference_and_skill():
    module = load_script()
    assert (module.MATCH_PERCENT, module.CONFLICT_PERCENT) == (80, 50)
    for text in (reference_text(), SKILL.read_text(encoding="utf-8")):
        for needle in ("80%", "50-79%", "match", "conflict", "adopt"):
            assert needle in text, needle


def test_reference_points_at_the_script():
    assert "skills/ios-conventions/scripts/detect-patterns.py" in reference_text()


def test_reference_documents_the_cache():
    text = reference_text()
    assert "## Pattern Detection Cache" in text
    for needle in (".artifacts/iet/cache/detected-patterns.json", "project_hash", "confidence", "evidence", "NO_PROJECT_FILES"):
        assert needle in text, needle


def test_skill_runs_the_script_with_cache_flag():
    text = SKILL.read_text(encoding="utf-8")
    assert "scripts/detect-patterns.py" in text
    assert "--write-cache" in text
    assert ".artifacts/iet/cache/detected-patterns.json" in text
    assert "references/pattern-detection.md" in text
    assert "detect-architecture" not in text


def test_skill_names_every_category_and_verdict():
    text = SKILL.read_text(encoding="utf-8")
    for word in list(SECTIONS) + ["architecture", "version", "match", "conflict", "adopt", "verdict_architecture"]:
        assert word in text, word


def test_agents_md_states_the_cache_contract():
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert "Cache contract" in text
    assert ".artifacts/iet/cache/detected-patterns.json" in text


@pytest.mark.parametrize("agent", ["ios-architect", "ios-developer"])
def test_convention_agents_read_the_cache(agent):
    text = (PROJECT_ROOT / "agents" / f"{agent}.md").read_text(encoding="utf-8")
    assert ".artifacts/iet/cache/detected-patterns.json" in text


def test_ere_translation_of_reference_quirks():
    module = load_script()
    rx = module.compile_pattern
    assert rx(module.PAT_UIKIT).search("final class Home : UIViewController {")
    assert rx(module.PAT_MVVM_OBSERVABLE).search("@Observable")
    assert rx(module.PAT_MVVM_OBSERVABLE).search("@Observable final class A {}")
    assert not rx(module.PAT_MVVM_OBSERVABLE).search("@ObservableState struct S {}")
    assert rx(module.PAT_MVVM_OBJECT).search("final class A: Base, ObservableObject {")
    assert rx(r"@Dependency\b|DependencyKey").search("@Dependency(\\.x) var x")
    assert not rx(r"static let shared\b").search("static let sharedInstance = 1")


def test_reference_documents_the_content_hash_key():
    text = reference_text()
    assert "root-level" not in text.split("### Computing `project_hash`")[1].split("## Report format")[0]
    for needle in ("<relpath>", "sha256", "Package.resolved", "*.xcconfig", "--hash", "any depth", "`version`"):
        assert needle in text, needle
    assert "Only root-level files count" not in text


def test_reference_has_a_pattern_audit_covering_every_sweep():
    section = reference_text().split("### Audit: what each sweep can miscount")[1].split("\n### ", 1)[0]
    for needle in ("@Reducer", "@Observable", "ObservableObject", "UIViewController", "DependencyKey", "static let shared",
                   "Factories", "import Testing", "XCTestCase", "@Model", "NavigationStack", "Coordinator", "@MainActor"):
        assert needle in section, needle
