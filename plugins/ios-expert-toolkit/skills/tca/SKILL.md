---
name: tca
description: "Use when writing, reviewing, testing, or migrating a feature built with The Composable Architecture (TCA) on iOS — reducers, state and actions, effects, dependencies, TestStore, navigation, shared state. Trigger on 'TCA', '@Reducer', '@ObservableState', 'TestStore', 'WithViewStore', 'StackState', '@Shared', 'swift-composable-architecture'. Not for plain SwiftUI or MVVM code (use swiftui-pro) or for choosing the architecture (use ios-conventions)."
argument-hint: "[feature, reducer, or file]"
---

# TCA (ComposableArchitecture 1.26)

Pinned to `ComposableArchitecture 1.26` (swift-composable-architecture 1.26.2, released 2026-08-28; the library supports iOS 16 and later). Every API below is cited to the DocC articles at that tag. Detail and code live in [tca](../../references/tca.md).

**Policy.** A new project uses TCA. An existing codebase keeps the style it has. The detection rule and the 80% threshold live in [ios-conventions](../ios-conventions/SKILL.md); do not restate them here.

**Version first.** Read the project's TCA version from `Package.resolved` (`ios-conventions` does this) before advising. Flag a legacy API only when the project's version is at or above the version that deprecated it (see Deprecated). Older projects get the API they can compile.

## Core shape

- `@Reducer struct Feature` with a nested `@ObservableState struct State`, an `enum Action`, and `var body: some ReducerOf<Self>` built from `Reduce { state, action in ... }`.
- Views hold `StoreOf<Feature>` and read `store.count` directly; use `@Bindable var store` to derive bindings (`$store.name`). Make actions `BindableAction` and add `BindingReducer()` for form fields.
- State changes happen only in the reducer. Side work returns an `Effect`.

## Effects

- `.run { send in ... }` for async work; capture state values by copy (`[count = state.count]`), never `state` itself.
- Cancel with `.cancellable(id:cancelInFlight:)` and `.cancel(id:)`. Use a private `CancelID` enum as the id.
- Handle failures with `.run(operation:catch:)` or a do/catch that sends a failure action. Use `Result`, not `TaskResult` (see Deprecated).
- Debounce and throttle with `clock.sleep` plus `cancelInFlight`, not Combine operators.

## Dependencies

- Declare `@Dependency(\.client) var client` in the reducer.
- A client is a struct of closures (or `@DependencyClient`). Conform it to `DependencyKey` with `liveValue`, add `testValue` (and `previewValue` when useful), and expose it through an extension on `DependencyValues`.
- Without a `testValue`, a test that touches the dependency fails by design. Override it per test with `withDependencies:` on the `TestStore`.
- **SwiftData (iOS 17+).** Keep `ModelContext` behind a `@Dependency` client (fetch, insert, delete closures). Never read `@Query` or `ModelContext` inside a reducer. Tests supply an in-memory container through `testValue`.

## TestStore

- **Exhaustive (default).** `TestStore(initialState:) { Feature() }`. Every state change must be asserted in the `send`/`receive` closure, every effect must finish, and unasserted received actions fail the test. Use for leaf features.
- **Non-exhaustive.** `store.exhaustivity = .off` (or `.off(showSkippedAssertions: true)`). Assert only the slice you care about. Use for integration tests across composed features. `skipReceivedActions()`, `skipInFlightEffects()` and `finish()` control leftovers.
- Receive with case key paths: `await store.receive(\.response.success) { ... }`. Mark tests and suites `@MainActor` and `async`. Test-framework rules: `ios-testing`.

## Navigation

- **Tree (optional state):** `@Presents var destination: Destination.State?`, `case destination(PresentationAction<Destination.Action>)`, `.ifLet(\.$destination, action: \.destination)`. Multiple destinations: `@Reducer enum Destination`. Present with `.sheet(item: $store.scope(state: \.destination?.edit, action: \.destination.edit))` or the 1.25 form `$store.scope(state: \.$destination, action: \.destination).edit`.
- **Stack (array of screens):** `@Reducer enum Path`, `var path = StackState<Path.State>()`, `case path(StackActionOf<Path>)`, `.forEach(\.path, action: \.path)`, and `NavigationStack(path: $store.scope(state: \.path, action: \.path))`.
- Choose tree for modals and one-step drill-in; stack for deep, data-driven flows. Children dismiss with `@Dependency(\.dismiss)`.

## Shared state

`@Shared(.appStorage("key"))`, `@Shared(.fileStorage(url))`, `@Shared(.inMemory("key"))`, or a plain `@Shared var x: T` passed from a parent. Mutate with `$x.withLock { $0 = ... }`. Data that is not simple key-value (a database) stays behind a dependency, not `@Shared`.

## Deprecated (by version)

Flag these only when the project's TCA version is the listed one or newer. Replacement first.

| Legacy API | Replace with | Deprecated in |
|------------|--------------|---------------|
| `WithViewStore`, `ViewStore` | `@ObservableState` and reading `store.property` | 1.7 |
| `@BindingState`, `BindingViewState`, `BindingViewStore` | `@Bindable var store` with `$store.property` | 1.7 (hard warning in 1.25) |
| `@PresentationState` | `@Presents` | 1.7 |
| `IfLetStore`, `ForEachStore`, `SwitchStore`/`CaseLet` | `if let store.scope(...)`, `ForEach(store.scope(...))`, `switch store.case` | 1.7 |
| `NavigationStackStore`, `sheet(store:)` and the other `*(store:)` modifiers | `NavigationStack(path: $store.scope(...))`, `sheet(item: $store.scope(...))` | 1.7 |
| `TaskResult` | `Result` plus `receive(\.response.success)` | 1.4 (soft) |
| Direct mutation of a `@Shared` value | `$value.withLock { ... }` | 1.11 |
| `Effect.debounce`, `.throttle`, `.animation`, `.transaction` | `clock.sleep` with `cancellable(id:cancelInFlight:)`; `send(_:animation:)` inside `.run` | 1.25 |
| `Store.withState`, `reducer.reduce(into:action:)`, `Scope` over enum state | `@ObservableState`; `store.send`; `@Reducer enum` or `ifCaseLet` | 1.25 |
| `store.publisher`, `Effect.concatenate`/`.map`, non-projected `$store.scope(state: \.destination ...)`, `onChange` with `(old, new)` reducer builder | `observe`/`Observations`; sequence inside `.run`; `\.$destination` scope; streamlined `onChange` | 1.25, only with the `ComposableArchitecture2Deprecations` trait |

## Done means

- Cited API names match the pinned version in [tca](../../references/tca.md).
- Any flagged legacy API names its replacement and the project version that deprecates it.
- For code changes: `ios-testing` tests cover the reducer, and the named test command exits 0.
