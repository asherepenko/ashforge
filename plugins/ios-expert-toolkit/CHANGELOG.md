# Changelog

All notable changes to the iOS Expert Toolkit plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html): major for removed or renamed skills and agents, minor for new ones, patch for docs and reference fixes.

## [1.1.5] - 2026-11-21

### Fixed

- Pattern audit: Coordinator, factory, `UIViewController`, `@Reducer`, `ObservableObject`, Testing/XCTest and navigation sweeps no longer match Representable coordinators, `makeUIView`/`makeBody`, look-alike type names or comments.
- `project_hash` is now content-based and identical in both toolkits: sha256 over sorted `<path>\t<sha256>` lines for every scanned source file plus every build file at any depth (empty → `NO_PROJECT_FILES`). Code or build-file edits anywhere, including subfolder projects, refresh the cache. `detect-patterns.py --hash` prints it; `preflight.py` imports the same function.
- Sweeps ignore matches inside comments and string literals (`strip_code`), except sweeps that target string contents.
- The cache gains a `version` entry (TCA, deployment target, Swift), safe now that `Package.resolved` is in the key.

## [1.1.4] - 2026-11-21

### Changed

- `run-sweeps.py` becomes `detect-patterns.py`, matching Android: same command line and output, covering architecture, DI, testing, persistence, concurrency, navigation and version. The NEW/TCA/MVVM/MIXED verdict is kept in the architecture section; usage errors now exit 2.
- `--write-cache` writes `.artifacts/iet/cache/detected-patterns.json` in Android's schema; `preflight.py` prints the project hash and cached patterns; ios-architect and ios-developer read the cache.

## [1.1.3] - 2026-11-21

### Changed

- `run-sweeps.py` moved from `tests/fixtures/` to `skills/ios-conventions/scripts/`, so installed copies of `/ios-conventions` always have the architecture-verdict script; the "when tests/ is included" fallback is gone.

## [1.1.2] - 2026-11-21

### Changed

- Own skills and the swiftui-pro fork follow the /create-skill rules: descriptions at 400 characters or less, a `Done means` section in every skill, and `evals/evals.json` for each.
- swiftui-pro drops the upstream `license` and `metadata` frontmatter; the attribution comment stays.
- Link tests check swiftui-pro instead of skipping it; the unused plugin-root skip is gone.
- `scripts/sync-ios-skills.sh` is now `scripts/sync-ios-skills.py` (Python, same flags and output).
- Skills, agents and references name skills as `/{name}`; `tests/test_skill_references.py` guards it.
- `ios-testing` Codex label shortened to 64 characters or less.

## [1.1.1] - 2026-11-21

### Changed

- Refreshed `swift-concurrency` to AvdLee/Swift-Concurrency-Agent-Skill@3b1580d.
- Re-exported the Xcode skills from Xcode 27.2 (27B52).

## [1.1.0] - 2026-11-12

### Added

- Third-party package facts point to a docs lookup tool when one is installed. `AGENTS.md` Agents section is runtime-neutral.
- Dropped `/doc-lookup` (a dotfiles-only skill) from the router, agents and references; API checks use the Xcode `DocumentationSearch` tool. `AGENTS.md` gains an Agents table, aligned with android-expert-toolkit.
- Skills are referenced as `/{name}` in skills, agents, references and router tables, and as `/{plugin}:{name}` in README and install docs. The rule is in `AGENTS.md`.
- Review mode (`references/review-rules.md`): reviews use fixed rows (C1–C5 from rubric-swiftui, A1–A6 from rubric-ios-architecture, reference checklist items), PASS/FAIL/N/A per row, one verdict rule, and one output template. On a diff, problems in untouched code are listed as `PRE-EXISTING` and do not change the verdict. The output block lives in `assets/review-template.md`, matching the avengers-council verdict block. The ios-expert router and the ios-architect agent point to it; `swiftui-pro` supplies line-level evidence.

## [1.0.2] - 2026-11-04

### Fixed

- The ios-conventions report shows areas as one rendered markdown table, matching android-conventions.

## [1.0.1] - 2026-11-04

### Added

- `references/rubric-swiftui.md` and `references/rubric-ios-architecture.md`: Strong/Weak grading criteria, used as the quality bar by `swiftui-expert` and `ios-architect`.
- `references/persisted-state-review.md`, `offline-sync.md`, `observability.md`, routed from `ios-expert` and loaded by `ios-developer`.
- `ios-conventions` runs `scripts/preflight.py` first: deployment targets, Swift mode, strict concurrency, TCA and package versions, test framework and observation counts.

### Changed

- `ios-expert` router: rows for the new references; the `ios-developer` row now matches the agent's scope.
- `ios-testing-specialist` routes test target and UI test setup to `xcode-build-engineer` and simulator checks to `device-interaction`.

### Fixed

- Plugin file references are relative links, so skills and agents resolve on Codex, Cursor, Pi and Zcode.
- Skills run their scripts by skill-relative path, and scripts locate the plugin root from their own file. No env vars or plugin-cache search.

## [1.0.0] - 2026-11-03

Live check: Claude lists all skills and the `xcode` MCP connects. Routing signed off by the maintainer ("routing OK", 2026-11-03).

### Added

- Codex and Cursor link hooks and the sweep test helper are Python (`hooks/link-codex-agents.py`, `hooks/link-cursor-agents.py`, `tests/fixtures/run-sweeps.py`). `sync-ios-skills.sh` stays shell.
- Plugin scaffold: Claude and Codex manifests, the Xcode MCP (`xcrun mcpbridge`), and maintainer docs.
- Claude manifest lists skill groups: `./skills/`, `./skills/community/`, `./skills/xcode/`. Codex scans `./skills/` recursively.
- 6 own skills: `ios-expert` (topic router), `tca`, `ios-conventions`, `ios-error-handling`, `ios-testing`, and `swiftui-pro` (a fork of the community SwiftUI skill).
- 3 community skills under `skills/community/`, pinned in `ios-skills.lock`: `swift-concurrency`, `swift-testing-expert`, `swiftdata-pro`.
- 9 Xcode 27.2 skills under `skills/xcode/`: `swiftui-specialist`, `swiftui-whats-new-27`, `app-intents-specialist`, `app-intents-whats-new-27`, `xctrace`, `modernize-tests`, `audit-xcode-security-settings`, `app-resizability`, `device-interaction`.
- 5 standalone agents: `ios-architect`, `ios-developer`, `swiftui-expert`, `xcode-build-engineer`, `ios-testing-specialist`. Codex TOML versions are generated into `codex-agents/`, and SessionStart link hooks register the agents with Codex and Cursor.
- `scripts/sync-ios-skills.sh` to refresh the vendored community and Xcode skills against the lock file.
- Xcode MCP server (`xcrun mcpbridge`) in `.mcp.json`.
