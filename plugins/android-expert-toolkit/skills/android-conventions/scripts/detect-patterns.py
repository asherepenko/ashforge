#!/usr/bin/env python3
"""Count Android pattern usage per category and apply the 80/20 matrix.

Usage: detect-patterns.py [--write-cache | --hash] <project-dir> [category ...]
Categories: state, di, testing, architecture, security, performance, accessibility
(default: all). Exit 2 on a usage error or a missing directory.

Sweep patterns are defined in references/pattern-detection.md; keep them identical
(tests/test_detect_patterns_reference.py parses the reference and compares). They are
written as POSIX BRE exactly as in the reference and translated when compiled.

A count is the number of files with at least one matching line (a file counts once).
Reference commands that pipe through `grep -v` keep their exclusion: it is tested
against the same "./path:line:text" string grep -rn prints. Directories pruned from
every sweep: build, generated, .gradle, .git, .idea, .artifacts, node_modules.
Test source sets are not pruned.

Sweeps match code, not prose: in .kt and .java files comments and string-literal contents are
blanked first (strip_code), so `// @HiltViewModel` or "every { }" is not a match. .xml files are
never stripped. A sweep whose purpose is text inside strings is declared `raw=True` and sees the
file as written: only hardcoded_secrets (keys and tokens live in string literals). Reference:
"Audit: what each sweep can miscount" in references/pattern-detection.md.

A decision may name a winner over a loser (`yields`): a file the winner matches is not
counted for the loser (a Hilt file is not a Dagger file; a MockK file is not a Mockito file).

Candidates that compete inside one decision share 100%. A decision's verdict:
match (dominant >= 80%), conflict (50-79%), adopt (< 50%), none (no matches).
Ties go to the candidate declared first. Sweeps outside a decision, and every sweep
in security, performance and accessibility (the reference defines no competing
patterns there), are printed as `count <id> files=N`.

--hash prints only `project_hash=<hex>`: the content key of the scanned files (see project_hash).

Output is `== section ==` blocks of `key=value` lines. With --write-cache the dominant
candidate of each decision is written to .artifacts/aet/cache/detected-patterns.json
under the project directory.
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

Grep = namedtuple("Grep", "id pattern exts exclude raw", defaults=(None, False))
Find = namedtuple("Find", "id names path", defaults=(None,))
Decision = namedtuple("Decision", "key candidates yields", defaults=((),))

MATCH_PERCENT = 80
CONFLICT_PERCENT = 50

KT = ("kt",)
KT_JAVA = ("kt", "java")

SWEEPS = {
    "state": (
        Grep("livedata", "LiveData<", KT_JAVA),
        Grep("stateflow", "StateFlow<", KT),
        Grep("mutable_livedata", "MutableLiveData<", KT_JAVA),
        Grep("flow", "Flow<", KT),
        Grep("rxjava", "Single<\\|Observable<\\|Completable\\|CompositeDisposable\\|subscribeOn\\|observeOn", KT_JAVA),
    ),
    "di": (
        Grep("hilt", "@HiltAndroidApp\\|@HiltViewModel\\|@AndroidEntryPoint\\|@InstallIn", KT_JAVA),
        Grep("dagger", "@Component\\|@Subcomponent", KT_JAVA),
        Grep("koin", "koinViewModel\\|by inject()\\|startKoin\\|koinModule", KT),
        Grep(
            "manual",
            "ViewModelProvider.Factory\\|ViewModelProvider.NewInstanceFactory\\|class Factory.*ViewModel",
            KT,
        ),
    ),
    "testing": (
        Grep("mockito", "@Mock\\b\\|\\bmock(\\|\\bverify(", KT_JAVA),
        Grep("mockk", "mockk<\\|mockk(\\|@MockK\\|every {\\|coEvery {\\|verify {\\|coVerify {", KT),
        Grep(
            "test_doubles",
            "class Test.*Repository\\|class Fake.*Repository\\|class Test.*DataSource",
            KT,
        ),
        Grep("turbine", "\\.test\\s*{", KT),
        Grep("assertthat", "assertThat(", KT_JAVA),
        Grep("junit", "assertEquals\\|assertTrue\\|assertNotNull", KT_JAVA),
    ),
    "architecture": (
        Grep("viewmodel", ": ViewModel()\\|: AndroidViewModel(\\|extends ViewModel\\|extends AndroidViewModel", KT_JAVA),
        Grep("compose", "@Composable", KT),
        Find("xml_layout", ("*.xml",), "*/res/layout/*"),
        Grep("repository", "interface.*Repository\\|class.*Repository", KT_JAVA),
        Grep("usecase", "interface.*UseCase\\|class.*UseCase", KT_JAVA),
        Grep("activity", "class.*Activity\\s*:", KT_JAVA),
        Grep("fragment", "class.*Fragment\\s*:", KT_JAVA),
        Grep("presenter", "Presenter\\|: MvpView\\|attachView", KT_JAVA),
    ),
    "security": (
        Find("network_security_config", ("network_security_config.xml",), "*/res/xml/*"),
        Grep("certificate_pinning", "CertificatePinner", KT_JAVA),
        Grep("encrypted_storage", "EncryptedSharedPreferences\\|EncryptedFile\\|MasterKey", KT),
        Grep("hardcoded_secrets", '"[A-Za-z0-9_-]\\{32,\\}"', KT, "test\\|Test\\|mock\\|Mock", True),
        Find("proguard_rules", ("proguard-rules.pro", "consumer-rules.pro"), None),
        Grep("cleartext_traffic", "cleartextTrafficPermitted\\|usesCleartextTraffic", ("xml",)),
    ),
    "performance": (
        Find("baseline_profile_file", ("baseline-prof.txt",), None),
        Grep("baseline_profile_generator", "BaselineProfileGenerator\\|@BaselineProfileRule", KT),
        Grep("global_scope", "GlobalScope", KT),
        Grep("lazy_items_without_key", "items(", KT, "key\\s*="),
        Grep("state_in_without_while_subscribed", "stateIn(", KT, "WhileSubscribed"),
        Grep("launch_without_dispatcher", "withContext\\|launch\\|async", KT, "Dispatchers\\."),
    ),
    "accessibility": (
        Grep("icon_without_content_description", "Icon(", KT, "contentDescription"),
        Grep("image_without_content_description", "Image(", KT, "contentDescription"),
        Grep("semantics", "Modifier.semantics\\|\\.semantics {", KT),
        Grep("merge_descendants", "mergeDescendants", KT),
        Grep("clickable", "\\.clickable", KT),
        Grep("min_touch_target", "\\.size.*48\\.dp\\|minimumInteractiveComponentSize", KT),
    ),
}

DECISIONS = {
    "state": (
        Decision(
            "state_management",
            {"livedata": ("livedata", "mutable_livedata"), "stateflow": ("stateflow",), "rxjava": ("rxjava",)},
        ),
    ),
    "di": (
        Decision(
            "di_framework",
            {"hilt": ("hilt",), "dagger": ("dagger",), "koin": ("koin",), "manual": ("manual",)},
            (("hilt", "dagger"),),
        ),
    ),
    "testing": (
        Decision(
            "testing_mocks",
            {"mockito": ("mockito",), "mockk": ("mockk",), "test_doubles": ("test_doubles",)},
            (("mockk", "mockito"),),
        ),
        Decision("testing_assertions", {"assertthat": ("assertthat",), "junit": ("junit",)}),
    ),
    "architecture": (
        Decision("ui_framework", {"compose": ("compose",), "xml_layout": ("xml_layout",)}),
        Decision("presentation", {"viewmodel": ("viewmodel",), "presenter": ("presenter",)}),
    ),
    "security": (),
    "performance": (),
    "accessibility": (),
}

PRUNE_DIRS = {"build", "generated", ".gradle", ".git", ".idea", ".artifacts", "node_modules"}
CACHE_PATH = Path(".artifacts/aet/cache/detected-patterns.json")
EVIDENCE_LIMIT = 3
PROG = "detect-patterns.py"


def compile_bre(pattern: str) -> "re.Pattern[str]":
    """Translate the reference's grep BRE (GNU: \\| alternation, \\{n,\\}, \\s) to Python."""
    out, i, n = [], 0, len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == "\\" and i + 1 < n:
            nxt = pattern[i + 1]
            out.append(nxt if nxt in "|{}()" else "\\" + nxt)
            i += 2
        elif ch == "[":
            j = i + 1
            if j < n and pattern[j] == "^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            j = pattern.find("]", j)
            j = n - 1 if j < 0 else j
            out.append(pattern[i : j + 1])
            i = j + 1
        elif ch in "(){}+?|":
            out.append("\\" + ch)
            i += 1
        else:
            out.append(ch)
            i += 1
    return re.compile("".join(out))


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


def _skip_string(text: str, i: int, out: list) -> int:
    """Blank the string literal opening at text[i] (a quote); return the index after it."""
    n = len(text)
    if text.startswith('"""', i):
        out.append('"""')
        i += 3
        while i < n and not text.startswith('"""', i):
            if text[i] == "\n":
                out.append("\n")
            i += 1
        out.append('"""' if i < n else "")
        return min(n, i + 3)
    out.append('"')
    i += 1
    while i < n and text[i] not in '"\n':
        if text[i] == "\\" and i + 1 < n and text[i + 1] != "\n":
            i += 2
        elif text.startswith("${", i):
            i = _skip_template(text, i + 2, out)
        else:
            i += 1
    if i < n and text[i] == '"':
        i += 1
    out.append('"')
    return i


def _skip_template(text: str, i: int, out: list) -> int:
    """Skip a `${ ... }` template expression body (braces and nested strings); return the index after `}`."""
    n, depth = len(text), 1
    while i < n and depth:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == '"':
            sink: list = []
            i = _skip_string(text, i, sink)
            out.extend("\n" * "".join(sink).count("\n"))
            continue
        elif ch == "\n":
            out.append("\n")
        i += 1
    return i


def strip_code(text: str) -> str:
    """Kotlin or Java source with comments removed and string-literal contents emptied; newlines kept.

    Handles `//` and `/* */` comments (block comments nest, as in Kotlin; harmless for Java),
    `"..."` strings with backslash escapes, `\"\"\"...\"\"\"` raw strings and text blocks (multi-line, no
    escapes), and char literals. A Kotlin string template is blanked whole: the `${...}` expression
    inside a string is not code to the sweeps. Line numbers stay valid. An unterminated `"` string
    ends at the line break; an unterminated comment or raw string runs to the end of the file.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        two = text[i : i + 2]
        ch = text[i]
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
        elif ch == '"':
            i = _skip_string(text, i, out)
        elif ch == "'":
            j = i + 1
            if j < n and text[j] == "\\":
                j += 2
                while j < n and text[j] not in "'\n":
                    j += 1
            elif j < n and text[j] != "\n":
                j += 1
            if j < n and text[j] == "'":
                out.append("''")
                i = j + 1
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


SCANNED_EXTS = (".kt", ".java", ".xml")
BUILD_FILES = {"settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts", "gradle.properties"}
BUILD_SUFFIXES = (".versions.toml",)
NO_PROJECT_FILES = "NO_PROJECT_FILES"


def is_hashed(rel: str) -> bool:
    base = rel.rsplit("/", 1)[-1]
    return rel.endswith(SCANNED_EXTS) or base in BUILD_FILES or base.endswith(BUILD_SUFFIXES)


def project_hash(root: Path) -> str:
    """Content key: sha256 of "<relpath>\\t<sha256 of bytes>\\n" lines sorted by relpath, over every
    scanned source/layout file and every build file at any depth outside the pruned directories."""
    lines = []
    for rel in list_files(root):
        if not is_hashed(rel):
            continue
        try:
            data = (root / rel).read_bytes()
        except OSError:
            continue
        lines.append(f"{rel}\t{hashlib.sha256(data).hexdigest()}\n")
    if not lines:
        return NO_PROJECT_FILES
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()


class Scanner:
    def __init__(self, root: Path):
        self.root = root
        self.files = list_files(root)
        self._lines = {}
        self._raw = {}

    def lines(self, rel: str, raw: bool = False) -> list:
        """Lines a sweep matches against: .kt and .java comments and strings blanked unless `raw`."""
        key = (rel, raw or not rel.endswith((".kt", ".java")))
        if key not in self._lines:
            if rel not in self._raw:
                try:
                    self._raw[rel] = (self.root / rel).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    self._raw[rel] = ""
            text = self._raw[rel]
            self._lines[key] = (text if key[1] else strip_code(text)).splitlines()
        return self._lines[key]

    def source_count(self) -> int:
        return sum(1 for f in self.files if f.endswith((".kt", ".java")))

    def matches(self, sweep) -> list:
        if isinstance(sweep, Find):
            return [f for f in self.files if self._find_match(sweep, f)]
        include = compile_bre(sweep.pattern)
        exclude = compile_bre(sweep.exclude) if sweep.exclude else None
        exts = tuple("." + e for e in sweep.exts)
        return [f for f in self.files if f.endswith(exts) and self._grep_match(include, exclude, f, sweep.raw)]

    @staticmethod
    def _find_match(sweep, rel: str) -> bool:
        base = rel.rsplit("/", 1)[-1]
        if not any(fnmatch.fnmatchcase(base, n) for n in sweep.names):
            return False
        return sweep.path is None or fnmatch.fnmatchcase("./" + rel, sweep.path)

    def _grep_match(self, include, exclude, rel: str, raw: bool) -> bool:
        for number, line in enumerate(self.lines(rel, raw), 1):
            if include.search(line) and not (exclude and exclude.search(f"./{rel}:{number}:{line}")):
                return True
        return False


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
    for winner, loser in decision.yields:
        files[loser] = [f for f in files[loser] if f not in set(files[winner])]
    total = sum(len(v) for v in files.values())
    dominant = max(files, key=lambda k: len(files[k])) if total else None
    count = len(files[dominant]) if dominant else 0
    return {"files": files, "total": total, "dominant": dominant, "count": count}


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


def write_cache(root: Path, patterns: dict) -> None:
    path = root / CACHE_PATH
    digest = project_hash(root)
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
    parser = argparse.ArgumentParser(prog=PROG, description="Count Android patterns per category.")
    parser.add_argument("project_dir")
    parser.add_argument("categories", nargs="*", metavar="category", help="|".join(SWEEPS) + "|all")
    parser.add_argument("--hash", action="store_true", help="print only project_hash=<hex> and exit")
    parser.add_argument("--write-cache", action="store_true", help="write .artifacts/aet/cache/detected-patterns.json")
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
    out = [
        "== project ==",
        f"dir={args.project_dir}",
        f"project_hash={project_hash(root)}",
        f"files_scanned={scanner.source_count()}",
    ]
    patterns = {}
    for category in categories:
        found = {s.id: scanner.matches(s) for s in SWEEPS[category]}
        out += report_category(category, found, patterns)
    print("\n".join(out))
    if args.write_cache:
        write_cache(root, patterns)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
