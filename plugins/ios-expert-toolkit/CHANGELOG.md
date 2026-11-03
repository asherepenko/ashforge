# Changelog

All notable changes to the iOS Expert Toolkit plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html): major for removed or renamed skills and agents, minor for new ones, patch for docs and reference fixes.

## [1.0.0] - 2026-11-03

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
