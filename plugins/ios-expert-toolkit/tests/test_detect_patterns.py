#!/usr/bin/env python3
"""Behavior pins for the ios-conventions detect-patterns script."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts" / "detect-patterns.py"
PREFLIGHT = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts" / "preflight.py"
CACHE = Path(".artifacts/iet/cache/detected-patterns.json")

CATEGORIES = ["architecture", "di", "testing", "persistence", "concurrency", "navigation", "version"]


def run(*args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=cwd,
        check=False,
    )


def parse(out: str) -> dict:
    """Section -> {decisions, counts, facts}; decisions hold cands, dominant, consistency, verdict."""
    result, section, decision = {}, None, None
    for line in out.splitlines():
        if line.startswith("== "):
            section = line[3:-3]
            result[section] = {"decisions": {}, "counts": {}, "facts": {}, "lines": []}
            decision = None
            continue
        result[section]["lines"].append(line)
        if line.startswith("decision "):
            decision = line.split()[1]
            result[section]["decisions"][decision] = {"cands": {}}
        elif line.startswith("count "):
            _, ident, files = line.split()
            result[section]["counts"][ident] = int(files.split("=")[1])
        elif line.startswith("  dominant="):
            fields = dict(item.split("=") for item in line.split())
            entry = result[section]["decisions"][decision]
            entry["dominant"] = fields["dominant"]
            entry["consistency"] = fields["consistency"]
            entry["verdict"] = fields["verdict"]
        elif line.startswith("  "):
            ident, files, share = line.split()
            result[section]["decisions"][decision]["cands"][ident] = (
                int(files.split("=")[1]),
                share.split("=")[1],
            )
        elif "=" in line:
            key, value = line.split("=", 1)
            result[section]["facts"][key] = value
    return result


def sweep(project: Path, *categories) -> dict:
    result = run(project, *categories)
    assert result.returncode == 0, result.stderr
    return parse(result.stdout)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_fixture(name: str, tmp_path: Path) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


# ---- fixtures: dominant pattern, share, verdict per category ----


def test_tca_full_app_every_category():
    report = sweep(FIXTURES / "tca-full-app")
    assert report["architecture"]["counts"] == {
        "tca": 2, "mvvm_observable": 0, "mvvm_object": 0, "mvvm": 0, "uikit": 0, "feature_files": 6,
    }
    assert report["architecture"]["facts"] == {"verdict_architecture": "TCA"}

    di = report["di"]["decisions"]["di_style"]
    assert di["cands"] == {"tca_dependency": (3, "100.0%"), "factory": (0, "0.0%"), "singleton": (0, "0.0%")}
    assert (di["dominant"], di["consistency"], di["verdict"]) == ("tca_dependency", "100.0%", "match")

    testing = report["testing"]["decisions"]["testing_framework"]
    assert testing["cands"] == {"swift_testing": (1, "50.0%"), "xctest": (1, "50.0%")}
    assert (testing["dominant"], testing["verdict"]) == ("swift_testing", "conflict")

    persistence = report["persistence"]["decisions"]["persistence_framework"]
    assert persistence["cands"] == {"swiftdata": (1, "100.0%"), "core_data": (0, "0.0%")}
    assert persistence["verdict"] == "match"

    assert report["concurrency"]["decisions"] == {}
    assert report["concurrency"]["counts"] == {"language_mode_settings": 2, "main_actor": 1}

    navigation = report["navigation"]["decisions"]["navigation_style"]
    assert navigation["cands"] == {"navigation_stack": (1, "100.0%"), "coordinator": (0, "0.0%")}
    assert (navigation["dominant"], navigation["verdict"]) == ("navigation_stack", "match")

    assert report["version"]["decisions"] == {} and report["version"]["counts"] == {}
    assert report["version"]["facts"] == {
        "tca_version": "1.17.0",
        "deployment_target": "17.0",
        "swift_version": "6.0",
        "swift_language_modes": "[.v6]",
    }


def test_mvvm_observable_app_every_category():
    report = sweep(FIXTURES / "mvvm-observable-app")
    assert report["architecture"]["counts"] == {
        "tca": 0, "mvvm_observable": 3, "mvvm_object": 1, "mvvm": 4, "uikit": 1, "feature_files": 8,
    }
    assert report["architecture"]["facts"]["verdict_architecture"] == "MVVM"

    di = report["di"]["decisions"]["di_style"]
    assert di["cands"] == {"tca_dependency": (0, "0.0%"), "factory": (1, "50.0%"), "singleton": (1, "50.0%")}
    assert (di["dominant"], di["verdict"]) == ("factory", "conflict")

    testing = report["testing"]["decisions"]["testing_framework"]
    assert testing["cands"]["xctest"] == (1, "100.0%")
    assert testing["dominant"] == "xctest"

    persistence = report["persistence"]["decisions"]["persistence_framework"]
    assert persistence["cands"] == {"swiftdata": (0, "0.0%"), "core_data": (1, "100.0%")}

    assert report["concurrency"]["counts"] == {"language_mode_settings": 1, "main_actor": 0}
    navigation = report["navigation"]["decisions"]["navigation_style"]
    assert (navigation["dominant"], navigation["verdict"]) == ("coordinator", "match")

    assert report["version"]["facts"] == {
        "tca_version": "none",
        "deployment_target": "16.0",
        "swift_version": "5.0",
        "swift_language_modes": "none",
    }


def test_mixed_60_40_is_a_conflict():
    report = sweep(FIXTURES / "mixed-60-40-app")
    assert report["architecture"]["facts"]["verdict_architecture"] == "MIXED"
    di = report["di"]["decisions"]["di_style"]
    assert di["cands"]["tca_dependency"] == (3, "60.0%")
    assert di["cands"]["singleton"] == (2, "40.0%")
    assert (di["dominant"], di["consistency"], di["verdict"]) == ("tca_dependency", "60.0%", "conflict")


def test_empty_project_reports_no_data(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    report = parse(result.stdout)
    assert list(report)[1:] == CATEGORIES
    assert report["architecture"]["facts"] == {"verdict_architecture": "NEW"}
    assert not any(report["architecture"]["counts"].values())
    for section in ("di", "testing", "persistence", "navigation"):
        for decision in report[section]["decisions"].values():
            assert (decision["dominant"], decision["consistency"], decision["verdict"]) == ("none", "0.0%", "none")
            assert all(files == 0 for files, _ in decision["cands"].values())
    assert not any(report["concurrency"]["counts"].values())
    assert set(report["version"]["facts"].values()) == {"none"}


def test_project_section_lists_dir_hash_and_scanned_files():
    result = run(FIXTURES / "tca-full-app")
    head = result.stdout.splitlines()[:4]
    assert head[0] == "== project =="
    assert head[1] == f"dir={FIXTURES / 'tca-full-app'}"
    assert re.fullmatch(r"project_hash=[0-9a-f]{64}", head[2])
    assert head[3] == "files_scanned=10"


# ---- architecture verdict boundaries ----


def arch_project(tmp_path: Path, tca: int, mvvm: int, uikit: int = 0, extra: int = 0) -> Path:
    for i in range(tca):
        write(tmp_path / f"T{i}.swift", "@Reducer struct T {}\n")
    for i in range(mvvm):
        write(tmp_path / f"M{i}.swift", "@Observable final class M {}\n")
    for i in range(uikit):
        write(tmp_path / f"U{i}.swift", "final class U: UIViewController {}\n")
    for i in range(extra):
        write(tmp_path / f"E{i}.swift", "struct E {}\n")
    return tmp_path


def verdict_of(project: Path) -> str:
    return sweep(project, "architecture")["architecture"]["facts"]["verdict_architecture"]


@pytest.mark.parametrize(
    "tca,mvvm,uikit,extra,expected",
    [
        (0, 0, 0, 0, "NEW"),
        (4, 1, 0, 0, "TCA"),
        (19, 5, 0, 0, "MIXED"),
        (1, 4, 0, 0, "MVVM"),
        (1, 2, 2, 0, "MVVM"),
        (3, 2, 0, 0, "MIXED"),
        (0, 0, 0, 1, "MIXED"),
        (0, 5, 0, 0, "MVVM"),
        (5, 0, 0, 0, "TCA"),
    ],
)
def test_architecture_verdict_boundaries(tmp_path, tca, mvvm, uikit, extra, expected):
    assert verdict_of(arch_project(tmp_path, tca, mvvm, uikit, extra)) == expected


def test_observable_state_is_not_mvvm(tmp_path):
    write(tmp_path / "A.swift", "@Reducer struct A { @ObservableState struct State {} }\n")
    counts = sweep(tmp_path, "architecture")["architecture"]["counts"]
    assert (counts["tca"], counts["mvvm"]) == (1, 0)


def test_template_files_alone_are_new(tmp_path):
    write(tmp_path / "ContentView.swift", "struct ContentView {}\n")
    write(tmp_path / "App.swift", "@main struct App {}\n")
    assert verdict_of(tmp_path) == "NEW"


# ---- 80/20 boundaries (di) ----


def di_project(tmp_path: Path, tca: int, singleton: int, factory: int = 0) -> Path:
    for i in range(tca):
        write(tmp_path / f"D{i}.swift", "@Dependency(\\.x) var x\n")
    for i in range(singleton):
        write(tmp_path / f"S{i}.swift", "static let shared = S()\n")
    for i in range(factory):
        write(tmp_path / f"F{i}.swift", "func makeThing() {}\n")
    return tmp_path


@pytest.mark.parametrize(
    "tca,singleton,dominant,share,verdict",
    [
        (4, 1, "tca_dependency", "80.0%", "match"),
        (19, 5, "tca_dependency", "79.2%", "conflict"),
        (100, 0, "tca_dependency", "100.0%", "match"),
        (1, 1, "tca_dependency", "50.0%", "conflict"),
        (49, 51, "singleton", "51.0%", "conflict"),
        (1, 4, "singleton", "80.0%", "match"),
    ],
)
def test_matrix_boundaries(tmp_path, tca, singleton, dominant, share, verdict):
    di = sweep(di_project(tmp_path, tca, singleton), "di")["di"]["decisions"]["di_style"]
    assert (di["dominant"], di["consistency"], di["verdict"]) == (dominant, share, verdict)


@pytest.mark.parametrize(
    "counts,verdict",
    [((1, 1, 1), "adopt"), ((2, 2, 1), "adopt"), ((5, 5, 0), "conflict"), ((4, 3, 3), "adopt"), ((5, 3, 2), "conflict")],
)
def test_matrix_adopt_below_fifty(tmp_path, counts, verdict):
    tca, singleton, factory = counts
    di = sweep(di_project(tmp_path, tca, singleton, factory), "di")["di"]["decisions"]["di_style"]
    assert di["verdict"] == verdict


def test_file_counts_once_even_with_many_matching_lines(tmp_path):
    write(tmp_path / "A.swift", "@Dependency(\\.a) var a\n@Dependency(\\.b) var b\nDependencyKey\n")
    write(tmp_path / "B.swift", "static let shared = B()\n")
    di = sweep(tmp_path, "di")["di"]["decisions"]["di_style"]
    assert di["cands"]["tca_dependency"] == (1, "50.0%")
    assert di["cands"]["singleton"] == (1, "50.0%")


def test_tie_goes_to_first_declared_candidate(tmp_path):
    write(tmp_path / "S.swift", "static let shared = S()\n")
    write(tmp_path / "D.swift", "DependencyKey\n")
    assert sweep(tmp_path, "di")["di"]["decisions"]["di_style"]["dominant"] == "tca_dependency"


@pytest.mark.parametrize(
    "category,key,a_text,b_text,a_name,b_name",
    [
        ("testing", "testing_framework", "import Testing\n", "final class T: XCTestCase {}\n", "swift_testing", "xctest"),
        ("persistence", "persistence_framework", "@Model final class M {}\n", "class C: NSManagedObject {}\n", "swiftdata", "core_data"),
        ("navigation", "navigation_style", "NavigationStack {}\n", "final class AppCoordinator {}\n", "navigation_stack", "coordinator"),
    ],
)
def test_two_way_decisions(tmp_path, category, key, a_text, b_text, a_name, b_name):
    for i in range(4):
        write(tmp_path / f"A{i}.swift", a_text)
    write(tmp_path / "B.swift", b_text)
    decision = sweep(tmp_path, category)[category]["decisions"][key]
    assert decision["cands"] == {a_name: (4, "80.0%"), b_name: (1, "20.0%")}
    assert (decision["dominant"], decision["verdict"]) == (a_name, "match")


def test_model_word_boundary(tmp_path):
    write(tmp_path / "A.swift", "struct ModelCatalog {}\n// @ModelContext\n")
    assert sweep(tmp_path, "persistence")["persistence"]["decisions"]["persistence_framework"]["cands"]["swiftdata"][0] == 0


def test_navigation_destination_counts_as_navigation_stack(tmp_path):
    write(tmp_path / "A.swift", ".navigationDestination(for: Int.self) { _ in }\n")
    assert sweep(tmp_path, "navigation")["navigation"]["counts"] == {}
    nav = sweep(tmp_path, "navigation")["navigation"]["decisions"]["navigation_style"]
    assert nav["cands"]["navigation_stack"][0] == 1


# ---- prune rules ----


def test_prune_vendored_build_and_tooling_dirs(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    decoy = "@Reducer struct D {}\nstatic let shared = D()\nNavigationStack {}\n@MainActor\n"
    for rel in (
        "Pods/Lib/Decoy.swift",
        "Carthage/Lib/Decoy.swift",
        ".build/checkouts/Decoy.swift",
        "SourcePackages/Decoy.swift",
        "DerivedData/Decoy.swift",
        ".git/Decoy.swift",
        ".artifacts/Decoy.swift",
        "node_modules/pkg/Decoy.swift",
        "Features/HomePreview.swift",
        "Preview Content/Decoy.swift",
    ):
        write(project / rel, decoy)
    report = sweep(project)
    assert report["architecture"]["counts"]["tca"] == 2
    assert report["di"]["decisions"]["di_style"]["cands"]["singleton"] == (0, "0.0%")
    assert report["navigation"]["decisions"]["navigation_style"]["cands"]["navigation_stack"][0] == 1
    assert report["concurrency"]["counts"]["main_actor"] == 1
    # preview paths are not swept but still count as scanned Swift files
    assert "files_scanned=12" in run(project).stdout.splitlines()[:5]


def test_tests_dirs_pruned_for_architecture_but_kept_for_testing(tmp_path):
    write(tmp_path / "FeatureTests/A.swift", "@Reducer struct A {}\nimport Testing\nstatic let shared = 1\n")
    write(tmp_path / "App.swift", "struct X {}\n")
    report = sweep(tmp_path)
    assert report["architecture"]["counts"]["tca"] == 0
    assert report["di"]["decisions"]["di_style"]["cands"]["singleton"] == (0, "0.0%")
    assert report["testing"]["decisions"]["testing_framework"]["cands"]["swift_testing"] == (1, "100.0%")


def test_non_swift_files_are_ignored_by_swift_sweeps(tmp_path):
    write(tmp_path / "A.txt", "@Reducer\n")
    write(tmp_path / "B.m", "@interface NSManagedObject\n")
    report = sweep(tmp_path)
    assert report["architecture"]["counts"]["tca"] == 0
    assert report["persistence"]["decisions"]["persistence_framework"]["cands"]["core_data"][0] == 0


def test_symlinked_files_are_skipped(tmp_path):
    real = tmp_path / "outside" / "Real.swift"
    write(real, "static let shared = 1\n")
    project = tmp_path / "project"
    project.mkdir()
    (project / "Link.swift").symlink_to(real)
    assert sweep(project, "di")["di"]["decisions"]["di_style"]["cands"]["singleton"][0] == 0


def test_language_mode_settings_only_read_root_manifest_and_project(tmp_path):
    write(tmp_path / "Package.swift", "swiftLanguageModes: [.v6]\n")
    write(tmp_path / "App.xcodeproj/project.pbxproj", "SWIFT_VERSION = 5.0;\n")
    write(tmp_path / "Sub/Package.swift", "swiftLanguageModes: [.v6]\n")
    write(tmp_path / "Sub/App.xcodeproj/project.pbxproj", "SWIFT_VERSION = 5.0;\n")
    assert sweep(tmp_path, "concurrency")["concurrency"]["counts"]["language_mode_settings"] == 2


# ---- version facts ----


def test_version_facts_merge_unique_sorted_values(tmp_path):
    write(tmp_path / "A.xcodeproj/project.pbxproj", "IPHONEOS_DEPLOYMENT_TARGET = 17.0;\nIPHONEOS_DEPLOYMENT_TARGET = 16.4;\nSWIFT_VERSION = 6.0;\n")
    write(tmp_path / "Package.swift", "swiftLanguageModes: [.v5, .v6]\n")
    resolved = {"object": {"pins": [{"package": "swift-composable-architecture", "state": {"version": "1.9.0"}}]}, "version": 1}
    write(tmp_path / "Package.resolved", json.dumps(resolved))
    facts = sweep(tmp_path, "version")["version"]["facts"]
    assert facts == {
        "tca_version": "1.9.0",
        "deployment_target": "16.4, 17.0",
        "swift_version": "6.0",
        "swift_language_modes": "[.v5, .v6]",
    }


def test_version_ignores_branch_pins_and_bad_json(tmp_path):
    write(tmp_path / "Package.resolved", "{nope")
    write(tmp_path / "Sub/Package.resolved", json.dumps({"pins": [{"identity": "swift-composable-architecture", "state": {"branch": "main"}}]}))
    assert sweep(tmp_path, "version")["version"]["facts"]["tca_version"] == "none"


def test_version_prints_no_verdict(tmp_path):
    section = run(tmp_path, "version").stdout.split("== version ==")[1]
    assert "verdict" not in section and "decision" not in section


# ---- category filter ----


def test_default_runs_every_category_in_order():
    assert list(sweep(FIXTURES / "tca-full-app"))[1:] == CATEGORIES


def test_all_keyword_equals_default():
    assert run(FIXTURES / "mixed-60-40-app", "all").stdout == run(FIXTURES / "mixed-60-40-app").stdout


def test_category_filter_keeps_canonical_order():
    assert list(sweep(FIXTURES / "tca-full-app", "di", "architecture")) == ["project", "architecture", "di"]


def test_single_category():
    assert list(sweep(FIXTURES / "tca-full-app", "version")) == ["project", "version"]


def test_all_among_categories_expands_to_every_category():
    assert list(sweep(FIXTURES / "tca-full-app", "di", "all"))[1:] == CATEGORIES


def test_repeated_category_runs_once():
    assert list(sweep(FIXTURES / "tca-full-app", "di", "di")) == ["project", "di"]


def test_output_is_deterministic():
    first = run(FIXTURES / "tca-full-app").stdout
    assert first == run(FIXTURES / "tca-full-app").stdout


# ---- cache ----


def read_cache(project: Path) -> dict:
    return json.loads((project / CACHE).read_text(encoding="utf-8"))


def project_files_hash(project: Path) -> str:
    digest = hashlib.sha256()
    files = [project / "Package.swift"] + sorted(project.glob("*.xcodeproj/project.pbxproj"))
    for path in files:
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_no_cache_without_flag(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    assert run(project).returncode == 0
    assert not (project / ".artifacts").exists()


def test_write_cache_shape_and_keys(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    result = run(project, "--write-cache")
    assert result.returncode == 0, result.stderr
    cache = read_cache(project)
    assert set(cache) == {"timestamp", "project_hash", "patterns"}
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", cache["timestamp"])
    assert cache["project_hash"] == project_files_hash(project)
    patterns = cache["patterns"]
    assert set(patterns) == {
        "architecture", "di_style", "testing_framework", "persistence_framework", "navigation_style",
    }
    for entry in patterns.values():
        assert set(entry) == {"detected", "confidence", "evidence"}
        assert isinstance(entry["detected"], str)
        assert 0.0 <= entry["confidence"] <= 1.0
        assert all(isinstance(item, str) for item in entry["evidence"])
    assert patterns["architecture"] == {
        "detected": "TCA",
        "confidence": 1.0,
        "evidence": ["Sources/Features/CounterFeature.swift:tca", "Sources/Features/FeedFeature.swift:tca"],
    }
    assert patterns["di_style"]["detected"] == "tca_dependency"
    assert patterns["di_style"]["confidence"] == 1.0
    assert patterns["navigation_style"]["evidence"] == ["Sources/Features/CounterView.swift:navigation_stack"]


def test_cache_architecture_entry_per_verdict(tmp_path):
    cases = {
        "mvvm-observable-app": ("MVVM", 1.0),
        "mixed-60-40-app": ("MIXED", 0.6),
        "new-app": ("NEW", 1.0),
    }
    for name, (verdict, confidence) in cases.items():
        project = copy_fixture(name, tmp_path)
        run(project, "--write-cache")
        entry = read_cache(project)["patterns"]["architecture"]
        assert (entry["detected"], entry["confidence"]) == (verdict, confidence), name
        assert len(entry["evidence"]) == (0 if verdict == "NEW" else 3), name


def test_cache_architecture_mvvm_evidence_includes_uikit_when_few_mvvm(tmp_path):
    write(tmp_path / "A.swift", "final class A: UIViewController {}\n")
    run(tmp_path, "--write-cache")
    assert read_cache(tmp_path)["patterns"]["architecture"]["evidence"] == ["A.swift:uikit"]


def test_cache_architecture_mixed_without_signal(tmp_path):
    write(tmp_path / "A.swift", "struct A {}\n")
    run(tmp_path, "--write-cache")
    assert read_cache(tmp_path)["patterns"]["architecture"] == {"detected": "MIXED", "confidence": 0.0, "evidence": []}


def test_cache_confidence_is_the_dominant_share(tmp_path):
    project = copy_fixture("mixed-60-40-app", tmp_path)
    run(project, "--write-cache")
    entry = read_cache(project)["patterns"]["di_style"]
    assert (entry["detected"], entry["confidence"]) == ("tca_dependency", 0.6)
    assert len(entry["evidence"]) == 3


def test_cache_with_no_matches_reports_none(tmp_path):
    run(tmp_path, "--write-cache")
    entry = read_cache(tmp_path)["patterns"]["di_style"]
    assert entry == {"detected": "none", "confidence": 0.0, "evidence": []}


def test_cache_hash_matches_preflight(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "--write-cache")
    out = subprocess.run(
        [sys.executable, str(PREFLIGHT)], cwd=project, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert out[out.index("== Project hash ==") + 1] == read_cache(project)["project_hash"]
    assert f"project_hash={read_cache(project)['project_hash']}" in run(project).stdout


def test_cache_hash_without_project_files(tmp_path):
    run(tmp_path, "--write-cache")
    assert read_cache(tmp_path)["project_hash"] == "NO_PROJECT_FILES"


def test_cache_hash_is_sha256_of_package_then_pbxproj(tmp_path):
    write(tmp_path / "Package.swift", "a\n")
    write(tmp_path / "B.xcodeproj/project.pbxproj", "c\n")
    write(tmp_path / "A.xcodeproj/project.pbxproj", "b\n")
    run(tmp_path, "--write-cache")
    assert read_cache(tmp_path)["project_hash"] == hashlib.sha256(b"a\nb\nc\n").hexdigest()


def test_cache_only_holds_requested_categories(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "di", "--write-cache")
    assert set(read_cache(project)["patterns"]) == {"di_style"}


def test_version_and_concurrency_write_no_cache_entries(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "version", "concurrency", "--write-cache")
    assert read_cache(project)["patterns"] == {}


def test_cache_merges_categories_while_hash_unchanged(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "di", "--write-cache")
    run(project, "architecture", "--write-cache")
    assert {"di_style", "architecture"} <= set(read_cache(project)["patterns"])


def test_cache_drops_old_entries_when_hash_changed(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "di", "--write-cache")
    write(project / "Package.swift", "// changed\n")
    run(project, "architecture", "--write-cache")
    cache = read_cache(project)
    assert set(cache["patterns"]) == {"architecture"}
    assert cache["project_hash"] == project_files_hash(project)


def test_cache_replaces_corrupt_file(tmp_path):
    write(tmp_path / CACHE, "{not json")
    assert run(tmp_path, "--write-cache").returncode == 0
    assert "patterns" in read_cache(tmp_path)


def test_cache_ignores_cwd(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert run(project, "--write-cache", cwd=elsewhere).returncode == 0
    assert (project / CACHE).is_file()
    assert not (elsewhere / ".artifacts").exists()


def test_cache_is_not_scanned_as_source(tmp_path):
    project = copy_fixture("tca-full-app", tmp_path)
    run(project, "--write-cache")
    assert sweep(project)["project"]["lines"][2] == "files_scanned=10"


# ---- usage errors ----


def test_no_arguments_is_a_usage_error():
    result = run()
    assert result.returncode == 2
    assert "usage" in result.stderr.lower()


def test_missing_directory(tmp_path):
    result = run(tmp_path / "nope")
    assert result.returncode == 2
    assert f"{tmp_path / 'nope'}: No such directory" in result.stderr
    assert result.stdout == ""


def test_path_that_is_a_file(tmp_path):
    write(tmp_path / "f.txt", "x")
    result = run(tmp_path / "f.txt")
    assert result.returncode == 2
    assert "No such directory" in result.stderr


def test_unknown_category(tmp_path):
    result = run(tmp_path, "security")
    assert result.returncode == 2
    assert "security" in result.stderr
    assert not (tmp_path / ".artifacts").exists()


def test_unknown_option(tmp_path):
    assert run(tmp_path, "--bogus").returncode == 2


def test_missing_directory_writes_no_cache(tmp_path):
    result = run(tmp_path / "nope", "--write-cache")
    assert result.returncode == 2
    assert not (tmp_path / "nope").exists()


def test_script_is_executable_python3():
    assert os.access(SCRIPT, os.X_OK)
    assert SCRIPT.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3\n")
    assert '"""' in SCRIPT.read_text(encoding="utf-8").split("\n", 2)[1]
