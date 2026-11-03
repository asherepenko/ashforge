#!/usr/bin/env python3
"""Pre-flight context for the android-conventions skill.

Output is labeled with `== section ==` headers.
Use the output to:
  1. Skip the cache compute step if hash matches cached project_hash (Step 1.5)
  2. Decide whether full Grep sweep is needed (skip if file count < 50)
  3. Pre-bias detection categories (e.g., DI fingerprint suggests Hilt -> skip Koin/Dagger sweeps)
"""

import hashlib
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


def matching_files(pattern, limit=5):
    found = [p for p in kotlin_files() if any(pattern.search(line) for line in lines_of(p))]
    return found[:limit]


def project_hash():
    names = [n for n in ("settings.gradle.kts", "build.gradle.kts") if os.path.isfile(n)]
    if not names:
        return "NO_GRADLE_FILES"
    digest = hashlib.sha256()
    for name in names:
        digest.update(Path(name).read_bytes())
    return digest.hexdigest()


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
    out.append(str(sum(1 for p in kotlin_files() for line in lines_of(p) if STATE.search(line))))

    out.append("== Testing fingerprint ==")
    out += matching_files(TESTING) or ["NO_TEST_MARKERS"]

    print("\n".join(out))


if __name__ == "__main__":
    main()
