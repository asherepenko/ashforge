---
name: ios-error-handling
description: "Use when defining or reviewing how an iOS/Swift app handles failures — domain error enums per layer, typed throws, converting errors where they are caught, CancellationError handling in async code, Result at boundaries, TCA effect failures, and mapping errors to user-facing strings. Trigger on 'error handling', 'typed throws', 'throws(', 'swallowing CancellationError', 'try? hides errors', 'catch {}', 'LocalizedError', 'show an error message'. Not for crash diagnosis or Swift Testing of errors (use ios-testing)."
argument-hint: "[file, layer, or error type]"
---

# iOS Error Handling

Expected failures are values with a name. The layer that owns a failure catches it once, converts it into a **closed domain error**, and every layer above works with that type. The UI shows a **localized string** chosen from the error, never `error.localizedDescription` of a raw system error.

**Detect, don't impose.** Use the error style the project already has. Introduce typed throws or a new `Result` wrapper only when the project has none and the user agrees. The rules below hold for every style.

## Rules

1. **Closed error types.** Each failure domain is an enum conforming to `Error`: `NetworkError`, `StorageError`, `PasswordError`. Switch over them without `default:` so adding a case forces every mapping to be updated.
2. **Catch where the error originates.**

   | Error from | Caught in | Becomes |
   |------------|-----------|---------|
   | `URLSession`, `URLError`, `DecodingError` | API client / repository | `NetworkError.*` |
   | SwiftData, Core Data, `FileManager`, Keychain | store / repository | `StorageError.*` |
   | Business rule violation | domain / validator | feature error (`PasswordError.tooShort`) |
   | Platform API in the UI layer (permissions, `openURL`) | presentation | presentation error |

   Upper layers never see raw `URLError` or `NSError` for expected failures.
3. **Catch specific types.** `catch let error as URLError`, `catch is DecodingError`. A bare `catch` is a last resort at a boundary, and it still handles cancellation first (rule 5).
4. **Typed throws is opt-in, not the default.**
5. **Never swallow cancellation.** Task cancellation surfaces as `CancellationError` (thrown by `Task.sleep`, `Task.checkCancellation()`, and most async APIs) or as `URLError(.cancelled)` from `URLSession`. Treating it as a failure shows a bogus error alert and breaks cooperative cancellation.
6. **UI shows localized strings from the error.** See [UI strings](#ui-strings).
7. **`Result` only at boundaries.** Use it to hand an outcome across a callback or to store a completed outcome in state. Inside `async` code, prefer `throws`.
8. **Programming errors still crash.** A broken invariant is a bug. Use `precondition`/`assertionFailure`, not a user-facing error. Never `fatalError` for something the user can recover from (offline, bad input, missing file the user chose).
9. **Log once, at the catching layer,** with `Logger` and the error attached; mark tokens and PII `privacy: .private` (the default for dynamic strings).

   ```swift
   private let logger = Logger(subsystem: "com.example.app", category: "sync")
   logger.error("Sync failed: \(error, privacy: .public)")
   ```

## Typed throws

Syntax: `func load() throws(LoadError) -> Item`, `async throws(LoadError)`, and `do throws(LoadError) { … } catch { /* error is LoadError */ }`. Introduced in SE-0413, available with Swift 6.0 compilers (Xcode 16) in both Swift 5 and Swift 6 language modes; no runtime or deployment-target requirement. Check `swift --version` and the project's tools version before using it.

The thrown type must be the **only** thing the body can throw. Any call to an untyped `throws` function widens the error to `any Error`, so convert it at the call site:

```swift
func load() async throws(LoadError) -> Item {
    do {
        return try await api.fetch()          // untyped throws
    } catch is CancellationError {
        throw .cancelled
    } catch let error as URLError where error.code == .notConnectedToInternet {
        throw .offline
    } catch {
        throw .server
    }
}
```

The compiler infers a `catch` over mixed sources as `any Error`; the exhaustive `catch` above is what makes the typed signature legal.

**When NOT to use it.** SE-0413 itself says untyped `throws` is better for most code, because typed errors lock the function's failure contract. Use typed throws when:

- the error never leaves the module or package, and the caller will handle every case;
- the function is generic and only forwards errors from a closure (`rethrows`-style, like `Task` and `Result`);
- the code is dependency-free and constrained (Embedded Swift).

Do not adopt it because a function happens to throw one kind of error today. Public API that may grow new sources of failure keeps `throws`.

## Cancellation

```swift
do {
    items = try await repository.items()
} catch is CancellationError {
    throw CancellationError()       // or: return, when the caller is the task owner
} catch {
    state = .failed(error.userMessage)
}
```

- Put the cancellation catch **before** any catch-all, or rethrow it from inside it with `try Task.checkCancellation()`.
- At the top of a task nobody awaits (a `.task {}` modifier, a `Task {}` fire-and-forget), cancellation ends quietly: no state change, no alert.
- `try?` on an async call also swallows `CancellationError`. Use it only when the result truly does not matter.
- Cancellation does not stop code by itself. Long loops call `try Task.checkCancellation()` or check `Task.isCancelled`.

## UI strings

Domain errors conform to `LocalizedError` and return strings from the string catalog. The UI renders those, never the system error text.

```swift
extension NetworkError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .offline: String(localized: "error.offline", defaultValue: "You're offline.")
        case .unauthorized: String(localized: "error.session_expired", defaultValue: "Your session expired.")
        case .server: String(localized: "error.server", defaultValue: "Something went wrong on our side.")
        }
    }
    var recoverySuggestion: String? {
        switch self {
        case .offline: String(localized: "error.offline.recovery", defaultValue: "Check your connection and try again.")
        default: nil
        }
    }
}
```

- State holds the domain error (or a `LocalizedStringResource`), not a pre-rendered `String`, so the view localizes at render time.
- A raw `URLError`/`NSError` reaching `localizedDescription` is device- and OS-dependent. Map it in the catching layer first.
- Retry is an action the view sends; error state stores no closure.

## TCA effects

Handle failures inside the effect, and send a typed failure action. Details of `.run`, cancellation IDs and `TestStore` live in [tca](../tca/SKILL.md); do not restate them here.

```swift
case .load:
    return .run { send in
        do {
            await send(.loaded(.success(try await client.items())))
        } catch is CancellationError {
            return
        } catch {
            await send(.loaded(.failure(NetworkError(error))))
        }
    }
```

- `.run(operation:catch:)` is the same idea: its `catch` closure receives everything the operation throws, **including `CancellationError`**, so check for it first.
- Use `Result<Value, NetworkError>` in the response action. `TaskResult` is deprecated since TCA 1.4 (soft); keep it only when the project's pinned version predates that and the tca skill's version check says so.
- Map to a domain error in the effect, so reducer state never holds `any Error`.

## Flag in review

- `try?` that discards an error the caller or user should hear about (network, save, decode of required data).
- `catch {}` or `catch { print(error) }`: the failure vanishes or reaches only the console. Use `Logger` plus a state change.
- A catch-all around `await` code that does not handle `CancellationError`, so cancelled work shows an alert or flips state to `.failed`.
- `fatalError`/`preconditionFailure` for a recoverable failure (offline, bad input, missing file).
- `try!` outside tests and previews.
- `error.localizedDescription` or `"\(error)"` shown to the user.
- `throws(E)` on a public function whose failure sources are likely to grow, or a typed signature that only compiles because a `catch` hides an untyped call.
- Several errors returned as `[Error]` or `Error?` plus a flag instead of one typed value.

## Review checklist

- [ ] Each catch converts to a named case; nothing returns `nil` or `[]` to mean "failed".
- [ ] `switch` over errors has no `default:`.
- [ ] `CancellationError` is handled before any catch-all.
- [ ] UI state holds a domain error or localized resource, not a raw `Error`.
- [ ] Tests cover each error case that maps to a distinct outcome, and a collaborator that throws (`/ios-testing`).

Related: pattern detection → [ios-conventions](../ios-conventions/SKILL.md).

## Done means

- Findings cite file and line for each rule broken, or state that the sweep found none.
- Any code change was compiled or tested, and the command and its exit code are shown.
