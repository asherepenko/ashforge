# Swift Testing Patterns

Code samples for the `ios-testing` method. Swift Testing API detail (expectations, traits, tags, parameterization, `confirmation`, migration from XCTest) is in the vendored `swift-testing-expert` skill under `skills/community/swift-testing-expert/references/`; this page only shows how the method uses it. TCA `TestStore` is covered by the `tca` skill.

## Contents

- Fake client with failure switches
- Parameterized single-angle test
- Throwing and `#require`
- Clock, Date, UUID injection
- Async events with `confirmation`
- `@MainActor` view model
- SwiftData in-memory container
- Stale response and double-tap

## Fake client with failure switches

```swift
protocol NoteClient: Sendable {
    func fetch() async throws -> [Note]
}

final class FakeNoteClient: NoteClient, @unchecked Sendable {
    var notes: [Note] = []
    var nextError: (any Error)?

    func fetch() async throws -> [Note] {
        if let nextError { throw nextError }
        return notes
    }
}
```

With a `@Dependency` client struct, the fake is the `testValue` or a per-test `withDependencies` override that holds behavior in its closures. The fake fails the way the real client fails: `URLError(.notConnectedToInternet)`, not a generic error.

## Parameterized single-angle test

One angle, many data points; one rejection branch:

```swift
@Test("Malformed emails are rejected", arguments: ["", " ", "a@", "@b.com", "a b@c.com", "a@b@c.com"])
func rejectsMalformedEmail(_ input: String) {
    #expect(EmailValidator().validate(input) == .invalid)
}
```

Pair inputs with expected outputs through `zip`, never a nested `for`. Separate angles get separate tests.

## Throwing and `#require`

```swift
@Test func fetchMapsOfflineToTypedError() async {
    let client = FakeNoteClient()
    client.nextError = URLError(.notConnectedToInternet)
    let repo = NoteRepository(client: client)

    await #expect(throws: NoteError.offline) {
        try await repo.refresh()
    }
}

@Test func firstNoteIsPinned() async throws {
    let notes = try await makeRepo(with: [.pinned, .plain]).all()
    let first = try #require(notes.first)
    #expect(first.isPinned)
}
```

## Clock, Date, UUID injection

Production code takes the time sources as inputs:

```swift
struct SessionStore {
    var now: () -> Date = Date.init
    var makeID: () -> UUID = UUID.init
    let ttl: TimeInterval

    func isExpired(_ s: Session) -> Bool { now() >= s.createdAt.addingTimeInterval(ttl) }
}
```

Tests pin them, and hit the boundary exactly:

```swift
@Test("Session expires exactly at ttl", arguments: [-1.0, 0.0, 1.0])
func expiryBoundary(offset: TimeInterval) {
    let created = Date(timeIntervalSince1970: 1_000)
    let store = SessionStore(now: { created.addingTimeInterval(60 + offset) }, ttl: 60)
    let session = Session(id: UUID(uuidString: "00000000-0000-0000-0000-000000000001")!, createdAt: created)
    #expect(store.isExpired(session) == (offset >= 0))
}
```

For delays, debounce, and timeouts, inject `any Clock<Duration>` and drive it:

```swift
@Test func debounceFiresOnceAfterQuietPeriod() async {
    let clock = TestClock()                       // swift-clocks
    let model = SearchModel(clock: clock)
    model.queryChanged("a"); model.queryChanged("ab")
    await clock.advance(by: .milliseconds(300))
    #expect(model.searchCount == 1)
}
```

Verify the `TestClock` / `ImmediateClock` names against the pinned swift-clocks version before use. In TCA features use `@Dependency(\.continuousClock)` and override with `TestClock` on the `TestStore`.

Time vectors worth a test each: a clock that goes backwards, a DST-length day via a fixed `Calendar` with an explicit `TimeZone`, epoch 0, and `expiresAt == now`.

## Async events with `confirmation`

```swift
@Test func emitsOnePerChange() async {
    let source = FakeEventSource()
    await confirmation("change events", expectedCount: 2) { confirm in
        source.onChange = { confirm() }
        source.emit(); source.emit()
    }
}

@Test func neverNotifiesWhenUnchanged() async {
    await confirmation(expectedCount: 0) { confirm in
        let source = FakeEventSource(); source.onChange = { confirm() }
        source.emit(same: true)
    }
}
```

No `Task.sleep` to "give it time". If the callback is truly asynchronous, bridge it with `withCheckedContinuation` or expose an `AsyncStream` and `await` its first element.

## `@MainActor` view model

```swift
@MainActor
struct LoginModelTests {
    @Test func submitShowsErrorOnFailure() async {
        let auth = FakeAuthClient(); auth.nextError = AuthError.badCredentials
        let model = LoginModel(auth: auth)
        await model.submit(email: "a@b.com", password: "x")
        #expect(model.errorMessage != nil)
        #expect(model.isLoading == false)
    }
}
```

Isolate the suite only because `LoginModel` is `@MainActor`. A pure validator test stays nonisolated.

## SwiftData in-memory container

```swift
@MainActor
func makeContainer() throws -> ModelContainer {
    try ModelContainer(
        for: Note.self,
        configurations: ModelConfiguration(isStoredInMemoryOnly: true)
    )
}

@MainActor
@Test func deleteRemovesNote() throws {
    let container = try makeContainer()
    let context = container.mainContext
    context.insert(Note(title: "a"))
    try context.save()
    try context.delete(model: Note.self)
    #expect(try context.fetch(FetchDescriptor<Note>()).isEmpty)
}
```

One container per test; never share it through a static. For model design and migration rules see the `swiftdata-pro` skill.

## Stale response and double-tap

```swift
@Test func slowOldResponseDoesNotOverwriteNewer() async throws {
    let client = GatedNoteClient()        // fake whose fetch suspends until released
    let model = NotesModel(client: client)
    async let first: Void = model.search("a")
    async let second: Void = model.search("ab")
    await client.release("ab", returning: [.ab])
    await client.release("a", returning: [.a])     // arrives last, must lose
    _ = await (first, second)
    #expect(model.results == [.ab])
}
```

A gated fake (continuations the test resumes in a chosen order) gives deterministic ordering without sleeps. Double-tap: call the action twice before releasing the gate and assert one request, one charge, one row.
