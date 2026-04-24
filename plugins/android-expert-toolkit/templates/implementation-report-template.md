---
agent: android-developer
feature: "{feature_slug}"
timestamp: "{run_timestamp}"
files_created: []
files_modified: []
dependencies_added: []
interfaces_exposed: []
---

# Implementation Report: [FEATURE NAME]

```yaml
Written by: [AGENT NAME]
Timestamp: [ISO 8601 - e.g., 2026-02-13T10:30:00Z]
```

## Pipeline Context

<!-- Copy verbatim from architecture-blueprint.md Pipeline Context section -->

**Original Prompt:** [Copy from blueprint]

**Business Purpose:** [Copy from blueprint]

**UX Intent:** [Copy from blueprint]

## Summary

**Feature Description:**
[Brief description of what was implemented]

**Modules Modified:**
```
[List of modules where code was added/modified]
feature/[feature-name]/impl/
core/data/
core/database/
```

**Key Components Created:**
- **ViewModels:** [List ViewModels with file paths]
- **Repositories:** [List repositories with file paths]
- **Data Sources:** [List data sources with file paths]
- **Models:** [List data models with file paths]
- **DAOs:** [List DAOs if Room was used]

## Decisions

**State Management:**
```kotlin
// UI State implementation
sealed interface [Feature]UiState {
    data object Loading : [Feature]UiState
    data class Error(val message: String) : [Feature]UiState
    data class Success(val data: [DataType]) : [Feature]UiState
}

// Location: [file path]
```

**ViewModel Implementation:**
```kotlin
// Reactive ViewModel with StateFlow
@HiltViewModel
class [Feature]ViewModel @Inject constructor(
    private val repository: [Repository],
) : ViewModel() {

    val uiState: StateFlow<[Feature]UiState> = /* ... */

    fun onAction(action: [Action]) {
        viewModelScope.launch {
            repository.performAction(action)
        }
    }
}

// Location: [file path]
```

**Repository Implementation:**
```kotlin
// Offline-first repository
class [Feature]RepositoryImpl @Inject constructor(
    private val localDataSource: [LocalDataSource],
    private val remoteDataSource: [RemoteDataSource],
) : [Feature]Repository {

    override val dataFlow: Flow<[DataType]> =
        localDataSource.observeData()
            .map { /* transform */ }

    override suspend fun performAction(action: [Action]) {
        // Write to local first
        localDataSource.save(action.data)
        // Sync to remote opportunistically
        remoteDataSource.sync(action.data)
    }
}

// Location: [file path]
```

## Artifacts Created

**Database Schema:**
```kotlin
// Room entities created/modified
@Entity(tableName = "[table_name]")
data class [Entity](
    @PrimaryKey val id: String,
    val field1: String,
    val field2: Int,
    // [Additional fields]
)

// Location: [file path]
```

**DAO Queries:**
```kotlin
@Dao
interface [Entity]Dao {
    @Query("SELECT * FROM [table_name]")
    fun observeAll(): Flow<List<[Entity]>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: [Entity])

    // [Additional queries]
}

// Location: [file path]
```

**Network API:**
```kotlin
interface [Feature]ApiService {
    @GET("[endpoint]")
    suspend fun getData(): Response<[DataType]>

    @POST("[endpoint]")
    suspend fun postData(@Body data: [DataType]): Response<Unit>
}

// Location: [file path]
```

## Dependency Injection

**Hilt Modules:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class [Feature]DataModule {

    @Binds
    abstract fun bind[Repository](
        impl: [Repository]Impl
    ): [Repository]
}

// Location: [file path]
```

**Provided Dependencies:**
- [Repository] → [RepositoryImpl]
- [DataSource] → [DataSourceImpl]
- [Additional bindings]

## Testing Interfaces

**Repository Interface for Testing:**
```kotlin
// Public interface for test doubles
interface [Feature]Repository {
    val dataFlow: Flow<[DataType]>
    suspend fun performAction(action: [Action])
}

// Test double location: core/testing/src/main/kotlin/[path]/Fake[Repository].kt
```

**Test Doubles Needed:**
```kotlin
// Test double interface for android-testing-specialist to implement
class Fake[Repository] : [Repository] {
    private val _data = MutableStateFlow<[DataType]>(/* initial */)

    override val dataFlow: Flow<[DataType]> = _data.asStateFlow()

    override suspend fun performAction(action: [Action]) {
        // Controllable test behavior
    }
}
```

## Build Requirements

**Gradle Dependencies Used:**
```kotlin
dependencies {
    // Hilt
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)

    // Room
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    // Retrofit
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)

    // [Additional dependencies]
}
```

**Minimum SDK Requirements:**
- Min SDK: [version]
- Target SDK: [version]
- Kotlin: [version]

## Verification Steps

**Manual Testing:**
1. [Step-by-step instructions to verify feature works]
2. [Expected behavior at each step]
3. [Edge cases to test]

**Automated Tests:**
```bash
# Run unit tests
./gradlew :[module]:testDebugUnitTest

# Run specific test class
./gradlew :[module]:testDebugUnitTest --tests [TestClassName]
```

**Database Verification:**
```bash
# Inspect database schema
adb pull /data/data/[package]/databases/[db-name] .
sqlite3 [db-name] ".schema"
```

## Known Issues and Limitations

**Current Limitations:**
- [List any known limitations]
- [Temporary workarounds]
- [Future enhancement opportunities]

**Technical Debt:**
- [Document any technical debt introduced]
- [Rationale for trade-offs made]

## Constraints

**Must Follow (for downstream agents):**
- [List architectural constraints from blueprint that must be respected]
- [Pattern choices that cannot be changed (e.g., StateFlow, Hilt)]
- [Module boundaries that must be maintained]
- [Performance targets that must be met]

**Must Not:**
- [List anti-patterns or forbidden approaches]
- [Frameworks that cannot be introduced]
- [Dependencies on other features (feature independence)]

**Example:**
- MUST use StateFlow (not LiveData) - architecture decision
- MUST maintain feature module independence - no feature-to-feature deps
- MUST achieve 80%+ test coverage - quality target
- MUST NOT introduce new DI framework - Hilt is standard

## Next Steps

**For compose-expert:**
1. [Read this report for ViewModel interfaces]
2. [Implement Compose UI using StateFlow]
3. [Wire up user actions to ViewModel]

**For android-testing-specialist:**
1. [Read Testing Interfaces section]
2. [Create test doubles listed above]
3. [Write unit tests for ViewModel and Repository]
4. [Write test-report.md handoff]

**For android-architect:**
1. [Review implementation against architecture-blueprint.md]
2. [Validate architectural patterns followed]
