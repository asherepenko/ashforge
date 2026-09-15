# Changelog

All notable changes to the Android Expert Toolkit plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html), scoped as described in `CLAUDE.md`: major for breaking skill or agent contract changes, minor for new skills, agents, or pipeline types, patch for docs, references, hook fixes, and agent prompt tuning.

## [3.3.1] - 2026-09-16

### Added

- `references/persisted-state-review.md`. Five checks for a change that touches state already stored on installed devices: a per-key upgrade-path table read from the old writer on the merge-base, ambiguous legacy values, composite string keys, locking changes that add callers, and test source sets that CI never invokes. Includes the evidence-rung requirement and a list of smaller repeats.

### Changed

- `skills/android-expert/SKILL.md` points at the new reference from the reference block and from the new-feature checklist.
- `agents/android-architect.md` reads the new reference on `code-review` and `migration` pipelines when the change touches persisted state.

## [3.3.0] - 2026-09-15

### Added

- Runtime-generic capability profiles (RUNTIME / SPAWN / TRANSPORT) emitted by the pipeline preflight, interpreted per `references/runtime-adapters.md`.
- Sequential single-orchestrator fallback for runtimes that report `SPAWN=none`, documented in `references/runtime-fallback.md`.

### Fixed

- Claude hook manifest commands no-op instead of failing when Codex auto-discovers `hooks/hooks.json` from the plugin cache.

## [3.2.0]

### Changed

- Audit hardening: plugin-root paths throughout, handoff contracts sourced from `hooks/validate-handoff.py` instead of hand-maintained lists, hook fixes.

### Added

- Skill-usage directive injected on session start.

## [3.1.2]

### Added

- Codex sandbox handling, `.gitignore`, end-to-end example pipeline output, and `update_plan` progress reporting.

## [3.1.1]

### Changed

- Codex documentation parity polish.

## [3.1.0]

### Added

- Codex `multi_agent` capability detection with fallback.

## [3.0.1]

### Added

- Explicit Codex hooks field in `.codex-plugin/plugin.json` and packaging tests.

## [3.0.0]

### Changed

- Dual-runtime support for Claude Code and Codex. Slash commands migrated to skills. Slash-command form is no longer supported.
