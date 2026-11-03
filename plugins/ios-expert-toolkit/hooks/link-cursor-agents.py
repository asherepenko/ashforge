#!/usr/bin/env python3
"""Cursor loads user subagents from ~/.cursor/agents/*.md in the same Markdown
format as agents/*.md, and nothing in a Claude plugin reaches that directory.
Keep one symlink per agent pointing at this plugin version so installs and
updates need no manual step. Runs only when Cursor's home exists.
Never fails the session: every error path exits 0.
"""

import fnmatch
import glob
import os
import sys

OWN_LINK_TARGET = "*/ios-expert-toolkit/*/agents/*.md"


def warn(message: str) -> None:
    print(f"ios-expert-toolkit: {message}", file=sys.stderr)


def main() -> int:
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cursor_home = os.environ.get("CURSOR_HOME") or os.path.join(os.path.expanduser("~"), ".cursor")
    agents_dir = os.path.join(cursor_home, "agents")

    if not (os.path.isdir(os.path.join(root, "agents")) and os.path.isdir(cursor_home)):
        return 0
    try:
        os.makedirs(agents_dir, exist_ok=True)
    except OSError:
        warn(f"cannot create {agents_dir}")
        return 0

    # Drop links from an earlier version whose agent no longer exists.
    for link in sorted(glob.glob(os.path.join(glob.escape(agents_dir), "*.md"))):
        if os.path.islink(link) and fnmatch.fnmatchcase(os.readlink(link), OWN_LINK_TARGET) and not os.path.exists(link):
            try:
                os.unlink(link)
            except OSError:
                pass

    for want in sorted(glob.glob(os.path.join(glob.escape(root), "agents", "*.md"))):
        if not os.path.isfile(want):
            continue
        link = os.path.join(agents_dir, os.path.basename(want))
        if os.path.islink(link):
            target = os.readlink(link)
            # Valid only when it targets this version and resolves; anything else is stale.
            if target == want and os.path.isfile(link):
                continue
            # Replace a stale link only when this plugin made it; never touch another plugin's link.
            if not fnmatch.fnmatchcase(target, OWN_LINK_TARGET):
                warn(f"{link} points at another plugin; leaving it alone")
                continue
        elif os.path.exists(link):
            warn(f"{link} exists and is not a symlink; leaving it alone")
            continue
        try:
            if os.path.islink(link):
                os.unlink(link)
            os.symlink(want, link)
        except OSError:
            warn(f"could not link {link} -> {want}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
