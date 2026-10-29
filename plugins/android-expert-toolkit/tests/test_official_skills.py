#!/usr/bin/env python3
"""Tests for the vendored official Android skills."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SKILLS = PROJECT_ROOT / "skills"
LOCK = PROJECT_ROOT / "android-skills.lock"
OWN_SKILLS = {"android-conventions", "android-expert", "android-testing", "android-error-handling"}


def lock_values(key: str) -> list[str]:
    return re.findall(rf"^{key}=(.+)$", LOCK.read_text(encoding="utf-8"), re.MULTILINE)


def test_lock_lists_exactly_the_vendored_skill_dirs():
    on_disk = {p.name for p in SKILLS.iterdir() if p.is_dir()} - OWN_SKILLS
    assert sorted(lock_values("skill")) == sorted(on_disk)


def test_lock_pins_a_commit():
    commits = lock_values("commit")
    assert len(commits) == 1 and re.fullmatch(r"[0-9a-f]{40}", commits[0]), commits
    assert lock_values("repo") == ["https://github.com/android/skills"]


def test_android_cli_is_never_vendored():
    assert not (SKILLS / "android-cli").exists()
    assert "android-cli" not in lock_values("skill")
    script = (PROJECT_ROOT / "scripts" / "sync-android-skills.sh").read_text(encoding="utf-8")
    skills_block = script.split("SKILLS=(", 1)[1].split(")", 1)[0]
    assert "android-cli" not in skills_block


def test_vendored_skills_carry_license_and_frontmatter_name():
    for name in lock_values("skill"):
        skill_dir = SKILLS / name
        assert (skill_dir / "LICENSE.txt").read_text(encoding="utf-8").lstrip().startswith("Apache License")
        frontmatter = (skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
        assert re.search(rf"^name: {re.escape(name)}$", frontmatter, re.MULTILINE), name


def test_third_party_notice_names_every_vendored_skill():
    notice = (PROJECT_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "Apache License, Version 2.0" in notice
    for name in lock_values("skill"):
        assert f"`{name}`" in notice, name
