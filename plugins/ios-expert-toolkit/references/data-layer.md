# Data Layer

## When to use

Read when designing repositories, choosing a persistence stack, or moving off Core Data. SwiftData rules (`@Model`, `@Query`, predicates, indexing, CloudKit) are in the vendored `swiftdata-pro` skill; this page covers the layer around it.

## Repository

- A repository is the source of truth for one kind of data. It hides whether data came from disk or network.
- Expose `async` functions for one-shot reads and writes, and an `AsyncStream` (or an `@Observable` store) for observed data.
- Map storage and network models to domain types at this boundary. Domain types never import `SwiftData` or `CoreData`.
- Throw typed domain errors (`ios-error-handling`).
- Put the repository behind a protocol, or a TCA `@Dependency` client, so tests use a fake.

## Choosing storage

| Need | Use |
|------|-----|
| Small settings and flags | `UserDefaults` (`@AppStorage` in views) |
| Secrets and tokens | Keychain ([security](security.md)) |
| Structured local data, iOS 17+ | SwiftData |
| Structured local data below iOS 17, or an existing Core Data stack | Core Data |
| Files and documents | `FileManager` in the app container |

## Core Data coexistence and migration to SwiftData

SwiftData uses Core Data underneath, so both can read the same SQLite store while you migrate. Requires iOS 17.

1. **Match the models.** Write `@Model` classes whose property names and types equal the Core Data entities' attributes and relationships. Keep entity names the same, or set `@Attribute(originalName:)` for renamed properties.
2. **Share one store.** Point the `ModelConfiguration` at the same store URL the `NSPersistentContainer` uses. Do not let both stacks run schema migration on the same file: let one stack own migrations (the Core Data one until the cutover).
3. **Migrate one feature at a time** behind a repository protocol. Each repository has one implementation per store; the call sites don't change.
4. **Cut over.** Once no code reads through `NSManagedObjectContext`, remove the Core Data stack and move schema changes to `VersionedSchema` and `SchemaMigrationPlan`.
5. **Test with a copy of production data**, including the oldest store version still in the field. Back up the store before the first launch of the new build.

CloudKit-synced stores have extra constraints (see `swiftdata-pro`). Isolation rules for `NSManagedObjectContext` are in `swift-concurrency`. Changing data already on devices is irreversible: treat every schema change as a migration.
