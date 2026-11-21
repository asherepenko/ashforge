#!/usr/bin/env python3
"""Behavior pins for the android-conventions detect-patterns script."""

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
SCRIPT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "detect-patterns.py"
PREFLIGHT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "preflight.py"
CACHE = Path(".artifacts/aet/cache/detected-patterns.json")

CATEGORIES = ["state", "di", "testing", "architecture", "security", "performance", "accessibility"]


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
    """Section name -> {decisions: {name: {cands, dominant, consistency, verdict}}, counts: {id: files}}."""
    result, section, decision = {}, None, None
    for line in out.splitlines():
        if line.startswith("== "):
            section = line[3:-3]
            result[section] = {"decisions": {}, "counts": {}, "lines": []}
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


def test_hilt_stateflow_app_state_and_di():
    report = sweep(FIXTURES / "hilt-stateflow-app")
    state = report["state"]["decisions"]["state_management"]
    assert state["cands"] == {"livedata": (0, "0.0%"), "stateflow": (2, "100.0%"), "rxjava": (0, "0.0%")}
    assert (state["dominant"], state["consistency"], state["verdict"]) == ("stateflow", "100.0%", "match")
    assert report["state"]["counts"] == {"flow": 3}

    di = report["di"]["decisions"]["di_framework"]
    assert di["cands"] == {
        "hilt": (3, "100.0%"),
        "dagger": (0, "0.0%"),
        "koin": (0, "0.0%"),
        "manual": (0, "0.0%"),
    }
    assert (di["dominant"], di["verdict"]) == ("hilt", "match")


def test_hilt_stateflow_app_testing_and_architecture():
    report = sweep(FIXTURES / "hilt-stateflow-app")
    mocks = report["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"] == {"mockito": (0, "0.0%"), "mockk": (0, "0.0%"), "test_doubles": (1, "100.0%")}
    assert (mocks["dominant"], mocks["verdict"]) == ("test_doubles", "match")
    asserts = report["testing"]["decisions"]["testing_assertions"]
    assert asserts["cands"] == {"assertthat": (1, "100.0%"), "junit": (0, "0.0%")}
    assert asserts["dominant"] == "assertthat"
    assert report["testing"]["counts"] == {"turbine": 1}

    ui = report["architecture"]["decisions"]["ui_framework"]
    assert ui["cands"] == {"compose": (1, "100.0%"), "xml_layout": (0, "0.0%")}
    assert (ui["dominant"], ui["verdict"]) == ("compose", "match")
    presentation = report["architecture"]["decisions"]["presentation"]
    assert presentation["cands"] == {"viewmodel": (2, "100.0%"), "presenter": (0, "0.0%")}
    assert report["architecture"]["counts"] == {"repository": 4, "usecase": 0, "activity": 1, "fragment": 0}


def test_hilt_stateflow_app_presence_categories():
    report = sweep(FIXTURES / "hilt-stateflow-app")
    assert report["security"]["decisions"] == {}
    assert report["security"]["counts"] == {
        "network_security_config": 1,
        "certificate_pinning": 0,
        "encrypted_storage": 0,
        "hardcoded_secrets": 1,
        "proguard_rules": 1,
        "cleartext_traffic": 1,
    }
    assert report["performance"]["counts"] == {
        "baseline_profile_file": 0,
        "baseline_profile_generator": 0,
        "global_scope": 1,
        "lazy_items_without_key": 1,
        "state_in_without_while_subscribed": 1,
        "launch_without_dispatcher": 1,
    }
    assert report["accessibility"]["counts"] == {
        "icon_without_content_description": 1,
        "image_without_content_description": 1,
        "semantics": 1,
        "merge_descendants": 0,
        "clickable": 1,
        "min_touch_target": 0,
    }


def test_koin_livedata_app_counts_java_and_xml():
    report = sweep(FIXTURES / "koin-livedata-app")
    state = report["state"]["decisions"]["state_management"]
    assert state["cands"]["livedata"] == (2, "100.0%")
    assert (state["dominant"], state["verdict"]) == ("livedata", "match")
    di = report["di"]["decisions"]["di_framework"]
    assert di["cands"]["koin"] == (2, "100.0%")
    assert di["dominant"] == "koin"
    ui = report["architecture"]["decisions"]["ui_framework"]
    assert ui["cands"] == {"compose": (0, "0.0%"), "xml_layout": (2, "100.0%")}
    assert ui["dominant"] == "xml_layout"
    assert report["architecture"]["counts"]["fragment"] == 1
    mocks = report["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["mockito"] == (1, "100.0%")
    assert report["testing"]["decisions"]["testing_assertions"]["dominant"] == "junit"


def test_mixed_60_40_is_a_conflict_everywhere():
    report = sweep(FIXTURES / "mixed-60-40-app")
    di = report["di"]["decisions"]["di_framework"]
    assert di["cands"]["hilt"] == (3, "60.0%")
    assert di["cands"]["koin"] == (2, "40.0%")
    assert (di["dominant"], di["consistency"], di["verdict"]) == ("hilt", "60.0%", "conflict")
    state = report["state"]["decisions"]["state_management"]
    assert state["cands"]["stateflow"] == (3, "60.0%")
    assert state["cands"]["livedata"] == (2, "40.0%")
    assert state["verdict"] == "conflict"


def test_empty_project_reports_no_data(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    report = parse(result.stdout)
    assert list(report)[1:] == CATEGORIES
    for section in ("state", "di", "testing", "architecture"):
        for decision in report[section]["decisions"].values():
            assert (decision["dominant"], decision["consistency"], decision["verdict"]) == ("none", "0.0%", "none")
            assert all(files == 0 for files, _ in decision["cands"].values())
    for section in ("security", "performance", "accessibility"):
        assert report[section]["counts"] and not any(report[section]["counts"].values())


def test_project_section_lists_dir_hash_and_scanned_files():
    result = run(FIXTURES / "hilt-stateflow-app")
    head = result.stdout.splitlines()[:4]
    assert head[0] == "== project =="
    assert head[1] == f"dir={FIXTURES / 'hilt-stateflow-app'}"
    assert re.fullmatch(r"project_hash=[0-9a-f]{64}", head[2])
    assert head[3] == "files_scanned=8"


# ---- 80/20 boundaries ----


def di_project(tmp_path: Path, hilt: int, koin: int) -> Path:
    for i in range(hilt):
        write(tmp_path / f"H{i}.kt", "@HiltViewModel\nclass H : ViewModel()\n")
    for i in range(koin):
        write(tmp_path / f"K{i}.kt", "val x = koinViewModel()\n")
    return tmp_path


@pytest.mark.parametrize(
    "hilt,koin,dominant,share,verdict",
    [
        (4, 1, "hilt", "80.0%", "match"),
        (19, 5, "hilt", "79.2%", "conflict"),
        (100, 0, "hilt", "100.0%", "match"),
        (1, 1, "hilt", "50.0%", "conflict"),
        (49, 51, "koin", "51.0%", "conflict"),
        (3, 7, "koin", "70.0%", "conflict"),
        (1, 4, "koin", "80.0%", "match"),
    ],
)
def test_matrix_boundaries(tmp_path, hilt, koin, dominant, share, verdict):
    di = sweep(di_project(tmp_path, hilt, koin))["di"]["decisions"]["di_framework"]
    assert (di["dominant"], di["consistency"], di["verdict"]) == (dominant, share, verdict)


@pytest.mark.parametrize(
    "counts,verdict",
    [
        ((1, 1, 1, 1), "adopt"),
        ((2, 2, 1, 0), "adopt"),
        ((5, 5, 0, 0), "conflict"),
        ((4, 3, 2, 1), "adopt"),
        ((5, 3, 1, 1), "conflict"),
    ],
)
def test_matrix_adopt_below_fifty(tmp_path, counts, verdict):
    hilt, koin, dagger, manual = counts
    for i in range(hilt):
        write(tmp_path / f"H{i}.kt", "@HiltViewModel\n")
    for i in range(koin):
        write(tmp_path / f"K{i}.kt", "startKoin {}\n")
    for i in range(dagger):
        write(tmp_path / f"D{i}.kt", "@Component\n")
    for i in range(manual):
        write(tmp_path / f"M{i}.kt", "object F : ViewModelProvider.Factory\n")
    di = sweep(tmp_path, "di")["di"]["decisions"]["di_framework"]
    assert di["verdict"] == verdict


def test_file_counts_once_even_with_many_matching_lines(tmp_path):
    write(tmp_path / "A.kt", "@HiltViewModel\n@Inject\n@HiltAndroidApp\n")
    write(tmp_path / "B.kt", "startKoin {}\n")
    di = sweep(tmp_path, "di")["di"]["decisions"]["di_framework"]
    assert di["cands"]["hilt"] == (1, "50.0%")
    assert di["cands"]["koin"] == (1, "50.0%")


def test_tie_goes_to_first_declared_candidate(tmp_path):
    write(tmp_path / "K.kt", "startKoin {}\n")
    write(tmp_path / "H.kt", "@HiltViewModel\n")
    assert sweep(tmp_path, "di")["di"]["decisions"]["di_framework"]["dominant"] == "hilt"


# ---- prune rules ----


def test_prune_build_generated_and_tooling_dirs(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    decoy = "startKoin {}\n@Composable\nGlobalScope.launch {}\n"
    for rel in (
        "app/build/generated/Decoy.kt",
        "build/Decoy.kt",
        ".gradle/Decoy.kt",
        ".idea/Decoy.kt",
        ".git/Decoy.kt",
        "node_modules/pkg/Decoy.kt",
        "app/src/main/generated/Decoy.kt",
        "generated/Decoy.kt",
        "app/build/res/layout/decoy.xml",
        "app/build/proguard-rules.pro",
    ):
        write(project / rel, decoy)
    report = sweep(project)
    assert report["di"]["decisions"]["di_framework"]["cands"]["koin"] == (0, "0.0%")
    assert report["architecture"]["decisions"]["ui_framework"]["cands"] == {
        "compose": (1, "100.0%"),
        "xml_layout": (0, "0.0%"),
    }
    assert report["performance"]["counts"]["global_scope"] == 1
    assert report["security"]["counts"]["proguard_rules"] == 1
    assert "files_scanned=8" in run(project).stdout.splitlines()[:5]


def test_test_directories_are_kept(tmp_path):
    write(tmp_path / "app/src/test/FakeUserRepository.kt", "class FakeUserRepository\n")
    write(tmp_path / "app/src/androidTest/FakeAuthRepository.kt", "class FakeAuthRepository\n")
    mocks = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["test_doubles"] == (2, "100.0%")


def test_secrets_ignore_test_and_mock_paths_and_lines(tmp_path):
    key = '"abcdefghijklmnopqrstuvwxyz0123456789ABCD"'
    write(tmp_path / "app/src/main/Real.kt", f"val k = {key}\n")
    write(tmp_path / "app/src/test/Secret.kt", f"val k = {key}\n")
    write(tmp_path / "app/src/main/MockKeys.kt", f"val k = {key}\n")
    write(tmp_path / "app/src/main/Other.kt", f"val mockKey = {key}\n")
    write(tmp_path / "app/src/main/Short.kt", 'val k = "tooshort"\n')
    assert sweep(tmp_path, "security")["security"]["counts"]["hardcoded_secrets"] == 1


def test_lines_with_content_description_are_not_flagged(tmp_path):
    write(
        tmp_path / "A.kt",
        'Icon(Icons.Default.Add, contentDescription = "add")\nImage(painter, contentDescription = null)\n',
    )
    counts = sweep(tmp_path, "accessibility")["accessibility"]["counts"]
    assert counts["icon_without_content_description"] == 0
    assert counts["image_without_content_description"] == 0


def test_symlinked_files_are_skipped(tmp_path):
    real = tmp_path / "outside" / "Real.kt"
    write(real, "@HiltViewModel\n")
    project = tmp_path / "project"
    project.mkdir()
    (project / "Link.kt").symlink_to(real)
    assert sweep(project, "di")["di"]["decisions"]["di_framework"]["cands"]["hilt"][0] == 0


# ---- category filter ----


def test_default_runs_every_category_in_order():
    assert list(sweep(FIXTURES / "hilt-stateflow-app"))[1:] == CATEGORIES


def test_all_keyword_equals_default():
    assert run(FIXTURES / "mixed-60-40-app", "all").stdout == run(FIXTURES / "mixed-60-40-app").stdout


def test_category_filter_limits_sections():
    report = sweep(FIXTURES / "hilt-stateflow-app", "di", "state")
    assert list(report) == ["project", "state", "di"]


def test_single_category():
    assert list(sweep(FIXTURES / "hilt-stateflow-app", "security")) == ["project", "security"]


def test_all_among_categories_expands_to_every_category():
    assert list(sweep(FIXTURES / "hilt-stateflow-app", "di", "all"))[1:] == CATEGORIES


def test_repeated_category_runs_once():
    assert list(sweep(FIXTURES / "hilt-stateflow-app", "di", "di")) == ["project", "di"]


def test_output_is_deterministic():
    first = run(FIXTURES / "hilt-stateflow-app").stdout
    assert first == run(FIXTURES / "hilt-stateflow-app").stdout


# ---- cache ----


def read_cache(project: Path) -> dict:
    return json.loads((project / CACHE).read_text(encoding="utf-8"))


def expected_hash(project: Path) -> str:
    """Independent restatement of the content-based key for the fixtures used here."""
    keep = (".kt", ".java", ".xml")
    names = {"settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts", "gradle.properties"}
    skip = {"build", "generated", ".gradle", ".git", ".idea", ".artifacts", "node_modules"}
    lines = []
    for path in project.rglob("*"):
        rel = path.relative_to(project)
        if not path.is_file() or path.is_symlink() or skip & set(rel.parts[:-1]):
            continue
        if path.suffix in keep or path.name in names or path.name.endswith(".versions.toml"):
            lines.append(f"{rel.as_posix()}\t{hashlib.sha256(path.read_bytes()).hexdigest()}\n")
    if not lines:
        return "NO_PROJECT_FILES"
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


def test_no_cache_without_flag(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    assert run(project).returncode == 0
    assert not (project / ".artifacts").exists()


def test_write_cache_shape_and_keys(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    result = run(project, "--write-cache")
    assert result.returncode == 0, result.stderr
    cache = read_cache(project)
    assert set(cache) == {"timestamp", "project_hash", "patterns"}
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", cache["timestamp"])
    assert cache["project_hash"] == expected_hash(project)
    patterns = cache["patterns"]
    assert {"di_framework", "state_management", "ui_framework"} <= set(patterns)
    for entry in patterns.values():
        assert set(entry) == {"detected", "confidence", "evidence"}
        assert isinstance(entry["detected"], str)
        assert 0.0 <= entry["confidence"] <= 1.0
        assert all(isinstance(item, str) for item in entry["evidence"])
    assert patterns["di_framework"]["detected"] == "hilt"
    assert patterns["di_framework"]["confidence"] == 1.0
    assert patterns["state_management"]["detected"] == "stateflow"
    assert patterns["ui_framework"]["detected"] == "compose"
    assert patterns["ui_framework"]["evidence"] == ["app/src/main/java/com/example/HomeScreen.kt:compose"]


def test_cache_confidence_is_the_dominant_share(tmp_path):
    project = copy_fixture("mixed-60-40-app", tmp_path)
    run(project, "--write-cache")
    entry = read_cache(project)["patterns"]["di_framework"]
    assert (entry["detected"], entry["confidence"]) == ("hilt", 0.6)
    assert len(entry["evidence"]) == 3


def test_cache_with_no_matches_reports_none(tmp_path):
    run(tmp_path, "--write-cache")
    entry = read_cache(tmp_path)["patterns"]["di_framework"]
    assert entry == {"detected": "none", "confidence": 0.0, "evidence": []}


def test_cache_hash_matches_preflight(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    run(project, "--write-cache")
    out = subprocess.run(
        [sys.executable, str(PREFLIGHT)], cwd=project, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert out[out.index("== Project hash ==") + 1] == read_cache(project)["project_hash"]
    assert f"project_hash={read_cache(project)['project_hash']}" in run(project).stdout


def test_cache_hash_without_project_files(tmp_path):
    run(tmp_path, "--write-cache")
    assert read_cache(tmp_path)["project_hash"] == "NO_PROJECT_FILES"


def test_cache_only_holds_requested_categories(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    run(project, "di", "--write-cache")
    assert set(read_cache(project)["patterns"]) == {"di_framework"}


def test_cache_merges_categories_while_hash_unchanged(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    run(project, "di", "--write-cache")
    run(project, "state", "--write-cache")
    assert {"di_framework", "state_management"} <= set(read_cache(project)["patterns"])


def test_cache_drops_old_entries_when_hash_changed(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    run(project, "di", "--write-cache")
    write(project / "settings.gradle.kts", 'rootProject.name = "changed"\n')
    run(project, "state", "--write-cache")
    cache = read_cache(project)
    assert set(cache["patterns"]) == {"state_management"}
    assert cache["project_hash"] == expected_hash(project)


def test_cache_replaces_corrupt_file(tmp_path):
    write(tmp_path / CACHE, "{not json")
    assert run(tmp_path, "--write-cache").returncode == 0
    assert "patterns" in read_cache(tmp_path)


def test_cache_ignores_cwd(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert run(project, "--write-cache", cwd=elsewhere).returncode == 0
    assert (project / CACHE).is_file()
    assert not (elsewhere / ".artifacts").exists()


def test_cache_is_not_scanned_as_source(tmp_path):
    project = copy_fixture("hilt-stateflow-app", tmp_path)
    run(project, "--write-cache")
    assert sweep(project)["project"]["lines"][2] == "files_scanned=8"


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
    result = run(tmp_path, "persistence")
    assert result.returncode == 2
    assert "persistence" in result.stderr
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


# ---- miscounting patterns ----


def decision(project: str, category: str, key: str) -> dict:
    return sweep(FIXTURES / project, category)[category]["decisions"][key]


def test_dagger_only_app_is_dagger_not_hilt():
    di = decision("dagger-only-app", "di", "di_framework")
    assert di["cands"]["hilt"] == (0, "0.0%")
    assert di["cands"]["dagger"] == (1, "100.0%")
    assert (di["dominant"], di["verdict"]) == ("dagger", "match")


def test_hilt_app_with_module_and_provides_has_no_dagger_files():
    di = decision("hilt-modules-app", "di", "di_framework")
    assert di["cands"]["dagger"] == (0, "0.0%")
    assert di["cands"]["hilt"] == (2, "100.0%")
    assert (di["dominant"], di["verdict"]) == ("hilt", "match")


def test_file_with_hilt_markers_does_not_count_as_dagger(tmp_path):
    write(tmp_path / "Both.kt", "@HiltAndroidApp\n@Component\n")
    write(tmp_path / "Plain.kt", "@Subcomponent\n")
    di = sweep(tmp_path, "di")["di"]["decisions"]["di_framework"]
    assert di["cands"]["hilt"] == (1, "50.0%")
    assert di["cands"]["dagger"] == (1, "50.0%")


def test_mockk_ignores_everything_and_verify_in_prose():
    mocks = decision("mockk-app", "testing", "testing_mocks")
    assert mocks["cands"]["mockk"][0] == 2
    assert mocks["cands"]["mockito"] == (0, "0.0%")
    assert (mocks["dominant"], mocks["verdict"]) == ("mockk", "match")


def test_mockk_annotation_file_is_not_mockito(tmp_path):
    write(tmp_path / "A.kt", "@MockK\nlateinit var client: Client\n")
    mocks = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["mockk"] == (1, "100.0%")
    assert mocks["cands"]["mockito"] == (0, "0.0%")


def test_mockk_file_calling_verify_with_parens_is_not_mockito(tmp_path):
    write(tmp_path / "A.kt", "val m = mockk<Foo>()\nverify(exactly = 1) { m.go() }\n")
    mocks = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["mockito"] == (0, "0.0%")


@pytest.mark.parametrize(
    "line",
    [
        "@Mock\nlateinit var repo: Repo",
        "val r = mock(Repo::class.java)",
        "val r = Mockito.mock(Repo::class.java)",
        "verify(repo).load()",
    ],
)
def test_mockito_markers_count(tmp_path, line):
    write(tmp_path / "A.kt", line + "\n")
    mocks = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["mockito"] == (1, "100.0%")


@pytest.mark.parametrize(
    "line",
    [
        "mockk<Foo>()",
        "mockk()",
        "@MockK lateinit var a: A",
        "every { a.b() } returns 1",
        "coEvery { a.b() } returns 1",
        "verify { a.b() }",
        "coVerify { a.b() }",
    ],
)
def test_mockk_markers_count(tmp_path, line):
    write(tmp_path / "A.kt", line + "\n")
    mocks = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_mocks"]
    assert mocks["cands"]["mockk"] == (1, "100.0%")


def test_assertthat_is_the_assertion_candidate_name(tmp_path):
    write(tmp_path / "A.kt", "assertThat(x).isEqualTo(1)\n")
    asserts = sweep(tmp_path, "testing")["testing"]["decisions"]["testing_assertions"]
    assert list(asserts["cands"]) == ["assertthat", "junit"]
    assert asserts["dominant"] == "assertthat"
    assert run(tmp_path, "testing", "--write-cache").returncode == 0
    assert read_cache(tmp_path)["patterns"]["testing_assertions"]["detected"] == "assertthat"


def test_compose_screens_calling_hilt_view_model_are_not_view_models():
    ui = sweep(FIXTURES / "compose-hiltviewmodel-app", "architecture")["architecture"]["decisions"]
    assert ui["presentation"]["cands"]["viewmodel"] == (1, "100.0%")
    assert ui["ui_framework"]["cands"]["compose"] == (2, "100.0%")


@pytest.mark.parametrize(
    "line",
    [
        "class A : ViewModel()",
        "class A(app: Application) : AndroidViewModel(app)",
        "public class A extends ViewModel {}",
    ],
)
def test_view_model_declarations_count(tmp_path, line):
    write(tmp_path / "A.kt", line + "\n")
    cands = sweep(tmp_path, "architecture")["architecture"]["decisions"]["presentation"]["cands"]
    assert cands["viewmodel"] == (1, "100.0%")


# ---- content-based project hash ----


def project_hash_of(project: Path) -> str:
    result = run("--hash", project)
    assert result.returncode == 0, result.stderr
    line = result.stdout.strip()
    assert re.fullmatch(r"project_hash=([0-9a-f]{64}|NO_PROJECT_FILES)", line), line
    return line.split("=", 1)[1]


def hash_project(tmp_path: Path) -> Path:
    write(tmp_path / "settings.gradle.kts", 'rootProject.name = "x"\n')
    write(tmp_path / "app/build.gradle.kts", "plugins {}\n")
    write(tmp_path / "gradle/libs.versions.toml", '[versions]\nkotlin = "2.0"\n')
    write(tmp_path / "app/src/main/A.kt", "class A\n")
    write(tmp_path / "app/src/main/res/layout/main.xml", "<LinearLayout/>\n")
    return tmp_path


def test_hash_flag_prints_only_the_hash(tmp_path):
    project = hash_project(tmp_path)
    assert run("--hash", project).stdout == f"project_hash={expected_hash(project)}\n"


def test_hash_matches_project_section_and_cache(tmp_path):
    project = hash_project(tmp_path)
    run(project, "--write-cache")
    digest = project_hash_of(project)
    assert f"project_hash={digest}" in run(project).stdout.splitlines()
    assert read_cache(project)["project_hash"] == digest


def test_hash_is_stable_across_runs(tmp_path):
    project = hash_project(tmp_path)
    assert project_hash_of(project) == project_hash_of(project)


def test_hash_independent_of_creation_and_walk_order(tmp_path):
    first = hash_project(tmp_path / "one")
    second = tmp_path / "two"
    write(second / "app/src/main/res/layout/main.xml", "<LinearLayout/>\n")
    write(second / "app/src/main/A.kt", "class A\n")
    write(second / "gradle/libs.versions.toml", '[versions]\nkotlin = "2.0"\n')
    write(second / "app/build.gradle.kts", "plugins {}\n")
    write(second / "settings.gradle.kts", 'rootProject.name = "x"\n')
    assert project_hash_of(first) == project_hash_of(second)

    import importlib.util

    spec = importlib.util.spec_from_file_location("detect_patterns_walk", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real_walk = os.walk

    def reversed_walk(top):
        for current, dirs, names in real_walk(top):
            yield current, list(reversed(dirs)), list(reversed(names))

    module.os.walk = reversed_walk
    try:
        assert module.project_hash(first) == project_hash_of(first)
    finally:
        module.os.walk = real_walk


@pytest.mark.parametrize(
    "rel,text",
    [
        ("app/src/main/A.kt", "class A { val changed = 1 }\n"),
        ("app/src/main/B.java", "class B {}\n"),
        ("app/src/main/res/layout/main.xml", "<FrameLayout/>\n"),
        ("app/build.gradle.kts", 'plugins { id("x") }\n'),
        ("settings.gradle.kts", 'rootProject.name = "y"\n'),
        ("gradle/libs.versions.toml", '[versions]\nkotlin = "2.1"\n'),
        ("gradle/other.versions.toml", "[versions]\n"),
        ("gradle.properties", "org.gradle.jvmargs=-Xmx2g\n"),
        ("lib/build.gradle", "apply plugin: 'java'\n"),
    ],
)
def test_hash_changes_when_scanned_or_build_file_changes(tmp_path, rel, text):
    project = hash_project(tmp_path)
    before = project_hash_of(project)
    write(project / rel, text)
    assert project_hash_of(project) != before


@pytest.mark.parametrize(
    "rel",
    [
        "app/build/Gen.kt",
        "build/outputs/x.gradle.kts",
        "app/build/generated/G.java",
        ".gradle/g.properties",
        ".artifacts/a.kt",
        "node_modules/p/build.gradle",
        "README.md",
        "app/src/main/notes.txt",
    ],
)
def test_hash_ignores_pruned_and_unscanned_files(tmp_path, rel):
    project = hash_project(tmp_path)
    before = project_hash_of(project)
    write(project / rel, "changed\n")
    assert project_hash_of(project) == before


def test_hash_for_project_with_gradle_files_in_a_subfolder(tmp_path):
    write(tmp_path / "sub/settings.gradle.kts", "x\n")
    write(tmp_path / "sub/app/build.gradle.kts", "plugins {}\n")
    before = project_hash_of(tmp_path)
    assert re.fullmatch(r"[0-9a-f]{64}", before)
    write(tmp_path / "sub/app/build.gradle.kts", 'plugins { id("x") }\n')
    assert project_hash_of(tmp_path) != before


def test_hash_includes_the_path_not_just_content(tmp_path):
    write(tmp_path / "a/A.kt", "x\n")
    one = project_hash_of(tmp_path)
    (tmp_path / "a/A.kt").rename(tmp_path / "a/B.kt")
    assert project_hash_of(tmp_path) != one


def test_hash_with_no_project_files(tmp_path):
    assert project_hash_of(tmp_path) == "NO_PROJECT_FILES"


def test_hash_flag_missing_directory(tmp_path):
    result = run("--hash", tmp_path / "nope")
    assert result.returncode == 2
    assert result.stdout == ""
