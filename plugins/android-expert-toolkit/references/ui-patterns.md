# UI Patterns

Extracted from SKILL.md for progressive disclosure. Referenced when the agent needs detailed Compose, navigation, and UI implementation guidance.

## When to use

Read this reference when implementing UI at a structural level: route/screen separation, navigation setup, or screen organization. Used by android-developer and compose-expert for general UI composition. For deep Compose-specific patterns (interop, performance, state hoisting), see `compose-patterns.md`.

## Jetpack Compose Best Practices

For comprehensive Compose patterns and implementation details, see **compose-expert** subagent.

### Quick Reference

**Core Patterns:**
- Route/Screen separation (stateful container + stateless screen)
- StateFlow collection with `collectAsStateWithLifecycle()`
- Material 3 components with dynamic theming
- Adaptive UI with WindowSizeClass
- Performance optimization (remember, key, derivedStateOf)

**When to Use compose-expert:**
- Implementing complex Compose UI screens
- Material 3 design system integration
- Custom layouts and animations
- Accessibility requirements (WCAG AA compliance)
- Performance optimization and profiling
- Compose-View interoperability patterns

## Navigation (Modern Pattern)

### Type-Safe Navigation (Navigation 3)

```kotlin
// Navigation routes
@Serializable
object HomeRoute

@Serializable
data class DetailRoute(val id: String)

// Navigation setup
NavHost(navController, startDestination = HomeRoute) {
    composable<HomeRoute> {
        HomeScreen(onNavigateToDetail = { id ->
            navController.navigate(DetailRoute(id))
        })
    }

    composable<DetailRoute> { backStackEntry ->
        val route = backStackEntry.toRoute<DetailRoute>()
        DetailScreen(id = route.id)
    }
}
```

## Performance Optimization

### Baseline Profile
- Generates ahead-of-time compilation hints
- Improves cold startup by 20-30%
- Run benchmark tests to generate profile

### Compose Performance
- See **compose-expert** for comprehensive performance optimization patterns

### Build Performance
- Gradle configuration cache enabled
- Module parallel compilation
- Convention plugins reduce build graph complexity
- KSP instead of kapt (2-3x faster)

## Observability & Monitoring

### Structured Logging with Timber

```kotlin
// Application setup
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        } else {
            Timber.plant(CrashlyticsTree())
            Timber.plant(AnalyticsTree())
        }
    }
}

// Crashlytics tree
class CrashlyticsTree : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        if (priority < Log.INFO) return

        Firebase.crashlytics.apply {
            setCustomKey("priority", priority)
            setCustomKey("tag", tag ?: "")
            setCustomKey("message", message)

            if (t != null) {
                recordException(t)
            } else if (priority >= Log.ERROR) {
                recordException(Exception(message))
            } else {
                log(message)
            }
        }
    }
}

// Analytics tree
class AnalyticsTree : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
        if (priority >= Log.WARN) {
            Firebase.analytics.logEvent("app_log") {
                param("level", priority.toString())
                param("tag", tag ?: "")
                param("message", message.take(100))
            }
        }
    }
}
```

### Custom Performance Metrics

```kotlin
object PerformanceMetrics {
    private val metrics = mutableMapOf<String, Long>()

    fun recordMetric(name: String, value: Long) {
        metrics[name] = value

        Firebase.performance.newTrace(name).apply {
            putMetric("value", value)
            start()
            stop()
        }

        Firebase.analytics.logEvent("performance_metric") {
            param("metric_name", name)
            param("metric_value", value.toDouble())
        }
    }

    inline fun <T> measureTime(name: String, block: () -> T): T {
        val startTime = System.currentTimeMillis()
        return block().also {
            val duration = System.currentTimeMillis() - startTime
            recordMetric(name, duration)
        }
    }

    fun trackScreenLoad(screenName: String, durationMs: Long) {
        recordMetric("${screenName}_load_time", durationMs)
        if (durationMs > 2000) {
            Timber.w("Slow screen load: $screenName took ${durationMs}ms")
        }
    }
}

// Usage in Composable
@Composable
fun ProfileRoute(viewModel: ProfileViewModel = hiltViewModel()) {
    val loadStartTime = remember { System.currentTimeMillis() }

    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(uiState) {
        if (uiState is ProfileUiState.Success) {
            val loadTime = System.currentTimeMillis() - loadStartTime
            PerformanceMetrics.trackScreenLoad("Profile", loadTime)
        }
    }

    ProfileScreen(uiState = uiState)
}
```

### Health Checks

```kotlin
interface HealthCheck {
    suspend fun check(): HealthStatus
}

data class HealthStatus(
    val healthy: Boolean,
    val message: String,
    val metrics: Map<String, Any> = emptyMap(),
)

class DatabaseHealthCheck @Inject constructor(
    private val database: AppDatabase,
) : HealthCheck {
    override suspend fun check(): HealthStatus = try {
        database.openHelper.writableDatabase.query("SELECT 1")
        HealthStatus(
            healthy = true,
            message = "Database accessible",
            metrics = mapOf(
                "version" to database.openHelper.readableDatabase.version,
            ),
        )
    } catch (e: Exception) {
        HealthStatus(
            healthy = false,
            message = "Database unreachable: ${e.message}",
        )
    }
}

class NetworkHealthCheck @Inject constructor(
    private val apiService: ApiService,
    private val networkMonitor: NetworkMonitor,
) : HealthCheck {
    override suspend fun check(): HealthStatus {
        if (!networkMonitor.isOnline) {
            return HealthStatus(healthy = false, message = "No network connection")
        }

        return try {
            withTimeout(5000) {
                apiService.healthCheck()
            }
            HealthStatus(healthy = true, message = "API reachable")
        } catch (e: Exception) {
            HealthStatus(healthy = false, message = "API unreachable: ${e.message}")
        }
    }
}

// Aggregate health check
class SystemHealthChecker @Inject constructor(
    private val healthChecks: Set<@JvmSuppressWildcards HealthCheck>,
) {
    suspend fun checkAll(): Map<String, HealthStatus> {
        return healthChecks.associate { check ->
            check::class.simpleName!! to check.check()
        }
    }
}
```
