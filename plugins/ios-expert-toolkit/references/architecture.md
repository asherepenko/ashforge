# Architecture

## When to use

Read when deciding where code lives, how layers depend on each other, or how dependencies are injected. Which architecture a codebase already uses is decided by `ios-conventions`; TCA detail is in [tca](tca.md).

## Layers

```
View (SwiftUI)  →  state holder (@Observable class or TCA Store)  →  service / repository  →  client (network, database, file)
```

- Dependencies point one way, toward the clients. A view never talks to a client.
- Domain types are plain `struct`/`enum` values with no UI or framework imports beyond `Foundation`.
- Each layer converts the errors it catches into its own error type (`ios-error-handling`).
- Mark UI-facing state holders `@MainActor`; keep services off the main actor and let `async` calls hop.

## Modules

- Split into local Swift packages when a boundary needs compile-time enforcement: feature, domain, data, shared UI. One target per package product.
- Features depend on domain protocols, not on other features. The app target wires concrete types together.
- A single-target app is fine until build time or ownership says otherwise. Don't split for its own sake.

## Dependency injection

| Style | Use when |
|-------|----------|
| Initializer parameters | Default for non-TCA code; protocols at the seams that tests replace |
| `@Environment` with `@Entry` | Values the view tree needs (theme, a client for previews). Defaults must be cheap and stable; see `swiftui-specialist` |
| `@Dependency` | TCA features; see [tca](tca.md) |
| Singletons | Avoid for anything with state or I/O; they block tests |

A manual composition root (one place that builds the object graph) beats a DI framework until the graph is hard to follow.

## State

- One state source per screen. Derived values are computed, not stored.
- Navigation and one-off messages are state (an optional or an enum), not callbacks fired at the view.
- Observation: `@Observable` needs iOS 17. Below that, `ObservableObject` with `@Published`.

## Concurrency

Isolation and Sendable rules live in `swift-concurrency`; patterns in [concurrency](concurrency.md).
