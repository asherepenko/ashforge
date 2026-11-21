#!/usr/bin/env python3
"""Pre-flight context for the android-conventions skill.

Output is labeled with `== section ==` headers.
Use the output to:
  1. Skip the cache compute step if hash matches cached project_hash (Step 1.5); the hash is the
     content key from detect-patterns.py (scanned code and build files at any depth)
  2. Decide whether full Grep sweep is needed (skip if file count < 50)
  3. Pre-bias detection categories (e.g., DI fingerprint suggests Hilt -> skip Koin/Dagger sweeps)

The DI, state and testing fingerprints match code only: comments and string contents are blanked
with strip_code from detect-patterns.py, as the sweeps do.
"""

import functools
import importlib.util
import os
import re
from pathlib import Path

CACHE = Path(".artifacts/aet/cache/detected-patterns.json")
DI = re.compile(r"@HiltAndroidApp|@HiltViewModel|startKoin\(|@Component")
STATE = re.compile(r"(StateFlow<|LiveData<|MutableLiveData<)")
TESTING = re.compile(r"@Test|mockk<|class Test[A-Z]|class Fake")


def kotlin_files():
    """Every *.kt under the working directory, as ./relative paths."""
    for dirpath, _dirs, files in os.walk("."):
        for name in files:
            if name.endswith(".kt"):
                yield os.path.join(dirpath, name)


def lines_of(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()
    except OSError:
        return []


def code_lines_of(path):
    """Lines of a Kotlin file with comments and string contents blanked (strip_code from detect-patterns.py)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return detect_patterns().strip_code(handle.read()).splitlines()
    except OSError:
        return []


def matching_files(pattern, limit=5):
    found = [p for p in kotlin_files() if any(pattern.search(line) for line in code_lines_of(p))]
    return found[:limit]


@functools.lru_cache(maxsize=None)
def detect_patterns():
    """detect-patterns.py, loaded once from the sibling file: the only copy of project_hash and strip_code."""
    path = Path(__file__).resolve().with_name("detect-patterns.py")
    spec = importlib.util.spec_from_file_location("detect_patterns", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_hash():
    """The content key from detect-patterns.py."""
    return detect_patterns().project_hash(Path("."))


def kotlin_count():
    skipped = ("build", ".gradle")
    return sum(
        1
        for p in kotlin_files()
        if not any(f"/{d}/" in p for d in skipped)
    )


def main():
    out = ["== Project hash ==", project_hash(), "== Cached patterns =="]
    if CACHE.is_file():
        out += lines_of(CACHE)[:30]
    else:
        out.append("NO_CACHE")

    out += ["== Kotlin file count ==", str(kotlin_count())]

    out.append("== DI fingerprint ==")
    out += matching_files(DI) or ["NO_DI_MARKERS"]

    out.append("== State fingerprint (StateFlow|LiveData|MutableLiveData counts) ==")
    out.append(str(sum(1 for p in kotlin_files() for line in code_lines_of(p) if STATE.search(line))))

    out.append("== Testing fingerprint ==")
    out += matching_files(TESTING) or ["NO_TEST_MARKERS"]

    print("\n".join(out))


if __name__ == "__main__":
    main()
