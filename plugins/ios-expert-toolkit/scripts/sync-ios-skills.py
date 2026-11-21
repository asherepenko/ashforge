#!/usr/bin/env python3
# Vendor pinned third-party skills into this plugin.
#
#   skills/community/<name>  from three MIT-licensed GitHub repos, at the commit
#                            pinned in ios-skills.lock (or --community-ref).
#   skills/xcode/<name>      from `xcrun agent skills export`, only with
#                            --update-xcode. Content depends on the installed
#                            Xcode build.
#
#   --fork-ref REF           print `diff -ruN` of the locked swiftui-pro upstream
#                            tree against REF's tree; writes nothing.
#
# Usage: scripts/sync-ios-skills.py [--community-ref REF] [--update-xcode] [--fork-ref REF]
#
# Safety: every skill is staged and validated in a temp dir before anything in
# the tree changes. The lock is written last. Any failure exits 1 and leaves
# the tree and lock as they were. Never edit vendored files by hand.
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile

PLUGIN_ROOT = os.environ.get("IOS_SKILLS_PLUGIN_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
COMMUNITY_DIR = os.path.join(PLUGIN_ROOT, "skills", "community")
XCODE_DIR = os.path.join(PLUGIN_ROOT, "skills", "xcode")
LOCK = os.path.join(PLUGIN_ROOT, "ios-skills.lock")

# name, repo, skill dir inside the repo, license
COMMUNITY = [
    ("swift-concurrency", "AvdLee/Swift-Concurrency-Agent-Skill", "skills/swift-concurrency", "MIT"),
    ("swift-testing-expert", "AvdLee/Swift-Testing-Agent-Skill", "swift-testing-expert", "MIT"),
    ("swiftdata-pro", "twostraws/SwiftData-Agent-Skill", "swiftdata-pro", "MIT"),
]

XCODE_SKILLS = [
    "swiftui-specialist",
    "swiftui-whats-new-27",
    "app-intents-specialist",
    "app-intents-whats-new-27",
    "xctrace",
    "modernize-tests",
    "audit-xcode-security-settings",
    "app-resizability",
    "device-interaction",
]

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def err(msg):
    print(f"sync-ios-skills: {msg}", file=sys.stderr)


def die(msg):
    err(msg)
    sys.exit(1)


def usage_error(msg):
    err(msg)
    sys.exit(2)


def lock_get(key):
    if not os.path.isfile(LOCK):
        return ""
    with open(LOCK, encoding="utf-8", errors="replace") as f:
        for line in f.read().split("\n"):
            k, sep, v = line.partition("=")
            if sep and k == key:
                return v
    return ""


def lock_lines(prefix):
    if not os.path.isfile(LOCK):
        return []
    with open(LOCK, encoding="utf-8", errors="replace") as f:
        return [ln for ln in f.read().split("\n") if ln.startswith(prefix)]


def rm_rf(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def mv(src, dst):
    """Move through the `mv` on PATH, as a failed move must carry mv's status."""
    return subprocess.run(["mv", src, dst]).returncode


# --- Destination guard -------------------------------------------------------
# Refuse before anything is staged or moved if a directory this run writes into
# is a symlink or resolves outside the plugin. A skill dir that is a symlink to
# a directory is refused too; a dangling one is replaced as a link, never followed.
def check_parent(path, plugin_phys, quiet):
    if not (os.path.exists(path) or os.path.islink(path)):
        return True
    if os.path.islink(path):
        if not quiet:
            err(f"refusing to write: '{path}' is a symlink")
        return False
    if not os.path.isdir(path):
        if not quiet:
            err(f"cannot resolve '{path}'")
        return False
    phys = os.path.realpath(path)
    if not phys.startswith(plugin_phys + "/"):
        if not quiet:
            err(f"refusing to write: '{path}' resolves outside the plugin ({phys})")
        return False
    return True


def guard_dest(dest, plugin_phys, quiet=False):
    """Every directory from the plugin root down to dest's parent must be a real
    directory inside the plugin, and dest must not be a symlink to a directory.
    Run again right before each swap, because the tree can change after staging."""
    d = os.path.dirname(dest)
    while d not in (PLUGIN_ROOT, "/", "."):
        if not check_parent(d, plugin_phys, quiet):
            return False
        d = os.path.dirname(d)
    if os.path.islink(dest) and os.path.isdir(dest):
        if not quiet:
            err(f"refusing to replace '{dest}': it is a symlink to a directory")
        return False
    return True


# Resolve a ref to one commit SHA: exact SHA, HEAD, branch or tag. A name that
# is both a branch and a tag pointing at different commits is rejected.
def resolve_ref(repo, ref):
    if SHA_RE.match(ref):
        return ref
    url = f"https://github.com/{repo}"
    if ref == "HEAD":
        p = subprocess.run(["git", "ls-remote", url, "HEAD"], stdout=subprocess.PIPE, text=True)
        if p.returncode != 0:
            return None
        lines = p.stdout.split("\n")
        sha = lines[0].split("\t")[0] if lines else ""
        return sha or None
    p = subprocess.run(
        ["git", "ls-remote", url, f"refs/heads/{ref}", f"refs/tags/{ref}", f"refs/tags/{ref}^{{}}"],
        stdout=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0 or not p.stdout.strip("\n"):
        return None
    heads = tag = peeled = ""
    for line in p.stdout.split("\n"):
        sha, _, rf = line.partition("\t")
        if rf == f"refs/heads/{ref}":
            heads = sha
        elif rf == f"refs/tags/{ref}^{{}}":
            peeled = sha
        elif rf == f"refs/tags/{ref}":
            tag = sha
    tag = peeled or tag
    if heads and tag and heads != tag:
        err(f"ref '{ref}' is ambiguous in {repo} (branch and tag differ)")
        return None
    return heads or tag or None


def check_tar(tgz, skill, members_file):
    """Reject archive entries with `..` or an absolute path anywhere in the
    archive. Entries under the skill path, or a LICENSE file at the repo root,
    are the only ones extracted; those must be a regular file or directory (no
    symlinks, hardlinks, devices, fifos). Links elsewhere in the repo are never
    extracted, so they are ignored. The in-scope member list is written to
    members_file."""
    try:
        with tarfile.open(tgz, "r:gz") as tf:
            infos = [(ti.name, ti.isreg(), ti.isdir(), ti.type) for ti in tf]
    except (tarfile.TarError, OSError, EOFError):
        die(f"cannot read archive {tgz}")
    for name, _, _, _ in infos:
        if name.startswith("/") or ".." in name.split("/"):
            die(f"unsafe path in archive: {name}")
    members = []
    for name, is_reg, is_dir, ttype in infos:
        _, sep, rel = name.partition("/")
        if not sep:
            continue
        rel = rel.rstrip("/")
        in_scope = rel == skill or rel.startswith(skill + "/") or rel in LICENSE_NAMES
        if not in_scope:
            continue
        if not (is_reg or is_dir):
            die(f"unsafe entry (link or special file) in archive: {name} (type {ttype!r})")
        members.append(name + "/" if is_dir else name)
    with open(members_file, "w", encoding="utf-8") as f:
        f.write("".join(m + "\n" for m in members))


def extract(tgz, members_file, dest, what):
    os.makedirs(dest, exist_ok=True)
    rc = subprocess.run(
        ["tar", "-xzf", tgz, "-C", dest, "--strip-components=1", "-T", members_file]
    ).returncode
    if rc != 0:
        die(f"cannot extract {what}")


def download(repo, sha, tgz):
    rc = subprocess.run(
        ["curl", "-fsSL", f"https://codeload.github.com/{repo}/tar.gz/{sha}", "-o", tgz]
    ).returncode
    if rc != 0:
        die(f"cannot download {repo}@{sha}")


def fm_name(path):
    """Value of `name:` in the SKILL.md frontmatter block."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    if not lines or not re.match(r"^---\s*$", lines[0]):
        return ""
    for line in lines[1:]:
        if re.match(r"^---\s*$", line):
            return ""
        if line.startswith("name:"):
            v = re.sub(r"^name:\s*", "", line)
            v = re.sub(r"\s+$", "", v)
            return re.sub(r"^[\"']|[\"']$", "", v)
    return ""


def check_skill(directory, expected):
    skill_md = os.path.join(directory, "SKILL.md")
    if not os.path.isfile(skill_md):
        die(f"{expected}: SKILL.md missing")
    got = fm_name(skill_md)
    if got != expected:
        die(f"{expected}: SKILL.md frontmatter name is '{got}', expected '{expected}'")


def has_symlink(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for n in dirnames + filenames:
            if os.path.islink(os.path.join(dirpath, n)):
                return True
    return False


class Sync:
    def __init__(self, community_ref, update_xcode, fork_ref):
        self.community_ref = community_ref
        self.update_xcode = update_xcode
        self.fork_ref = fork_ref
        self.work = tempfile.mkdtemp(prefix="tmp.")
        self.committed = False
        self.swaps = []  # (dest, backup or None), recorded before the first move

    # Undo swaps newest first. An entry is recorded before its first move, so each
    # step checks what actually happened: with a backup present the old content is
    # put back (dest holds the new content or nothing); without one the old content
    # never moved and dest is left alone. No backup is expected for a dest that did
    # not exist, so dest is removed there.
    def rollback(self):
        plugin_phys = os.path.realpath(PLUGIN_ROOT)
        for dest, backup in reversed(self.swaps):
            if not guard_dest(dest, plugin_phys, quiet=True):
                err(f"not rolling back '{dest}': its path is no longer safe")
                continue
            if backup is not None:
                if os.path.exists(backup) or os.path.islink(backup):
                    rm_rf(dest)
                    mv(backup, dest)
            else:
                rm_rf(dest)

    def cleanup(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            if not self.committed:
                self.rollback()
        except Exception:
            pass
        try:
            os.unlink(f"{LOCK}.tmp.{os.getpid()}")
        except OSError:
            pass
        shutil.rmtree(self.work, ignore_errors=True)

    # --- Fork drift check ----------------------------------------------------
    def fork_fetch(self, repo, path, sha, dest):
        tgz = os.path.join(self.work, f"fork-{sha}.tgz")
        members = os.path.join(self.work, f"fork-{sha}.members")
        download(repo, sha, tgz)
        check_tar(tgz, path, members)
        extract(tgz, members, dest, f"{repo}@{sha}")
        if not os.path.isdir(os.path.join(dest, path)):
            die(f"'{path}' not found in {repo}@{sha}")

    def fork_check(self):
        """Print `diff -ruN` of the locked upstream tree against REF's tree. Writes
        nothing to the plugin; exit 0 whatever the diff says, 1 if REF cannot resolve."""
        repo = lock_get("fork.swiftui-pro.repo")
        locked = lock_get("fork.swiftui-pro.commit")
        path = "swiftui-pro"
        if not repo or not locked:
            die("no fork.swiftui-pro lock lines to compare against")
        sha = resolve_ref(repo, self.fork_ref)
        if not sha:
            die(f"cannot resolve ref '{self.fork_ref}' in {repo}")
        self.fork_fetch(repo, path, locked, os.path.join(self.work, "fork-locked"))
        self.fork_fetch(repo, path, sha, os.path.join(self.work, "fork-new"))
        sys.stdout.flush()
        subprocess.run(["diff", "-ruN", "fork-locked", "fork-new"], cwd=self.work)

    # --- Main flow -----------------------------------------------------------
    def run(self):
        work = self.work
        stage_community = os.path.join(work, "stage", "community")
        stage_xcode = os.path.join(work, "stage", "xcode")
        for d in (stage_community, stage_xcode, os.path.join(work, "backup")):
            os.makedirs(d)

        if self.fork_ref:
            self.fork_check()
            return

        if not os.path.isdir(PLUGIN_ROOT):
            die(f"cannot resolve plugin root '{PLUGIN_ROOT}'")
        plugin_phys = os.path.realpath(PLUGIN_ROOT)
        for name, *_ in COMMUNITY:
            if not guard_dest(os.path.join(COMMUNITY_DIR, name), plugin_phys):
                sys.exit(1)
        if self.update_xcode:
            for name in XCODE_SKILLS:
                if not guard_dest(os.path.join(XCODE_DIR, name), plugin_phys):
                    sys.exit(1)

        # --- Xcode build bookkeeping ---
        installed_build = ""
        installed_version = ""
        if shutil.which("xcodebuild"):
            p = subprocess.run(
                ["xcodebuild", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in p.stdout.split("\n"):
                if line.startswith("Xcode ") and not installed_version:
                    installed_version = line[len("Xcode "):]
                if line.startswith("Build version ") and not installed_build:
                    installed_build = line[len("Build version "):]
        if not self.update_xcode:
            locked_build = lock_get("xcode.build")
            if locked_build and installed_build and locked_build != installed_build:
                err(
                    f"warning: installed Xcode build {installed_build} differs from locked "
                    f"{locked_build}; run with --update-xcode to refresh skills/xcode"
                )

        swaps = []  # (staged, dest)

        # --- Community skills ---
        lock_community = []
        for name, repo, path, license_ in COMMUNITY:
            ref = self.community_ref or lock_get(f"community.{name}.commit") or "HEAD"
            sha = resolve_ref(repo, ref)
            if not sha:
                die(f"cannot resolve ref '{ref}' in {repo}")
            tgz = os.path.join(work, f"{name}.tgz")
            members = os.path.join(work, f"{name}.members")
            download(repo, sha, tgz)
            check_tar(tgz, path, members)
            src = os.path.join(work, f"src-{name}")
            os.mkdir(src)
            extract(tgz, members, src, f"{repo}@{sha}")
            if not os.path.isdir(os.path.join(src, path)):
                die(f"{name}: '{path}' not found in {repo}@{sha}")
            lic_file = next(
                (os.path.join(src, c) for c in LICENSE_NAMES if os.path.isfile(os.path.join(src, c))),
                None,
            )
            if not lic_file:
                die(f"{name}: no LICENSE in {repo}@{sha}")
            staged = os.path.join(stage_community, name)
            shutil.copytree(os.path.join(src, path), staged, symlinks=True)
            shutil.copyfile(lic_file, os.path.join(staged, "LICENSE"))
            check_skill(staged, name)
            swaps.append((staged, os.path.join(COMMUNITY_DIR, name)))
            lock_community += [
                f"community.{name}.repo={repo}",
                f"community.{name}.commit={sha}",
                f"community.{name}.license={license_}",
                f"community.{name}.path={path}",
            ]

        # --- Xcode skills ---
        if self.update_xcode:
            if not shutil.which("xcrun"):
                die("--update-xcode needs xcrun (install Xcode)")
            if not installed_build:
                die("--update-xcode needs xcodebuild -version to report the build")
            xport = os.path.join(work, "xport")
            os.mkdir(xport)
            log_path = os.path.join(work, "xport.log")
            with open(log_path, "w") as log:
                rc = subprocess.run(
                    ["xcrun", "agent", "skills", "export", "--output-dir", xport],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                ).returncode
            if rc != 0:
                with open(log_path, encoding="utf-8", errors="replace") as f:
                    tail = "\n".join(f.read().rstrip("\n").split("\n")[-3:])
                die(f"xcrun agent skills export failed: {tail}")
            if has_symlink(xport):
                die("Xcode export contains a symlink")
            for name in XCODE_SKILLS:
                if not os.path.isdir(os.path.join(xport, name)):
                    die(f"{name}: missing from Xcode export")
                staged = os.path.join(stage_xcode, name)
                shutil.copytree(os.path.join(xport, name), staged, symlinks=True)
                check_skill(staged, name)
                swaps.append((staged, os.path.join(XCODE_DIR, name)))
            lock_xcode = [f"xcode.version={installed_version}", f"xcode.build={installed_build}"]
            lock_xcode += [f"xcode.skill={n}" for n in XCODE_SKILLS]
        else:
            lock_xcode = lock_lines("xcode.")

        lock_fork = lock_lines("fork.")

        # --- Swap everything in, then write the lock last ---
        # INT/TERM are ignored from the first move until the lock is in place, so the
        # swap, the lock write and the commit flag cannot be split by a signal.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        n = 0
        for staged, dest in swaps:
            if os.path.isdir(dest) and subprocess.run(
                ["diff", "-r", staged, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode == 0:
                continue
            if not guard_dest(dest, plugin_phys):
                sys.exit(1)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            backup = None
            if os.path.exists(dest) or os.path.islink(dest):
                n += 1
                backup = os.path.join(work, "backup", str(n))
            self.swaps.append((dest, backup))
            if backup is not None:
                rc = mv(dest, backup)
                if rc != 0:
                    sys.exit(rc)
            rc = mv(staged, dest)
            if rc != 0:
                sys.exit(rc)

        header = "# Generated by scripts/sync-ios-skills.py; do not edit."
        new_lock = "".join(ln + "\n" for ln in [header, *lock_community, *lock_xcode, *lock_fork])
        old_lock = None
        if os.path.isfile(LOCK):
            with open(LOCK, encoding="utf-8", errors="replace") as f:
                old_lock = f.read()
        if old_lock != new_lock:
            tmp = f"{LOCK}.tmp.{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new_lock)
            rc = mv(tmp, LOCK)
            if rc != 0:
                sys.exit(rc)
        self.committed = True

        msg = f"Synced {len(COMMUNITY)} community skills"
        if self.update_xcode:
            msg += f" and {len(XCODE_SKILLS)} Xcode skills"
        print(msg)


def parse_args(argv):
    community_ref = ""
    update_xcode = False
    fork_ref = ""
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--community-ref":
            if len(argv) - i < 2:
                usage_error("--community-ref needs a value")
            community_ref = argv[i + 1]
            i += 2
        elif arg == "--fork-ref":
            if len(argv) - i < 2:
                usage_error("--fork-ref needs a value")
            fork_ref = argv[i + 1]
            i += 2
        elif arg == "--update-xcode":
            update_xcode = True
            i += 1
        else:
            usage_error(f"unknown argument '{arg}'")
    return community_ref, update_xcode, fork_ref


def on_signal(signum, frame):
    sys.exit(130)


def main():
    community_ref, update_xcode, fork_ref = parse_args(sys.argv[1:])
    sync = Sync(community_ref, update_xcode, fork_ref)
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    try:
        sync.run()
    finally:
        sync.cleanup()


if __name__ == "__main__":
    main()
