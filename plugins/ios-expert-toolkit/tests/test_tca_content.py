#!/usr/bin/env python3
"""Structural checks on the tca skill. Each check is a function over text so a
stripped copy can prove it fails (negative controls)."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SKILL = PROJECT_ROOT / "skills" / "tca" / "SKILL.md"
REFERENCE = PROJECT_ROOT / "references" / "tca.md"
OPENAI = PROJECT_ROOT / "skills" / "tca" / "agents" / "openai.yaml"

PIN = re.compile(r"ComposableArchitecture \d+\.\d+")
VERSION = re.compile(r"\b\d+\.\d+\b")
LEGACY = [
    "WithViewStore",
    "ViewStore",
    "@BindingState",
    "@PresentationState",
    "IfLetStore",
    "ForEachStore",
    "NavigationStackStore",
    "TaskResult",
]
CORE_SECTIONS = {
    "Dependencies": ["@Dependency", "DependencyKey", "testValue", "liveValue"],
    "Effects": [".run", ".cancellable", "cancelInFlight"],
    "Navigation": ["@Presents", "ifLet", "StackState", "forEach"],
    "Shared state": ["@Shared", "withLock"],
    "Core shape": ["@Reducer", "@ObservableState"],
}


def section(text: str, title: str) -> str:
    """Body of the `## <title>...` section, up to the next `## ` heading."""
    match = re.search(rf"^## {re.escape(title)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def check_pin(text: str) -> bool:
    return bool(PIN.search(text))


def table_rows(body: str) -> list:
    rows = []
    for line in body.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:]  # drop header


def check_deprecated(text: str, apis=LEGACY) -> bool:
    """Every legacy API sits in a Deprecated row: legacy cell, replacement cell, version cell."""
    rows = table_rows(section(text, "Deprecated"))
    for api in apis:
        ok = any(
            len(r) >= 3 and api in r[0] and r[1] and api not in r[1] and VERSION.search(r[2])
            for r in rows
        )
        if not ok:
            return False
    return True


def check_teststore(text: str) -> bool:
    body = section(text, "TestStore")
    return (
        "TestStore" in body
        and re.search(r"\*\*Exhaustive", body) is not None
        and re.search(r"\*\*Non-exhaustive", body) is not None
        and "exhaustivity = .off" in body
    )


def check_core_sections(text: str) -> bool:
    return all(
        all(token in section(text, title) for token in tokens)
        for title, tokens in CORE_SECTIONS.items()
    )


def check_swiftdata_behind_dependency(text: str) -> bool:
    body = section(text, "Dependencies")
    return "ModelContext" in body and "SwiftData" in body and "@Dependency" in body


def check_version_aware(text: str) -> bool:
    return "Package.resolved" in text and "ios-conventions" in text


def check_new_project_policy_links_conventions(text: str) -> bool:
    return re.search(r"\]\(\.\./ios-conventions/SKILL\.md\)", text) is not None


def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


# --- real files ---

def test_pin_stated_in_skill_and_reference():
    assert check_pin(skill())
    assert check_pin(reference())
    assert PIN.search(skill()).group(0) == PIN.search(reference()).group(0)


def test_legacy_apis_deprecated_with_replacement_and_version():
    assert check_deprecated(skill())


def test_reference_lists_deprecations_with_versions():
    body = section(reference(), "Deprecations by version")
    assert check_deprecated("## Deprecated\n" + body, apis=["WithViewStore", "TaskResult"])


def test_teststore_names_exhaustive_and_non_exhaustive():
    assert check_teststore(skill())


def test_core_apis_covered_in_their_sections():
    assert check_core_sections(skill())


def test_swiftdata_context_behind_dependency():
    assert check_swiftdata_behind_dependency(skill())


def test_version_awareness_and_policy_link():
    assert check_version_aware(skill())
    assert check_new_project_policy_links_conventions(skill())


def test_openai_yaml_short_description():
    text = OPENAI.read_text(encoding="utf-8")
    match = re.search(r'short_description:\s*"([^"]+)"', text)
    assert match and 25 <= len(match.group(1)) <= 64


def test_reference_link_resolves():
    assert (SKILL.parent / "../../references/tca.md").resolve().exists()


# --- negative controls ---

def test_neg_pin_stripped():
    assert not check_pin(PIN.sub("ComposableArchitecture", skill()))


def test_neg_deprecated_section_removed():
    stripped = re.sub(r"^## Deprecated.*?(?=^## )", "", skill(), flags=re.M | re.S)
    assert not check_deprecated(stripped)


def test_neg_legacy_api_outside_deprecated_section():
    text = skill()
    moved = re.sub(r"^\| `WithViewStore`, `ViewStore`[^\n]*\n", "", text, flags=re.M)
    moved = moved.replace("## Core shape\n", "## Core shape\n\nUse WithViewStore and ViewStore.\n")
    assert not check_deprecated(moved)


def test_neg_deprecated_row_without_version():
    text = skill()
    bad = re.sub(r"(\| `TaskResult` \| [^|]*\| )1\.4 \(soft\)", r"\1soon", text)
    assert bad != text and not check_deprecated(bad)


def test_neg_deprecated_row_without_replacement():
    text = skill()
    bad = re.sub(r"(\| `TaskResult` \| )[^|]*(\| 1\.4)", r"\1 \2", text)
    assert bad != text and not check_deprecated(bad)


def test_neg_teststore_missing_non_exhaustive():
    stripped = skill().replace("**Non-exhaustive.**", "**Other.**")
    assert not check_teststore(stripped)


def test_neg_teststore_missing_exhaustive():
    stripped = skill().replace("**Exhaustive (default).**", "**Default.**")
    assert not check_teststore(stripped)


def test_neg_core_section_stripped():
    assert not check_core_sections(skill().replace("@Shared", "").replace("withLock", ""))


def test_neg_swiftdata_not_behind_dependency():
    assert not check_swiftdata_behind_dependency(skill().replace("ModelContext", "context"))


def test_neg_version_awareness_stripped():
    assert not check_version_aware(skill().replace("Package.resolved", "the lockfile"))
    assert not check_new_project_policy_links_conventions(
        skill().replace("../ios-conventions/SKILL.md", "")
    )
