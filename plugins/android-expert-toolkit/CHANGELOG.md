# Changelog

All notable changes to the Android Expert Toolkit plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html), scoped as described in `CLAUDE.md`: major for breaking skill or agent contract changes, minor for new skills, agents, or pipeline types, patch for docs, references, hook fixes, and agent prompt tuning.

## [4.0.0] - 2026-10-30

Breaking: the multi-agent pipeline is gone. The plugin is now a lean Android knowledge plugin — a router skill, focused skills, vendored official Android skills, and standalone agents.

### Renamed

- Skill `/aet-check` is now `/android-conventions`. Its cache path `.artifacts/aet/cache/detected-patterns.json` is unchanged.

### Removed

- Skills `/aet-pipeline` and `/aet-status`, with their preflight scripts.
- All hooks (`session-start.py`, `track-progress.*`, `validate-handoff.py`, `validate-dependencies.py`) and both hook manifests; the Codex manifest no longer declares `hooks`.
- Handoff templates, the example pipeline run, the settings template (`android-expert-toolkit.local.md`), and pipeline-only references (`handoff-protocol`, `pipeline-error-scenarios`, `conflict-resolution`, `runtime-adapters`, `runtime-fallback`, `agent-routing`).
- `scripts/review-grade.sh` and `scripts/change-size.sh` (only the pipeline's code-review report used them).
- The large references (`architecture-patterns`, `compose-patterns`, `developer-patterns`, `testing-patterns-detail`, `gradle-patterns`, `data-layer-patterns`, `ui-patterns`, `architect-code-examples`, `performance-targets`, `pragmatic-examples`), replaced by topic files below.

### Added

- Official Android skills vendored from android/skills at a pinned commit by `scripts/sync-android-skills.sh` (`android-skills.lock`, Apache-2.0 attribution in `THIRD_PARTY_NOTICES.md`): navigation-3, navigation-event, edge-to-edge, adaptive, jetpack-compose-performance, migrate-xml-views-to-jetpack-compose, agp-9-upgrade, r8-analyzer, anr-audit-and-fix, android-profiler, testing-setup, android-intent-security, android-permissions-security. `android-cli` is deliberately excluded.
- `android-testing` skill: adversarial break-vector method, the redundancy rule, unit = behavior, contract-first vectors, fakes first, SavedStateHandle testing.
- `android-error-handling` skill: closed typed errors at the catching layer, `CancellationException` rethrow, resource-based UI errors.
- Codex agent definitions in `codex-agents/*.toml`, generated from `agents/*.md` by `scripts/codex-agents-gen.py` and checked by tests.
- Topic references, each ≤ ~300 lines: architecture, presentation, data-layer, offline-sync, dependency-injection, compose-ui, accessibility, navigation, gradle-convention-plugins, gradle-build-config, security, performance, observability, testing-patterns, kotlin-java-interop, pragmatics.

### Changed

- `android-expert` is a short router: topic → reference, skill, or agent.
- Compose and presentation guidance checked against current Android docs: `compose-ui.md` gains state placement (hoisting), side-effect keys and `rememberUpdatedState`, state-based text fields (`TextFieldState`; value-based fields are deprecated), custom modifiers (`Modifier.Node`, never `composed {}`), an animation-API table, and design-system component rules; `presentation.md` models ViewModel-originated messages and navigation as state instead of event channels, holds text input as `TextFieldState` saved through `SavedStateHandle.saveable`, and requires `UiText` args as a `List`; `android-testing` adds format/path strings, mutable returned collections, and one redundancy case.
- The five agents work from a plain brief (goal, acceptance criteria, files, verify command) with no handoff files, and point at skills/references instead of embedding patterns.
- `aet-check` keeps its cache at `.artifacts/aet/cache/detected-patterns.json`.

### Fixed

- Navigation 2 code was labelled "Navigation 3"; Nav 2 is now labelled as such and Nav 3 defers to the `navigation-3` skill.
- Convention plugins are AGP 9-correct: no `org.jetbrains.kotlin.android`, `kotlin { compilerOptions }` instead of `kotlinOptions`, non-parameterized `CommonExtension`. The version catalog no longer references undefined `agp`/`ksp` versions and uses placeholders instead of hard-pinned versions.
- Catch-all `catch (e: Exception)` blocks that swallowed `CancellationException` now rethrow it or catch specific exceptions.
- UI state no longer carries `it.message ?: "Unknown error"` or a `retry: () -> Unit` lambda; errors are string-resource references and retry is an action.
- Adaptive guidance and the Compose rubric use `NavigationSuiteScaffold` and Nav 3 scene strategies instead of hand-rolled WindowSizeClass rails.
- R8 guidance drops package-wide keep rules and defers to `r8-analyzer`.
- Screenshot testing is no longer Roborazzi-only; tool choice defers to `testing-setup`.
- "No mocking" is now "fakes first; mocks for final framework classes".
- Compose performance no longer targets recomposition counts or "<8ms"; it defers to `jetpack-compose-performance`.
- `EncryptedFile`/`security-crypto` is no longer recommended: the library is deprecated (all APIs deprecated in 1.1.0, no further releases, per developer.android.com Cryptography guide); guidance uses Android Keystore AES-GCM.
- Performance targets use Play vitals bad-behavior thresholds instead of invented numbers.

## [3.4.0] - 2026-10-21

### Added

- Code-review reports carry a `**Quality:** X — N critical, N high, N medium, N low` line. The letter comes from `scripts/review-grade.sh --ladder severity`, which the android-architect runs after filling the Severity Summary. Info findings never count.
- `hooks/validate-handoff.py` rejects a code-review report that lacks a `**Quality:** [A-F] —` line.
- `scripts/review-grade.sh` and `scripts/change-size.sh`, vendored byte-identical from the dotfiles source. `tests/test_review_grade.py` checks the grade ladder and fails when either copy drifts from the avengers-council plugin copy or from `~/.agents/scripts/`.

## [3.3.3] - 2026-10-11

### Fixed

- Feature builds wait for Gradle setup when target modules or required build files do not exist. Gradle and implementation run in parallel only when their prerequisites are independent.
- Concurrent progress hooks lock the complete state update and replace JSON atomically, preserving reports from parallel stages. Platforms without the locking backend use the orchestrator's inline state updates.
- Runtime detection recognizes current Codex `agents.enabled` settings and legacy `features.multi_agent` settings. The running session's tools determine whether subagent dispatch is available.
- Dispatch instructions handle Claude teammate idle notifications, retain agent IDs for recovery, and use bounded worker batches with continuation when no close tool is available.

### Changed

- Runtime adapters, agent handoffs, routing examples, and setup documentation describe the same prerequisite and completion rules.

## [3.3.2] - 2026-09-16

### Fixed

- `QUICK_START.md` Scenario 4 used `aet-check ui`, which is not a valid detection category — the Compose-vs-XML sweep lives under `architecture`. Corrected to `aet-check architecture`.
- `skills/android-expert/SKILL.md` referenced companion skills in the retired slash-command form (`/aet-pipeline`, `/aet-status`, `/aet-check`); normalized to plain skill names.

### Added

- README "When to Use" section: a routing table mapping intents to the four skills, plus an explicit out-of-scope note (backend Kotlin, plain Gradle JVM), matching the avengers-council README structure.

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
