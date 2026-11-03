#!/usr/bin/env python3
"""Failure matrix for scripts/sync-ios-skills.sh.

The script runs as a subprocess against a temp copy of the plugin. PATH holds
only symlinks to the tools the script needs plus stub `curl`, `git`, `xcrun`
and `xcodebuild`, so nothing touches the network or the real Xcode.
"""

import io
import os
import re
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "sync-ios-skills.sh"

# name -> (repo, skill dir inside repo)
COMMUNITY = {
    "swift-concurrency": ("AvdLee/Swift-Concurrency-Agent-Skill", "skills/swift-concurrency"),
    "swift-testing-expert": ("AvdLee/Swift-Testing-Agent-Skill", "swift-testing-expert"),
    "swiftdata-pro": ("twostraws/SwiftData-Agent-Skill", "swiftdata-pro"),
}
XCODE = [
    "swiftui-specialist", "swiftui-whats-new-27", "app-intents-specialist",
    "app-intents-whats-new-27", "xctrace", "modernize-tests",
    "audit-xcode-security-settings", "app-resizability", "device-interaction",
]
OLD_SHA = {name: f"{i}" * 40 for i, name in zip("123", COMMUNITY)}
NEW_SHA = {name: f"{i}" * 40 for i, name in zip("abc", COMMUNITY)}

TOOLS = (
    "bash env seq sleep kill tar sed find cp mv rm mkdir mktemp cmp diff grep head tail cut sort cat "
    "dirname basename tr awk ls date wc xargs uniq tee readlink chmod"
).split()

CURL = """#!/bin/bash
out=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o) out="$2"; shift 2 ;;
    http*) url="$1"; shift ;;
    *) shift ;;
  esac
done
echo "$url" >>"$STUB_LOG/curl.log"
rest="${url#https://codeload.github.com/}"
owner="${rest%%/*}"; rest="${rest#*/}"
repo="${rest%%/*}"; sha="${rest##*/}"
f="$STUB_FIXTURES/${owner}__${repo}__${sha}.tgz"
[ -f "$f" ] || exit 22
cp "$f" "$out"
"""

GIT = """#!/bin/bash
[ "$1" = ls-remote ] || exit 2
url="$2"; shift 2
rest="${url#https://github.com/}"
f="$STUB_LSREMOTE/${rest//\\//__}.txt"
[ -f "$f" ] || exit 0
while IFS=$'\\t' read -r sha ref; do
  for p in "$@"; do
    [ "$ref" = "$p" ] && printf '%s\\t%s\\n' "$sha" "$ref"
  done
done <"$f"
exit 0
"""

XCRUN = """#!/bin/bash
[ "$1 $2 $3" = "agent skills export" ] || exit 2
shift 3
[ "$1" = "--output-dir" ] || exit 2
cp -R "$STUB_EXPORT"/. "$2"
"""

XCODEBUILD = """#!/bin/bash
echo "Xcode 27.2"
echo "Build version $STUB_XCODE_BUILD"
"""

# Programmable `mv`. Counts calls in $STUB_LOG/mv.count and acts on env knobs:
#   MV_FAIL_LOCK=1       a move onto ios-skills.lock exits 1 (after INT/TERM
#                        signals to the parent when MV_SIGNAL_LOCK=N)
#   MV_FAIL_AFTER_N=n    call n does the real move, then exits 1
#   MV_SIGNAL_ON_N=n     call n sends SIGINT to the parent, then moves for real
MV = """#!/bin/bash
for a in "$@"; do last="$a"; done
n=$(( $(cat "$STUB_LOG/mv.count" 2>/dev/null || echo 0) + 1 ))
echo "$n" >"$STUB_LOG/mv.count"
case "$last" in
  *ios-skills.lock)
    if [ -n "$MV_FAIL_LOCK" ]; then
      for _ in $(seq 1 "${MV_SIGNAL_LOCK:-0}"); do kill -INT "$PPID"; sleep 0.2; done
      exit 1
    fi ;;
esac
[ "$n" = "$MV_SIGNAL_ON_N" ] && { kill -INT "$PPID"; sleep 0.2; }
"$REAL_MV" "$@" || exit $?
[ "$n" = "$MV_FAIL_AFTER_N" ] && exit 1
exit 0
"""


def skill_md(name: str, body: str = "body") -> bytes:
    return f"---\nname: {name}\ndescription: test skill\n---\n{body}\n".encode()


def write_tar(path: Path, top: str, files: dict, extra=None):
    """Write a gzip tarball with a single top-level dir like codeload does."""
    with tarfile.open(path, "w:gz") as tf:
        for rel, data in files.items():
            info = tarfile.TarInfo(f"{top}/{rel}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        for info in extra or []:
            tf.addfile(info)


def snapshot(root: Path) -> dict:
    snap = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            snap[rel] = ("l", os.readlink(p))
        elif p.is_dir():
            snap[rel] = ("d",)
        else:
            snap[rel] = ("f", p.read_bytes())
    return snap


class Env:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.plugin = tmp / "plugin"
        self.fixtures = tmp / "fixtures"
        self.lsremote = tmp / "lsremote"
        self.export = tmp / "export"
        self.bin = tmp / "bin"
        self.log = tmp / "log"
        for d in (self.fixtures, self.lsremote, self.export, self.bin, self.log):
            d.mkdir()
        self.xcode_build = "27B52"
        self._make_bin()
        self._make_plugin()
        for name in COMMUNITY:
            self.add_repo(name, NEW_SHA[name])
        self.make_export()

    def _stub(self, name: str, content: str):
        p = self.bin / name
        p.write_text(content)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)

    def _make_bin(self):
        for tool in TOOLS:
            real = shutil.which(tool)
            assert real, tool
            (self.bin / tool).symlink_to(real)
        self.real_mv = shutil.which("mv")
        for name, content in (("curl", CURL), ("git", GIT), ("xcrun", XCRUN), ("xcodebuild", XCODEBUILD)):
            self._stub(name, content)

    def _make_plugin(self):
        lock = ["# Generated by scripts/sync-ios-skills.sh; do not edit."]
        for name, (repo, path) in COMMUNITY.items():
            lock += [f"community.{name}.repo={repo}", f"community.{name}.commit={OLD_SHA[name]}",
                     f"community.{name}.license=MIT", f"community.{name}.path={path}"]
            d = self.plugin / "skills" / "community" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_bytes(skill_md(name, "OLD"))
            (d / "LICENSE").write_text("OLD LICENSE\n")
            self.add_repo(name, OLD_SHA[name], body="OLD")
            self.set_refs(name, OLD_SHA[name])
        lock += ["xcode.version=27.1", "xcode.build=27B52"] + [f"xcode.skill={n}" for n in XCODE]
        for n in XCODE:
            d = self.plugin / "skills" / "xcode" / n
            d.mkdir(parents=True)
            (d / "SKILL.md").write_bytes(skill_md(n, "OLD"))
        lock += ["fork.swiftui-pro.repo=twostraws/SwiftUI-Agent-Skill",
                 "fork.swiftui-pro.commit=" + "f" * 40, "fork.swiftui-pro.license=MIT"]
        (self.plugin / "ios-skills.lock").write_text("\n".join(lock) + "\n")

    def set_refs(self, name: str, sha: str, extra=()):
        repo = COMMUNITY[name][0]
        lines = [f"{sha}\tHEAD", f"{sha}\trefs/heads/main", *extra]
        (self.lsremote / (repo.replace("/", "__") + ".txt")).write_text("\n".join(lines) + "\n")

    def add_repo(self, name: str, sha: str, body="NEW", license_=True, fm_name=None, extra=None):
        repo, path = COMMUNITY[name]
        files = {f"{path}/SKILL.md": skill_md(fm_name or name, body),
                 f"{path}/references/a.md": b"ref\n"}
        if license_:
            files["LICENSE"] = b"MIT License upstream\n"
        write_tar(self.fixtures / f"{repo.replace('/', '__')}__{sha}.tgz",
                  f"{repo.split('/')[1]}-{sha}", files, extra)

    def make_export(self, skip=(), fm_name=None, extra_dirs=("extra-skill",)):
        shutil.rmtree(self.export)
        self.export.mkdir()
        for n in [*XCODE, *extra_dirs]:
            if n in skip:
                continue
            d = self.export / n
            d.mkdir()
            (d / "SKILL.md").write_bytes(skill_md(fm_name if fm_name and n == XCODE[0] else n, "NEW"))
            (d / "references").mkdir()
            (d / "references" / "x.md").write_text("x\n")

    def run(self, *args, with_xcrun=True, fail_lock_mv=False, mv_env=None):
        if not with_xcrun:
            (self.bin / "xcrun").unlink()
        if fail_lock_mv or mv_env:
            (self.bin / "mv").unlink()
            self._stub("mv", MV)
        env = {
            "PATH": str(self.bin),
            "HOME": str(self.tmp),
            "TMPDIR": str(self.tmp),
            "IOS_SKILLS_PLUGIN_ROOT": str(self.plugin),
            "STUB_FIXTURES": str(self.fixtures),
            "STUB_LSREMOTE": str(self.lsremote),
            "STUB_EXPORT": str(self.export),
            "STUB_LOG": str(self.log),
            "STUB_XCODE_BUILD": self.xcode_build,
            "REAL_MV": self.real_mv,
            **({"MV_FAIL_LOCK": "1"} if fail_lock_mv else {}),
            **(mv_env or {}),
        }
        return subprocess.run([shutil.which("bash"), str(SCRIPT), *args], env=env,
                              capture_output=True, text=True, timeout=60)

    def lock(self) -> dict:
        out = {}
        for line in (self.plugin / "ios-skills.lock").read_text().splitlines():
            if line and not line.startswith("#"):
                out.setdefault(line.split("=", 1)[0], []).append(line.split("=", 1)[1])
        return out


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def assert_failed_unchanged(env: Env, before: dict, proc, rc=1):
    assert proc.returncode == rc, proc.stderr
    assert snapshot(env.plugin) == before
    assert not list(env.tmp.glob("tmp.*")), "temp dir leaked"


# --- failure matrix ---------------------------------------------------------

def test_bad_ref_exits_1_and_tree_unchanged(env):
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "nope")
    assert_failed_unchanged(env, before, proc)
    assert "cannot resolve ref 'nope'" in proc.stderr


def test_ambiguous_ref_exits_1(env):
    for name in COMMUNITY:
        env.set_refs(name, OLD_SHA[name], extra=[f"{NEW_SHA[name]}\trefs/tags/main"])
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main")
    assert_failed_unchanged(env, before, proc)
    assert "ambiguous" in proc.stderr


@pytest.mark.parametrize("entry", ["traversal", "absolute", "symlink", "hardlink"])
def test_unsafe_tar_entry_exits_1_and_tree_unchanged(env, entry):
    # The unsafe archive is the LAST skill, so earlier skills were already staged.
    last = list(COMMUNITY)[-1]
    top = f"{COMMUNITY[last][0].split('/')[1]}-{OLD_SHA[last]}"
    inside = f"{top}/{COMMUNITY[last][1]}"
    if entry == "traversal":
        info = tarfile.TarInfo("../evil.txt")
        info.size = 0
    elif entry == "absolute":
        info = tarfile.TarInfo("/tmp/evil.txt")
        info.size = 0
    elif entry == "symlink":
        info = tarfile.TarInfo(f"{inside}/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
    else:
        info = tarfile.TarInfo(f"{inside}/hard")
        info.type = tarfile.LNKTYPE
        info.linkname = f"{top}/LICENSE"
    env.add_repo(last, OLD_SHA[last], extra=[info])
    before = snapshot(env.plugin)
    proc = env.run()
    assert_failed_unchanged(env, before, proc)
    assert "unsafe" in proc.stderr
    assert not (env.tmp / "evil.txt").exists()


def _top(name, sha):
    return f"{COMMUNITY[name][0].split('/')[1]}-{sha}"


def test_symlink_outside_skill_path_is_ignored(env):
    name = "swift-concurrency"
    info = tarfile.TarInfo(f"{_top(name, NEW_SHA[name])}/{name}")
    info.type = tarfile.SYMTYPE
    info.linkname = "skills/swift-concurrency"
    env.add_repo(name, NEW_SHA[name], extra=[info])
    for n in COMMUNITY:
        env.set_refs(n, NEW_SHA[n])
    proc = env.run("--community-ref", "main")
    assert proc.returncode == 0, proc.stderr
    skill = env.plugin / "skills" / "community" / name
    assert b"NEW" in (skill / "SKILL.md").read_bytes()
    assert not any(p.is_symlink() for p in skill.rglob("*"))


def test_dotdot_symlink_inside_skill_path_exits_1(env):
    name = "swiftdata-pro"
    info = tarfile.TarInfo(f"{_top(name, NEW_SHA[name])}/{COMMUNITY[name][1]}/escape")
    info.type = tarfile.SYMTYPE
    info.linkname = "../../../outside"
    env.add_repo(name, NEW_SHA[name], extra=[info])
    for n in COMMUNITY:
        env.set_refs(n, NEW_SHA[n])
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main")
    assert_failed_unchanged(env, before, proc)
    assert "unsafe" in proc.stderr


def test_members_outside_skill_path_are_not_extracted(env):
    name = "swift-testing-expert"
    top = _top(name, NEW_SHA[name])
    info = tarfile.TarInfo(f"{top}/other/secret.txt")
    info.size = 0
    env.add_repo(name, NEW_SHA[name], extra=[info])
    for n in COMMUNITY:
        env.set_refs(n, NEW_SHA[n])
    (env.bin / "tar").unlink()
    env._stub("tar", """#!/bin/bash
prev=""
for a in "$@"; do
  [ "$prev" = "-T" ] && cat "$a" >>"$STUB_LOG/tar.members"
  prev="$a"
done
exec "$REAL_TAR" "$@"
""")
    proc = subprocess.run(
        [shutil.which("bash"), str(SCRIPT), "--community-ref", "main"],
        env={"PATH": str(env.bin), "HOME": str(env.tmp), "TMPDIR": str(env.tmp),
             "IOS_SKILLS_PLUGIN_ROOT": str(env.plugin), "STUB_FIXTURES": str(env.fixtures),
             "STUB_LSREMOTE": str(env.lsremote), "STUB_EXPORT": str(env.export),
             "STUB_LOG": str(env.log), "STUB_XCODE_BUILD": env.xcode_build,
             "REAL_TAR": shutil.which("tar")},
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    members = (env.log / "tar.members").read_text()
    assert f"{top}/swift-testing-expert/SKILL.md" in members
    assert f"{top}/LICENSE" in members
    assert "secret.txt" not in members


def test_missing_license_exits_1_and_tree_unchanged(env):
    last = list(COMMUNITY)[-1]
    env.add_repo(last, OLD_SHA[last], license_=False)
    before = snapshot(env.plugin)
    proc = env.run()
    assert_failed_unchanged(env, before, proc)
    assert "no LICENSE" in proc.stderr


def test_frontmatter_name_mismatch_exits_1(env):
    last = list(COMMUNITY)[-1]
    env.add_repo(last, OLD_SHA[last], fm_name="something-else")
    before = snapshot(env.plugin)
    proc = env.run()
    assert_failed_unchanged(env, before, proc)
    assert "frontmatter name" in proc.stderr


def test_update_xcode_without_xcrun_exits_1(env):
    before = snapshot(env.plugin)
    proc = env.run("--update-xcode", with_xcrun=False)
    assert_failed_unchanged(env, before, proc)
    assert "xcrun" in proc.stderr


def test_listed_xcode_skill_missing_from_export_exits_1(env):
    env.make_export(skip=[XCODE[-1]])
    before = snapshot(env.plugin)
    proc = env.run("--update-xcode")
    assert_failed_unchanged(env, before, proc)
    assert f"{XCODE[-1]}: missing from Xcode export" in proc.stderr


def test_xcode_export_frontmatter_mismatch_exits_1(env):
    env.make_export(fm_name="wrong-name")
    before = snapshot(env.plugin)
    proc = env.run("--update-xcode")
    assert_failed_unchanged(env, before, proc)


def test_failed_lock_write_rolls_back_every_skill(env):
    # Lock is written last; if that step fails nothing may stay swapped in.
    for name in COMMUNITY:
        env.set_refs(name, NEW_SHA[name])
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main", fail_lock_mv=True)
    assert proc.returncode != 0
    assert snapshot(env.plugin) == before


def _community_update(env):
    for name in COMMUNITY:
        env.set_refs(name, NEW_SHA[name])


def test_dangling_symlink_dest_survives_failed_swap(env):
    victim = env.plugin / "skills" / "community" / list(COMMUNITY)[0]
    shutil.rmtree(victim)
    victim.symlink_to(env.tmp / "does-not-exist")
    _community_update(env)
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main", fail_lock_mv=True)
    assert proc.returncode != 0
    assert victim.is_symlink() and os.readlink(victim) == str(env.tmp / "does-not-exist")
    assert snapshot(env.plugin) == before


@pytest.mark.parametrize("n", [1, 2, 3])
def test_mv_failing_after_it_moved_leaves_tree_unchanged(env, n):
    # Call 1 = dest->backup, 2 = staged->dest of the first skill, 3 = backup of the second.
    # The move itself succeeds but reports failure, so the swap state must already be recorded.
    _community_update(env)
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main", mv_env={"MV_FAIL_AFTER_N": str(n)})
    assert proc.returncode != 0
    assert snapshot(env.plugin) == before
    assert not list(env.tmp.glob("tmp.*")), "temp dir leaked"


@pytest.mark.parametrize("n", [1, 2, 4])
def test_sigint_during_swap_cannot_leave_a_partial_tree(env, n):
    # The swap is a critical section: the signal is deferred, so the run either
    # finishes fully (lock + every skill new) or leaves everything as it was.
    _community_update(env)
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main", mv_env={"MV_SIGNAL_ON_N": str(n)})
    if proc.returncode == 0:
        lock = env.lock()
        for name in COMMUNITY:
            assert lock[f"community.{name}.commit"] == [NEW_SHA[name]]
            assert (env.plugin / "skills/community" / name / "SKILL.md").read_bytes() == skill_md(name, "NEW")
    else:
        assert snapshot(env.plugin) == before
    assert not list(env.tmp.glob("tmp.*")), "temp dir leaked"


def test_sigint_after_lock_move_does_not_roll_back_skills(env):
    # Lock is the last mv (call 7: 3 backups + 3 swaps + lock). A signal sent
    # as it lands must not undo the skills while the new lock stays.
    _community_update(env)
    proc = env.run("--community-ref", "main", mv_env={"MV_SIGNAL_ON_N": "7"})
    assert proc.returncode == 0, proc.stderr
    lock = env.lock()
    for name in COMMUNITY:
        assert lock[f"community.{name}.commit"] == [NEW_SHA[name]]
        assert (env.plugin / "skills/community" / name / "SKILL.md").read_bytes() == skill_md(name, "NEW")


def test_repeated_signals_do_not_abort_rollback(env):
    _community_update(env)
    before = snapshot(env.plugin)
    proc = env.run("--community-ref", "main", fail_lock_mv=True, mv_env={"MV_SIGNAL_LOCK": "3"})
    assert proc.returncode != 0
    assert snapshot(env.plugin) == before
    assert not list(env.tmp.glob("tmp.*")), "temp dir leaked"


FORK_REPO = "twostraws/SwiftUI-Agent-Skill"
FORK_LOCKED = "f" * 40
FORK_NEW = "e" * 40


def add_fork_tree(env: Env, sha: str, views: bytes, extra_files=None):
    files = {"swiftui-pro/SKILL.md": skill_md("swiftui-pro"), "swiftui-pro/references/views.md": views,
             "LICENSE": b"MIT License upstream\n", **(extra_files or {})}
    write_tar(env.fixtures / f"{FORK_REPO.replace('/', '__')}__{sha}.tgz", f"SwiftUI-Agent-Skill-{sha}", files)


def set_fork_refs(env: Env, *pairs):
    lines = [f"{sha}\t{ref}" for sha, ref in pairs]
    (env.lsremote / (FORK_REPO.replace("/", "__") + ".txt")).write_text("\n".join(lines) + "\n")


def test_fork_ref_prints_diff_and_writes_nothing(env):
    add_fork_tree(env, FORK_LOCKED, b"old rule\n")
    add_fork_tree(env, FORK_NEW, b"new rule\n", {"swiftui-pro/references/extra.md": b"added\n"})
    set_fork_refs(env, (FORK_NEW, "refs/tags/3.0.0"))
    before = snapshot(env.plugin)
    proc = env.run("--fork-ref", "3.0.0")
    assert_failed_unchanged(env, before, proc, rc=0)
    assert "-old rule" in proc.stdout and "+new rule" in proc.stdout
    assert "extra.md" in proc.stdout and "+added" in proc.stdout


def test_fork_ref_with_no_changes_prints_nothing_and_exits_0(env):
    add_fork_tree(env, FORK_LOCKED, b"same\n")
    set_fork_refs(env, (FORK_LOCKED, "refs/tags/2.0.0"))
    before = snapshot(env.plugin)
    proc = env.run("--fork-ref", "2.0.0")
    assert_failed_unchanged(env, before, proc, rc=0)
    assert proc.stdout == ""


def test_fork_ref_unresolvable_exits_1_and_writes_nothing(env):
    add_fork_tree(env, FORK_LOCKED, b"old\n")
    set_fork_refs(env, (FORK_NEW, "refs/tags/3.0.0"))
    before = snapshot(env.plugin)
    proc = env.run("--fork-ref", "nope")
    assert_failed_unchanged(env, before, proc, rc=1)
    assert proc.stdout == ""
    assert "cannot resolve" in proc.stderr


def test_fork_ref_sha_without_tarball_exits_1(env):
    add_fork_tree(env, FORK_LOCKED, b"old\n")
    before = snapshot(env.plugin)
    proc = env.run("--fork-ref", "d" * 40)
    assert_failed_unchanged(env, before, proc, rc=1)


def test_fork_ref_rejects_unsafe_archive_entry(env):
    add_fork_tree(env, FORK_LOCKED, b"old\n")
    add_fork_tree(env, FORK_NEW, b"new\n", {"swiftui-pro/../evil": b"x\n"})
    set_fork_refs(env, (FORK_NEW, "refs/tags/3.0.0"))
    before = snapshot(env.plugin)
    proc = env.run("--fork-ref", "3.0.0")
    assert_failed_unchanged(env, before, proc, rc=1)


def test_unknown_argument_exits_2(env):
    before = snapshot(env.plugin)
    assert_failed_unchanged(env, before, env.run("--bogus"), rc=2)


# --- success paths ----------------------------------------------------------

def test_default_run_fetches_locked_shas_with_upstream_license(env):
    proc = env.run()
    assert proc.returncode == 0, proc.stderr
    fetched = (env.log / "curl.log").read_text().split()
    for name, (repo, _) in COMMUNITY.items():
        assert f"https://codeload.github.com/{repo}/tar.gz/{OLD_SHA[name]}" in fetched
        d = env.plugin / "skills" / "community" / name
        assert (d / "SKILL.md").read_bytes() == skill_md(name, "OLD")
        assert (d / "LICENSE").read_text() == "MIT License upstream\n"
        assert (d / "references" / "a.md").exists()


def test_community_ref_moves_skills_and_lock_to_new_commit(env):
    for name in COMMUNITY:
        env.set_refs(name, NEW_SHA[name])
    proc = env.run("--community-ref", "main")
    assert proc.returncode == 0, proc.stderr
    lock = env.lock()
    for name, (repo, path) in COMMUNITY.items():
        assert lock[f"community.{name}.commit"] == [NEW_SHA[name]]
        assert lock[f"community.{name}.repo"] == [repo]
        assert lock[f"community.{name}.license"] == ["MIT"]
        assert lock[f"community.{name}.path"] == [path]
        assert re.fullmatch(r"[0-9a-f]{40}", lock[f"community.{name}.commit"][0])
        assert (env.plugin / "skills/community" / name / "SKILL.md").read_bytes() == skill_md(name, "NEW")
    assert lock["fork.swiftui-pro.commit"] == ["f" * 40]


def test_update_xcode_copies_only_the_listed_skills_and_rewrites_lock(env):
    proc = env.run("--update-xcode")
    assert proc.returncode == 0, proc.stderr
    xdir = env.plugin / "skills" / "xcode"
    assert sorted(p.name for p in xdir.iterdir()) == sorted(XCODE)
    assert not (xdir / "extra-skill").exists()
    for n in XCODE:
        assert (xdir / n / "SKILL.md").read_bytes() == skill_md(n, "NEW")
        assert (xdir / n / "references" / "x.md").exists()
    lock = env.lock()
    assert lock["xcode.version"] == ["27.2"]
    assert lock["xcode.build"] == ["27B52"]
    assert lock["xcode.skill"] == XCODE


def test_lock_is_written_with_header_and_fork_lines_kept(env):
    env.run("--update-xcode")
    lines = (env.plugin / "ios-skills.lock").read_text().splitlines()
    assert lines[0] == "# Generated by scripts/sync-ios-skills.sh; do not edit."
    assert "fork.swiftui-pro.repo=twostraws/SwiftUI-Agent-Skill" in lines


def test_build_mismatch_without_flag_warns_and_writes_nothing(env):
    # Bring the tree to the fixtures' content first, so a no-op run changes nothing.
    for name in COMMUNITY:
        env.set_refs(name, NEW_SHA[name])
    assert env.run("--community-ref", "main", "--update-xcode").returncode == 0
    env.xcode_build = "27B99"
    before = snapshot(env.plugin)
    proc = env.run()
    assert proc.returncode == 0, proc.stderr
    assert "warning" in proc.stderr and "27B99" in proc.stderr and "27B52" in proc.stderr
    assert snapshot(env.plugin) == before


def test_without_flag_never_touches_xcode_dir_or_lines(env):
    before_xcode = snapshot(env.plugin / "skills" / "xcode")
    env.run()
    assert snapshot(env.plugin / "skills" / "xcode") == before_xcode
    lock = env.lock()
    assert lock["xcode.version"] == ["27.1"]
    assert lock["xcode.skill"] == XCODE


def test_second_run_changes_nothing(env):
    assert env.run().returncode == 0
    after_first = snapshot(env.plugin)
    assert env.run().returncode == 0
    assert snapshot(env.plugin) == after_first
