# iOS Architecture Quality Rubric

Grading criteria for iOS architecture and data-layer work. Use both as **generation targets** (what to aim for when building) and **evaluation criteria** (what to check when reviewing). Each criterion describes what strong and weak work looks like.

## When to use

Read this reference when designing a feature or module (to aim at the "Strong" column) or when reviewing architecture work (to grade against the rubric). Used by ios-architect for generation and by any reviewer for evaluation. The rules graded here live in [architecture](architecture.md), [tca](tca.md), and [concurrency](concurrency.md).

## 1. Layering

**Strong**: Dependencies point one way: view, then state holder, then service or repository, then client. A view never calls a client. Domain types are plain `struct`/`enum` values that import only `Foundation`. Each layer converts the errors it catches into its own error type (`ios-error-handling`). Package splits exist where a boundary needs compile-time enforcement, and features depend on domain protocols, not on other features.

**Weak**: A view calls `URLSession` or a `ModelContext` directly. Domain types import SwiftUI. One feature imports another feature's internals. Errors from the network layer reach the view unchanged. Packages split for their own sake, with no boundary they enforce.

## 2. Architecture Fit

**Strong**: The pattern matches the `ios-conventions` decision. A `TCA` or `NEW` codebase gets TCA for new features. An `MVVM` codebase keeps MVVM, with `@Observable` view models on iOS 17 and `ObservableObject` below it. A `MIXED` codebase follows the pattern in the feature's folder. The choice is stated, with the detection result behind it.

**Weak**: TCA forced into an MVVM codebase. A plain view model added to a TCA codebase. `@Observable` used with a deployment target below iOS 17. Two patterns mixed in one feature with no reason given.

## 3. State and Data Flow

**Strong**: One state source per screen. Derived values are computed, not stored. Navigation and one-off messages are state (an optional or an enum), not callbacks fired at the view. In TCA, state is `@ObservableState`, child features are composed with `Scope`/`ifLet`/`forEach`, and shared values use `@Shared`. Data flows down as values and events flow up as actions or method calls.

**Weak**: The same value stored in two places that drift apart. A flag like `isLoading` next to an optional result that can contradict it. Navigation driven by closures the view must remember to call. Deprecated TCA APIs (`WithViewStore`, `ViewStore`) in new code.

## 4. Concurrency Safety

**Strong**: UI-facing state holders are `@MainActor`. Services run off the main actor. Types that cross isolation are `Sendable`. Child work uses structured concurrency so it is cancelled with its parent. Long-running TCA effects have cancel IDs. `CancellationError` is rethrown, never shown to the user. The project's strict concurrency mode is known and the code compiles clean under it. Detailed rules belong to the `swift-concurrency` skill.

**Weak**: `@unchecked Sendable` with no lock or actor behind it. `DispatchQueue.main.async` sprinkled to fix warnings. Unstructured `Task { }` with no handle that outlives its screen. `catch` blocks that turn cancellation into an error alert. The main actor blocked by a semaphore.

## 5. Dependency Injection

**Strong**: Non-TCA code takes dependencies through initializer parameters, with protocols at the seams that tests replace. TCA features use `@Dependency` clients with live, preview, and test values. `@Environment` carries only values the view tree needs, with cheap defaults. One composition root builds the object graph.

**Weak**: Singletons with state or I/O called from deep inside features. A DI framework added for a graph of five objects. A TCA dependency with no test value, so tests hit the network. `@Environment` used to smuggle services past the initializer.

## 6. Testability

**Strong**: State holders and reducers are tested without a UI. TCA features are tested with `TestStore` and exhaustive assertions. Non-TCA code is tested with fakes passed through the initializer. Clocks, UUIDs, and dates are injected, so tests are deterministic. Each test covers one behavior (`ios-testing`).

**Weak**: Logic only reachable through UI tests. Tests that sleep to wait for async work. Real network or disk in unit tests. `TestStore` with `exhaustivity = .off` to hide unasserted state changes.
