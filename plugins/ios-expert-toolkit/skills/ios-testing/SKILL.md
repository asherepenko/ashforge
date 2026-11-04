---
name: ios-testing
description: "Use when writing or reviewing iOS/Swift unit tests — view models, reducers, validators, mappers, services, repositories with fakes, SwiftData stores, async and @MainActor code. Applies an adversarial 'how would I break this?' method with Swift Testing: enumerate break vectors from the contract before writing tests, keep one distinct angle per test. Trigger on 'write tests for', 'unit test this view model', 'test the validator', 'fake client', '@Test', '#expect', 'what edge cases am I missing', 'review these tests'. Not for TCA TestStore mechanics (use tca) or Swift Testing API detail (use swift-testing-expert)."
argument-hint: "[type or file under test]"
---

# iOS Testing

Write tests as an adversary paid to make the code produce a wrong answer, crash, hang, or corrupt its state. Assume a bug is there; find the input, ordering, or collaborator response that exposes it.

**Framework: Swift Testing first.** Use `@Test`, `#expect`, `#require`, parameterized `arguments:`, traits and tags. Use XCTest only for UI tests (`XCUIApplication`), performance metrics, and files in a legacy XCTest-only target. Follow the module's existing style when it is mixed (`ios-conventions testing`). API detail (expectations, traits, parameterization, `confirmation`, parallelism, XCTest migration) lives in [swift-testing-expert](../community/swift-testing-expert/SKILL.md); read it instead of working from memory. Code samples for this method: [testing-patterns](../../references/testing-patterns.md). TCA reducers: [tca](../tca/SKILL.md) owns `TestStore`.

## Method

1. **Map the attack surface.** List every public function and parameter, every state property and emitted event, every branch of every return value (each thrown error), every collaborator and each outcome it can produce, and every implicit input (injected clock, `Date`, `UUID`, locale, time zone, defaults, environment).
2. **Ask "how would I break this?" for each item.** Write the break vectors as a plain list before any test code. Keep going until the list stops growing. Prompts: what is legal for the type but illegal for the domain? What happens at the boundary and one past it? What if this arrives twice, out of order, or never? What if the collaborator succeeds with nothing useful? What would a careless user paste here?
3. **Keep only distinct angles** (see the redundancy rule), then stop when you cannot name another way to break the unit without changing its public contract. A vector you can name but not observe through the public API means the unit needs an observation point, not that the vector should be dropped.

**Contract first.** Derive vectors from the contract (signature, doc comment, acceptance criteria, the bug report) before reading the implementation. Reading the code first makes you test what it does instead of what it should do.

## Break vectors

Consider every category; skip one consciously, never by forgetting.

- **Text:** empty, whitespace-only, newlines. Grapheme clusters: `"👍🏽".count == 1` but `.utf16.count == 4`; any `NSString` length, `prefix`, or `utf16` slicing can cut a cluster in half. Combining characters (`"é"` as U+00E9 vs `"e\u{301}"`): Swift `==` treats them as equal, `Data`/UTF-8 comparison does not. RTL, CJK, locale case folding (`"ß".uppercased() == "SS"`), control and invisible characters, max length and one past it, strings that look like other types (`"007"`, `"1,5"`).
- **Numbers:** 0, 1, -1, both sides of every boundary. `Int.max + 1` traps (use `addingReportingOverflow` / `&+` deliberately), `abs(Int.min)` traps. `Double.nan != .nan`, `-0.0`, `0.1 + 0.2`; money in `Double` is a design flag, prefer `Decimal`. Unit confusion: seconds vs milliseconds, percent as 0.5 vs 50.
- **Collections:** empty, one, page size, page size + 1, duplicates, unsorted where sorted is assumed, sort ties, a very large input on an O(n²) path.
- **Time:** an injected clock that returns the same instant twice or goes backwards; DST days (23 h / 25 h), Feb 29, year rollover, `Date(timeIntervalSince1970: 0)`, exactly at expiry (`expiresAt == now`), `Calendar`/`TimeZone` mismatch between stored and displayed values.
- **Ordering and lifecycle:** double-tap (the same action twice), an action while a request is in flight, a stale response that arrives after newer state, cancellation mid-flight then retry, loading → error → retry → success, initial state before any action.
- **Collaborators:** each thrown error individually when they map to different outcomes; success with a degenerate payload (empty array, blank fields); an `AsyncStream` that finishes without emitting or emits the same value twice.

## Redundancy rule

> **Two tests are redundant if one change to the production code would make both fail for the same reason.**

Before keeping a test, name the behavior or branch that only it guards. If you can't, drop it.

| Redundant | Distinct |
|-----------|----------|
| "empty email invalid" + "blank email invalid", one branch handles both | the same pair when the validator trims first, two branches |
| one test per error case when all map to the same message | one test per case when each maps to a different message |
| "loads notes" + "loads notes and shows them" | "loads notes" + "keeps previous notes when refresh fails" |

Use one `@Test(arguments:)` for one angle across many data points (twelve malformed emails, one rejection branch). Do not hide several angles in one parameterized test; each angle deserves its own named test.

## What a unit test is

A unit is a unit of behavior, not a type. A unit test runs in-process and in memory with no I/O: no disk, network, real database, real clock, or real concurrency. It may wire many real types together as long as none crosses those boundaries.

- `LoginViewModel` + real `EmailValidator` + fake `AuthClient` → unit test.
- A repository over an in-memory SwiftData `ModelContainer` → integration test; keep it, label it, keep it fast.

If a collaborator is pure logic and cheap to build, use the real one. Fake only what crosses an I/O boundary.

## Test doubles: fakes first

- Default to **fakes**: working in-memory implementations of a protocol (or a `@Dependency` client struct) with switches for failure modes (`nextError = URLError(.notConnectedToInternet)`). Fakes assert behavior (state, emissions), survive refactors, and are shared across tests.
- A fake must fail the way the real thing fails; one that only succeeds hides bugs.
- Stubs inside a closure-based client (`var fetch: @Sendable () async throws -> [Note]`) count as fakes when they hold behavior, not call-count expectations.
- Hand-written spies are acceptable for a side effect with no observable result (analytics, haptics). Assert the recorded value, not the call count, when state already proves the behavior.
- Wrap framework or third-party classes you cannot subclass (`UNUserNotificationCenter`, `CLLocationManager`) in a thin protocol and fake that.

## Pitfalls

- **`@MainActor`.** Isolate a test (or suite) to `@MainActor` only when the type under test is main-actor-isolated, which is every `@Observable` view model under main-actor default isolation. Elsewhere it hides real concurrency bugs. Isolation errors in tests are the compiler telling you about a real design question; do not silence them with `nonisolated(unsafe)`.
- **No sleeps.** `Task.sleep` and arbitrary waits make tests slow and flaky. Await the operation directly, inject a `Clock` (below), or use `confirmation` for event-style callbacks and `AsyncStream` for multi-fire output.
- **`confirmation` for events.** Set `expectedCount` explicitly, and make sure every `confirm()` happens before the closure returns. Zero is valid (`expectedCount: 0`) for "must never fire".
- **Unstructured `Task { }` in the unit.** A test that returns before the task finishes passes vacuously. Expose the task, or await a deterministic signal (an `AsyncStream` element, a fake that resumes a continuation).
- **Parallel by default.** Swift Testing runs tests in parallel in random order. Shared statics, `UserDefaults.standard`, and singletons leak between tests. Create fresh instances per test; use `.serialized` only as a last resort.
- **`Clock`, `Date`, `UUID` injection.** Take a `any Clock<Duration>` (or `@Dependency(\.continuousClock)`), `now: () -> Date`, and `uuid: () -> UUID` as inputs. Tests then drive time with `TestClock` / `ImmediateClock` from swift-clocks, or a fixed closure. Calling `Date()` or `UUID()` inside the unit makes it untestable at the exact boundaries the Time vectors need.
- **Cancellation.** Cancel the task mid-operation and assert nothing half-applied remains.
- **SwiftData.** Build `ModelContainer(for:configurations: ModelConfiguration(isStoredInMemoryOnly: true))` per test, never the app container. See the reference for the helper.

## What not to test

- Framework behavior: that `Codable` encodes, `List` renders, `@Query` fetches.
- Private members and reflection into storage; test through the public surface.
- Trivial pass-through code with no branch, and generated code (macro expansions).
- Call sequences on a mock when resulting state proves the behavior.
- Pixel layout and SwiftUI view bodies. Test the model behind the view; use previews or snapshot tooling for appearance.
- Exact copy strings that localization owns, unless the contract is the key.

## Anti-patterns

| Anti-pattern | Instead |
|--------------|---------|
| Happy path only; ASCII only; mid-range numbers only | walk the break vectors: emoji, boundaries, overflow |
| Several tests that fail on the same one-line change | keep one; spend the rest on new angles |
| Tests written from the implementation | write vectors from the contract first |
| `XCTAssert*` or `XCTestCase` for new logic tests | `#expect` / `#require` in `@Test` |
| `Task.sleep` to wait for async work | await it, inject a clock, or `confirmation` |
| `for` loop over cases inside one test | `@Test(arguments:)` |
| Shared mutable static between tests | fresh instances per test |
| Fake that swallows errors and returns success | mirror real failure modes |

## Output

When asked to write tests, show the break-vector list first (one line each, marked kept / skipped-with-reason), then the tests. When reviewing tests, report missing vectors and redundant pairs by name.
