# Performance

## When to use

Read when setting performance goals, adding Baseline Profiles or Macrobenchmarks, or deciding which tool to reach for. Measure before and after any optimization; no "faster" without numbers. Hand off to official skills:

| Problem | Skill |
|---------|-------|
| Compose recomposition, stability, lazy-list jank, `remember` misuse | `jetpack-compose-performance` |
| Recording and reading traces, heap dumps, CPU/memory profiles | `android-profiler` |
| ANR risk audit, ANR stack dumps | `anr-audit-and-fix` |
| APK size, keep rules, shrinking | `r8-analyzer` |

## Targets that matter

Use Google Play's Android vitals thresholds as the floor (developer.android.com, *Android vitals*):

| Metric | Bad behavior threshold |
|--------|------------------------|
| User-perceived crash rate | ≥ 1.09% of daily active users overall; ≥ 8% on a single device model |
| User-perceived ANR rate | ≥ 0.47% of daily active users overall; ≥ 8% on a single device model |
| Excessive startup | cold ≥ 5 s, warm ≥ 2 s, hot ≥ 1.5 s |

Product targets should sit well inside these. Set them per app from measured baselines (Macrobenchmark on a mid-range device, Play vitals percentiles), not from generic numbers.

Compose: don't chase a recomposition count or a per-recomposition millisecond budget. Strong skipping mode is the default; follow the `jetpack-compose-performance` rules (defer state reads, stable lazy keys, avoid backwards writes, don't sprinkle `@Stable`/`ImmutableList`) and judge results by frame timing in a release build.

## Baseline Profiles

AOT hints for startup and critical journeys. One generator module per app.

```kotlin
// :baselineprofile module
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    @get:Rule val rule = BaselineProfileRule()

    @Test fun generate() = rule.collect(packageName = "com.example.app", includeInStartupProfile = true) {
        pressHome()
        startActivityAndWait()
        device.findObject(By.res("item_list")).fling(Direction.DOWN)   // critical journey
        device.waitForIdle()
    }
}
```

- Apply the `androidx.baselineprofile` Gradle plugin to the app and the generator module; generate with `./gradlew :app:generateBaselineProfile` on a device or Gradle Managed Device.
- Commit the generated `baseline-prof.txt`; regenerate after large UI changes.
- Library modules can ship their own profiles.
- Verify the gain with a Macrobenchmark comparing `CompilationMode.None()` against `CompilationMode.Partial(BaselineProfileMode.Require)`.

## Macrobenchmark

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule val rule = MacrobenchmarkRule()

    @Test fun coldStartup() = rule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        iterations = 10,
        startupMode = StartupMode.COLD,
        compilationMode = CompilationMode.Partial(),
    ) {
        pressHome()
        startActivityAndWait()
    }
}
```

- Run on a physical mid-range device or a Gradle Managed Device, release-like build (`benchmark` build type, minified, not debuggable).
- `FrameTimingMetric` for scroll and animation journeys; compare P50/P90/P99 before and after.
- Report the numbers with the change; a single run is not a baseline.

## Runtime hygiene

- Nothing slow on the main thread: disk, network, JSON parsing of large payloads, bitmap decoding.
- `reportFullyDrawn()` after the first meaningful content loads, so startup metrics reflect what users see.
- Defer SDK initialization; App Startup library or lazy init instead of everything in `Application.onCreate`.
- Lazy lists: stable `key`, `contentType`, no heavy work in item composables.
- Images sized to their container (Coil does this when the size is known).

## Build performance

Configuration cache, build cache, parallel execution, KSP instead of kapt, convention plugins, and non-transitive R classes — see `gradle-build-config.md`. Measure with `--scan` or `--profile` before and after.

## Monitoring

Watch Play vitals (crash, ANR, startup, excessive wake-ups) per release and per device model; alert on a regression against the previous release, not against a fixed number. Crash/ANR traces → `anr-audit-and-fix`; local investigation → `android-profiler`.
