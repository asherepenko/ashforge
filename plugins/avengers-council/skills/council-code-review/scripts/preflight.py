#!/usr/bin/env python3
"""Pre-flight context for the council-code-review skill.

Output is labeled with `== section ==` headers. Probes run in parallel and
are printed serially in a fixed order so section blocks never interleave.
Use the output to bound review scope before Step 1 — if working tree is
clean and no commits ahead, there is no `--diff` to review.
"""
import concurrent.futures
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

# scripts/ -> <skill>/ -> skills/ -> plugin root
PLUGIN_ROOT = Path(__file__).resolve().parents[3]

HOME = os.environ.get("HOME", "")


def git(*args):
    """Run git, return (returncode, stdout) with stderr discarded."""
    p = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.returncode, p.stdout.decode("utf-8", errors="surrogateescape")


def newest(pattern, limit, empty):
    """`ls -1t PATTERN | head -N`, or the `empty` marker when nothing matches."""
    paths = [p for p in glob.glob(pattern) if os.path.exists(p)]
    if not paths:
        return empty + "\n"
    paths.sort(key=lambda p: (-os.stat(p).st_mtime_ns, p))
    return "".join(p + "\n" for p in paths[:limit])


def head(text, limit):
    return "".join(text.splitlines(keepends=True)[:limit])


def tail(text, limit):
    return "".join(text.splitlines(keepends=True)[-limit:])


def branch():
    rc, out = git("branch", "--show-current")
    return out if rc == 0 else "NOT_A_REPO\n"


def resolve_base():
    for ref in ("origin/main", "main", "master"):
        rc, out = git("merge-base", "HEAD", ref)
        if rc == 0:
            return out.rstrip("\n")
    return ""


# One manifest list feeds both the manifest probe (include) and the
# code-files probe (exclude): a dependency or CI change is never "code".
MANIFEST_NAMES = """package.json package-lock.json yarn.lock pnpm-lock.yaml pyproject.toml poetry.lock uv.lock
requirements*.txt build.gradle build.gradle.kts libs.versions.toml Podfile Podfile.lock Package.resolved
go.mod go.sum Cargo.toml Cargo.lock Gemfile Gemfile.lock Dockerfile""".split()
MANIFEST_GLOBS = [f"**/{n}" for n in MANIFEST_NAMES] + [".github/workflows/**"]
MARKERS = ["build.gradle.kts", "package.json", "pyproject.toml", "go.mod", "Cargo.toml", "settings.gradle.kts"]
DEF_RE = re.compile(r"^\+[ \t\n\r\f\v]*(def|fun|func|class|function|interface|struct|object) ")


def diff_stat(base):
    if not base:
        return "NO_BASE\n"
    return tail(git("diff", "--stat", f"{base}...HEAD")[1], 30)


def commits_ahead(base):
    if not base:
        return "NONE\n"
    return head(git("log", "--oneline", f"{base}..HEAD")[1], 20)


def status():
    rc, out = git("status", "-s")
    return head(out, 40) if rc == 0 else "NO_REPO\n"


def project_markers():
    found = sorted((m for m in MARKERS if os.path.exists(m)), key=str.casefold)
    return "".join(m + "\n" for m in found) or "NO_MARKERS\n"


def manifests_changed(base):
    if not base:
        return "UNKNOWN — no base\n"
    specs = [f":(glob){g}" for g in MANIFEST_GLOBS]
    paths = [p for p in git("diff", "-z", "--name-only", f"{base}...HEAD", "--", *specs)[1].split("\0") if p]
    return "".join(p + "\n" for p in paths) or "NONE\n"


def code_files(base):
    if not base:
        return "UNKNOWN — no base\n"
    # Docs and config/assets are not code.
    specs = [".", ":(exclude)docs", ":(exclude,glob)**/docs/**", ":(exclude,glob)**/.env*"]
    specs += [f":(exclude,glob){g}" for g in MANIFEST_GLOBS]
    specs += [f":(exclude,glob)**/*.{ext}" for ext in
              "md json yaml yml toml ini lock png jpg jpeg gif svg webp ico".split()]
    tokens = git("diff", "-z", "--name-status", "-M", "--diff-filter=AR", f"{base}...HEAD", "--", *specs)[1].split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    paths, i = [], 0
    while i < len(tokens):
        status_code = tokens[i]
        if status_code.startswith("R"):
            path = tokens[i + 2] if i + 2 < len(tokens) else ""
            i += 3
        else:
            path = tokens[i + 1] if i + 1 < len(tokens) else ""
            i += 2
        paths.append(path)
    patch = git("diff", "-U0", f"{base}...HEAD", "--", *specs)[1]
    defs = sum(1 for line in patch.split("\n") if DEF_RE.match(line))
    out = f"COUNT={len(paths)}\nADDED_DEFS={defs}\n"
    out += "".join(p + "\n" for p in paths[:30]) if paths else "NONE\n"
    return out

def _codex_profile():
    cfg = os.path.join(os.environ.get("CODEX_HOME") or os.path.join(HOME, ".codex"), "config.toml")
    spawn = "prompt-embed"
    # Modern agents.enabled defaults true. Config is only a hint: exposed
    # spawn tools and session restrictions are authoritative in the skill.
    if os.path.isfile(cfg):
        section, modern, legacy = "", "", ""
        with open(cfg, encoding="utf-8", errors="replace") as fh:
            for line in fh.read().split("\n"):
                if re.match(r"\[agents\]", line):
                    section = "agents"
                elif re.match(r"\[features\]", line):
                    section = "features"
                elif line.startswith("["):
                    section = ""
                elif section == "agents" and re.match(r"[ \t\r\f\v]*enabled[ \t\r\f\v]*=", line):
                    modern = line
                elif section == "features" and re.match(r"[ \t\r\f\v]*multi_agent[ \t\r\f\v]*=", line):
                    legacy = line
        if re.search(r"=[ \t\r\f\v]*false([ \t\r\f\v]|$)", modern or legacy):
            spawn = "none"
    notes = ("config hint only; discover actual spawn/continuation tools before dispatch; "
             "agents.enabled defaults true, features.multi_agent is legacy")
    return "codex", spawn, "hub", notes


def probe_runtime():
    env = os.environ
    runtime, spawn, transport, notes = "unknown", "unknown", "unknown", ""
    # Definitive env markers of the RUNNING runtime first; install-dir
    # heuristics (~/.codex etc.) only when nothing else matched — a directory
    # proves installation, not the current runtime.
    if env.get("ZCODE_APP_VERSION"):
        runtime, spawn, transport = "zcode", "registry", "hub"
        notes = "result-returning Agent spawns; SendMessage resume available; TaskCreate -> TodoWrite"
    elif env.get("CLAUDECODE") or env.get("CLAUDE_PLUGIN_ROOT"):
        runtime, spawn, transport = "claude-code", "registry", "hub"
        notes = ("ordinary subagents; only select stay-alive after verifying interactive session "
                 "and enabled agent teams; main is ordinary-subagent lead")
        if env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0") == "1" and env.get("AVENGERS_COUNCIL_INTERACTIVE", "0") == "1":
            transport = "stay-alive"
            notes = "interactive hint supplied by orchestrator; confirm actual teammate launch before using team-lead"
    elif env.get("CODEX_HOME"):
        runtime, spawn, transport, notes = _codex_profile()
    elif os.path.isdir(os.path.join(HOME, ".antigravity")):
        runtime, transport = "antigravity", "hub"
        notes = "discover actual spawn tools before dispatch"
    elif os.path.isdir(os.path.join(HOME, ".pi")):
        runtime, spawn, transport = "pi", "none", "hub"
        notes = "no native subagent tool; discover installed subagent extension before dispatch"
    elif os.path.isdir(os.path.join(HOME, ".codex")):
        runtime, spawn, transport, notes = _codex_profile()
    return (f"RUNTIME={runtime}\nSPAWN={spawn}\nTRANSPORT={transport}\nNOTES={notes or 'none'}\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="surrogateescape")
    sys.stdout.write(f"== Plugin root ==\n{PLUGIN_ROOT}\n")
    base = resolve_base()
    probes = [
        ("Current branch", branch),
        ("Working tree status", status),
        ("Diff stat (vs base)", lambda: diff_stat(base)),
        ("Commits ahead", lambda: commits_ahead(base)),
        ("Project markers", project_markers),
        ("Recent reviews", lambda: newest(".artifacts/reviews/*.md", 5, "NO_REVIEWS")),
        ("Runtime capability", lambda: probe_runtime()),
        ("Dependency manifests changed", lambda: manifests_changed(base)),
        ("Code files added or moved", lambda: code_files(base)),
    ]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = [pool.submit(probe) for _, probe in probes]
        for (title, _), future in zip(probes, futures):
            sys.stdout.write(f"== {title} ==\n{future.result()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
