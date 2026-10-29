# Android Expert Toolkit

Android knowledge for Claude Code and Codex: a topic router, focused skills, the official Google Android skills, and five standalone agents for modern Kotlin/Compose/Gradle work.

## What it ships

- **`android-expert`** — a router skill: topic → the reference, skill, or agent to load.
- **`android-testing`** — adversarial unit testing: break vectors from the contract, one distinct angle per test, fakes first.
- **`android-error-handling`** — closed typed errors, `CancellationException`-safe catches, string-resource errors in UI state.
- **`aet-check`** — read-only 80/20 pattern detection (DI, state, testing, architecture, security, performance, accessibility). Caches results at `.artifacts/aet/cache/detected-patterns.json`.
- **Official Android skills** vendored from [android/skills](https://github.com/android/skills) (Apache-2.0): `navigation-3`, `navigation-event`, `edge-to-edge`, `adaptive`, `jetpack-compose-performance`, `migrate-xml-views-to-jetpack-compose`, `agp-9-upgrade`, `r8-analyzer`, `anr-audit-and-fix`, `android-profiler`, `testing-setup`, `android-intent-security`, `android-permissions-security`. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- **Agents** that work from a plain brief (goal, acceptance criteria, files):

| Agent | Scope |
|-------|-------|
| `android-architect` | module/layer structure, data flow, ADRs, architecture review |
| `android-developer` | ViewModels, repositories, Room/DataStore, networking, WorkManager, DI |
| `compose-expert` | screens, components, previews per state, accessibility, adaptive UI |
| `gradle-build-engineer` | modules, convention plugins (AGP 9), version catalog, build performance |
| `android-testing-specialist` | tests and test review using the `android-testing` method |

- **References** (`references/`, each ≤ ~300 lines) on architecture, presentation, data layer, offline sync, DI, Compose UI, accessibility, navigation (Nav 2), Gradle, security, performance, observability, testing mechanics, and Kotlin–Java interop.

## Installation

### Claude Code

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/reload-plugins
```

### Codex (CLI / App)

```bash
codex plugin marketplace add asherepenko/ashforge
```

Enable it in the Codex UI or `~/.codex/config.toml`:

```toml
[plugins."android-expert-toolkit@ashforge"]
enabled = true
```

Codex loads the skills from the plugin. Its custom agents are TOML files: the generated `codex-agents/*.toml` mirror `agents/*.md`. To use them, copy or symlink them into `~/.codex/agents/` (or a project's `.codex/agents/`).

## Usage

Ask an Android question or name the task; the `android-expert` router picks what to load. Examples:

- "How should this ViewModel expose errors?" → `presentation.md` + `android-error-handling`
- "Write tests for `LoginValidator`" → `android-testing`
- "Upgrade to AGP 9" → `agp-9-upgrade`
- "Make the home screen work on tablets" → `adaptive`
- "Which DI does this project use?" → `aet-check di`

Delegate implementation to an agent with a brief:

```
Agent: android-developer
Goal: add offline refresh to ItemsRepository
Acceptance: refresh() returns a typed error on no network; cached items stay visible
Files: core/data/src/main/.../ItemsRepository.kt, OfflineFirstItemsRepository.kt
Verify: ./gradlew :core:data:testDebugUnitTest
```

## Maintenance

- Update the official skills: `scripts/sync-official-skills.sh main` (pins the new upstream commit in `official-skills.lock`). Never edit vendored skill files by hand.
- After editing `agents/*.md`: `python3 scripts/codex-agents-gen.py --write`.
- Tests: `pytest tests -q`.

## License

MIT (see [LICENSE](LICENSE)). Vendored official skills are Apache-2.0 (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).
