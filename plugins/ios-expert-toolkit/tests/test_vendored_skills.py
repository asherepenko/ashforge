#!/usr/bin/env python3
"""Vendored skills on disk match ios-skills.lock. Names come from the lock."""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
LOCK = PROJECT_ROOT / "ios-skills.lock"
SKILLS = PROJECT_ROOT / "skills"


def read_lock() -> dict:
    out: dict = {}
    if not LOCK.exists():
        return out
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            out.setdefault(key, []).append(value)
    return out


def community_names(lock: dict) -> list:
    return sorted({k.split(".")[1] for k in lock if k.startswith("community.")})


def xcode_names(lock: dict) -> list:
    return lock.get("xcode.skill", [])


def frontmatter_name(skill_md: Path) -> str:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{skill_md}: no frontmatter"
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"name:\s*['\"]?([^'\"]+?)['\"]?\s*$", line)
        if m:
            return m.group(1)
    raise AssertionError(f"{skill_md}: no name in frontmatter")


@pytest.fixture(scope="module")
def lock():
    data = read_lock()
    if not community_names(data) and not xcode_names(data):
        pytest.skip("ios-skills.lock lists no skills yet; run scripts/sync-ios-skills.sh --update-xcode")
    return data


def test_community_skills_match_lock(lock):
    for name in community_names(lock):
        d = SKILLS / "community" / name
        assert re.fullmatch(r"[0-9a-f]{40}", lock[f"community.{name}.commit"][0]), name
        assert lock[f"community.{name}.repo"] and lock[f"community.{name}.license"], name
        assert (d / "SKILL.md").is_file(), f"{name}: SKILL.md missing"
        assert (d / "LICENSE").is_file(), f"{name}: upstream LICENSE missing"
        assert frontmatter_name(d / "SKILL.md") == name


def test_xcode_skills_match_lock(lock):
    names = xcode_names(lock)
    if not names:
        pytest.skip("ios-skills.lock has no xcode.skill lines yet")
    for name in names:
        assert (SKILLS / "xcode" / name / "SKILL.md").is_file(), name
        assert frontmatter_name(SKILLS / "xcode" / name / "SKILL.md") == name
    on_disk = sorted(p.name for p in (SKILLS / "xcode").iterdir() if p.is_dir())
    assert on_disk == sorted(names), "skills/xcode holds skills the lock does not list"


def test_no_vendored_skill_at_top_level(lock):
    for name in community_names(lock) + xcode_names(lock):
        assert not (SKILLS / name).exists(), f"skills/{name} shadows the vendored copy"
