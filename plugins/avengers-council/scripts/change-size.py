#!/usr/bin/env python3
"""change-size.py — the Change Sizing bucket for a diff.

SKILL.md anchors the buckets at ~100 (good), ~300 (acceptable if one logical
change) and ~1000 (too large). The cut points sit between those anchors so
every reviewer lands on the same bucket, and this file is the only place the
thresholds live. /two-stage-review prints the bucket as its Size line and
verify-signals.sh reads it; neither feeds the Quality letter.

Usage:
  change-size.py <base> [<head>]   lines added+deleted in <base>...<head> (head defaults to HEAD)
  change-size.py --classify <N>    bucket for N lines
Output: LINES=<n>  BUCKET=good|acceptable|too-large   (--classify: bucket only)
Exit:   0 ok · 2 usage error or unknown base
"""
import re
import subprocess
import sys

GOOD_MAX = 200
ACCEPTABLE_MAX = 600


def usage():
    print("usage: change-size.py <base> [<head>] | --classify <lines>", file=sys.stderr)
    sys.exit(2)


def classify(n):
    if n <= GOOD_MAX:
        return "good"
    if n <= ACCEPTABLE_MAX:
        return "acceptable"
    return "too-large"


def commit_exists(rev):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", rev + "^{commit}"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def main(argv):
    if not argv:
        usage()
    if argv[0] == "--classify":
        if len(argv) != 2 or not re.fullmatch(r"[0-9]+", argv[1]):
            usage()
        print(classify(int(argv[1])))
        return 0
    if len(argv) > 2:
        usage()
    base = argv[0]
    head = argv[1] if len(argv) > 1 else "HEAD"
    if not commit_exists(base):
        print(f"change-size.py: unknown base '{base}'", file=sys.stderr)
        return 2
    if not commit_exists(head):
        print(f"change-size.py: unknown head '{head}'", file=sys.stderr)
        return 2

    diff = subprocess.run(["git", "diff", "--numstat", f"{base}...{head}"],
                          stdout=subprocess.PIPE, text=True, errors="replace")
    if diff.returncode != 0:
        return diff.returncode
    lines = 0
    for row in diff.stdout.splitlines():
        parts = row.split("\t")
        # Binary files show "-" in numstat and carry no reviewable lines.
        if len(parts) >= 2 and parts[0] != "-":
            lines += int(parts[0]) + int(parts[1])
    print(f"LINES={lines}")
    print(f"BUCKET={classify(lines)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
