#!/usr/bin/env python3
"""Behavior pins for the android-conventions pre-flight script."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "preflight.py"
DETECT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "detect-patterns.py"

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
    assert parsed[HEADERS[0]] == ["NO_PROJECT_FILES"]
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
    expected_hash = detect_hash(tmp_path)
    assert parsed[HEADERS[0]] == [expected_hash]
    assert parsed[HEADERS[1]] == [f"line{i}" for i in range(30)]
    assert parsed[HEADERS[2]] == ["2"]
    assert parsed[HEADERS[3]] == ["./app/A.kt"]
    # Counts matching lines, not occurrences, and does not skip build/: A.kt has 2, build/Gen.kt 1.
    assert parsed[HEADERS[4]] == ["3"]
    assert parsed[HEADERS[5]] == ["./app/ATest.kt"]


def detect_hash(project: Path) -> str:
    out = subprocess.run(
        [sys.executable, str(DETECT), "--hash", str(project)], capture_output=True, text=True, check=True
    ).stdout
    return out.strip().split("=", 1)[1]


def test_hash_with_only_build_file(tmp_path):
    (tmp_path / "build.gradle.kts").write_text("a\n", encoding="utf-8")
    parsed = sections(run(tmp_path).stdout)
    line = f"build.gradle.kts\t{hashlib.sha256(b'a' + bytes([10])).hexdigest()}\n"
    assert parsed[HEADERS[0]] == [hashlib.sha256(line.encode()).hexdigest()]


def test_hash_agrees_with_detect_patterns_for_nested_project(tmp_path):
    (tmp_path / "proj" / "app").mkdir(parents=True)
    (tmp_path / "proj" / "app" / "build.gradle.kts").write_text("plugins {}\n", encoding="utf-8")
    (tmp_path / "proj" / "app" / "A.kt").write_text("class A\n", encoding="utf-8")
    value = sections(run(tmp_path).stdout)[HEADERS[0]]
    assert value == [detect_hash(tmp_path)]
    assert value != ["NO_PROJECT_FILES"]


def test_hash_changes_with_source_edit(tmp_path):
    (tmp_path / "A.kt").write_text("class A\n", encoding="utf-8")
    before = sections(run(tmp_path).stdout)[HEADERS[0]]
    (tmp_path / "A.kt").write_text("class B\n", encoding="utf-8")
    assert sections(run(tmp_path).stdout)[HEADERS[0]] != before


def test_preflight_has_no_second_hash_implementation():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "detect-patterns.py" in text
    assert "sha256" not in text


def test_runs_from_other_cwd_without_plugin_root_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.endswith("PLUGIN_ROOT")}
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert list(sections(result.stdout)) == HEADERS


def test_fingerprints_ignore_comments_and_strings(tmp_path):
    (tmp_path / "A.kt").write_text(
        '// @HiltViewModel\n/* @Component\n StateFlow<X> */\nval s = "startKoin( LiveData<Int> @Test"\n',
        encoding="utf-8",
    )
    parsed = sections(run(tmp_path).stdout)
    assert parsed[HEADERS[3]] == ["NO_DI_MARKERS"]
    assert parsed[HEADERS[4]] == ["0"]
    assert parsed[HEADERS[5]] == ["NO_TEST_MARKERS"]
    (tmp_path / "A.kt").write_text("/* c */\n@HiltViewModel\nclass A\n", encoding="utf-8")
    assert sections(run(tmp_path).stdout)[HEADERS[3]] == ["./A.kt"]


def test_preflight_has_no_second_strip_code():
    assert "def strip_code" not in SCRIPT.read_text(encoding="utf-8")
