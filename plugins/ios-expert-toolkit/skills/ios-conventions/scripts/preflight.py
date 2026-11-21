#!/usr/bin/env python3
"""Pre-flight context for the ios-conventions skill.

Read-only. Run from the project root. Output is labeled with `== section ==`
headers. Missing files print NOT_FOUND or NONE; the script never fails hard.
Use the output for the cache-hit check (project hash against the cached
`project_hash`), the version sweep, and to pre-bias the testing and
architecture sweeps.
"""

import importlib.util
import json
import os
import re
from pathlib import Path

CACHE = Path(".artifacts/iet/cache/detected-patterns.json")
SKIP_DIRS = {".build", "Pods", "Carthage", "SourcePackages", "DerivedData", ".git"}
DEPLOY = re.compile(r"IPHONEOS_DEPLOYMENT_TARGET\s*=\s*([\d.]+)")
SWIFT_VERSION = re.compile(r"SWIFT_VERSION\s*=\s*([\d.]+)")
STRICT = re.compile(r"SWIFT_STRICT_CONCURRENCY\s*=\s*(\w+)")
TOOLS = re.compile(r"swift-tools-version\s*:\s*([\d.]+)")
PLATFORM = re.compile(r"\.(?:iOS|macOS|tvOS|watchOS|visionOS|macCatalyst)\([^)]*\)")
LANG_MODES = re.compile(r"swiftLanguageModes\s*:\s*\[[^\]]*\]")
STRICT_SPM = re.compile(r"\.enableUpcomingFeature\(\"StrictConcurrency\"\)|\.enableExperimentalFeature\(\"StrictConcurrency[^\"]*\"\)")
TESTING = re.compile(r"^\s*(?:@testable\s+)?import\s+Testing\b", re.M)
XCTEST = re.compile(r"^\s*import\s+XCTest\b", re.M)
OBSERVABLE = re.compile(r"@Observable\b")
OBSERVABLE_OBJECT = re.compile(r"\bObservableObject\b")


def walk(suffix=None, name=None):
    """Files under the working directory, skipping vendored and build dirs."""
    for dirpath, dirs, files in os.walk("."):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if (suffix and f.endswith(suffix)) or (name and f == name):
                yield os.path.join(dirpath, f)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def pbxproj_text():
    return "\n".join(read(p) for p in walk(name="project.pbxproj") if ".xcodeproj" in p)


def package_text():
    return "\n".join(read(p) for p in walk(name="Package.swift"))


def resolved_pins():
    pins = {}
    for path in walk(name="Package.resolved"):
        try:
            data = json.loads(read(path))
        except ValueError:
            continue
        entries = data.get("pins") or data.get("object", {}).get("pins") or []
        for pin in entries:
            ident = pin.get("identity") or pin.get("package", "").lower()
            state = pin.get("state") or {}
            pins[ident] = state.get("version") or state.get("branch") or state.get("revision", "?")[:7]
    return pins


def detect_patterns():
    """The sibling detect-patterns.py module; the hyphen rules out a plain import."""
    spec = importlib.util.spec_from_file_location("detect_patterns", Path(__file__).with_name("detect-patterns.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_hash():
    """The cache key, computed by detect-patterns.py so both scripts always agree."""
    return detect_patterns().project_hash(Path("."))


def cached_patterns():
    if not CACHE.is_file():
        return ["NO_CACHE"]
    return read(CACHE).splitlines()[:40]


def unique(values):
    return sorted(set(values)) or ["NOT_FOUND"]


def count_files(pattern, sources):
    return sum(1 for text in sources if pattern.search(text))


def main():
    pbx, pkg, pins = pbxproj_text(), package_text(), resolved_pins()
    strip = detect_patterns().strip_code
    sources = [strip(read(p)) for p in walk(suffix=".swift") if not p.endswith("Package.swift")]

    lang = [f"SWIFT_VERSION = {v}" for v in sorted(set(SWIFT_VERSION.findall(pbx)))]
    lang += sorted(set(LANG_MODES.findall(pkg)))
    strict = [f"SWIFT_STRICT_CONCURRENCY = {v}" for v in sorted(set(STRICT.findall(pbx)))]
    strict += sorted(set(STRICT_SPM.findall(pkg)))

    out = ["== Project hash ==", project_hash(), "== Cached patterns =="] + cached_patterns()
    out += ["== Deployment targets (IPHONEOS_DEPLOYMENT_TARGET) =="]
    out += unique(DEPLOY.findall(pbx))
    out += ["== Package platforms =="] + unique(PLATFORM.findall(pkg))
    out += ["== swift-tools-version =="] + unique(TOOLS.findall(pkg))
    out += ["== Swift language mode (SWIFT_VERSION|swiftLanguageModes) =="] + (lang or ["NOT_FOUND"])
    out += ["== Strict concurrency =="] + (strict or ["NOT_FOUND"])
    out += ["== TCA (swift-composable-architecture) =="]
    out.append(pins.get("swift-composable-architecture", "NOT_FOUND"))
    out += ["== Key packages =="] + ([f"{k} {v}" for k, v in sorted(pins.items())] or ["NONE"])
    out += ["== Test frameworks (import Testing|import XCTest file counts) =="]
    out += [f"Testing: {count_files(TESTING, sources)}", f"XCTest: {count_files(XCTEST, sources)}"]
    out += ["== Observation (@Observable|ObservableObject file counts) =="]
    out += [
        f"@Observable: {count_files(OBSERVABLE, sources)}",
        f"ObservableObject: {count_files(OBSERVABLE_OBJECT, sources)}",
    ]
    print("\n".join(out))


if __name__ == "__main__":
    main()
