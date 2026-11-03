# TCA reference (ComposableArchitecture 1.26)

Pinned to `ComposableArchitecture 1.26` (swift-composable-architecture 1.26.2, released 2026-08-28). Package floor: iOS 16, macOS 13. Dependencies library used: swift-dependencies 1.17.2. On iOS 16 the observation tools come from the Perception backport (`WithPerceptionTracking`).

## Contents

- [Sources](#sources)
- [Reducer and state](#reducer-and-state)
- [Effects and cancellation](#effects-and-cancellation)
- [Dependencies](#dependencies)
- [SwiftData behind a dependency](#swiftdata-behind-a-dependency)
- [TestStore](#teststore)
- [Tree navigation](#tree-navigation)
- [Stack navigation](#stack-navigation)
- [Shared state](#shared-state)
- [Deprecations by version](#deprecations-by-version)

## Sources

DocC sources at tag `1.26.2`, under `Sources/ComposableArchitecture/Documentation.docc/`:

| Topic | Source |
|-------|--------|
| Reducer, State, Action, Store | `Articles/GettingStarted.md` |
| Bindings | `Articles/Bindings.md` |
| Effects | `Extensions/Effect.md`, `Effect.swift` (`Effect.run(priority:operation:catch:...)`), `Effects/Cancellation.swift` |
| Dependencies | `Articles/DependencyManagement.md`, `Articles/GettingStarted.md`; swift-dependencies 1.17.2 `DependencyKey.swift` |
| Testing | `Articles/TestingTCA.md`, `TestStore.swift` |
| Tree navigation | `Articles/TreeBasedNavigation.md` |
| Stack navigation | `Articles/StackBasedNavigation.md` |
| Shared state | `Articles/SharingState.md` |
| Observation backport | `Articles/ObservationBackport.md` |
| Deprecations | `Articles/MigrationGuides/MigratingTo1.4.md`, `1.7`, `1.11`, `1.25`; `Internal/Deprecations.swift` |

## Reducer and state

```swift
@Reducer
struct Feature {
  @ObservableState
  struct State: Equatable {
    var count = 0
    var numberFact: String?
  }
  enum Action {
    case incrementButtonTapped
    case numberFactButtonTapped
    case numberFactResponse(String)
  }
  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .incrementButtonTapped:
        state.count += 1
        return .none
      case .numberFactButtonTapped:
        return .run { [count = state.count] send in
          await send(.numberFactResponse(try await fetch(count)))
        }
      case let .numberFactResponse(fact):
        state.numberFact = fact
        return .none
      }
    }
  }
}

struct FeatureView: View {
  let store: StoreOf<Feature>
  var body: some View {
    Button("Fact") { store.send(.numberFactButtonTapped) }
    Text("\(store.count)")
  }
}
```

Bindings: `@Bindable var store: StoreOf<Feature>`, `TextField("Name", text: $store.name)`. Make `Action: BindableAction` with `case binding(BindingAction<State>)` and put `BindingReducer()` in `body`.

Entry point: `Store(initialState: Feature.State()) { Feature() }`.

## Effects and cancellation

`Effect.run(priority:operation:catch:)` takes an async closure and an optional `catch` handler `(Error, Send<Action>) async -> Void`.

```swift
private enum CancelID { case search }

case .queryChanged(let query):
  return .run { send in
    try await clock.sleep(for: .milliseconds(300))
    await send(.response(Result { try await client.search(query) }))
  }
  .cancellable(id: CancelID.search, cancelInFlight: true)

case .cancelTapped:
  return .cancel(id: CancelID.search)
```

- `cancellable(id:cancelInFlight:)` and `Effect.cancel(id:)` take any `Hashable & Sendable` id.
- Capture state by value. Effects run outside the reducer.
- Stores cancel in-flight effects when they deallocate (1.18).
- Use `@Dependency(\.continuousClock)` for sleeps so tests control time.

## Dependencies

```swift
struct NumberFactClient { var fetch: (Int) async throws -> String }

extension NumberFactClient: DependencyKey {
  static let liveValue = Self(fetch: { number in /* URLSession */ "" })
  static let testValue = Self(fetch: { "\($0) is a good number" })
}

extension DependencyValues {
  var numberFact: NumberFactClient {
    get { self[NumberFactClient.self] }
    set { self[NumberFactClient.self] = newValue }
  }
}

@Reducer struct Feature { @Dependency(\.numberFact) var numberFact }
```

- `liveValue` is required. Reading it in a test fails the test.
- `testValue` defaults to `previewValue`, then to `liveValue`, but triggers a failure when accessed; provide your own to make tests quiet.
- `previewValue` defaults to `liveValue`.
- Override per test: `TestStore(initialState:) { Feature() } withDependencies: { $0.numberFact.fetch = { _ in "ok" } }`.
- Prefer `@Dependency(\.uuid)`, `\.date`, `\.continuousClock` over `UUID()`, `Date()`, `Task.sleep` in reducers.

## SwiftData behind a dependency

Needs iOS 17. The reducer never sees `ModelContext`; it sees a client of closures.

```swift
struct TodoStore {
  var fetch: @Sendable () async throws -> [TodoItem]   // TodoItem is a Sendable value type, not @Model
  var add: @Sendable (String) async throws -> Void
  var delete: @Sendable (TodoItem.ID) async throws -> Void
}

extension TodoStore: DependencyKey {
  static let liveValue: TodoStore = {
    let container = try! ModelContainer(for: TodoModel.self)
    // build closures over ModelContext(container) inside one actor-isolated helper
    return TodoStore(fetch: { [] }, add: { _ in }, delete: { _ in })
  }()
  static let testValue = TodoStore(fetch: { [] }, add: { _ in }, delete: { _ in })
}
```

- Map `@Model` classes to plain `Sendable` structs at the client boundary. `@Model` types are not `Sendable` and do not belong in `State`.
- Do all `ModelContext` work in one actor (`@ModelActor`) inside the live client. Tests use the closure stubs or an in-memory `ModelConfiguration(isStoredInMemoryOnly: true)`.
- Views may still use `@Query` for read-only lists in a non-TCA leaf view; keep writes in the client.
- For SwiftData API detail use `swiftdata-pro`; for Core Data coexistence see `data-layer`.

## TestStore

```swift
@MainActor
struct FeatureTests {
  @Test func fact() async {
    let store = TestStore(initialState: Feature.State()) {
      Feature()
    } withDependencies: {
      $0.numberFact.fetch = { "\($0) is great" }
    }
    await store.send(.numberFactButtonTapped)
    await store.receive(\.numberFactResponse) {
      $0.numberFact = "0 is great"
    }
  }
}
```

Exhaustive is the default (`Exhaustivity.on`): all state changes asserted, all received actions asserted, all effects finished before deallocation. Use `await store.finish()` to wait for effects.

Non-exhaustive:

```swift
store.exhaustivity = .off                              // pass silently
store.exhaustivity = .off(showSkippedAssertions: true) // log what was skipped
await store.send(\.login.submitButtonTapped)
await store.receive(\.login.delegate.didLogin) { $0.selectedTab = .activity }
```

Helpers: `skipReceivedActions()`, `skipInFlightEffects()`. Rule of thumb from the docs: exhaustive for leaf features, non-exhaustive for integration of many features.

## Tree navigation

Optional state drives presentation; `nil` dismisses.

```swift
@ObservableState struct State { @Presents var addItem: ItemForm.State? }
enum Action { case addItem(PresentationAction<ItemForm.Action>) }

var body: some ReducerOf<Self> {
  Reduce { state, action in /* state.addItem = ItemForm.State() */ .none }
    .ifLet(\.$addItem, action: \.addItem) { ItemForm() }
}

.sheet(item: $store.scope(state: \.addItem, action: \.addItem)) { ItemFormView(store: $0) }
```

Several destinations use an enum reducer:

```swift
@Reducer enum Destination { case add(ItemForm); case edit(ItemEdit) }
@Presents var destination: Destination.State?
.ifLet(\.$destination, action: \.destination)
// 1.25 view syntax:
.sheet(item: $store.scope(state: \.$destination, action: \.destination).edit) { ... }
```

Non-feature cases (such as `AlertState`) need `@ReducerCaseIgnored` plus an explicit `Action` enum (1.25 guide). Children dismiss via `@Dependency(\.dismiss)` called from an effect.

## Stack navigation

```swift
@Reducer enum Path { case detail(DetailFeature); case edit(EditFeature) }

@ObservableState struct State { var path = StackState<Path.State>() }
enum Action { case path(StackActionOf<Path>) }
var body: some ReducerOf<Self> {
  Reduce { state, action in
    switch action {
    case .path(.element(id: _, action: .detail(.editTapped))):
      state.path.append(.edit(EditFeature.State()))
      return .none
    default: return .none
    }
  }
  .forEach(\.path, action: \.path)
}

NavigationStack(path: $store.scope(state: \.path, action: \.path)) { Root() }
  destination: { store in switch store.case { case .detail(let s): DetailView(store: s) ... } }
```

Pop with `state.path.popLast()` or `state.path.pop(from: id)`. `StackState` assigns element ids.

## Shared state

```swift
@Shared(.appStorage("count")) var count = 0
@Shared(.fileStorage(.todosURL)) var todos: IdentifiedArrayOf<Todo> = []
@Shared(.inMemory("session")) var session = Session()
@ObservableState struct State { @Shared var count: Int }   // handed down by parent
state.$count.withLock { $0 += 1 }
```

- Persistence strategies: `appStorage`, `fileStorage` (value must be `Codable`), `inMemory`, custom `SharedKey`.
- Mutate only through `withLock` (1.11 deprecated direct mutation from async contexts).
- `@Shared` comes from the swift-sharing package (extracted in 1.17; Sharing 2.0 support from 1.17.1).

## Deprecations by version

Flag only for projects whose resolved TCA version is the listed one or newer.

| Legacy | Replacement | Version | Evidence |
|--------|-------------|---------|----------|
| `WithViewStore`, `ViewStore` | `@ObservableState` | 1.7 | `MigratingTo1.7#Using-ObservableState`; `@available(*, deprecated)` in `Deprecations.swift` |
| `@BindingState`, `BindingViewState`, `BindingViewStore`, `ViewStore.binding` | `@Bindable` store bindings | 1.7; hard warning 1.25 | `MigratingTo1.7#BindingState`; `MigratingTo1.25` |
| `@PresentationState` | `@Presents` | 1.7 | `MigratingTo1.7#Replacing-PresentationState-with-Presents` |
| `IfLetStore`, `ForEachStore`, `SwitchStore`, `CaseLet` | `if let`, `ForEach`, `switch store.case` | 1.7 | `MigratingTo1.7` |
| `NavigationStackStore`, `sheet(store:)` family | `NavigationStack(path:)`, `sheet(item:)` with `$store.scope` | 1.7 | `MigratingTo1.7` |
| `Store.publisher`, `Store.ifLet` (UIKit) | `observe { }` | 1.7 (publisher also trait-deprecated 1.25) | `MigratingTo1.7#Observing-for-UIKit`; `MigratingTo1.25` |
| `TaskResult` | `Result` | 1.4, soft | `MigratingTo1.4#Moving-off-of-TaskResult` |
| Direct `@Shared` mutation | `withLock` | 1.11 | `MigratingTo1.11` |
| `Effect.animation/transaction/debounce/throttle` | `.run` with `send(_:animation:)`, `clock.sleep` | 1.25 | `MigratingTo1.25#Hard-deprecations` |
| `Store.withState`, `reducer.reduce`, enum-state `Scope` | `@ObservableState`, `store.send`, `@Reducer enum`/`ifCaseLet` | 1.25 | same |
| `Effect.concatenate/map`, `StorePublisher`, non-projected destination scope, `onChange` reducer builder | `.run` sequencing, `observe`, `\.$destination` scope, streamlined `onChange` | 1.25 with `ComposableArchitecture2Deprecations` trait | `MigratingTo1.25#Trait-deprecations` |

Enable the 1.25 trait in `Package.swift`: `.package(url: ..., from: "1.25.0", traits: ["ComposableArchitecture2Deprecations"])`.
