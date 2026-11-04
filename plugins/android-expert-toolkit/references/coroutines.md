# Coroutines and Flow

## When to use

Read when writing or reviewing suspend functions, scopes, dispatchers, or `Flow` pipelines. Layer placement → `architecture.md`. Typed errors and `catch` blocks → `android-error-handling` skill. Test mechanics (Turbine, fakes) → `testing-patterns.md`.

## Dispatchers

- Main-safe suspend functions: the callee switches with `withContext`, not the caller.
- `Dispatchers.IO` for blocking I/O; `Dispatchers.Default` for CPU work. Room and Retrofit suspend APIs are already main-safe.
- Inject a `CoroutineDispatcher` only into classes that switch dispatchers **and** are unit-tested. ViewModels using `viewModelScope` are covered by `Dispatchers.setMain`.
- Never hardcode `Dispatchers.Main` in a repository or data source.

```kotlin
class FileStore @Inject constructor(
    @IoDispatcher private val io: CoroutineDispatcher,
) {
    suspend fun read(name: String): ByteArray = withContext(io) { /* blocking read */ }
}
```

## Scopes and structured concurrency

- `viewModelScope` for UI work; never `GlobalScope`.
- In a composable, `LaunchedEffect` or `rememberCoroutineScope`. In an Activity or Fragment, `lifecycleScope` with `repeatOnLifecycle(Lifecycle.State.STARTED)` to collect.
- Work that must outlive the screen goes to WorkManager or an injected application-scope `CoroutineScope`, not a leaked job.
- Parallel work: `coroutineScope { async {} }` so one failure cancels the siblings and the caller waits for all.

## Flow

- Cold flows to UI state: `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`. The 5 s window keeps the upstream alive across a configuration change.
- `shareIn` when several collectors need the same hot stream and no current value is needed.
- Prefer `combine` over nested `collect`; `distinctUntilChanged` before expensive mapping.
- `flatMapLatest` for "latest query wins"; `debounce` for typed input.
- `flowOn` changes the upstream dispatcher only. Do not call `withContext` inside `flow {}`.
- Collect in Compose with `collectAsStateWithLifecycle()`.

## Cancellation

- Cancellation is cooperative. Long loops call `ensureActive()` or `yield()`.
- Every catch-all `catch` in a suspend function rethrows `CancellationException`. `runCatching` around a suspend call swallows it; avoid it there.
- Cleanup goes in `finally` or `onCompletion`, not after the suspend call. Suspending cleanup needs `withContext(NonCancellable)`.

```kotlin
try {
    repository.sync()
} catch (e: CancellationException) {
    throw e
} catch (e: IOException) {
    _state.update { it.copy(error = R.string.error_network) }
}
```

## Exceptions

- An uncaught exception in a child cancels the parent and all siblings.
- `supervisorScope` or `SupervisorJob` when one child's failure must not cancel the others.
- `CoroutineExceptionHandler` only works on a root `launch`. It is a last-resort logger, not error handling.
- `async` holds the exception until `await()`; catch it there.
- Flow errors: `catch {}` operator upstream of `collect`; it does not catch errors thrown in the collector.

## Testing

- `runTest` for every coroutine test; it skips `delay`.
- Set `Dispatchers.setMain(StandardTestDispatcher())` in a rule; reset it after.
- Pass the same `TestDispatcher` (via `testScheduler`) to injected dispatchers so one scheduler controls time.
- `StandardTestDispatcher` queues work; drive it with `advanceUntilIdle()` or `runCurrent()`. `UnconfinedTestDispatcher` runs eagerly; use it for collectors that must start first.
- `backgroundScope` for collectors that should not block test completion.

## Review checklist

- [ ] No `GlobalScope`; no hardcoded dispatchers in tested classes.
- [ ] `CancellationException` rethrown from every catch-all; no `runCatching` around suspend calls.
- [ ] UI collects with `collectAsStateWithLifecycle` or `repeatOnLifecycle`.
- [ ] `stateIn` uses `WhileSubscribed` with a timeout unless the stream must stay hot.
- [ ] Tests use `runTest` and a shared `TestDispatcher`.
