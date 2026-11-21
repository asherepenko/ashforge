#!/usr/bin/env python3
"""The detect-patterns constants must equal the sweeps in references/pattern-detection.md."""

import importlib.util
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE = PROJECT_ROOT / "references" / "pattern-detection.md"
SKILL = PROJECT_ROOT / "skills" / "android-conventions" / "SKILL.md"
SCRIPT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "detect-patterns.py"

SECTIONS = {
    "state": "State Management Patterns",
    "di": "Dependency Injection Patterns",
    "testing": "Testing Patterns",
    "architecture": "Architecture Patterns",
    "security": "Security Patterns",
    "performance": "Performance Patterns",
    "accessibility": "Accessibility Patterns",
}

GREP = re.compile(r"""^grep -rn?\s+(?:"([^"]*)"|'([^']*)')\s+((?:--include="[^"]+"\s*)+)\.(.*)$""")
EXCLUDE = re.compile(r"""\|\s*grep -v\s+"([^"]*)"\s*\|\s*wc -l\s*$""")
FIND = re.compile(r"^find \. (.*?)\s*\|\s*wc -l")


def load_script():
    spec = importlib.util.spec_from_file_location("detect_patterns", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_blocks() -> dict:
    text = REFERENCE.read_text(encoding="utf-8")
    out = {}
    for category, title in SECTIONS.items():
        section = text.split(f"### {title}\n", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
        out[category] = re.search(r"```bash\n(.*?)```", section, re.S).group(1)
    return out


def reference_sweeps(category: str) -> set:
    """Normalised (kind, pattern, extensions/path, exclude) tuples read from the bash block."""
    sweeps = set()
    for line in reference_blocks()[category].splitlines():
        line = line.split("   # ")[0].strip()
        if line.startswith("#") or not line:
            continue
        grep = GREP.match(line)
        if grep:
            pattern = grep.group(1) if grep.group(1) is not None else grep.group(2)
            exts = frozenset(re.findall(r'--include="\*\.(\w+)"', grep.group(3)))
            exclude = EXCLUDE.search(line)
            sweeps.add(("grep", pattern, exts, exclude.group(1) if exclude else None))
            continue
        find = FIND.match(line)
        assert find, f"unparsed reference line: {line}"
        names = frozenset(re.findall(r'-name "([^"]+)"', find.group(1)))
        path = re.search(r'-path "([^"]+)"', find.group(1))
        sweeps.add(("find", names, path.group(1) if path else None, None))
    return sweeps


def script_sweeps(module, category: str) -> set:
    sweeps = set()
    for sweep in module.SWEEPS[category]:
        if isinstance(sweep, module.Grep):
            sweeps.add(("grep", sweep.pattern, frozenset(sweep.exts), sweep.exclude))
        else:
            sweeps.add(("find", frozenset(sweep.names), sweep.path, None))
    return sweeps


@pytest.mark.parametrize("category", sorted(SECTIONS))
def test_script_sweeps_equal_reference(category):
    expected = reference_sweeps(category)
    assert expected, category
    assert script_sweeps(load_script(), category) == expected


def test_reference_parser_sees_every_command_in_the_seven_sections():
    total = sum(len(reference_sweeps(c)) for c in SECTIONS)
    assert total == 41


def test_parity_negative_control():
    module = load_script()
    first = module.SWEEPS["di"][0]
    mutated = set(script_sweeps(module, "di"))
    mutated.discard(("grep", first.pattern, frozenset(first.exts), first.exclude))
    mutated.add(("grep", first.pattern + "x", frozenset(first.exts), first.exclude))
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


def test_every_category_is_covered():
    module = load_script()
    assert list(module.SWEEPS) == list(SECTIONS)


def test_thresholds_are_the_reference_matrix():
    module = load_script()
    text = REFERENCE.read_text(encoding="utf-8")
    assert (module.MATCH_PERCENT, module.CONFLICT_PERCENT) == (80, 50)
    for needle in ("≥80%", "50-79%", "<50%"):
        assert needle in text, needle
    assert "80/20" in text


def test_skipped_reference_sections_are_not_categories():
    module = load_script()
    text = REFERENCE.read_text(encoding="utf-8")
    for title in ("Data Layer Patterns", "Serialization Patterns", "Language Distribution"):
        assert f"### {title}" in text
    assert set(module.SWEEPS) == set(SECTIONS)


def test_reference_points_at_the_script():
    assert "skills/android-conventions/scripts/detect-patterns.py" in REFERENCE.read_text(encoding="utf-8")


def test_skill_runs_the_script_with_cache_flag():
    text = SKILL.read_text(encoding="utf-8")
    assert "scripts/detect-patterns.py" in text
    assert "--write-cache" in text
    assert ".artifacts/aet/cache/detected-patterns.json" in text
    assert "references/pattern-detection.md" in text


def test_skill_names_every_category_and_verdict():
    text = SKILL.read_text(encoding="utf-8")
    for word in list(SECTIONS) + ["match", "conflict", "adopt"]:
        assert word in text, word


def test_bre_translation_of_reference_quirks():
    module = load_script()
    rx = module.compile_bre
    assert rx(r"koinViewModel\|by inject()").search("val x by inject()")
    assert not rx(r"koinViewModel\|by inject()").search("by inject")
    assert rx(r"\.test\s*{").search("flow.test {")
    assert rx(r'"[A-Za-z0-9_-]\{32,\}"').search('"' + "a" * 32 + '"')
    assert not rx(r'"[A-Za-z0-9_-]\{32,\}"').search('"' + "a" * 31 + '"')
    assert rx("mock(").search("val m = mock(Foo)")
    assert not rx("Single<\\|Observable<").search("Singleton")
