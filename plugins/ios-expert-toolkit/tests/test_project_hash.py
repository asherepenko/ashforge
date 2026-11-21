#!/usr/bin/env python3
"""The cache key is a content hash over every scanned file plus every project file."""

import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
SCRIPTS = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts"
DETECT = SCRIPTS / "detect-patterns.py"
PREFLIGHT = SCRIPTS / "preflight.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def hash_flag(project: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(DETECT), "--hash", str(project)], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stderr
    match = re.fullmatch(r"project_hash=(NO_PROJECT_FILES|[0-9a-f]{64})\n", result.stdout)
    assert match, repr(result.stdout)
    return match.group(1)


def preflight_hash(project: Path) -> str:
    out = subprocess.run(
        [sys.executable, str(PREFLIGHT)], cwd=project, capture_output=True, text=True, timeout=60, check=True
    ).stdout.splitlines()
    return out[out.index("== Project hash ==") + 1]


def make_project(root: Path) -> Path:
    write(root / "Sources/A.swift", "struct A {}\n")
    write(root / "Package.swift", "// manifest\n")
    write(root / "Package.resolved", '{"pins": []}\n')
    write(root / "App.xcodeproj/project.pbxproj", "SWIFT_VERSION = 6.0;\n")
    write(root / "Config/Debug.xcconfig", "A = 1\n")
    return root


def test_hash_flag_prints_only_the_hash_line(tmp_path):
    make_project(tmp_path)
    result = subprocess.run(
        [sys.executable, str(DETECT), "--hash", str(tmp_path)], capture_output=True, text=True, check=True
    )
    assert result.stdout.count("\n") == 1 and result.stdout.startswith("project_hash=")


def test_hash_matches_the_documented_algorithm(tmp_path):
    make_project(tmp_path)
    expected = {
        "App.xcodeproj/project.pbxproj": b"SWIFT_VERSION = 6.0;\n",
        "Config/Debug.xcconfig": b"A = 1\n",
        "Package.resolved": b'{"pins": []}\n',
        "Package.swift": b"// manifest\n",
        "Sources/A.swift": b"struct A {}\n",
    }
    lines = "".join(f"{rel}\t{hashlib.sha256(data).hexdigest()}\n" for rel, data in sorted(expected.items()))
    assert hash_flag(tmp_path) == hashlib.sha256(lines.encode("utf-8")).hexdigest()


def test_empty_set_is_no_project_files(tmp_path):
    write(tmp_path / "README.md", "hello\n")
    assert hash_flag(tmp_path) == "NO_PROJECT_FILES"


@pytest.mark.parametrize(
    "rel",
    [
        "Sources/A.swift",
        "Package.resolved",
        "Package.swift",
        "App.xcodeproj/project.pbxproj",
        "Config/Debug.xcconfig",
    ],
)
def test_editing_a_keyed_file_changes_the_hash(tmp_path, rel):
    make_project(tmp_path)
    before = hash_flag(tmp_path)
    (tmp_path / rel).write_text("edited\n", encoding="utf-8")
    assert hash_flag(tmp_path) != before


def test_editing_a_nested_package_resolved_changes_the_hash(tmp_path):
    make_project(tmp_path)
    write(tmp_path / "App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved", "{}\n")
    before = hash_flag(tmp_path)
    write(tmp_path / "App.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved", '{"a":1}\n')
    assert hash_flag(tmp_path) != before


def test_editing_a_nested_pbxproj_changes_the_hash(tmp_path):
    make_project(tmp_path)
    write(tmp_path / "Sub/App.xcodeproj/project.pbxproj", "one\n")
    before = hash_flag(tmp_path)
    write(tmp_path / "Sub/App.xcodeproj/project.pbxproj", "two\n")
    assert hash_flag(tmp_path) != before


@pytest.mark.parametrize("rel", [".build/checkouts/V.swift", "Pods/P/P.swift", "Pods/Pods.xcodeproj/project.pbxproj", "Carthage/Build/x.swift"])
def test_pruned_directories_do_not_change_the_hash(tmp_path, rel):
    make_project(tmp_path)
    write(tmp_path / rel, "one\n")
    before = hash_flag(tmp_path)
    write(tmp_path / rel, "two\n")
    assert hash_flag(tmp_path) == before


def test_cache_file_itself_does_not_change_the_hash(tmp_path):
    make_project(tmp_path)
    before = hash_flag(tmp_path)
    write(tmp_path / ".artifacts/iet/cache/detected-patterns.json", "{}\n")
    assert hash_flag(tmp_path) == before


def test_project_in_a_subfolder_gets_a_real_hash(tmp_path):
    write(tmp_path / "ios/App.xcodeproj/project.pbxproj", "x\n")
    assert hash_flag(tmp_path) != "NO_PROJECT_FILES"
    assert re.fullmatch(r"[0-9a-f]{64}", hash_flag(tmp_path))


def test_hash_is_stable_and_independent_of_creation_order(tmp_path):
    names = ["z/Z.swift", "a/A.swift", "Package.swift", "m/App.xcodeproj/project.pbxproj", "Package.resolved"]
    first, second = tmp_path / "one", tmp_path / "two"
    for rel in names:
        write(first / rel, f"{rel}\n")
    for rel in reversed(names):
        write(second / rel, f"{rel}\n")
    assert hash_flag(first) == hash_flag(first) == hash_flag(second)


def test_same_content_at_a_different_path_hashes_differently(tmp_path):
    write(tmp_path / "one/A.swift", "x\n")
    write(tmp_path / "two/B.swift", "x\n")
    assert hash_flag(tmp_path / "one") != hash_flag(tmp_path / "two")


@pytest.mark.parametrize("fixture", ["tca-full-app", "pods-ignored-app", "mvvm-app"])
def test_preflight_and_flag_agree_on_fixtures(tmp_path, fixture):
    project = tmp_path / fixture
    shutil.copytree(FIXTURES / fixture, project)
    assert preflight_hash(project) == hash_flag(project)


def test_preflight_and_flag_agree_for_a_subfolder_project(tmp_path):
    make_project(tmp_path)
    write(tmp_path / "Sub/App.xcodeproj/project.pbxproj", "one\n")
    assert preflight_hash(tmp_path) == hash_flag(tmp_path) != "NO_PROJECT_FILES"


def test_write_cache_records_the_same_hash(tmp_path):
    make_project(tmp_path)
    subprocess.run([sys.executable, str(DETECT), str(tmp_path), "--write-cache"], capture_output=True, check=True)
    cache = (tmp_path / ".artifacts/iet/cache/detected-patterns.json").read_text(encoding="utf-8")
    assert f'"project_hash": "{hash_flag(tmp_path)}"' in cache


def test_preflight_reuses_the_detect_patterns_implementation():
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "detect-patterns.py" in text and "importlib" in text
    assert "hashlib" not in text
