#!/usr/bin/env python3
"""Print the architecture verdict (NEW, TCA, MVVM or MIXED) for an iOS project directory.

Sweep patterns are defined in references/pattern-detection.md; keep them identical.
The patterns are written as POSIX ERE, exactly as in the reference; `[[:space:]]` is
translated to `\\s` when compiled.
"""

import fnmatch
import os
import re
import sys

PAT_TCA = '@Reducer'
PAT_MVVM_OBSERVABLE = '@Observable([^A-Za-z]|$)'
PAT_MVVM_OBJECT = 'class[^{]*:[^{]*ObservableObject'
PAT_UIKIT = 'class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*:[[:space:]]*UI[A-Za-z]*ViewController'

PRUNE_NAMES = ("Pods", "Carthage", ".build", "SourcePackages", "*Tests", "*Preview*")


def compile_ere(pattern: str) -> "re.Pattern[str]":
    return re.compile(pattern.replace("[[:space:]]", r"\s"))


def pruned(name: str) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in PRUNE_NAMES)


def swift_files(root: str) -> list:
    if not os.path.isdir(root):
        raise FileNotFoundError(root)
    if pruned(os.path.basename(os.path.normpath(root))):
        return []
    found = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not pruned(d)]
        for name in names:
            path = os.path.join(current, name)
            if name.endswith(".swift") and not pruned(name) and not os.path.islink(path):
                found.append(path)
    return found


def read_lines(path: str) -> list:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()
    except OSError:
        return []


def main(argv: list) -> int:
    if len(argv) < 2 or not argv[1]:
        print("run-sweeps.py: usage: run-sweeps.py <project-dir>", file=sys.stderr)
        return 1
    try:
        files = swift_files(argv[1])
    except FileNotFoundError:
        print(f"run-sweeps.py: {argv[1]}: No such directory", file=sys.stderr)
        return 1

    lines = {f: read_lines(f) for f in files}

    def matching(pattern: str) -> set:
        rx = compile_ere(pattern)
        return {f for f, ls in lines.items() if any(rx.search(line) for line in ls)}

    tca = len(matching(PAT_TCA))
    mvvm = len(matching(PAT_MVVM_OBSERVABLE) | matching(PAT_MVVM_OBJECT))
    uikit = len(matching(PAT_UIKIT))

    feature = sum(
        1
        for f in files
        if os.path.basename(f) != "ContentView.swift" and not any("@main" in line for line in lines[f])
    )

    total = tca + mvvm + uikit
    print(f"tca={tca} mvvm={mvvm} uikit={uikit} feature_files={feature}", file=sys.stderr)

    if feature == 0:
        print("NEW")
    elif total > 0 and tca * 10 >= 8 * total:
        print("TCA")
    elif total > 0 and (mvvm + uikit) * 10 >= 8 * total:
        print("MVVM")
    else:
        print("MIXED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
