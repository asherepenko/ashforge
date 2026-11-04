---
name: ios-expert
description: "Use for iOS app development questions, implementation guidance, and code review — SwiftUI, @Observable and MVVM, TCA, SwiftData and Core Data, Swift concurrency, navigation and deep links, Swift Testing, App Intents, Instruments, Xcode builds and security settings. Routes to the right reference or skill (including the vendored community and Xcode skills), to the Xcode MCP tools, and to the five iOS agents. Trigger on 'how should I build X on iOS', 'review this iOS code', 'which pattern for Y', 'SwiftUI screen', 'iOS architecture'. Not for server-side Swift or non-Apple platforms."
argument-hint: "[question or topic] — e.g. 'SwiftData migration', 'deep links', 'Swift 6 data race'"
---

# iOS Expert

A router. Find the topic, load only what it names, then answer or act.

**Rules up front.**

1. On existing code, run `ios-conventions` first: it reads the architecture, `Package.resolved`, the deployment target and the Swift language mode. Then follow [pragmatics](../../references/pragmatics.md): user instructions, then codebase consistency, then constraints, then best practice.
2. Check API availability against the deployment target and the Swift language mode before recommending anything. `@Observable` and SwiftData need iOS 17. Anything from a `*-whats-new-27` skill needs iOS 27. Below the target, give the API the project can compile.
3. Verify API claims you are unsure of with the Xcode `DocumentationSearch` tool or `/doc-lookup`, not memory.

## Topic → load

Each row owns its trigger phrases; no phrase appears in two rows. References live in [references](../../references/). Skills are loaded by name.

| Triggers | Load |
|----------|------|
| which architecture does this app use, check patterns, iOS conventions, TCA or MVVM for new code | `ios-conventions` |
| @Reducer, TestStore, @ObservableState, @Shared, swift-composable-architecture | `tca` |
| error handling, typed throws, try? hides errors, catch {} swallows, map error to message | `ios-error-handling` |
| write tests for, unit test this view model, fake repository, what edge cases am I missing | `ios-testing` |
| #expect, #require, traits and tags, parameterized tests, flaky Swift Testing test | `swift-testing-expert` |
| migrate XCTest to Swift Testing, modernize this test suite | `modernize-tests` |
| review my SwiftUI, build a SwiftUI screen, SwiftUI best practices | `swiftui-pro` |
| @Observable, @Environment, ForEach identity, deprecated SwiftUI API, @Animatable | `swiftui-specialist` |
| what's new in SwiftUI 27, iOS 27 SwiftUI APIs, @State macro compile error | `swiftui-whats-new-27` |
| data race, Sendable, @MainActor, actor isolation, Swift 6 migration | `swift-concurrency` |
| SwiftData, @Model, @Query, ModelContext, #Predicate | `swiftdata-pro` |
| App Intents, AppEntity, App Shortcuts, intent perform() | `app-intents-specialist` |
| supportedModes, openAppWhenRun, App Intents iOS 27, continueInForeground | `app-intents-whats-new-27` |
| xctrace, Instruments trace, why is the app slow, CPU or memory profile | `xctrace` |
| Xcode security settings, hardened build settings, audit the project settings | `audit-xcode-security-settings` |
| resizable window, multiple windows, Stage Manager, split-screen layout | `app-resizability` |
| run on the simulator, screenshot the app, tap through the UI, check behavior on device | `device-interaction` |
| layers, modules, dependency injection, where should this live | [architecture](../../references/architecture.md) |
| UIViewRepresentable, hosting controller, UIKit interop, SwiftUI state and view composition | [swiftui](../../references/swiftui.md) |
| repositories, persistence layer, Core Data coexistence, migrate Core Data to SwiftData, CloudKit sync | [data-layer](../../references/data-layer.md) |
| async/await patterns, Task lifetime, AsyncStream, structured concurrency basics | [concurrency](../../references/concurrency.md) |
| NavigationStack, deep links, universal links, onOpenURL, apple-app-site-association | [navigation](../../references/navigation.md) |
| launch time, hangs, MetricKit, memory growth, scroll hitches | [performance](../../references/performance.md) |
| Keychain, App Transport Security, secrets in the bundle, privacy manifest basics | [security](../../references/security.md) |
| VoiceOver, Dynamic Type, accessibility labels, reduce motion | [accessibility](../../references/accessibility.md) |
| matching vs changing existing patterns, scope discipline | [pragmatics](../../references/pragmatics.md) |
| architecture detection sweep, 80/20 rule, sweep patterns | [pattern-detection](../../references/pattern-detection.md) |
| test code mechanics, fakes and spies, test fixtures, async test helpers | [testing-patterns](../../references/testing-patterns.md) |
| TCA reference detail, dependency clients, TCA navigation, SwiftData behind @Dependency | [tca](../../references/tca.md) |
| changing data already on devices, schema migration, renaming a stored key, VersionedSchema | [persisted-state-review](../../references/persisted-state-review.md) |
| offline queue, pending changes, conflict resolution, BGTaskScheduler, NWPathMonitor | [offline-sync](../../references/offline-sync.md) |
| logging, os.Logger, signposts, crash reporting, analytics | [observability](../../references/observability.md) |
| grade this SwiftUI screen, UI quality bar | [rubric-swiftui](../../references/rubric-swiftui.md) |
| grade this architecture, architecture quality bar | [rubric-ios-architecture](../../references/rubric-ios-architecture.md) |

## Xcode MCP

The plugin's `.mcp.json` registers the `xcode` server, which runs `xcrun mcpbridge` over stdio. The tools work on workspaces open in Xcode: call `XcodeListWorkspaces` or `XcodeOpenWorkspace` first, then `XcodeListSchemes` and `XcodeSwitchScheme` if the active scheme is wrong. Without Xcode the server does not connect; use `xcodebuild` and `xcrun simctl` instead.

Tool names below come from a `tools/list` call against Xcode 27.2 (build 27B52).

| Job | Tools |
|-----|-------|
| Build | `BuildProject`, then `GetBuildLog` for errors and warnings |
| Test | `XcodeListTestPlans`, `GetTestList`, `RunSomeTests`, `RunAllTests` |
| Preview | `RenderPreview` — builds and returns a snapshot of one `#Preview` |
| Diagnostics | `XcodeRefreshCodeIssuesInFile` for compiler errors and warnings in one file; `GetConsoleOutput` for runtime logs |
| Run and device | `RunProject`, `StopProject`, `XcodeListRunDestinations`, `DeviceInteractionInstallAndRun` |
| Docs | `DocumentationSearch` for Apple Developer Documentation |
| Build settings | `GetTargetBuildSettings`, `UpdateTargetBuildSetting` |

Prefer `RunSomeTests` over `RunAllTests`: run only the tests that cover the change.

## Agents

Delegate a scoped task with a plain brief — goal, acceptance criteria, files, verification command. Agents need nothing beyond the brief and don't call each other; the caller sequences them.

| Agent | Give it |
|-------|---------|
| `ios-architect` | structure, placement, layering, ADRs, architecture review |
| `ios-developer` | reducers and view models, dependency clients, repositories, SwiftData and persistence, networking, concurrency |
| `swiftui-expert` | screens, components, previews, accessibility, adaptive layout |
| `ios-testing-specialist` | tests and test review using the `ios-testing` method |
| `xcode-build-engineer` | targets, schemes, build settings, Swift packages, signing, CI build steps |

Typical order for a new feature: architect (if structure changes) → build engineer (if new targets or packages) → developer → swiftui-expert → testing specialist. Skip any step the change doesn't need.

## Defaults when the codebase has no precedent

- New project: TCA (see `ios-conventions` for the decision rule). Plain SwiftUI code: `@Observable` view models, `@MainActor` isolation, one state source per screen.
- Repository is the source of truth; `async` functions and `AsyncStream` for observed data; typed errors; `CancellationError` rethrown.
- Constructor injection; in TCA, `@Dependency` clients.
- Swift Testing for new tests; fakes over mocks; tests from break vectors, not the happy path.
- Package versions, deployment target, Swift version: read the project; never pin from memory.
