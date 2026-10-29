---
name: android-testing
description: "Use when writing or reviewing Android/Kotlin unit tests — ViewModels, reducers, validators, mappers, use cases, repositories with fakes, SavedStateHandle restoration, Flow/StateFlow emissions. Applies an adversarial 'how would I break this?' method: enumerate break vectors from the contract before writing tests, keep one distinct angle per test. Trigger on 'write tests for', 'unit test this ViewModel', 'test the validator', 'fake repository', 'Turbine', 'runTest', 'what edge cases am I missing', 'review these tests'. Not for test infrastructure setup or screenshot/E2E tooling (use testing-setup)."
argument-hint: "[class or file under test]"
---

# Android Testing

Write tests as an adversary paid to make the code produce a wrong answer, crash, hang, or corrupt its state. Assume a bug is there; find the input, ordering, or collaborator response that exposes it.

**Stack: detect, don't impose.** Use the test framework, assertion library, and result type the project already uses (`aet-check testing`). JUnit 4 or 5, Truth/AssertK/kotlin.test, Turbine or manual collection — follow the module's existing tests. Mechanics and code samples: `${CLAUDE_PLUGIN_ROOT}/references/testing-patterns.md`. Test infrastructure, instrumented/screenshot/E2E setup: the `testing-setup` skill.

## Method

1. **Map the attack surface.** List every public function and parameter, every state field and emitted event, every branch of every return value (each error variant), every collaborator and each outcome it can produce, and every implicit input (`SavedStateHandle`, injected clock, locale, defaults).
2. **Ask "how would I break this?" for each item.** Write the break vectors down as a plain list before any test code. Keep going until the list stops growing. Prompts: what input breaks the function's assumption? What is legal for the type but illegal for the domain? What happens at the boundary and one past it? What if this arrives twice, out of order, or never? What if the collaborator succeeds with nothing useful? What would a careless user paste here?
3. **Walk the break-vector catalogue** below. Consider every category; skip one consciously, never by forgetting.
4. **Keep only distinct angles** (see the redundancy rule).
5. **Stop** when you cannot name another way to break the unit without changing its public contract. A vector you can name but can't observe through the public API means the unit needs an observation point, not that the vector should be dropped.

**Contract first.** Derive vectors from the contract (signature, KDoc, acceptance criteria, the bug report) before reading the implementation. Reading the code first makes you test what it does instead of what it should do.

## Break-vector catalogue

**Text**
- Empty, whitespace-only, newlines/tabs, leading/trailing spaces.
- Emoji and grapheme clusters: `"👍🏽".length == 4`, `"👨‍👩‍👧‍👦".length == 11`. Any `length` limit, `substring`, truncation, initials, or character counter is suspect — assert a ZWJ sequence is never cut in half and `"😀😀😀"` isn't counted as 6.
- Combining characters: `"é"` (U+00E9) vs `"é"` — equal on screen, unequal as strings. Test equality, dedup, and search with both.
- RTL, CJK, and other scripts; locale case folding (Turkish `ı`; `"ß".uppercase() == "SS"` changes length).
- Max length exactly, one below, one above; 10k-char input.
- Control and invisible characters (U+0000, U+200B, U+202E); homoglyphs where uniqueness matters.
- Strings that look like other types: `"007"`, `"1e5"`, `"NaN"`, `"1,5"` vs `"1.5"`, `"  12  "`.

**Numbers**
- 0, 1, -1, and both sides of every domain boundary.
- **Overflow:** `Int.MAX_VALUE + 1` wraps to negative with no exception. Sums, counters, `page * pageSize`, byte totals, millis durations. `abs(Int.MIN_VALUE)` is negative.
- Negative modulo (`-7 % 3 == -1`), integer division truncation, division by zero (`Int` throws, `Double` gives `Infinity`).
- Floating point: **`NaN != NaN`** (breaks `equals`, `distinctUntilChanged`, sorting, `contains`), `-0.0` vs `0.0`, `0.1 + 0.2 != 0.3`. Money in a `Double` is a design flag.
- Unit confusion: seconds vs millis, percent as 0.5 vs 50.

**Collections**
- Empty, one, exactly page size, page size + 1; duplicates; all equal; unsorted where sorted is assumed; sort ties.
- Nulls inside a "non-null" list from deserialization; very large inputs on an O(n²) path.

**Time**
- A fake clock returning the same instant twice; a clock that **goes backwards** (NTP correction).
- DST days (23 h / 25 h), Feb 29, year rollover, epoch 0, far future.
- Exactly at expiry (`expiresAt == now`); timezone mismatch between stored and displayed values.

**Ordering, state, lifecycle**
- **Double-tap:** the same action twice in a row (submit, pay, delete).
- An action while a request is already in flight.
- **Stale response:** a slow result arriving after the state moved on must not overwrite newer state.
- Cancellation mid-flight, then retry; loading → error → retry → success.
- Initial state before any action; restoration from `SavedStateHandle` after process death, including mid-flow.

**Collaborators**
- Every error variant individually when they map to different outcomes.
- The collaborator throwing instead of returning an error; success with a degenerate payload (empty list, blank fields); a `Flow` that completes without emitting or emits the same value twice.

## Redundancy rule

> **Two tests are redundant if one change to the production code would make both fail for the same reason.**

Before keeping a test, name the behavior or branch that only it guards. If you can't, drop it.

| Redundant | Distinct |
|-----------|----------|
| "empty email invalid" + "blank email invalid", one branch handles both | the same pair when the validator trims first — two branches |
| one test per error variant when all map to the same message | one test per variant when each maps to a different message |
| "loads notes" + "loads notes and shows them" | "loads notes" + "keeps previous notes when refresh fails" |

Use a parameterized test for one angle across many data points (twelve malformed emails, one rejection branch). Don't hide several angles in one parameterized test — each angle deserves a name.

## What a unit test is

A **unit is a unit of behavior, not a class.** A unit test runs in-process and in memory with no I/O: no disk, network, database, real clock, or real concurrency. It may wire many real classes together as long as none crosses those boundaries.

- `LoginViewModel` + real `LoginValidator` + real `EmailNormalizer` + fake `AuthRepository` → unit test.
- `UserDao` on in-memory Room, or a repository over `MockWebServer` → integration test.

If a collaborator is pure logic and cheap to build, use the real one. Fake only what crosses an I/O boundary.

## Test doubles: fakes first

- Default to **fakes**: working in-memory implementations of the interface, with switches for failure modes (`nextError = DataError.Network.NO_INTERNET`). Fakes assert behavior (state, emissions), survive refactors, and are shared across tests (`core:testing`).
- A fake must fail the way the real thing fails; one that only ever succeeds hides bugs.
- **Mocks are allowed** for final framework or third-party classes you can't subclass and don't own, and for a side effect with no observable result. Prefer a thin wrapper interface you can fake when the class is used in many places.
- Don't assert call counts on a fake when the resulting state already proves the behavior.

## SavedStateHandle

Build it directly; never mock it.

```kotlin
val handle = SavedStateHandle(mapOf("title" to "Draft", "body" to "Half-written"))
val viewModel = EditNoteViewModel(handle, FakeNoteRepository())
// assert restored state equals what the user typed before process death
```

Test both directions: input written to the handle on change, and state restored from a pre-filled handle. For Nav 2 routes, build the handle from the route the screen receives.

## Coroutines

- `runTest` for every suspending test; `Dispatchers.setMain(testDispatcher)` for ViewModels (or the project's main-dispatcher rule).
- Inject a dispatcher only into classes that switch dispatchers *and* are unit-tested.
- No `Thread.sleep` or real `delay`; use virtual time (`advanceTimeBy`, `advanceUntilIdle`) and a fake clock.
- Cancellation is a vector: cancel the scope mid-operation and assert nothing half-applied remains.

## Anti-patterns

| Anti-pattern | Instead |
|--------------|---------|
| Happy path only; ASCII only; mid-range numbers only | walk the catalogue: emoji, boundaries, overflow |
| Several tests that fail on the same one-line change | keep one; spend the rest on new angles |
| Tests written from the implementation | write vectors from the contract first |
| `verify { … }` on call patterns | assert resulting state or emissions via a fake |
| Shared mutable state between tests | fresh instances per test |
| Reflection into private fields | test through the public surface |
| Fake that swallows exceptions and returns success | mirror real failure modes |

## Output

When asked to write tests, show the break-vector list first (one line each, marked kept / skipped-with-reason), then the tests. When reviewing tests, report missing vectors and redundant pairs by name.
