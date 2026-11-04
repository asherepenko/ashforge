#!/usr/bin/env python3
"""Behavior pins for the ios-conventions pre-flight script."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts" / "preflight.py"

HEADERS = [
    "== Deployment targets (IPHONEOS_DEPLOYMENT_TARGET) ==",
    "== Package platforms ==",
    "== swift-tools-version ==",
    "== Swift language mode (SWIFT_VERSION|swiftLanguageModes) ==",
    "== Strict concurrency ==",
    "== TCA (swift-composable-architecture) ==",
    "== Key packages ==",
    "== Test frameworks (import Testing|import XCTest file counts) ==",
    "== Observation (@Observable|ObservableObject file counts) ==",
]


def run(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, text=True, check=False)


def sections(out: str) -> dict:
    result, current = {}, None
    for line in out.splitlines():
        if line.startswith("== "):
            current = line
            result[current] = []
        else:
            result[current].append(line)
    return result


def test_empty_project(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    parsed = sections(result.stdout)
    assert list(parsed) == HEADERS
    assert parsed[HEADERS[0]] == ["NOT_FOUND"]
    assert parsed[HEADERS[1]] == ["NOT_FOUND"]
    assert parsed[HEADERS[2]] == ["NOT_FOUND"]
    assert parsed[HEADERS[3]] == ["NOT_FOUND"]
    assert parsed[HEADERS[4]] == ["NOT_FOUND"]
    assert parsed[HEADERS[5]] == ["NOT_FOUND"]
    assert parsed[HEADERS[6]] == ["NONE"]
    assert parsed[HEADERS[7]] == ["Testing: 0", "XCTest: 0"]
    assert parsed[HEADERS[8]] == ["@Observable: 0", "ObservableObject: 0"]


def test_populated_project(tmp_path):
    proj = tmp_path / "App.xcodeproj"
    proj.mkdir()
    (proj / "project.pbxproj").write_text(
        "IPHONEOS_DEPLOYMENT_TARGET = 17.0;\nIPHONEOS_DEPLOYMENT_TARGET = 17.0;\n"
        "IPHONEOS_DEPLOYMENT_TARGET = 16.4;\nSWIFT_VERSION = 6.0;\n"
        "SWIFT_STRICT_CONCURRENCY = complete;\n",
        encoding="utf-8",
    )
    (tmp_path / "Package.swift").write_text(
        "// swift-tools-version: 6.0\n"
        "let package = Package(\n  platforms: [.iOS(.v17), .macOS(.v14)],\n"
        "  swiftLanguageModes: [.v6]\n)\n",
        encoding="utf-8",
    )
    resolved = {
        "pins": [
            {"identity": "swift-composable-architecture", "state": {"version": "1.17.0"}},
            {"identity": "swift-dependencies", "state": {"version": "1.6.2"}},
            {"identity": "some-branch-pin", "state": {"branch": "main", "revision": "abc"}},
        ],
        "version": 2,
    }
    (tmp_path / "Package.resolved").write_text(json.dumps(resolved), encoding="utf-8")
    src = tmp_path / "Sources"
    src.mkdir()
    (src / "Model.swift").write_text("@Observable\nfinal class Model {}\n@Observable class B {}\n", encoding="utf-8")
    (src / "Old.swift").write_text("final class Old: ObservableObject {}\n", encoding="utf-8")
    tests = tmp_path / "Tests"
    tests.mkdir()
    (tests / "ATests.swift").write_text("import Testing\n", encoding="utf-8")
    (tests / "BTests.swift").write_text("import XCTest\n", encoding="utf-8")
    (tests / "CTests.swift").write_text("import XCTest\n", encoding="utf-8")
    vendored = tmp_path / ".build" / "checkouts"
    vendored.mkdir(parents=True)
    (vendored / "V.swift").write_text("import XCTest\n@Observable class V {}\n", encoding="utf-8")

    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    parsed = sections(result.stdout)
    assert parsed[HEADERS[0]] == ["16.4", "17.0"]
    assert parsed[HEADERS[1]] == [".iOS(.v17)", ".macOS(.v14)"]
    assert parsed[HEADERS[2]] == ["6.0"]
    assert parsed[HEADERS[3]] == ["SWIFT_VERSION = 6.0", "swiftLanguageModes: [.v6]"]
    assert parsed[HEADERS[4]] == ["SWIFT_STRICT_CONCURRENCY = complete"]
    assert parsed[HEADERS[5]] == ["1.17.0"]
    assert parsed[HEADERS[6]] == ["some-branch-pin main", "swift-composable-architecture 1.17.0", "swift-dependencies 1.6.2"]
    assert parsed[HEADERS[7]] == ["Testing: 1", "XCTest: 2"]
    assert parsed[HEADERS[8]] == ["@Observable: 1", "ObservableObject: 1"]


def test_bad_package_resolved_does_not_crash(tmp_path):
    (tmp_path / "Package.resolved").write_text("{not json", encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    parsed = sections(result.stdout)
    assert parsed[HEADERS[5]] == ["NOT_FOUND"]
    assert parsed[HEADERS[6]] == ["NONE"]
