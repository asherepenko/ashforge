#!/usr/bin/env python3
"""swiftui-pro fork: kept references match the lock, removed ones are gone,
and the review steps delegate to swiftui-specialist. All checks run offline."""

import hashlib
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
LOCK = PROJECT_ROOT / "ios-skills.lock"
SKILL_DIR = PROJECT_ROOT / "skills" / "swiftui-pro"
SPECIALIST = PROJECT_ROOT / "skills" / "xcode" / "swiftui-specialist" / "references"

REMOVED = ["api.md", "data.md", "localization.md"]
DELEGATION = [
    "soft-deprecation.md", "soft-deprecated-apis.md", "dataflow.md",
    "environment.md", "foreach.md", "localization.md",
]
LINK = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]*)?\)")


def lock_lines(prefix: str) -> dict:
    out = {}
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix) and "=" in line:
            key, value = line.split("=", 1)
            out[key[len(prefix):]] = value
    return out


def delegation_problems(skill_md: Path) -> list:
    """Every delegated review step names swiftui-specialist and links its reference file."""
    text = skill_md.read_text(encoding="utf-8")
    steps = [ln for ln in text.splitlines() if ln.startswith("1. ")]
    problems = []
    for ref in DELEGATION:
        hits = [ln for ln in steps if f"/{ref})" in ln]
        if not hits:
            problems.append(f"no review step links {ref}")
            continue
        for ln in hits:
            if "swiftui-specialist" not in ln:
                problems.append(f"step for {ref} does not name swiftui-specialist")
    return problems


def test_kept_references_match_lock_hashes():
    hashes = lock_lines("fork.swiftui-pro.sha256.")
    assert hashes, "no fork.swiftui-pro.sha256.* lines in lock"
    for name, expected in hashes.items():
        path = SKILL_DIR / "references" / name
        assert path.is_file(), f"{name} listed in lock but missing"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"{name} differs from upstream"


def test_every_unmodified_reference_is_locked():
    locked = set(lock_lines("fork.swiftui-pro.sha256."))
    on_disk = {p.name for p in (SKILL_DIR / "references").glob("*.md")}
    assert on_disk - locked == {"views.md"}, "only views.md may be modified and unlocked"


def test_fork_lock_pins_upstream():
    meta = lock_lines("fork.swiftui-pro.")
    assert meta["repo"] == "twostraws/SwiftUI-Agent-Skill"
    assert re.fullmatch(r"[0-9a-f]{40}", meta["commit"])
    assert meta["license"] == "MIT"


@pytest.mark.parametrize("name", REMOVED)
def test_removed_references_are_absent(name):
    assert not (SKILL_DIR / "references" / name).exists()


def test_skill_links_to_specialist_files_resolve():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    targets = {(SKILL_DIR / m.group(1)).resolve() for m in LINK.finditer(text)}
    for ref in DELEGATION:
        assert (SPECIALIST / ref).resolve() in targets, f"SKILL.md does not link {ref}"
        assert (SPECIALIST / ref).is_file()
    for t in targets:
        assert t.exists(), f"broken link {t}"


def test_delegation_steps_name_swiftui_specialist():
    assert delegation_problems(SKILL_DIR / "SKILL.md") == []


def test_negative_control_without_delegation_fails(tmp_path):
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    stripped = text.replace("swiftui-specialist", "other-skill")
    copy = tmp_path / "SKILL.md"
    copy.write_text(stripped, encoding="utf-8")
    assert delegation_problems(copy), "check must fail when delegation is removed"


def test_negative_control_missing_reference_link_fails(tmp_path):
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    copy = tmp_path / "SKILL.md"
    copy.write_text(text.replace("localization.md)", "gone.md)"), encoding="utf-8")
    assert delegation_problems(copy)


def test_upstream_license_and_notes_kept():
    assert "MIT License" in (SKILL_DIR / "LICENSE").read_text(encoding="utf-8")
    assert (SKILL_DIR / "FORK.md").is_file()
    assert (SKILL_DIR / "agents" / "openai.yaml").is_file()
