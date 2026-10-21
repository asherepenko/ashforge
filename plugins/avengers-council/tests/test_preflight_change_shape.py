import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/council-code-review/scripts/preflight.sh"
MANIFESTS = "== Dependency manifests changed =="
CODE = "== Code files added or moved =="


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def write(repo, rel, text="x\n"):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_repo(tmp_path, base_files=None):
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    write(repo, "seed.txt")
    for rel, text in (base_files or {}).items():
        write(repo, rel, text)
    git(repo, "add", "-A", "-f")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "checkout", "-q", "-b", "feat")
    return repo


def commit(repo):
    git(repo, "add", "-A", "-f")
    git(repo, "commit", "-q", "-m", "change")


def run(repo):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_PLUGIN_ROOT")}
    env["HOME"] = str(repo.parent / "home")
    out = subprocess.run(["bash", str(SCRIPT)], cwd=repo, env=env,
                         capture_output=True, text=True, check=True).stdout
    return out


def section(out, header):
    lines = out.splitlines()
    start = lines.index(header) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("== ")), len(lines))
    return lines[start:end]


def test_manifest_and_new_code_file(tmp_path):
    repo = make_repo(tmp_path, {"README.md": "a\n"})
    write(repo, "package.json", "{}\n")
    write(repo, "src/new.py", "x = 1\n")
    write(repo, "README.md", "b\n")
    commit(repo)
    out = run(repo)
    assert section(out, MANIFESTS) == ["package.json"]
    code = section(out, CODE)
    assert code[0] == "COUNT=1"
    assert "src/new.py" in code
    assert "README.md" not in code


def test_nested_lockfile_only(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "app/package-lock.json", "{}\n")
    commit(repo)
    out = run(repo)
    assert section(out, MANIFESTS) == ["app/package-lock.json"]
    assert section(out, CODE)[0] == "COUNT=0"


def test_two_ecosystems(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "go.sum")
    write(repo, "svc/Cargo.lock")
    commit(repo)
    assert sorted(section(run(repo), MANIFESTS)) == ["go.sum", "svc/Cargo.lock"]


def test_workflow_prefix(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, ".github/workflows/ci.yml")
    commit(repo)
    assert section(run(repo), MANIFESTS) == [".github/workflows/ci.yml"]


def test_requirements_glob_and_none(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "requirements-dev.txt")
    commit(repo)
    assert section(run(repo), MANIFESTS) == ["requirements-dev.txt"]
    repo2 = make_repo(tmp_path / "b")
    write(repo2, "src/a.py")
    commit(repo2)
    assert section(run(repo2), MANIFESTS) == ["NONE"]


def test_config_only_additions(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "config.yaml")
    write(repo, "logo.png")
    write(repo, "docs/guide.txt")
    commit(repo)
    assert section(run(repo), CODE) == ["COUNT=0", "ADDED_DEFS=0", "NONE"]


def test_rename_counted_by_destination(tmp_path):
    repo = make_repo(tmp_path, {"src/a.py": "def f():\n    return 1\n" * 3})
    (repo / "lib").mkdir()
    git(repo, "mv", "src/a.py", "lib/a.py")
    commit(repo)
    code = section(run(repo), CODE)
    assert code[0] == "COUNT=1"
    assert "lib/a.py" in code
    assert "src/a.py" not in code


def test_count_before_display_cap(tmp_path):
    repo = make_repo(tmp_path)
    for i in range(31):
        write(repo, f"src/f{i:02d}.py")
    commit(repo)
    code = section(run(repo), CODE)
    assert code[0] == "COUNT=31"
    assert len([l for l in code if l.startswith("src/")]) == 30


def test_added_def_in_existing_file(tmp_path):
    repo = make_repo(tmp_path, {"src/app.py": "x = 1\n"})
    write(repo, "src/app.py", "x = 1\n\ndef helper():\n    return 2\n")
    commit(repo)
    code = section(run(repo), CODE)
    assert code[0] == "COUNT=0"
    assert "ADDED_DEFS=1" in code


def test_path_with_spaces(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "src/my file.py")
    commit(repo)
    assert "src/my file.py" in section(run(repo), CODE)


def test_no_base_is_unknown(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "trunk")
    write(repo, "a.txt")
    commit(repo)
    out = run(repo)
    assert section(out, MANIFESTS) == ["UNKNOWN — no base"]
    assert section(out, CODE) == ["UNKNOWN — no base"]


def test_probes_after_capability_block_and_no_transport(tmp_path):
    repo = make_repo(tmp_path)
    write(repo, "package.json")
    commit(repo)
    out = run(repo)
    assert out.index("== Runtime capability ==") < out.index(MANIFESTS) < out.index(CODE)
    for header in (MANIFESTS, CODE):
        body = "\n".join(section(out, header))
        assert "TRANSPORT=" not in body and "SPAWN=" not in body


def test_manifests_and_ci_never_count_as_code(tmp_path):
    repo = make_repo(tmp_path)
    names = ["go.mod", "go.sum", "Dockerfile", "requirements-dev.txt", "build.gradle.kts",
             ".github/workflows/ci.yml"]
    for name in names:
        write(repo, name, "def x():\n")
    commit(repo)
    out = run(repo)
    assert sorted(section(out, MANIFESTS)) == sorted(names)
    assert section(out, CODE) == ["COUNT=0", "ADDED_DEFS=0", "NONE"]


def test_nested_requirements_glob_not_expanded_by_root_file(tmp_path):
    repo = make_repo(tmp_path, {"requirements.txt": "a\n"})
    write(repo, "requirements.txt", "def x():\n")
    write(repo, "services/api/requirements-dev.txt", "def y():\n")
    commit(repo)
    out = run(repo)
    assert sorted(section(out, MANIFESTS)) == ["requirements.txt", "services/api/requirements-dev.txt"]
    assert section(out, CODE) == ["COUNT=0", "ADDED_DEFS=0", "NONE"]
