#!/usr/bin/env python3
"""Codex plugins cannot declare agents, but Codex loads every *.toml under
$CODEX_HOME/agents/ and follows symlinks there. Keep one link pointing at
this plugin version's codex-agents/ so installs and updates need no manual step.
"""

import os
import sys


def say(message: str) -> None:
    print(f"android-expert-toolkit: {message}", file=sys.stderr)


def main() -> None:
    root = os.environ.get("PLUGIN_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    want = os.path.join(root, "codex-agents")
    codex_home = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
    agents_dir = os.path.join(codex_home, "agents")
    link = os.path.join(agents_dir, "android-expert-toolkit")

    if not os.path.isdir(want):
        return

    if os.path.islink(link):
        # Valid only when it targets this version and resolves; anything else is stale.
        if os.readlink(link) == want and os.path.isdir(link):
            return
    elif os.path.exists(link):
        say(f"{link} exists and is not a symlink; leaving it alone")
        return

    try:
        os.makedirs(agents_dir, exist_ok=True)
        if os.path.islink(link):
            os.unlink(link)
        os.symlink(want, link)
    except OSError:
        say(f"could not link {link} -> {want}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
