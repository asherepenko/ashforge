---
name: android-expert
description: "Use for Android app development questions, implementation guidance, and code review — Jetpack Compose, ViewModel/StateFlow, Hilt/Koin, Room, DataStore, coroutines/Flow, Navigation 2/3, WorkManager, Gradle convention plugins and AGP 9, R8, security, performance, testing. Routes to the right reference or skill (including the vendored official Android skills) and to the five Android agents. Trigger on 'how should I build X on Android', 'review this Android code', 'which pattern for Y', 'Compose screen', 'Android architecture'. Not for backend/server Kotlin or non-Android Gradle builds."
argument-hint: "[question or topic] — e.g. 'Room offline-first', 'ViewModel error state', 'AGP 9 convention plugin'"
---

# Android Expert

A router. Find the topic, load only what it names, then answer or act.

**Rules up front.**

1. On existing code, run `android-conventions` first: it reads the architecture, DI, state and testing patterns. Then follow [pragmatics](../../references/pragmatics.md): user instructions, then codebase consistency, then constraints, then best practice.
2. Check API availability before recommending an API. Read `minSdk`, `targetSdk` and `compileSdk` from the build files, and the Compose BOM and AGP versions from the version catalog. Below `minSdk`, give the compat API (AndroidX, `*Compat`) or an `if (Build.VERSION.SDK_INT >= ...)` guard.
3. Verify API claims you are unsure of with `android docs search "<query>"`, not memory.

## Topic → load

Each row owns its trigger phrases; no phrase appears in two rows. References are linked; skills are loaded by name.

| Triggers | Load |
|----------|------|
| which patterns does this codebase use, check patterns, which DI is used, Android conventions | `android-conventions` skill |
| layers, modules, dependency rules, where should this live | [architecture](../../references/architecture.md) |
| viewModelScope, dispatchers, stateIn, shareIn, WhileSubscribed, structured concurrency, runTest, StandardTestDispatcher | [coroutines](../../references/coroutines.md) |
| ViewModel, UI state, actions, one-off events, SavedStateHandle, Route/Screen split | [presentation](../../references/presentation.md) |
| error types, try/catch, CancellationException, error message in UI | `android-error-handling` skill |
| repositories, Room, DataStore, Retrofit, Ktor, WorkManager, Paging | [data-layer](../../references/data-layer.md) |
| sync queue, conflict resolution | [offline-sync](../../references/offline-sync.md) |
| changing data already stored on devices, schema migration | [persisted-state-review](../../references/persisted-state-review.md) |
| Hilt, Koin, Dagger, manual DI | [dependency-injection](../../references/dependency-injection.md) |
| Compose components, state placement, side effects, text fields, custom modifiers, animations, previews, lists, theme, View interop | [compose-ui](../../references/compose-ui.md) |
| accessibility, TalkBack, content descriptions | [accessibility](../../references/accessibility.md) |
| window sizes, nav bar vs rail, list-detail, foldables, keyboard and mouse | `adaptive` skill |
| edge-to-edge, insets, system bars | `edge-to-edge` skill |
| home screen widget layout, Glance canonical layouts, widget UI | `glance-canonical-layouts` skill |
| widget updates, updateAll, Glance background sync, RemoteViews bitmap memory | `glance-appwidget-updates-and-memory` skill |
| recomposition, stability, Compose jank | `jetpack-compose-performance` skill |
| XML layout to Compose | `migrate-xml-views-to-jetpack-compose` skill |
| Navigation 2, NavHost, deep links, App Links | [navigation](../../references/navigation.md) |
| Navigation 3, NavDisplay, Nav 2 to 3 migration, scenes | `navigation-3` skill |
| predictive back, back-gesture handling | `navigation-event` skill |
| convention plugins, module build files | [gradle-convention-plugins](../../references/gradle-convention-plugins.md) |
| version catalog, gradle.properties, build cache, signing, CI | [gradle-build-config](../../references/gradle-build-config.md) |
| upgrade to AGP 9 | `agp-9-upgrade` skill |
| R8 keep rules, shrinking, app size | `r8-analyzer` skill |
| network trust, secrets, token storage, release hardening | [security](../../references/security.md) |
| exported components, intents, PendingIntent | `android-intent-security` skill |
| runtime permissions, component protection | `android-permissions-security` skill |
| startup time, Baseline Profiles, Macrobenchmark, vitals targets | [performance](../../references/performance.md) |
| traces, heap dumps, profiling | `android-profiler` skill |
| ANR, main-thread blocking | `anr-audit-and-fix` skill |
| logging, crash reporting, analytics, custom traces | [observability](../../references/observability.md) |
| write tests for, review these tests, what edge cases am I missing | `android-testing` skill |
| test code mechanics, fakes, Turbine, Compose tests, Room tests | [testing-patterns](../../references/testing-patterns.md) |
| test infrastructure, screenshot tests, E2E setup | `testing-setup` skill |
| Java to Kotlin interop, Java callers | [kotlin-java-interop](../../references/kotlin-java-interop.md) |
| grade architecture or Compose work | [rubric-android-architecture](../../references/rubric-android-architecture.md), [rubric-compose-ui](../../references/rubric-compose-ui.md) |
| matching vs changing existing patterns, scope discipline | [pragmatics](../../references/pragmatics.md) |
| detection sweep, 80/20 rule | [pattern-detection](../../references/pattern-detection.md) |

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
