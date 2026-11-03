#!/usr/bin/env python3
"""Pre-flight context for the council-plan-review skill.

Output is labeled with `== section ==` headers. Probes run in parallel and
are printed serially in a fixed order so section blocks never interleave.
Use the output to short-circuit Step 1 plan auto-detection and to surface
domain artifacts (DOMAIN.md / docs/adr/) that feed every reviewer's brief.
"""
import concurrent.futures
import glob
import os
import re
import subprocess
import sys

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


def domain_glossary():
    for name in ("DOMAIN-MAP.md", "DOMAIN.md", "CONTEXT-MAP.md", "CONTEXT.md"):
        if os.path.isfile(name):
            return name + "\n"
    return "NONE\n"

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


PROBES = [
    ("Local plans dir", lambda: newest(".claude/plans/*.md", 10, "NO_LOCAL_PLANS")),
    ("Global plans dir", lambda: newest(os.path.join(glob.escape(HOME), ".claude/plans/*.md"), 10, "NO_GLOBAL_PLANS")),
    ("Artifact specs (PRDs)", lambda: newest(".artifacts/specs/prd-*.md", 5, "NO_PRDS")),
    ("Recent reviews", lambda: newest(".artifacts/reviews/*.md", 5, "NO_REVIEWS")),
    ("Domain glossary", domain_glossary),
    ("ADRs (most recent 20)", lambda: newest("docs/adr/*.md", 20, "NONE")),
    ("Active branch", branch),
    ("Runtime capability", lambda: probe_runtime()),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="surrogateescape")
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = [pool.submit(probe) for _, probe in PROBES]
        for (title, _), future in zip(PROBES, futures):
            sys.stdout.write(f"== {title} ==\n{future.result()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
