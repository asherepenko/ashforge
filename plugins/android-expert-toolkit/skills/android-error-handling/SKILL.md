---
name: android-error-handling
description: "Use when defining or reviewing how an Android/Kotlin app handles failures — typed error hierarchies, converting exceptions at the layer that catches them, Result/Either wrappers, try/catch around suspend calls, CancellationException handling, and mapping errors to user-facing strings. Trigger on 'error handling', 'typed errors', 'DataError', 'catch (e: Exception)', 'swallowing CancellationException', 'show an error message', 'map error to string', 'Unknown error'. Not for crash/ANR diagnosis (use anr-audit-and-fix or android-profiler)."
argument-hint: "[file, layer, or error type]"
---

# Android Error Handling

Expected failures are values, not exceptions. The layer that owns a failure catches it once, converts it into a **closed, typed error**, and every layer above works with that type. The UI shows a **string resource** chosen from the error, never `Throwable.message`.

**Detect, don't impose.** Use the result type the project already has — a custom `Result<T, E>`, `kotlin.Result`, Arrow `Either`, or a sealed outcome per call (`android-conventions`). Introduce a new wrapper only when there is none and the user agrees. The rules below hold for all of them.

## Rules

1. **Closed error types.** Each failure domain is a sealed interface or enum the compiler can check exhaustively: `DataError.Network`, `DataError.Local`, `PasswordError`. No `else ->` branches in `when` over them, so adding a variant forces every mapping to be updated.
2. **Catch where the exception originates.**

   | Exception from | Caught in | Becomes |
   |----------------|-----------|---------|
   | HTTP client, socket, serialization | data source / repository | `DataError.Network.*` |
   | SQLite, disk, DataStore `IOException` | data source / repository | `DataError.Local.*` |
   | Business rule violation | domain / validator | feature error (`PasswordError.TooShort`) |
   | Platform API in the UI layer (intent resolution, permission) | presentation | presentation error |

   Upper layers never see raw exceptions for expected failures.
3. **Catch specific types.** `IOException`, `HttpException`, `SerializationException`, `SQLiteException`. A catch-all is a last resort at a boundary.
4. **Never swallow `CancellationException`.** Coroutine cancellation is an exception; catching it as a failure keeps cancelled work running and corrupts structured concurrency.

   ```kotlin
   try {
       Result.Success(api.fetch())
   } catch (e: CancellationException) {
       throw e
   } catch (e: IOException) {
       Result.Error(DataError.Network.NO_INTERNET)
   }
   ```

   If you must write `catch (e: Exception)` (or `Throwable`, or `runCatching` around a suspend call), rethrow cancellation first: `if (e is CancellationException) throw e`. `runCatching { suspendCall() }` swallows cancellation — avoid it for suspend calls or rethrow from the failure branch.
5. **One error per result.** A result carries a single error value. Validation that must report several problems returns a dedicated type (`Set<FieldError>`), not a list smuggled into a generic error.
6. **UI state holds resource references, not messages.** Map each user-visible error to a string resource in the presentation layer:

   ```kotlin
   fun DataError.toUiText(): UiText = when (this) {
       DataError.Network.NO_INTERNET -> UiText.StringResource(R.string.error_no_internet)
       DataError.Network.UNAUTHORIZED -> UiText.StringResource(R.string.error_session_expired)
       DataError.Network.SERVER_ERROR -> UiText.StringResource(R.string.error_server)
       DataError.Local.DISK_FULL -> UiText.StringResource(R.string.error_disk_full)
       // … every variant, no else
   }
   ```

   Place the mapping in the feature's presentation code (feature errors) or a shared presentation module (shared errors). Errors never shown to users need no mapping. Not `it.message ?: "Unknown error"`: exception messages aren't localized, leak internals, and differ by device and library version.
7. **Retry is an action.** Recoverable errors render a retry control that dispatches an action to the ViewModel; error state never stores a `() -> Unit`.
8. **Programming errors still crash.** `IllegalStateException` from a broken invariant, `NullPointerException`, and similar bugs are not converted into user errors; let them reach the crash reporter. Catch-alls at the top of a flow should log and rethrow or report, not hide.
9. **Log once, at the catching layer,** with the exception attached; never log tokens or PII.

## Review checklist

- [ ] No `catch (e: Exception)` / `runCatching` around suspend code that lets `CancellationException` through as a failure.
- [ ] Each catch converts to a named error variant; nothing returns `null` or `emptyList()` to mean "failed".
- [ ] `when` over error types has no `else`.
- [ ] UI state contains `UiText`/`@StringRes`, never `Throwable` or `.message`.
- [ ] Tests cover each error variant that maps to a distinct outcome, plus the collaborator throwing instead of returning (`android-testing` skill).

Related: presentation wiring → `${CLAUDE_PLUGIN_ROOT}/references/presentation.md`; repository `safeCall` example → `${CLAUDE_PLUGIN_ROOT}/references/data-layer.md`.
