# Android Expert Toolkit

Android knowledge for Claude Code and Codex: a topic router, focused skills, the official Google Android skills, and five standalone agents for modern Kotlin/Compose/Gradle work.

## What it ships

- **`/android-expert-toolkit:android-expert`** — a router skill: topic → the reference, skill, or agent to load.
- **`/android-expert-toolkit:android-testing`** — adversarial unit testing: break vectors from the contract, one distinct angle per test, fakes first.
- **`/android-expert-toolkit:android-error-handling`** — closed typed errors, `CancellationException`-safe catches, string-resource errors in UI state.
- **`/android-expert-toolkit:android-conventions`** — read-only 80/20 pattern detection (DI, state, testing, architecture, security, performance, accessibility). Caches results at `.artifacts/aet/cache/detected-patterns.json`.
- **Official Android skills** vendored from [android/skills](https://github.com/android/skills) (Apache-2.0): `/android-expert-toolkit:navigation-3`, `/android-expert-toolkit:navigation-event`, `/android-expert-toolkit:edge-to-edge`, `/android-expert-toolkit:adaptive`, `/android-expert-toolkit:jetpack-compose-performance`, `/android-expert-toolkit:migrate-xml-views-to-jetpack-compose`, `/android-expert-toolkit:agp-9-upgrade`, `/android-expert-toolkit:r8-analyzer`, `/android-expert-toolkit:anr-audit-and-fix`, `/android-expert-toolkit:android-profiler`, `/android-expert-toolkit:testing-setup`, `/android-expert-toolkit:android-intent-security`, `/android-expert-toolkit:android-permissions-security`, `/android-expert-toolkit:glance-appwidget-updates-and-memory`, `/android-expert-toolkit:glance-canonical-layouts`, `/android-expert-toolkit:ios-to-android`. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- **Kotlin docs MCP**: `kotlinlang` (`https://mcp.kotlinlang.org/mcp`, read-only kotlinlang.org search), declared in `.mcp.json`.
- **Agents** that work from a plain brief (goal, acceptance criteria, files):

| Agent | Scope |
|-------|-------|
| `android-architect` | module/layer structure, data flow, ADRs, architecture review |
| `android-developer` | ViewModels, repositories, Room/DataStore, networking, WorkManager, DI |
| `compose-expert` | screens, components, previews per state, accessibility, adaptive UI |
| `gradle-build-engineer` | modules, convention plugins (AGP 9), version catalog, build performance |
| `android-testing-specialist` | tests and test review using the `/android-expert-toolkit:android-testing` method |

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

Codex loads the skills from the plugin. Its custom agents are TOML files: the generated `codex-agents/*.toml` mirror `agents/*.md`. Codex plugins cannot declare agents, so a Codex `SessionStart` hook (`hooks/link-codex-agents.py`), keeps `~/.codex/agents/android-expert-toolkit` symlinked to the installed version's `codex-agents/`. It repairs a missing, broken or stale link, never replaces a real directory, and does nothing when the link is valid. Trust it once with `/hooks` in Codex. A fresh install or update shows the agents from the next Codex session.

### Cursor

Cursor has no plugin route for these agents, but it loads user subagents from `~/.cursor/agents/*.md` in the same Markdown format ([Cursor subagents](https://cursor.com/docs/subagents)). With the plugin installed in Claude Code, a Claude `SessionStart` hook (`hooks/link-cursor-agents.py`) keeps one symlink per agent in `~/.cursor/agents/` pointing at the installed version. It runs only when `~/.cursor` exists, repairs missing, broken or stale links, removes links to agents a newer version dropped, and never replaces a real file. After an install or update, open one Claude Code session; Cursor shows the agents from its next session.

## Usage

Ask an Android question or name the task; the `/android-expert-toolkit:android-expert` router picks what to load. Examples:

- "How should this ViewModel expose errors?" → `presentation.md` + `/android-expert-toolkit:android-error-handling`
- "Write tests for `LoginValidator`" → `/android-expert-toolkit:android-testing`
- "Upgrade to AGP 9" → `/android-expert-toolkit:agp-9-upgrade`
- "Make the home screen work on tablets" → `/android-expert-toolkit:adaptive`
- "Which DI does this project use?" → `android-conventions di`

Delegate implementation to an agent with a brief:

```
Agent: android-developer
Goal: add offline refresh to ItemsRepository
Acceptance: refresh() returns a typed error on no network; cached items stay visible
Files: core/data/src/main/.../ItemsRepository.kt, OfflineFirstItemsRepository.kt
Verify: ./gradlew :core:data:testDebugUnitTest
```

## Maintenance

- Update the official skills: `scripts/sync-android-skills.sh main` (pins the new upstream commit in `android-skills.lock`). Never edit vendored skill files by hand.
- After editing `agents/*.md`: `python3 scripts/codex-agents-gen.py --write`.
- Tests: `pytest tests -q`.

## License

MIT (see [LICENSE](LICENSE)). Vendored official skills are Apache-2.0 (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).
