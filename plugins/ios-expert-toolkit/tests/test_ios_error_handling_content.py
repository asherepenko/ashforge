#!/usr/bin/env python3
"""Structural checks on the ios-error-handling skill. Each check is a function
over text so a stripped copy can prove it fails (negative controls)."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SKILL = PROJECT_ROOT / "skills" / "ios-error-handling" / "SKILL.md"
OPENAI = PROJECT_ROOT / "skills" / "ios-error-handling" / "agents" / "openai.yaml"

FLAG_TOKENS = ["try?", "catch {}", "CancellationError", "try!"]


def section(text: str, title: str) -> str:
    """Body of the `## <title>...` section, up to the next `## ` heading."""
    match = re.search(rf"^## {re.escape(title)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def check_flag_section(text: str) -> bool:
    body = section(text, "Flag in review")
    return all(token in body for token in FLAG_TOKENS)


def check_typed_throws(text: str) -> bool:
    body = section(text, "Typed throws")
    return "throws(" in body and "SE-0413" in body and "When NOT to use" in body


def check_ui_strings(text: str) -> bool:
    body = section(text, "UI strings")
    return "LocalizedError" in body and "String(localized:" in body


def check_cancellation(text: str) -> bool:
    body = section(text, "Cancellation")
    return "CancellationError" in body and "Task.isCancelled" in body


def check_tca_effects(text: str) -> bool:
    body = section(text, "TCA effects")
    return (
        ".run" in body
        and "catch" in body
        and "TaskResult" in body
        and re.search(r"\]\(\.\./tca/SKILL\.md\)", body) is not None
    )


def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


# --- real files ---

def test_flag_section_lists_swallowing_patterns():
    assert check_flag_section(skill())


def test_typed_throws_section():
    assert check_typed_throws(skill())


def test_localized_error_in_ui_strings_section():
    assert check_ui_strings(skill())


def test_cancellation_section():
    assert check_cancellation(skill())


def test_tca_effects_section_links_tca_skill():
    assert check_tca_effects(skill())


def test_tca_link_resolves():
    assert (SKILL.parent / "../tca/SKILL.md").resolve().exists()


def test_openai_yaml_short_description():
    text = OPENAI.read_text(encoding="utf-8")
    match = re.search(r'short_description:\s*"([^"]+)"', text)
    assert match and 25 <= len(match.group(1)) <= 64


# --- negative controls ---

def test_neg_flag_section_removed():
    stripped = re.sub(r"^## Flag in review.*?(?=^## )", "", skill(), flags=re.M | re.S)
    assert stripped != skill() and not check_flag_section(stripped)


def test_neg_flag_tokens_only_outside_flag_section():
    text = skill()
    body = section(text, "Flag in review")
    moved = text.replace(body, "\n- `fatalError` for recoverable failures.\n\n")
    assert moved != text and not check_flag_section(moved)


def test_neg_flag_missing_each_token():
    text = skill()
    body = section(text, "Flag in review")
    for token in FLAG_TOKENS:
        assert not check_flag_section(text.replace(body, body.replace(token, "")))


def test_neg_typed_throws_section_removed():
    stripped = re.sub(r"^## Typed throws.*?(?=^## )", "", skill(), flags=re.M | re.S)
    assert not check_typed_throws(stripped)


def test_neg_typed_throws_without_when_not():
    assert not check_typed_throws(skill().replace("When NOT to use", "When to use"))


def test_neg_localized_error_outside_ui_strings():
    text = skill()
    body = section(text, "UI strings")
    moved = text.replace(body, body.replace("LocalizedError", "Error"))
    assert moved != text and not check_ui_strings(moved)


def test_neg_cancellation_passthrough_stripped():
    text = skill()
    body = section(text, "Cancellation")
    assert not check_cancellation(text.replace(body, body.replace("Task.isCancelled", "")))


def test_neg_tca_link_stripped():
    assert not check_tca_effects(skill().replace("../tca/SKILL.md", ""))


def test_neg_tca_taskresult_stripped():
    assert not check_tca_effects(skill().replace("TaskResult", "Outcome"))
