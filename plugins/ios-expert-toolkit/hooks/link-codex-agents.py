#!/usr/bin/env python3
"""Codex plugins cannot declare agents, but Codex loads every *.toml under
$CODEX_HOME/agents/ and follows symlinks there. Keep one link pointing at
this plugin version's codex-agents/ so installs and updates need no manual step.
Never fails the session: every error path exits 0.
"""

import os
import sys


def main() -> int:
    root = os.environ.get("PLUGIN_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    want = os.path.join(root, "codex-agents")
    agents_dir = os.path.join(os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex"), "agents")
    link = os.path.join(agents_dir, "ios-expert-toolkit")

    if not os.path.isdir(want):
        return 0

    if os.path.islink(link):
        # Valid only when it targets this version and resolves; anything else is stale.
        if os.readlink(link) == want and os.path.isdir(link):
            return 0
    elif os.path.exists(link):
        print(f"ios-expert-toolkit: {link} exists and is not a symlink; leaving it alone", file=sys.stderr)
        return 0

    try:
        os.makedirs(agents_dir, exist_ok=True)
        if os.path.islink(link):
            os.unlink(link)
        os.symlink(want, link)
    except OSError:
        print(f"ios-expert-toolkit: could not link {link} -> {want}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
