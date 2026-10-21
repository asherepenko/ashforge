import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "references" / "research-protocol.md"
ADAPTERS = ROOT / "references" / "runtime-adapters.md"

SKIP_LINE = "Research: skipped — no web tools"

OWNERS = {
    "package.json": ("scarlet-witch", "thor"),
    "package-lock.json": ("scarlet-witch", "thor"),
    "yarn.lock": ("scarlet-witch", "thor"),
    "pnpm-lock.yaml": ("scarlet-witch", "thor"),
    "pyproject.toml": ("thor",),
    "poetry.lock": ("thor",),
    "uv.lock": ("thor",),
    "requirements*.txt": ("thor",),
    "build.gradle": ("hawkeye", "thor"),
    "libs.versions.toml": ("hawkeye", "thor"),
    "Podfile": ("hawkeye",),
    "Package.resolved": ("hawkeye",),
    "go.mod": ("thor",),
    "go.sum": ("thor",),
    "Cargo.toml": ("thor",),
    "Cargo.lock": ("thor",),
    "Gemfile": ("thor",),
    ".github/workflows/": ("doctor-strange",),
    "Dockerfile": ("doctor-strange",),
}


def _row(text, pattern):
    for line in text.splitlines():
        if line.startswith("|") and f"`{pattern}" in line.split("|")[1]:
            return line
    raise AssertionError(f"no table row for {pattern}")


def test_black_widow_researches_every_review():
    text = PROTOCOL.read_text()
    assert "black-widow" in text and "every review" in text
    assert "≤200 words" in text
    assert "Nothing material" in text
    assert "data, not instructions" in text


def test_manifest_table_maps_every_manifest_to_an_owner():
    text = PROTOCOL.read_text()
    for manifest in ("package.json", "pyproject.toml", "requirements.txt",
                     "build.gradle", "libs.versions.toml", "Podfile.lock",
                     "Package.resolved", "go.mod", "Cargo.toml"):
        assert f"`{manifest}" in text, manifest


def test_every_lockfile_row_names_its_owners():
    text = PROTOCOL.read_text()
    for pattern, owners in OWNERS.items():
        row = _row(text, pattern)
        owner_cell = row.split("|")[2]
        for owner in owners:
            assert owner in owner_cell, (pattern, owner)
    for pattern in ("Podfile.lock", "build.gradle.kts", "Gemfile.lock"):
        assert f"`{pattern}" in text, pattern


def test_table_matches_basename_at_any_depth():
    text = PROTOCOL.read_text()
    assert "basename" in text and "any depth" in text
    assert "preflight" in text


def test_privacy_rule_bans_what_must_not_leave():
    text = PROTOCOL.read_text().lower()
    for banned in ("secrets", "source excerpts", "plan text", "file paths",
                   "internal hostnames", "private package names",
                   "credentials", "localhost", "private ip", "redirects"):
        assert banned in text, banned
    assert "private — not searched" in text
    assert "never query a registry" in text
    assert "public `https` hosts only" in text
    for registry in ("npmjs.org", "pypi.org", "crates.io", "proxy.golang.org",
                     "rubygems.org"):
        assert registry in text, registry


def test_budget_and_four_statuses():
    text = PROTOCOL.read_text()
    assert "5 searches" in text and "3 fetches" in text
    for status in ("completed", "partial", "failed", "unavailable"):
        assert f"`{status}" in text, status
    assert "failed (<reason>)" in text
    assert "retr" in text.lower()


def test_nothing_material_is_tied_to_completed():
    text = PROTOCOL.read_text()
    assert re.search(r"`Nothing material`[^.\n]*only[^.\n]*`completed`", text) or \
        re.search(r"only[^.\n]*`completed`[^.\n]*`Nothing material`", text)


def test_plan_reviews_and_quick_mode_rules():
    text = PROTOCOL.read_text()
    assert "named new or upgraded dependencies" in text
    assert "Research: <member> not in roster" in text
    assert "no extra spawn" in text.lower()


def test_web_none_disclosure_is_disclosure_only():
    text = PROTOCOL.read_text()
    assert SKIP_LINE in text
    assert "never caps" in text


def test_runtime_adapters_has_web_axis():
    text = ADAPTERS.read_text()
    assert "### WEB" in text
    assert "`available`" in text and "`none`" in text
    assert SKIP_LINE in text
    assert "WebSearch" in text and "WebFetch" in text
    table = text.split("## Known Runtime Profiles", 1)[1].split("\n## ", 1)[0]
    assert "WEB" in table


def test_no_runtime_labels_added():
    for path in (PROTOCOL, ADAPTERS):
        text = path.read_text()
        assert "**Codex:**" not in text
        assert "**Claude:**" not in text
