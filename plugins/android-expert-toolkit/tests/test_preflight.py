#!/usr/bin/env python3
"""Behavior pins for the android-conventions pre-flight script."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "preflight.py"

HEADERS = [
    "== Project hash ==",
    "== Cached patterns ==",
    "== Kotlin file count ==",
    "== DI fingerprint ==",
    "== State fingerprint (StateFlow|LiveData|MutableLiveData counts) ==",
    "== Testing fingerprint ==",
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
    assert result.returncode == 0
    parsed = sections(result.stdout)
    assert list(parsed) == HEADERS
    assert parsed[HEADERS[0]] == ["NO_GRADLE_FILES"]
    assert parsed[HEADERS[1]] == ["NO_CACHE"]
    assert parsed[HEADERS[2]] == ["0"]
    assert parsed[HEADERS[3]] == ["NO_DI_MARKERS"]
    assert parsed[HEADERS[4]] == ["0"]
    assert parsed[HEADERS[5]] == ["NO_TEST_MARKERS"]


def test_populated_project(tmp_path):
    settings = "rootProject.name = \"x\"\n"
    (tmp_path / "settings.gradle.kts").write_text(settings, encoding="utf-8")
    (tmp_path / "build.gradle.kts").write_text("plugins {}\n", encoding="utf-8")
    cache = tmp_path / ".artifacts" / "aet" / "cache"
    cache.mkdir(parents=True)
    (cache / "detected-patterns.json").write_text("".join(f"line{i}\n" for i in range(40)), encoding="utf-8")
    src = tmp_path / "app"
    src.mkdir()
    (src / "A.kt").write_text("@HiltViewModel\nclass A { val s: StateFlow<Int>; val l: LiveData<Int> }\nval m: MutableLiveData<X>\n", encoding="utf-8")
    (src / "ATest.kt").write_text("@Test\nfun t() {}\n", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "Gen.kt").write_text("StateFlow<X>\n", encoding="utf-8")
    (tmp_path / ".gradle").mkdir()
    (tmp_path / ".gradle" / "G.kt").write_text("x\n", encoding="utf-8")

    result = run(tmp_path)
    assert result.returncode == 0
    parsed = sections(result.stdout)
    expected_hash = hashlib.sha256((settings + "plugins {}\n").encode()).hexdigest()
    assert parsed[HEADERS[0]] == [expected_hash]
    assert parsed[HEADERS[1]] == [f"line{i}" for i in range(30)]
    assert parsed[HEADERS[2]] == ["2"]
    assert parsed[HEADERS[3]] == ["./app/A.kt"]
    # Counts matching lines, not occurrences, and does not skip build/: A.kt has 2, build/Gen.kt 1.
    assert parsed[HEADERS[4]] == ["3"]
    assert parsed[HEADERS[5]] == ["./app/ATest.kt"]


def test_hash_with_only_build_file(tmp_path):
    (tmp_path / "build.gradle.kts").write_text("a\n", encoding="utf-8")
    parsed = sections(run(tmp_path).stdout)
    assert parsed[HEADERS[0]] == [hashlib.sha256(b"a\n").hexdigest()]


def test_runs_from_other_cwd_without_plugin_root_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.endswith("PLUGIN_ROOT")}
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert list(sections(result.stdout)) == HEADERS
