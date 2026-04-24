# Performance Targets & SLAs

Extracted from SKILL.md for progressive disclosure. Referenced when the agent needs detailed performance benchmarks and monitoring thresholds.

## When to use

Read this reference when setting performance SLAs, validating benchmarks, or reviewing performance-sensitive code (startup time, memory, battery, frame time). Use both as generation targets (what to aim for when building) and as evaluation criteria (what to check when reviewing).

Production-grade Android apps should meet these benchmarks:

## Startup Performance
- **Cold start**: <2.0s (target: 1.5s)
- **Warm start**: <1.0s
- **Hot start**: <0.5s
- **Time to interactive**: <2.5s

## Runtime Performance
- **Memory baseline**: <100MB (target: 80MB)
- **Memory peak**: <200MB during normal operation
- **Battery drain**: <4% per hour of active use
- **Frame rate**: 60fps minimum (120fps for ProMotion displays)
- **Touch response**: <16ms (1 frame @ 60fps)
- **ANR-free rate**: 100% (zero ANRs tolerated)

## App Size
- **Initial download**: <50MB (target: 40MB)
- **Installed size**: <120MB
- **Asset optimization**: WebP/AVIF for images, vector graphics where possible

## Quality Metrics
- **Crash-free rate**: >99.5% (target: >99.9%)
- **ANR-free sessions**: >99.9%
- **Test coverage**: >80% overall, >90% for business logic
- **API response time**: <200ms p95, <500ms p99
- **Network error recovery**: <3s retry with exponential backoff

## Build Performance
- **Clean build**: <2 minutes (20-module project)
- **Incremental build**: <30 seconds
- **Test execution**: <5 minutes (unit + integration)
- **CI/CD pipeline**: <10 minutes (build + test + deploy)

## Baseline Profiles & Startup Profiles

Baseline Profiles provide ahead-of-time (AOT) compilation hints to the Android runtime, improving cold start time and reducing jank for critical user journeys.

### BaselineProfileRule Setup

```kotlin
// benchmark/src/main/kotlin/com/example/benchmark/BaselineProfileGenerator.kt
@OptIn(ExperimentalBaselineProfilesApi::class)
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {

    @get:Rule
    val rule = BaselineProfileRule()

    @Test
    fun generateBaselineProfile() {
        rule.collect(
            packageName = "com.example.app",
            maxIterations = 5,
            stableIterations = 3,
        ) {
            // Cold start
            pressHome()
            startActivityAndWait()

            // Critical user journeys
            device.findObject(By.text("Items")).click()
            device.waitForIdle()

            device.findObject(By.res("item_list")).scroll(Direction.DOWN, 2f)
            device.waitForIdle()
        }
    }
}
```

### build.gradle.kts Configuration

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.androidx.baselineprofile)
}

android {
    buildTypes {
        release {
            // Baseline profiles are automatically included in release builds
        }
    }
}

dependencies {
    implementation(libs.androidx.profileinstaller)
    baselineProfile(project(":benchmark"))
}

baselineProfile {
    automaticGenerationDuringBuild = true
    saveInSrc = true
}
```

```kotlin
// benchmark/build.gradle.kts
plugins {
    alias(libs.plugins.android.test)
    alias(libs.plugins.androidx.baselineprofile)
}

android {
    namespace = "com.example.benchmark"
    targetProjectPath = ":app"
}
```

### Startup Profile

```kotlin
// Startup profiles optimize classes and methods needed during app startup
@OptIn(ExperimentalBaselineProfilesApi::class)
@RunWith(AndroidJUnit4::class)
class StartupProfileGenerator {

    @get:Rule
    val rule = BaselineProfileRule()

    @Test
    fun generateStartupProfile() {
        rule.collect(
            packageName = "com.example.app",
            includeInStartupProfile = true,
        ) {
            pressHome()
            startActivityAndWait()
            // Only measure startup — no further interactions
        }
    }
}
```

### Cold Start Measurement with Macrobenchmark

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {

    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun startupCompilationNone() = startup(CompilationMode.None())

    @Test
    fun startupCompilationBaselineProfile() =
        startup(CompilationMode.Partial(baselineProfileMode = BaselineProfileMode.Require))

    private fun startup(compilationMode: CompilationMode) {
        benchmarkRule.measureRepeated(
            packageName = "com.example.app",
            metrics = listOf(StartupTimingMetric()),
            iterations = 10,
            startupMode = StartupMode.COLD,
            compilationMode = compilationMode,
        ) {
            pressHome()
            startActivityAndWait()
        }
    }
}
```

### Version Catalog

```toml
[versions]
androidx-benchmark = "1.3.3"
androidx-profileinstaller = "1.4.1"

[libraries]
androidx-profileinstaller = { group = "androidx.profileinstaller", name = "profileinstaller", version.ref = "androidx-profileinstaller" }

[plugins]
androidx-baselineprofile = { id = "androidx.baselineprofile", version.ref = "androidx-benchmark" }
```

## Monitoring Thresholds
- **Critical alerts**: Crash rate >1%, ANR rate >0.1%
- **Warning alerts**: Memory >150MB, startup >2.5s, battery >5%/hour
- **Performance regression**: >10% degradation in any metric
