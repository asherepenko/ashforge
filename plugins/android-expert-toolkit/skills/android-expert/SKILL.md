---
name: android-expert
description: "Use for Android app development questions, implementation guidance, and code review — Jetpack Compose, ViewModel/StateFlow, Hilt/Koin, Room, DataStore, coroutines/Flow, Navigation 2/3, WorkManager, Gradle convention plugins and AGP 9, R8, security, performance, testing. Routes to the right reference or skill (including the vendored official Android skills) and to the five Android agents. Trigger on 'how should I build X on Android', 'review this Android code', 'which pattern for Y', 'Compose screen', 'Android architecture'. Not for backend/server Kotlin or non-Android Gradle builds."
argument-hint: "[question or topic] — e.g. 'Room offline-first', 'ViewModel error state', 'AGP 9 convention plugin'"
---

# Android Expert

A router. Find the topic, load only what it names, then answer or act. Before recommending a pattern, check what the project already uses (`android-conventions`) and follow `${CLAUDE_PLUGIN_ROOT}/references/pragmatics.md`: user instructions, then codebase consistency, then constraints, then best practice. Verify API claims you aren't sure of with `android docs search "<query>"` rather than memory.

## Topic → load

References live in `${CLAUDE_PLUGIN_ROOT}/references/`. Skills are loaded by name.

| Topic | Load |
|-------|------|
| Which patterns does this codebase use (DI, state, testing, a11y) | `android-conventions` skill |
| Layers, modules, dependency rules, coroutines | `architecture.md` |
| ViewModel, UI state, actions, events, SavedStateHandle, Route/Screen | `presentation.md` |
| Error types, try/catch, CancellationException, error messages in UI | `android-error-handling` skill |
| Repositories, Room, DataStore, Retrofit/Ktor, WorkManager, Paging | `data-layer.md` |
| Sync queues, conflict resolution | `offline-sync.md` |
| Changing data already stored on devices | `persisted-state-review.md` |
| Hilt, Koin, Dagger, manual DI | `dependency-injection.md` |
| Compose components, state placement, side effects, text fields, custom modifiers, animations, previews, lists, theme, interop | `compose-ui.md` |
| Accessibility | `accessibility.md` |
| Window sizes, nav bar vs rail, list-detail, foldables, keyboard/mouse | `adaptive` skill |
| Edge-to-edge, insets, system bars | `edge-to-edge` skill |
| Compose recomposition, stability, jank | `jetpack-compose-performance` skill |
| XML layout → Compose | `migrate-xml-views-to-jetpack-compose` skill |
| Navigation 2 (`NavHost`), deep links, App Links | `navigation.md` |
| Navigation 3 (`NavDisplay`), Nav 2 → 3 migration, scenes | `navigation-3` skill |
| Predictive back, back-gesture handling | `navigation-event` skill |
| Convention plugins, module build files | `gradle-convention-plugins.md` |
| Version catalog, gradle.properties, build cache, signing, CI | `gradle-build-config.md` |
| Upgrading to AGP 9 | `agp-9-upgrade` skill |
| R8 keep rules, shrinking, app size | `r8-analyzer` skill |
| Network trust, secrets, token storage, release hardening | `security.md` |
| Exported components, intents, PendingIntent | `android-intent-security` skill |
| Runtime permissions, component protection | `android-permissions-security` skill |
| Startup, Baseline Profiles, Macrobenchmark, vitals targets | `performance.md` |
| Traces, heap dumps, profiling | `android-profiler` skill |
| ANRs | `anr-audit-and-fix` skill |
| Logging, crash reporting, analytics, custom traces | `observability.md` |
| Writing or reviewing unit tests, edge cases | `android-testing` skill |
| Test code mechanics (fakes, Turbine, Compose tests, Room tests) | `testing-patterns.md` |
| Test infrastructure, screenshot tests, E2E setup | `testing-setup` skill |
| Java ↔ Kotlin interop | `kotlin-java-interop.md` |
| Grading architecture or Compose work | `rubric-android-architecture.md`, `rubric-compose-ui.md` |
| Matching vs changing existing patterns, scope discipline | `pragmatics.md`, `pattern-detection.md` |

## Agents

Delegate a scoped task with a plain brief — goal, acceptance criteria, files, verification command. Agents need nothing beyond the brief and don't call each other; the caller sequences them.

| Agent | Give it |
|-------|---------|
| `android-architect` | structure, placement, layering, ADRs, architecture review |
| `android-developer` | ViewModels, repositories, persistence, networking, DI wiring |
| `compose-expert` | screens, components, previews, accessibility, adaptive UI |
| `gradle-build-engineer` | modules, convention plugins, catalog, build performance |
| `android-testing-specialist` | tests and test review using the `android-testing` method |

Typical order for a new feature: architect (if structure changes) → gradle (if new modules) → developer → compose → testing. Skip any step the change doesn't need.

## Defaults when the codebase has no precedent

- Single `StateFlow` of UI state per screen; actions in, state out; errors as string resources; ViewModel-originated messages and navigation as state, not event channels.
- Repository is the source of truth; `Flow` for observed data; typed errors; `CancellationException` rethrown.
- Constructor injection with the project's DI (Hilt for new Android-only apps).
- Fakes over mocks; tests from break vectors, not the happy path.
- Kotlin, AGP, and library versions: read the project's catalog; never pin from memory.
