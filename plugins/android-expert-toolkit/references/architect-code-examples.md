# Architect Code Examples

Code examples and implementation snippets for the android-architect agent.

## When to use

Read this reference when authoring or illustrating architectural patterns in the blueprint (state management contracts, repository interfaces, DI module scaffolding). Used by android-architect during blueprint creation. For downstream implementation code, prefer `developer-patterns.md`.

## State Management Pattern

```kotlin
// UI State (sealed interface)
sealed interface FeatureUiState {
    data object Loading : FeatureUiState
    data class Error(val message: String) : FeatureUiState
    data class Success(val data: Data) : FeatureUiState
}

// ViewModel (reactive state)
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository,
) : ViewModel() {

    val uiState: StateFlow<FeatureUiState> =
        repository.dataFlow
            .map { FeatureUiState.Success(it) }
            .catch { emit(FeatureUiState.Error(it.message ?: "Unknown")) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = FeatureUiState.Loading,
            )

    fun onAction(action: Action) {
        viewModelScope.launch {
            repository.performAction(action)
        }
    }
}
```

## Data Flow Architecture

```
User Action -> Composable -> ViewModel -> Repository -> DataSource -> Room/Retrofit
                                                                         |
User sees update <- Composable <- ViewModel <- Flow <- Repository <- Flow <- Room/Retrofit
```

## Multi-Module Navigation

```kotlin
// Feature API module (navigation contract)
@Serializable
data class FeatureRoute(val id: String)

// Feature Impl module (implementation)
fun NavGraphBuilder.featureGraph(
    onNavigateToOtherFeature: (String) -> Unit,
) {
    composable<FeatureRoute> { backStackEntry ->
        val route = backStackEntry.toRoute<FeatureRoute>()
        FeatureRoute(
            id = route.id,
            onNavigateToOtherFeature = onNavigateToOtherFeature,
        )
    }
}
```

## Offline-First Sync Strategy

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val repository: Repository,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = try {
        repository.sync()
        Result.success()
    } catch (e: Exception) {
        if (runAttemptCount < 3) Result.retry() else Result.failure()
    }
}
```

## Complex State Composition

```kotlin
val combinedUiState: StateFlow<CombinedUiState> =
    combine(
        repo1.dataFlow,
        repo2.dataFlow,
        repo3.dataFlow,
    ) { data1, data2, data3 ->
        CombinedUiState(data1, data2, data3)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = CombinedUiState.Loading,
    )
```

## Decision Council Protocol - Example Decision

```markdown
## Decision: State Management Pattern for Profile Feature

### Status Quo Advocate's Position:
"The codebase uses LiveData in 47 ViewModels across 12 modules.
Introducing StateFlow creates inconsistency and maintenance burden.

Current usage:
- 47 ViewModels use LiveData
- Team has 2 years LiveData experience
- Code review patterns established
- Zero production issues with current approach

If we match existing pattern:
- Zero learning curve for team
- Consistent with code reviews
- No migration documentation needed
- Lower risk of bugs from unfamiliar patterns
- Feature can ship faster"

### Best Practices Advocate's Position:
"StateFlow is the modern Kotlin-first approach recommended by Google
since 2021. LiveData is maintenance mode.

Technical benefits:
- Type-safe empty states (no null handling)
- Better coroutine integration
- More composable with other Flows
- Superior testing story with Turbine
- Cold Flow semantics prevent subscription leaks

Long-term value:
- Aligns with Android platform direction
- Better performance (no main thread posting)
- This feature is greenfield - ideal opportunity
- Sets foundation for eventual migration"

### Pragmatic Synthesis:
Both perspectives are valid. Constraint analysis:

Timeline: 3 weeks (moderate pressure)
Team: 4 developers, 2 seniors familiar with Flow
Risk: Medium visibility feature (10K daily users)
Business: Profile is key retention feature

Recommendation: Use StateFlow with guardrails
1. This feature is isolated (no ViewModel dependencies)
2. Team has moderate Flow experience
3. Provides learning opportunity without high risk
4. Document pattern for future reference

Incremental path:
- Phase 1: Use StateFlow for this feature only
- Write team guide with code examples
- Update code review checklist
- Monitor for issues during beta (2 weeks)
- Phase 2: Plan broader migration for Q3 (if successful)

Success criteria:
- Feature ships on time
- No Flow-related production bugs
- Team comfort level increases
- Positive code review feedback

### Decision:
Use StateFlow for profile feature
Document in ADR-042: "StateFlow for New Features"
Create Flow/StateFlow team guide
Schedule Flow lunch-and-learn
Q3 planning: Evaluate broader LiveData->StateFlow migration
Rollback plan: Can revert to LiveData if issues arise
```

## Architecture Review Checklist

```
STRUCTURE
- Module organization follows standard pattern
- Feature API/Impl split properly implemented
- Core modules properly isolated
- No circular dependencies

DATA FLOW
- Repositories expose Flow (not snapshots)
- ViewModels use StateFlow for UI state
- Sealed interfaces model all UI states
- Offline-first pattern implemented

DEPENDENCY INJECTION
- Hilt used throughout
- Constructor injection (no field injection)
- Abstract modules with @Binds
- Test doubles available

TESTING
- Unit tests use test doubles (no mocking)
- Fast test execution (<5s)
- 80%+ coverage for business logic
- Integration tests for critical flows

PERFORMANCE
- Cold startup <2s, warm <1s
- Jank-free UI (60fps)
- Module build times <10s
- Full build <2min (20 modules)

DOCUMENTATION
- Architecture overview documented
- Dependency graph generated
- ADRs written for key decisions
- Onboarding guide available
```
