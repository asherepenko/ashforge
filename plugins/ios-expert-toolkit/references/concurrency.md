# Concurrency

## When to use

Read for everyday async patterns. Diagnosing data races, Sendable errors, actor isolation, and Swift 6 migration belong to the vendored `swift-concurrency` skill; load it rather than restating its rules.

## Patterns

- Prefer `async`/`await` over completion handlers. Wrap a callback API once with `withCheckedThrowingContinuation` and resume exactly once.
- Isolate UI-facing state holders with `@MainActor`. Services do their work off the main actor; awaiting them hops back automatically.
- Use structured concurrency (`async let`, `withTaskGroup`) so child work is cancelled with its parent. Use an unstructured `Task { }` only to start async work from a synchronous context, and keep its handle if it needs cancelling.
- In SwiftUI, `.task { }` runs when the view appears and is cancelled when it disappears. Use `.task(id:)` to restart on a changed value.
- Cancellation is cooperative: check `Task.isCancelled` or call `try Task.checkCancellation()` in long loops, and rethrow `CancellationError` rather than turning it into a user-facing failure (`ios-error-handling`).
- Observed data: expose an `AsyncStream`, or let an `@Observable` store hold the latest value.
- Debounce and throttle with a cancelled-and-restarted `Task` or with swift-async-algorithms (`async-algorithms` in `swift-concurrency`).

## Checks

- Strict concurrency checking on, at least `complete` warnings, before turning on the Swift 6 language mode. Read the project's mode from the build settings.
- Do not silence a Sendable diagnostic with `@unchecked Sendable` unless the type guards its state with a lock or actor and a comment says which.
- Never block the main actor with `DispatchSemaphore` or `Task.sleep` loops that wait on async work.
