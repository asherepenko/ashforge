#!/usr/bin/env python3
"""Count iOS pattern usage per category, apply the 80/20 matrix and the architecture verdict.

Usage: detect-patterns.py [--write-cache] <project-dir> [category ...]
       detect-patterns.py --hash <project-dir>
Categories: architecture, di, testing, persistence, concurrency, navigation, version
(default: all). Exit 2 on a usage error or a missing directory.

Sweep patterns are defined in references/pattern-detection.md; keep them identical
(tests/test_detect_patterns_reference.py parses the reference and compares). The
architecture patterns are POSIX ERE and the other sweeps are rg regexes, written exactly
as in the reference; `[[:space:]]` is translated to `\\s` when compiled.

A count is the number of Swift files with at least one matching line (a file counts
once). Matching runs on code only: comments and the contents of string literals are
blanked first (line structure kept), so `// @Reducer` and `"Factory"` never count. Every Swift sweep skips Pods, Carthage, .build, SourcePackages and any path
component matching *Preview*; all but the testing sweeps also skip any *Tests path
component. Directories pruned from everything: DerivedData, .git, .artifacts, node_modules.

Candidates that compete inside one decision share 100%. A decision's verdict:
match (dominant >= 80%), conflict (50-79%), adopt (< 50%), none (no matches).
Ties go to the candidate declared first. Sweeps outside a decision are printed as
`count <id> files=N`.

The architecture section also prints `verdict_architecture=NEW|TCA|MVVM|MIXED`:
NEW when no Swift file exists beyond the Xcode template (the @main file and
ContentView.swift), TCA when TCA files are >= 80% of TCA + MVVM + UIKit, MVVM when
MVVM + UIKit files are >= 80%, MIXED otherwise. The version section prints
key=value facts, no verdict.

With --write-cache the architecture verdict, the dominant candidate of each
decision and the version facts are written to .artifacts/iet/cache/detected-patterns.json
under the project directory, keyed by project_hash: sha256 over the lines
"<relpath>\t<sha256 of file bytes>\n", sorted by relpath, for every .swift file after
pruning plus every Package.swift, Package.resolved, *.xcodeproj/project.pbxproj and
*.xcconfig at any depth (NO_PROJECT_FILES when there are none). --hash prints only
`project_hash=<hex>`; preflight.py imports project_hash from this file.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path

Grep = namedtuple("Grep", "id pattern in_tests", defaults=(False,))
Settings = namedtuple("Settings", "id pattern paths")
Decision = namedtuple("Decision", "key candidates")

MATCH_PERCENT = 80
CONFLICT_PERCENT = 50

PAT_TCA = "@Reducer([^A-Za-z0-9_]|$)"
PAT_MVVM_OBSERVABLE = "@Observable([^A-Za-z0-9_]|$)"
PAT_MVVM_OBJECT = "(^|[^A-Za-z0-9_])class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*(<[^{]*>)?[[:space:]]*:([^{]*[^A-Za-z0-9_])?ObservableObject([^A-Za-z0-9_]|$)"
PAT_UIKIT = "(^|[^A-Za-z0-9_])class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*:[[:space:]]*UI[A-Za-z]*ViewController([^A-Za-z0-9_]|$)"

PAT_DEPENDENCY = r"@Dependency\b|(^|[^A-Za-z0-9_])(Test)?DependencyKey([^A-Za-z0-9_]|$)"
PAT_FACTORY = (
    "Factory([^a-z]|$)|func make[A-Z][A-Za-z]*"
    "(ViewModel|Service|Client|Repository|Manager|Provider|UseCase|Interactor|Presenter)\\("
)
PAT_SWIFT_TESTING = "import Testing([^A-Za-z0-9_]|$)"
PAT_XCTEST = "XCTestCase([^A-Za-z0-9_]|$)"
PAT_NAV_STACK = r"(^|[^A-Za-z0-9_])NavigationStack(Store)?([^A-Za-z0-9_]|$)|\.navigationDestination\("
PAT_COORDINATOR = (
    "(class|struct|actor)[[:space:]]+[A-Za-z0-9_]+Coordinator([^A-Za-z0-9_]|$)"
    "|protocol[[:space:]]+[A-Za-z0-9_]*Coordinator([^A-Za-z0-9_]|$)"
    "|UINavigationController([^A-Za-z0-9_]|$)"
)

SETTINGS_PATHS = ("Package.swift", "*.xcodeproj/project.pbxproj")

SWEEPS = {
    "architecture": (
        Grep("tca", PAT_TCA),
        Grep("mvvm_observable", PAT_MVVM_OBSERVABLE),
        Grep("mvvm_object", PAT_MVVM_OBJECT),
        Grep("uikit", PAT_UIKIT),
    ),
    "di": (
        Grep("tca_dependency", PAT_DEPENDENCY),
        Grep("singleton", r"static let shared\b"),
        Grep("factory", PAT_FACTORY),
    ),
    "testing": (
        Grep("swift_testing", PAT_SWIFT_TESTING, True),
        Grep("xctest", PAT_XCTEST, True),
    ),
    "persistence": (
        Grep("swiftdata", r"@Model\b"),
        Grep("core_data", "NSManagedObject"),
    ),
    "concurrency": (
        Settings("language_mode_settings", "swiftLanguageModes|SWIFT_VERSION", SETTINGS_PATHS),
        Grep("main_actor", "@MainActor"),
    ),
    "navigation": (
        Grep("navigation_stack", PAT_NAV_STACK),
        Grep("coordinator", PAT_COORDINATOR),
    ),
    "version": (),
}

DECISIONS = {
    "architecture": (),
    "di": (
        Decision(
            "di_style",
            {"tca_dependency": ("tca_dependency",), "factory": ("factory",), "singleton": ("singleton",)},
        ),
    ),
    "testing": (
        Decision("testing_framework", {"swift_testing": ("swift_testing",), "xctest": ("xctest",)}),
    ),
    "persistence": (
        Decision("persistence_framework", {"swiftdata": ("swiftdata",), "core_data": ("core_data",)}),
    ),
    "concurrency": (),
    "navigation": (
        Decision("navigation_style", {"navigation_stack": ("navigation_stack",), "coordinator": ("coordinator",)}),
    ),
    "version": (),
}

PRUNE_DIRS = {"Pods", "Carthage", ".build", "SourcePackages", "DerivedData", ".git", ".artifacts", "node_modules"}
PREVIEW_GLOB = "*Preview*"
TESTS_GLOB = "*Tests"
CACHE_PATH = Path(".artifacts/iet/cache/detected-patterns.json")
EVIDENCE_LIMIT = 3
PROG = "detect-patterns.py"

DEPLOY = re.compile(r"IPHONEOS_DEPLOYMENT_TARGET\s*=\s*([\d.]+)")
SWIFT_VERSION = re.compile(r"SWIFT_VERSION\s*=\s*([\d.]+)")
LANG_MODES = re.compile(r"swiftLanguageModes\s*:\s*(\[[^\]]*\])")


def compile_pattern(pattern: str) -> "re.Pattern[str]":
    return re.compile(pattern.replace("[[:space:]]", r"\s"))


def strip_code(text: str) -> str:
    """Swift source with comments removed and string-literal contents emptied; newlines kept."""
    out, i, n = [], 0, len(text)
    while i < n:
        two = text[i : i + 2]
        if two == "//":
            while i < n and text[i] != "\n":
                i += 1
        elif two == "/*":
            depth, i = 1, i + 2
            while i < n and depth:
                if text.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    out.append("\n" if text[i] == "\n" else "")
                    i += 1
        elif text[i] in '#"':
            j = i
            while j < n and text[j] == "#":
                j += 1
            if j >= n or text[j] != '"':
                out.append(text[i])
                i += 1
                continue
            hashes = text[i:j]
            multi = text.startswith('"""', j)
            quote = '"""' if multi else '"'
            out.append(quote)
            i = j + len(quote)
            closer = quote + hashes
            while i < n and not text.startswith(closer, i):
                if text[i] == "\\" and i + 1 < n and text[i + 1 : i + 1 + len(hashes)] == hashes:
                    i += 1 + len(hashes)
                if i < n and text[i] == "\n":
                    if not multi:
                        break
                    out.append("\n")
                i += 1
            if text.startswith(closer, i):
                i += len(closer)
            out.append(quote)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def is_project_file(rel: str) -> bool:
    parts = rel.split("/")
    name = parts[-1]
    return (
        name in ("Package.swift", "Package.resolved")
        or name.endswith(".xcconfig")
        or (name == "project.pbxproj" and len(parts) > 1 and parts[-2].endswith(".xcodeproj"))
    )


def project_hash(root: Path, files: list = None) -> str:
    """sha256 over sorted `<relpath>\\t<sha256 of bytes>\\n` lines of every scanned and project file."""
    root = Path(root)
    rows = []
    for rel in files if files is not None else list_files(root):
        if rel.endswith(".swift") or is_project_file(rel):
            try:
                content = (root / rel).read_bytes()
            except OSError:
                continue
            rows.append((rel, hashlib.sha256(content).hexdigest()))
    if not rows:
        return "NO_PROJECT_FILES"
    digest = hashlib.sha256()
    for rel, sha in sorted(rows):
        digest.update(f"{rel}\t{sha}\n".encode("utf-8", "surrogateescape"))
    return digest.hexdigest()


def list_files(root: Path) -> list:
    """Relative POSIX paths of regular files, sorted, with pruned directories skipped."""
    found = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in PRUNE_DIRS)
        for name in names:
            path = os.path.join(current, name)
            if not os.path.islink(path):
                found.append(Path(os.path.relpath(path, root)).as_posix())
    return sorted(found)


def skipped(rel: str, in_tests: bool) -> bool:
    for part in rel.split("/"):
        if fnmatch.fnmatchcase(part, PREVIEW_GLOB) or (not in_tests and fnmatch.fnmatchcase(part, TESTS_GLOB)):
            return True
    return False


def glob_matches(rel: str, glob: str) -> bool:
    rel_parts, glob_parts = rel.split("/"), glob.split("/")
    return len(rel_parts) == len(glob_parts) and all(
        fnmatch.fnmatchcase(r, g) for r, g in zip(rel_parts, glob_parts)
    )


class Scanner:
    def __init__(self, root: Path):
        self.root = root
        self.files = list_files(root)
        self.swift = [f for f in self.files if f.endswith(".swift")]
        self._text = {}
        self._code = {}

    def code(self, rel: str) -> str:
        """Text the sweeps match against: Swift files with comments and strings blanked, others raw."""
        if rel not in self._code:
            text = self.text(rel)
            self._code[rel] = strip_code(text) if rel.endswith(".swift") else text
        return self._code[rel]

    def text(self, rel: str) -> str:
        if rel not in self._text:
            try:
                self._text[rel] = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._text[rel] = ""
        return self._text[rel]

    def lines(self, rel: str) -> list:
        return self.code(rel).splitlines()

    def matches(self, sweep) -> list:
        include = compile_pattern(sweep.pattern)
        if isinstance(sweep, Settings):
            candidates = [f for f in self.files if any(glob_matches(f, g) for g in sweep.paths)]
        else:
            candidates = [f for f in self.swift if not skipped(f, sweep.in_tests)]
        return [f for f in candidates if any(include.search(line) for line in self.lines(f))]

    def feature_files(self) -> int:
        return sum(
            1
            for f in self.swift
            if not skipped(f, False)
            and f.rsplit("/", 1)[-1] != "ContentView.swift"
            and not any("@main" in line for line in self.lines(f))
        )

    def version_facts(self) -> dict:
        pbx = [f for f in self.files if f.endswith(".pbxproj")]
        manifests = [f for f in self.files if f.rsplit("/", 1)[-1] == "Package.swift"]
        resolved = [f for f in self.files if f.rsplit("/", 1)[-1] == "Package.resolved"]
        return {
            "tca_version": sorted(self._tca_versions(resolved)),
            "deployment_target": sorted({v for f in pbx for v in DEPLOY.findall(self.text(f))}),
            "swift_version": sorted({v for f in pbx for v in SWIFT_VERSION.findall(self.text(f))}),
            "swift_language_modes": sorted({v for f in manifests for v in LANG_MODES.findall(self.code(f))}),
        }

    def version_sources(self) -> list:
        """`path:kind` for each file a version fact came from, sorted."""
        sources = set()
        for rel in self.files:
            name = rel.rsplit("/", 1)[-1]
            if rel.endswith(".pbxproj"):
                if DEPLOY.search(self.text(rel)):
                    sources.add(f"{rel}:deployment_target")
                if SWIFT_VERSION.search(self.text(rel)):
                    sources.add(f"{rel}:swift_version")
            elif name == "Package.swift" and LANG_MODES.search(self.code(rel)):
                sources.add(f"{rel}:swift_language_modes")
            elif name == "Package.resolved" and self._tca_versions([rel]):
                sources.add(f"{rel}:tca_version")
        return sorted(sources)

    def _tca_versions(self, resolved: list) -> set:
        versions = set()
        for rel in resolved:
            try:
                data = json.loads(self.text(rel))
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            obj = data.get("object")
            pins = data.get("pins") or (obj.get("pins") if isinstance(obj, dict) else None) or []
            for pin in pins:
                if not isinstance(pin, dict):
                    continue
                ident = pin.get("identity") or str(pin.get("package", "")).lower()
                state = pin.get("state") or {}
                if ident == "swift-composable-architecture" and state.get("version"):
                    versions.add(state["version"])
        return versions


def percent(count: int, total: int) -> str:
    return f"{100 * count / total:.1f}%" if total else "0.0%"


def verdict(count: int, total: int) -> str:
    if total == 0:
        return "none"
    if count * 100 >= MATCH_PERCENT * total:
        return "match"
    if count * 100 >= CONFLICT_PERCENT * total:
        return "conflict"
    return "adopt"


def evaluate(decision: Decision, found: dict) -> dict:
    files = {}
    for name, members in decision.candidates.items():
        files[name] = sorted({f for m in members for f in found[m]})
    total = sum(len(v) for v in files.values())
    dominant = max(files, key=lambda k: len(files[k])) if total else None
    count = len(files[dominant]) if dominant else 0
    return {"files": files, "total": total, "dominant": dominant, "count": count}


def architecture_verdict(found: dict, feature_files: int) -> dict:
    """The NEW/TCA/MVVM/MIXED verdict with the cache entry it implies."""
    tca = found["tca"]
    mvvm = sorted(set(found["mvvm_observable"]) | set(found["mvvm_object"]))
    uikit = found["uikit"]
    total = len(tca) + len(mvvm) + len(uikit)
    counts = {"tca": len(tca), "mvvm": len(mvvm), "uikit": len(uikit)}
    mvvm_side = [f"{f}:mvvm" for f in mvvm] + [f"{f}:uikit" for f in uikit]
    tca_side = [f"{f}:tca" for f in tca]
    if feature_files == 0:
        name, confidence, evidence = "NEW", 1.0, []
    elif total > 0 and len(tca) * 10 >= 8 * total:
        name, confidence, evidence = "TCA", len(tca) / total, tca_side
    elif total > 0 and (len(mvvm) + len(uikit)) * 10 >= 8 * total:
        name, confidence, evidence = "MVVM", (len(mvvm) + len(uikit)) / total, mvvm_side
    else:
        leader_is_tca = len(tca) >= len(mvvm) + len(uikit)
        share = max(len(tca), len(mvvm) + len(uikit)) / total if total else 0.0
        name, confidence, evidence = "MIXED", share, tca_side if leader_is_tca and total else mvvm_side
    return {
        "verdict": name,
        "counts": counts,
        "entry": {
            "detected": name,
            "confidence": round(confidence, 2),
            "evidence": evidence[:EVIDENCE_LIMIT],
        },
    }


def report_architecture(scanner: Scanner, found: dict, patterns: dict) -> list:
    arch = architecture_verdict(found, scanner.feature_files())
    union = sorted(set(found["mvvm_observable"]) | set(found["mvvm_object"]))
    out = ["== architecture =="]
    out.append(f"count tca files={len(found['tca'])}")
    out.append(f"count mvvm_observable files={len(found['mvvm_observable'])}")
    out.append(f"count mvvm_object files={len(found['mvvm_object'])}")
    out.append(f"count mvvm files={len(union)}")
    out.append(f"count uikit files={len(found['uikit'])}")
    out.append(f"count feature_files files={scanner.feature_files()}")
    out.append(f"verdict_architecture={arch['verdict']}")
    patterns["architecture"] = arch["entry"]
    return out


def report_version(scanner: Scanner, patterns: dict) -> list:
    out = ["== version =="]
    facts = scanner.version_facts()
    for key, values in facts.items():
        out.append(f"{key}={', '.join(values) if values else 'none'}")
    joined = {key: ",".join(values) if values else "none" for key, values in facts.items()}
    patterns["version"] = {
        "detected": (
            f"tca={joined['tca_version']};deployment={joined['deployment_target']};"
            f"swift={joined['swift_version']};modes={joined['swift_language_modes']}"
        ),
        "confidence": 1.0,
        "evidence": scanner.version_sources()[:EVIDENCE_LIMIT],
    }
    return out


def report_category(category: str, found: dict, patterns: dict) -> list:
    out = [f"== {category} =="]
    in_decision = set()
    for decision in DECISIONS[category]:
        result = evaluate(decision, found)
        dominant, count, total = result["dominant"], result["count"], result["total"]
        out.append(f"decision {decision.key}")
        for name, files in result["files"].items():
            out.append(f"  {name} files={len(files)} share={percent(len(files), total)}")
        out.append(f"  dominant={dominant or 'none'} consistency={percent(count, total)} verdict={verdict(count, total)}")
        in_decision.update(m for members in decision.candidates.values() for m in members)
        patterns[decision.key] = {
            "detected": dominant or "none",
            "confidence": round(count / total, 2) if total else 0.0,
            "evidence": [f"{f}:{dominant}" for f in result["files"][dominant][:EVIDENCE_LIMIT]] if dominant else [],
        }
    for sweep in SWEEPS[category]:
        if sweep.id not in in_decision:
            out.append(f"count {sweep.id} files={len(found[sweep.id])}")
    return out


def write_cache(root: Path, patterns: dict, digest: str) -> None:
    path = root / CACHE_PATH
    merged = {}
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("project_hash") == digest and isinstance(old.get("patterns"), dict):
            merged = old["patterns"]
    except (OSError, ValueError, AttributeError):
        pass
    merged.update(patterns)
    payload = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_hash": digest,
        "patterns": merged,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(prog=PROG, description="Count iOS patterns per category.")
    parser.add_argument("project_dir")
    parser.add_argument("categories", nargs="*", metavar="category", help="|".join(SWEEPS) + "|all")
    parser.add_argument("--hash", action="store_true", help="print only project_hash=<hex> and exit")
    parser.add_argument("--write-cache", action="store_true", help="write .artifacts/iet/cache/detected-patterns.json")
    args = parser.parse_intermixed_args(argv)

    for name in args.categories:
        if name != "all" and name not in SWEEPS:
            parser.error(f"unknown category: {name} (expected one of {', '.join(SWEEPS)}, all)")
    root = Path(args.project_dir)
    if not root.is_dir():
        print(f"{PROG}: {args.project_dir}: No such directory", file=sys.stderr)
        return 2

    if args.hash:
        print(f"project_hash={project_hash(root)}")
        return 0

    wanted = set(args.categories)
    categories = [c for c in SWEEPS if not wanted or "all" in wanted or c in wanted]
    scanner = Scanner(root)
    digest = project_hash(root, scanner.files)
    out = [
        "== project ==",
        f"dir={args.project_dir}",
        f"project_hash={digest}",
        f"files_scanned={len(scanner.swift)}",
    ]
    patterns = {}
    for category in categories:
        found = {s.id: scanner.matches(s) for s in SWEEPS[category]}
        if category == "architecture":
            out += report_architecture(scanner, found, patterns)
        elif category == "version":
            out += report_version(scanner, patterns)
        else:
            out += report_category(category, found, patterns)
    print("\n".join(out))
    if args.write_cache:
        write_cache(root, patterns, digest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
