# Observability

## When to use

Read when adding logging, crash reporting, analytics events, or custom performance traces. Match the project's existing logger and crash reporter.

## Logging

```kotlin
class App : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.DEBUG) Timber.plant(Timber.DebugTree()) else Timber.plant(CrashReportingTree())
    }
}

class CrashReportingTree : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        if (priority < Log.INFO) return
        crashReporter.log("$tag: $message")                 // breadcrumb
        if (t != null && priority >= Log.ERROR) crashReporter.recordNonFatal(t)
    }
}
```

- Log once, where the error is caught and typed (`android-error-handling`); attach the throwable.
- Never log tokens, credentials, full request/response bodies, or PII. Release builds drop `DEBUG`/`VERBOSE`.
- Don't record a non-fatal for expected failures (offline, 404 on a missing item); they drown real problems. Record them as typed-error counts in analytics if the product needs them.
- `CancellationException` is not an error; never report it.

## Crash reporting

- Set user-independent custom keys that help triage (screen, feature flag variant, build flavor); no personal data.
- Upload the R8 mapping file per release so stack traces deobfuscate.
- ANR traces and clusters → `anr-audit-and-fix` skill.

## Performance traces

```kotlin
inline fun <T> trace(name: String, block: () -> T): T {
    val start = SystemClock.elapsedRealtime()            // monotonic: not affected by wall-clock changes
    return try { block() } finally { perfReporter.record(name, SystemClock.elapsedRealtime() - start) }
}
```

- Measure durations with a monotonic clock (`SystemClock.elapsedRealtime()` / `System.nanoTime()`), never `System.currentTimeMillis()` — wall time can jump backwards.
- Screen "time to content": start in the Route when it enters composition, stop on the first `Success` state; call `reportFullyDrawn()` for the launch screen.
- `androidx.tracing` `trace("section") { }` sections show up in system traces for the `android-profiler` skill.
- Production monitoring of startup, ANR, and crash rates: Play vitals (`performance.md`).

## Analytics events

- One typed event API (`sealed interface AnalyticsEvent`) mapped to the vendor in one place; features don't call the SDK directly.
- Event names and params are a contract with analysts: version changes, don't rename silently.
- Fake the analytics interface in tests and assert the events a behavior emits when the event is the requirement.
