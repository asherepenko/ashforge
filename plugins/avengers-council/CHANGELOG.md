# Changelog

All notable changes to the Avengers Council plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html): major for breaking skill or agent contract changes, minor for new skills, agents, or review modes, patch for docs, references, hook fixes, and agent prompt tuning.

## [3.3.1] - 2026-09-16

### Fixed

- README and AGENTS.md described `agents/` as holding "8 core members + captain-america (ref) + optional members" — the directory holds only the 8 core member personas. Captain America's orchestrator persona lives in `references/captain-america-orchestrator.md` and optional members in `references/member-registry.md`; both docs now say so.

## [3.3.0] - 2026-09-15

### Added

- Runtime capability profiles (RUNTIME / SPAWN / TRANSPORT / NOTES) emitted by the skill preflights, replacing the hardcoded Claude and Codex split with the capability axes SPAWN, TRANSPORT, PROGRESS, ASK, ROOT_ENV, HOOKS, and SANDBOX.
- Cost-controlled Quick Mode. The orchestrator downgrades autonomously when hub-only transport, proportionality, and user unavailability all hold, and announces the downgrade in session and in the verdict.
- Run Mode field in the verdict template.
- `tests/test_runtime_packaging.py` pinning the runtime contracts.

### Changed

- `references/codex-tools.md` became `references/runtime-adapters.md`, `references/codex-fallback.md` became `references/runtime-fallback.md`, and `codex-runtime-notes.md` was absorbed into the adapters reference.
- The orchestration protocol branches on stay-alive transport against hub transport.
- Skills resolve the plugin root through `ZCODE_PLUGIN_ROOT` with a plugin-cache fallback.
- Plan auto-detection scans the `<agent>/plans/` family.
- Persona embedding rewrites `${CLAUDE_PLUGIN_ROOT}` for runtimes that embed the prompt.

### Fixed

- The plan hook is guarded on the resolved plugin root.

## [3.2.0]

### Changed

- Audit hardening: least-privilege agent tool lists, contracts sourced from a single place, and deduplicated reference content.

## [3.1.5]

### Changed

- Dropped the `-reference` suffix from reference filenames. Reference content edits throughout.

## [3.1.3]

### Added

- STRIDE, mobile, and LLM lenses in the security reference.

## [3.1.2]

### Added

- Codex sandbox handling, `.gitignore`, end-to-end examples, and `update_plan` progress reporting.

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

- Dual-runtime support for Claude Code and Codex. Slash commands migrated to skills.

## [2.6.0]

### Added

- ADR and glossary consistency criteria across agents. An ADR contradiction is a red line. Verdict template gains a Domain Alignment section.
- Symmetric domain-model guard on iron-man and ADR criteria on scarlet-witch.
- Explicit silent-skip policy when `CONTEXT.md` and ADRs are absent.
